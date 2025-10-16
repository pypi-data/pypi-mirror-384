import os
import io
import uuid
import pandas
import logging
import fsspec
from typing import List
from datetime import datetime
from packaging import version
from pandas.io.common import get_handle

import modin.config as cfg
from modin import __version__
from modin.core.execution.ray.implementations.pandas_on_ray.io.io import PandasOnRayIO, RayIO, RayWrapper
from modin.core.execution.ray.implementations.pandas_on_ray.partitioning import PandasOnRayDataframePartition
from modin.core.execution.ray.implementations.pandas_on_ray.dataframe import PandasOnRayDataframe
from modin.core.execution.dispatching.factories.factories import BaseFactory
from modin.core.storage_formats.pandas.query_compiler import PandasQueryCompiler
from modin.core.storage_formats.pandas.parsers import PandasParquetParser

from .dxdispatchers import DXParquetDispatcher


MINIMUM_PART_SIZE = 5 * 2 ** 20 # 5MB
REPARTITION_SIZE = 6 * 2 ** 20 # 6MB

logger = logging.getLogger("dxfs")

class DXPandasOnRayIO(PandasOnRayIO):
    build_args = dict(
        frame_partition_cls=PandasOnRayDataframePartition,
        query_compiler_cls=PandasQueryCompiler,
        frame_cls=PandasOnRayDataframe,
        base_io=RayIO,
    )
    def __make_read(*classes, build_args=build_args):
        
        # used to reduce code duplication
        return type("", (RayWrapper, *classes), build_args).read
    
    def __make_write(*classes, build_args=build_args):
        # used to reduce code duplication
        return type("", (RayWrapper, *classes), build_args).write

    read_parquet = __make_read(PandasParquetParser, DXParquetDispatcher)

    @classmethod
    def get_partition_length(cls, qc, **kwargs):
        def func(df, **kw):
            dev_null_io = open(os.devnull, "w")
            df.to_csv(dev_null_io)
            
            return dev_null_io.tell()

        qc._modin_frame._propagate_index_objs(axis=None)
        result = qc._modin_frame._partition_mgr_cls.map_axis_partitions(
            axis=1,
            partitions=qc._modin_frame._partitions,
            map_func=func,
            keep_partitioning=True,
            lengths=None,
            enumerate_partitions=True,
            max_retries=0,
        )
        # pending completion
        return RayWrapper.materialize(
            [part.list_of_blocks[0] for row in result for part in row]
        )
    
    @classmethod
    def repartition(cls, qc: PandasQueryCompiler, nparts: int) -> PandasQueryCompiler:
        cfg.NPartitions.put(nparts)
        return qc.repartition()

    @classmethod
    def to_csv(cls, qc: PandasQueryCompiler, **kwargs):
        """
        Write records stored in the `qc` to a CSV file.

        Parameters
        ----------
        qc : BaseQueryCompiler
            The query compiler of the Modin dataframe that we want to run ``to_csv`` on.
        **kwargs : dict
            Parameters for ``pandas.to_csv(**kwargs)``.
        """
        from modin.core.execution.ray.implementations.pandas_on_ray.io.io import SignalActor, RayIO
        if not cls._to_csv_check_support(kwargs):
            return RayIO.to_csv(qc, **kwargs)
        
        partition_len: List[int] = cls.get_partition_length(qc, **kwargs)
        logger.debug("Data length of partitions:", partition_len)
        
        has_small_part = any([l < MINIMUM_PART_SIZE for l in partition_len[:-2]])
        logger.debug("Has small partitions:", has_small_part)

        if has_small_part:
            logger.info("fsspec_dnanexus is doing repartitioning DataFrame")
            # get current npartitions
            old_nparts = cfg.NPartitions.get()
            # calculate new npartitions
            # should divide 6MB to make sure each part > 5MB
            new_nparts = sum(partition_len) // REPARTITION_SIZE
            new_nparts = max(new_nparts, 1)
            
            logger.debug("New NPartitions:", new_nparts)
            # repartition with new npartitions
            qc = cls.repartition(qc=qc, nparts=new_nparts)
            # reset npartitions
            cfg.NPartitions.put(old_nparts)

        signals = SignalActor.remote(len(qc._modin_frame._partitions) + 1)
        n_partitions = len(qc._modin_frame._partitions)
        marker_id = str(uuid.uuid4())
        logger.debug("N partitions:", n_partitions)

        def func(df, **kw):  # pragma: no cover
            """
            Dump a chunk of rows as csv, then save them to target maintaining order.

            Parameters
            ----------
            df : pandas.DataFrame
                A chunk of rows to write to a CSV file.
            **kw : dict
                Arguments to pass to ``pandas.to_csv(**kw)`` plus an extra argument
                `partition_idx` serving as chunk index to maintain rows order.
            """
            partition_idx = kw["partition_idx"]
            logger.debug("Partition index:", partition_idx)
            # the copy is made to not implicitly change the input parameters;
            # to write to an intermediate buffer, we need to change `path_or_buf` in kwargs
            csv_kwargs = kwargs.copy()
            if partition_idx != 0:
                # we need to create a new file only for first recording
                # all the rest should be recorded in appending mode
                if "w" in csv_kwargs["mode"]:
                    csv_kwargs["mode"] = csv_kwargs["mode"].replace("w", "a")
                # It is enough to write the header for the first partition
                csv_kwargs["header"] = False

            # for parallelization purposes, each partition is written to an intermediate buffer
            path_or_buf = csv_kwargs["path_or_buf"]
            is_binary = "b" in csv_kwargs["mode"]
            csv_kwargs["path_or_buf"] = io.BytesIO() if is_binary else io.StringIO()
            
            storage_options = csv_kwargs.pop("storage_options") or {}
            storage_options.update({
                "n_partitions": n_partitions,
                "partition_idx": partition_idx,
                "marker_id": marker_id,
                "dx_buffered_cls": "DXBufferedFileOnRay"
            })
            
            df.to_csv(**csv_kwargs)
            
            csv_kwargs.update({"storage_options": storage_options})
            
            content = csv_kwargs["path_or_buf"].getvalue()
            csv_kwargs["path_or_buf"].close()

            # each process waits for its turn to write to a file
            RayWrapper.materialize(signals.wait.remote(partition_idx))

            # preparing to write data from the buffer to a file
            with get_handle(
                path_or_buf,
                # in case when using URL in implicit text mode
                # pandas try to open `path_or_buf` in binary mode
                csv_kwargs["mode"] if is_binary else csv_kwargs["mode"] + "t",
                encoding=kwargs["encoding"],
                errors=kwargs["errors"],
                compression=kwargs["compression"],
                storage_options=storage_options,
                is_text=not is_binary,
            ) as handles:
                handles.handle.write(content)

            # signal that the next process can start writing to the file
            RayWrapper.materialize(signals.send.remote(partition_idx + 1))
            # used for synchronization purposes
            return pandas.DataFrame()

        # signaling that the partition with id==0 can be written to the file
        RayWrapper.materialize(signals.send.remote(0))
        # Ensure that the metadata is syncrhonized
        qc._modin_frame._propagate_index_objs(axis=None)
        result = qc._modin_frame._partition_mgr_cls.map_axis_partitions(
            axis=1,
            partitions=qc._modin_frame._partitions,
            map_func=func,
            keep_partitioning=True,
            lengths=None,
            enumerate_partitions=True,
            max_retries=0,
        )
        # pending completion
        RayWrapper.materialize(
            [part.list_of_blocks[0] for row in result for part in row]
        )

    @classmethod
    def to_parquet(cls, qc, **kwargs):
        """
        Write a ``DataFrame`` to the binary parquet format.

        Parameters
        ----------
        qc : BaseQueryCompiler
            The query compiler of the Modin dataframe that we want to run `to_parquet` on.
        **kwargs : dict
            Parameters for `pandas.to_parquet(**kwargs)`.
        """
        if not cls._to_parquet_check_support(kwargs):
            return RayIO.to_parquet(qc, **kwargs)

        output_path = kwargs["path"]
        storage_options = kwargs.get("storage_options") or {}
        client_kwargs = storage_options.get("client_kwargs", {})
        fs, url = fsspec.core.url_to_fs(output_path, client_kwargs=client_kwargs)

        # if folder already exists
        if fs.isdir(url):
            if not storage_options.get("allow_duplicate_filenames"):
                # remove all files in folder
                # do not remove folder for safety
                fs.remove_files_in_folder(url)
            else:
                # rename existing folder by adding a suffix
                folder_name = os.path.basename(url.rstrip("/"))
                now = datetime.now().strftime('%Y%m%d_%H%M%S')
                new_name = f"{folder_name} copy {now}"
                fs.rename_folder(path=url, new_name=new_name)
        
        fs.mkdirs(url, exist_ok=True)

        def func(df, **kw):
            """
            Dump a chunk of rows as parquet, then save them to target maintaining order.

            Parameters
            ----------
            df : pandas.DataFrame
                A chunk of rows to write to a parquet file.
            **kw : dict
                Arguments to pass to ``pandas.to_parquet(**kwargs)`` plus an extra argument
                `partition_idx` serving as chunk index to maintain rows order.
            """
            compression = kwargs["compression"]
            partition_idx = kw["partition_idx"]
            kwargs[
                "path"
            ] = f"{output_path}/part-{partition_idx:04d}.{compression}.parquet"
            df.to_parquet(**kwargs)
            return pandas.DataFrame()

        # Ensure that the metadata is synchronized
        qc._modin_frame._propagate_index_objs(axis=None)
        result = qc._modin_frame._partition_mgr_cls.map_axis_partitions(
            axis=1,
            partitions=qc._modin_frame._partitions,
            map_func=func,
            keep_partitioning=True,
            lengths=None,
            enumerate_partitions=True,
        )
        # pending completion
        RayWrapper.materialize(
            [part.list_of_blocks[0] for row in result for part in row]
        )

    if version.parse(__version__) >= version.parse("0.21.0"):
        to_parquet = __make_write(DXParquetDispatcher)

    del __make_read  # to not pollute class namespace
    del __make_write  # to not pollute class namespace

class DXPandasOnRayFactory(BaseFactory):
    @classmethod
    def prepare(cls):
        cls.io_cls = DXPandasOnRayIO