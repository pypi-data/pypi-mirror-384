import os
import io
import pandas
import fsspec
from datetime import datetime
from packaging import version
import pandas._libs.lib as lib

from pandas.io.common import stringify_path
from fsspec.core import url_to_fs
from modin.core.io import ParquetDispatcher

from fsspec_dnanexus.core import DXFileSystemException, DXBufferedFile

class DXParquetDispatcher(ParquetDispatcher):

    @classmethod
    def _read(cls, path, engine, columns, use_nullable_dtypes, dtype_backend, **kwargs):
        """
        Load a parquet object from the file path, returning a query compiler.

        Parameters
        ----------
        path : str, path object or file-like object
            The filepath of the parquet file in local filesystem or hdfs.
        engine : {"auto", "pyarrow", "fastparquet"}
            Parquet library to use.
        columns : list
            If not None, only these columns will be read from the file.
        use_nullable_dtypes : Union[bool, lib.NoDefault]
        dtype_backend : {"numpy_nullable", "pyarrow", lib.no_default}
        **kwargs : dict
            Keyword arguments.

        Returns
        -------
        BaseQueryCompiler
            A new Query Compiler.

        Notes
        -----
        ParquetFile API is used. Please refer to the documentation here
        https://arrow.apache.org/docs/python/parquet.html
        """
        if isinstance(path, DXBufferedFile) or isinstance(path, io.BufferedReader):
            import pandas
            from modin.error_message import ErrorMessage
            
            reason = (
                "Passing a file-like object as the input is not appropriate in the distributed cluster context.\n"
                + "Please consider to use a file path or file URL in case of using fsspec."
            )
            ErrorMessage.default_to_pandas("`read_parquet` from file descriptor", reason=reason)
            
            pandas_frame = pandas.read_parquet(
                path=path,
                engine=engine,
                columns=columns,
                use_nullable_dtypes=use_nullable_dtypes,
                dtype_backend=dtype_backend,
                **kwargs)

            return cls.query_compiler_cls.from_pandas(pandas_frame, cls.frame_cls)

        storage_options = kwargs.get("storage_options")
        if storage_options is not None:
            fs, fs_path = url_to_fs(stringify_path(path), **storage_options)
        else:
            fs, fs_path = url_to_fs(stringify_path(path))
        is_file = fs.isfile(fs_path)
        is_dir = fs.isdir(fs_path)

        if is_dir and is_file:
            raise DXFileSystemException("The path is ambiguous. It matches file and folder.")

        from packaging import version
        from modin import __version__ as cur_modin_version
        if version.parse(cur_modin_version) >= version.parse("0.24.0"):
            # Breaking changes from 0.24.0 and 0.24.1
            # ref https://github.com/modin-project/modin/blob/0.24.0/modin/core/io/column_stores/parquet_dispatcher.py#L304
            has_extra_storage_params = (set(kwargs) - {"storage_options", "filters", "filesystem"})
        else:
            # ref https://github.com/modin-project/modin/blob/0.23.1/modin/core/io/column_stores/parquet_dispatcher.py#L593
            has_extra_storage_params = any(arg not in ("storage_options",) for arg in kwargs)

        if (is_file or has_extra_storage_params or use_nullable_dtypes != lib.no_default):
            return cls.single_worker_read(
                path,
                engine=engine,
                columns=columns,
                use_nullable_dtypes=use_nullable_dtypes,
                dtype_backend=dtype_backend,
                reason="Parquet options that are not currently supported",
                **kwargs,
            )
        path = stringify_path(path)

        if isinstance(path, list):
            # TODO(https://github.com/modin-project/modin/issues/5723): read all
            # files in parallel.
            compilers: list[cls.query_compiler_cls] = [
                cls._read(
                    p, engine, columns, use_nullable_dtypes, dtype_backend, **kwargs
                )
                for p in path
            ]
            return compilers[0].concat(axis=0, other=compilers[1:], ignore_index=True)
        if isinstance(path, str):
            if os.path.isdir(path):
                path_generator = os.walk(path)
            else:
                path_generator = fs.walk(fs_path)
            partitioned_columns = set()
            # We do a tree walk of the path directory because partitioned
            # parquet directories have a unique column at each directory level.
            # Thus, we can use os.walk(), which does a dfs search, to walk
            # through the different columns that the data is partitioned on
            for _, dir_names, files in path_generator:
                if dir_names:
                    partitioned_columns.add(dir_names[0].split("=")[0])
                if files:
                    # Metadata files, git files, .DSStore
                    # TODO: fix conditional for column partitioning, see issue #4637
                    if len(files[0]) > 0 and files[0][0] == ".":
                        continue
                    break
            partitioned_columns = list(partitioned_columns)
            if len(partitioned_columns):
                return cls.single_worker_read(
                    path,
                    engine=engine,
                    columns=columns,
                    use_nullable_dtypes=use_nullable_dtypes,
                    dtype_backend=dtype_backend,
                    reason="Mixed partitioning columns in Parquet",
                    **kwargs,
                )

        dataset = cls.get_dataset(path, engine, kwargs.get("storage_options") or {})
        index_columns = (
            dataset.pandas_metadata.get("index_columns", [])
            if dataset.pandas_metadata
            else []
        )
        # If we have columns as None, then we default to reading in all the columns
        column_names = columns if columns else dataset.columns
        columns = [
            c
            for c in column_names
            if c not in index_columns and not cls.index_regex.match(c)
        ]

        return cls.build_query_compiler(
            dataset, columns, index_columns, dtype_backend=dtype_backend, **kwargs
        )
    
    @staticmethod
    def _to_parquet_check_support(kwargs):
        """
        Check if parallel version of `to_parquet` could be used.

        Parameters
        ----------
        kwargs : dict
            Keyword arguments passed to `.to_parquet()`.

        Returns
        -------
        bool
            Whether parallel version of `to_parquet` is applicable.
        """
        path = kwargs["path"]
        compression = kwargs["compression"]
        if not isinstance(path, str):
            return False
        if any((path.endswith(ext) for ext in [".gz", ".bz2", ".zip", ".xz"])):
            return False
        if compression is None or not compression == "snappy":
            return False
        return True

    @classmethod
    def write(cls, qc, **kwargs):
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
            return cls.base_io.to_parquet(qc, **kwargs)

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

        def func(df, **kw):  # pragma: no cover
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
        cls.materialize([part.list_of_blocks[0] for row in result for part in row])
