import os
import dxpy
import logging
import threading

from fsspec.utils import tokenize
from typing import Tuple, Union, Any

from dxpy import api, DXFile, DXError, new_dxfile
from dxpy.exceptions import ResourceNotFound, InvalidAuthentication, PermissionDenied

from fsspec.spec import AbstractFileSystem, AbstractBufferedFile
from fsspec.utils import setup_logging, stringify_path

logger = logging.getLogger("dxfs")

if "FSSPEC_DNANEXUS_LOGGING_LEVEL" in os.environ:
    setup_logging(logger=logger, level=os.environ["FSSPEC_DNANEXUS_LOGGING_LEVEL"])

PROTOCOL = "dnanexus"

FILE_REQUEST_TIMEOUT = 60
WRITE_PERMS = ["CONTRIBUTE", "ADMINISTER", "UPLOAD"]
READ_PERMS = ["VIEW", *WRITE_PERMS]

DIRECTORY_TYPE = "directory"
FILE_TYPE = "file"

class DXFileSystemException(Exception):
    pass

class DXFileSystem(AbstractFileSystem):

    cachable = False # do not cache this instance
    default_block_size = 5 * 2**20
    protocol = ["dnanexus", "DNANEXUS"]
    api_host = "api.dnanexus.com"
    root_marker = "/"

    def __init__(
        self,
        block_size=None,
        cache_type="readahead",
        asynchronous=False,
        loop=None,
        **storage_options,
    ):
        """
        :param Dict[str, Any] storage_options: a dictionary including
            :token str:
                Set to authentication of dxpy
            :staging bool: default False
                Login to staging
            :allow_duplicate_filenames bool: default False
                Write a new file if the filename already exists in folder
        """
        super().__init__(loop=loop, asynchronous=asynchronous, skip_instance_cache=True, **storage_options)

        self.block_size = block_size or self.default_block_size
        self.cache_type = cache_type
        self.dx_path_extractor = DXPathExtractor()
        self.storage_options = storage_options

        # prefer token to FSSPEC_DNANEXUS_TOKEN
        self.token = storage_options.get("token", None) or os.environ.get("FSSPEC_DNANEXUS_TOKEN")

        if storage_options.get("staging", False):
            self.api_host = "stagingapi.dnanexus.com"

        self.dx_login(token=self.token, api_host=self.api_host)

    @classmethod
    def _strip_protocol(cls, path):
        """Turn path from fully-qualified to file-system-specific

        May require FS-specific handling, e.g., for relative paths or links.
        """
        if isinstance(path, list):
            return [cls._strip_protocol(p) for p in path]
        path = stringify_path(path)
        protos = (cls.protocol,) if isinstance(cls.protocol, str) else cls.protocol
        for protocol in protos:
            if path.startswith(protocol + "://"):
                path = path[len(protocol) + 3 :]
            elif path.startswith(protocol + "::"):
                path = path[len(protocol) + 2 :]
        # use of root_marker to make minimum required path, e.g., "/"
        return path or cls.root_marker

    # override _parent method to support upload with format of path
    def _parent(self, path):
        path = self._strip_protocol(path)
        project_id, _, fullpath = self.dx_path_extractor.extract(path)
        if not fullpath:
            raise DXFileSystemException(f"ValueError: Unsupported upload with format of this path {path}")
        return f"{project_id}:{os.path.dirname(fullpath)}"

    def dx_login(self, token=None, api_host="api.dnanexus.com"):
        # if token is not provided, dxfsspec uses thes token of dxpy by default
        if not token:
            return

        try:
            dxpy.set_api_server_info(host=api_host, protocol='https')
            dxpy.set_security_context({'auth_token_type': 'Bearer', 'auth_token': token})
            dxpy.set_workspace_id(None)
            logger.debug(f'Logged as: {dxpy.whoami()}')
        except InvalidAuthentication as e:
            raise DXFileSystemException(f'Login failed! {e}')

    def _open(self, path, mode="rb",
        block_size=None,
        autocommit=True,
        cache_type=None,
        cache_options=None,
        **kwargs):
        if block_size is None:
            block_size = self.block_size
        if cache_type is None:
            cache_type = self.cache_type

        from .utils import FILECLASS_DICT

        dx_buffered_cls = self.storage_options.get("dx_buffered_cls", None)
        dx_buffered_cls = FILECLASS_DICT[dx_buffered_cls] if dx_buffered_cls in FILECLASS_DICT else DXBufferedFile

        return dx_buffered_cls(
            fs=self,
            path=path,
            mode=mode,
            block_size=block_size,
            cache_type=cache_type,
            autocommit=autocommit,
            cache_options=cache_options
        )

    def info(self, path, **kwargs):
        path = self._strip_protocol(path)

        is_file = self.isfile(path)
        is_dir = self.isdir(path)

        if is_dir and is_file:
            raise DXFileSystemException("The path is ambiguous. It matches file and folder.")

        if is_dir:
            return {"type": "directory", "name": path, "size": 0}

        project_id, file_id, _ = self.dx_path_extractor.extract(path)

        if not project_id or not file_id:
            raise DXFileSystemException(f"ValueError: Unsupported format of this path {path}")

        logger.debug(f"Get info of '{file_id}' in '{project_id}'")
        try:
            desc = DXFile(file_id, project=project_id).describe()
            desc["type"] = desc["class"]
            return desc
        except ResourceNotFound as e:
            raise DXFileSystemException(f"FileNotFound: {e}")

    def exists(self, path, **kwargs):
        logger.debug(f"Check if {path} exists")
        describe = self._file_describe(path, **kwargs)
        return describe is not None

    def isdir(self, path, **kwargs):
        logger.debug(f"Check if {path} is directory")

        path = self._strip_protocol(path)
        project_id, _, fullpath = self.dx_path_extractor.extract(path)

        if fullpath is None:
            return False

        try:
            api.project_list_folder(project_id, input_params={"folder": fullpath, "only": "folders"})
            return True
        except ResourceNotFound:
            return False

    def isfile(self, path, **kwargs):
        logger.debug(f"Check if {path} is file")
        describe = self._file_describe(path, **kwargs)
        if not describe:
            return False
        return describe['class'] == 'file'

    def _file_describe(self, path, **kwargs):
        path = self._strip_protocol(path)
        try:
            project_id, file_id, _ = self.dx_path_extractor.extract(path)
            logger.debug(f"Describe {file_id} in {project_id}")
            if project_id and file_id:
                return api.file_describe(file_id, input_params={"project": project_id})
        except (DXError, DXFileSystemException):
            return None
        return None

    def ls(self, path, detail=False, unique=False, **kwargs):
        def filter_duplicated_filenames(files):
            logger.debug(f"Filter duplicate filenames")
            res = {}
            for file in files:
                name = file["name"]
                # file name doest not exist
                if name not in res:
                    res[name] = file
                else: # already exists
                    # check the latest created time
                    if file["created"] > res[name]["created"]:
                        res[name] = file
            return list(res.values())

        path = self._strip_protocol(path)

        project_id, _, folder_path = self.dx_path_extractor.extract(path)

        if folder_path is None:
            raise DXFileSystemException(f"ResourceNotFound: The specified folder could not be found in {project_id}")

        logger.debug(f"List information about files and directories in folder '{folder_path}' of {project_id}")

        try:
            results = api.project_list_folder(object_id=project_id,
                                input_params={"folder": folder_path,
                                                "includeHidden": True,
                                                "describe": dict(fields={"id": True,
                                                                        "project": True,
                                                                        "name": True,
                                                                        "class": True,
                                                                        "folder": True,
                                                                        "created": True,
                                                                        "createdBy": True,
                                                                        "modified": True,
                                                                        "hidden": True,
                                                                        "tags": True,
                                                                        "media": True,
                                                                        "archivalState": True,
                                                                        "cloudAccount": True,
                                                                        "size": True,
                                                                        "state": True})})
            folders = results["folders"]
            # get object describe
            # filter files that are not in closed state
            logger.debug(f"Filter files that are not in 'closed' state.")
            objects = [obj["describe"] for obj in results["objects"] if obj["describe"]["state"] == "closed"]
            # only return filename if detail is False
            if not detail:
                logger.debug(f"Return objects without detail.")
                objects = [os.path.join(obj["folder"], obj["name"]) for obj in objects]
                if unique:
                    logger.debug(f"Filter duplicate filenames")
                    objects = list(set(objects))
                return folders + objects

            logger.debug(f"Return folders and objects with detail.")
            # add type for folders
            folders = [{
                            "name": folder,
                            "project": project_id,
                            "type": DIRECTORY_TYPE,
                            "full_url": f"{PROTOCOL}://{project_id}:{folder}",
                            "size": 0
                        }
                        for folder in folders]

            # filter the duplicated file names
            if unique:
                objects = filter_duplicated_filenames(objects)

            logger.debug(f"Add more info including type, name, full_url.")
            for obj in objects:
                obj["type"] = obj["class"]
                obj["name"] = os.path.join(folder_path, obj["name"])
                obj["full_url"] = f"{PROTOCOL}://{obj['project']}:{obj['name']}"
                if not unique:
                    obj["full_url"] = f"{PROTOCOL}://{obj['project']}:{obj['id']}"

            return folders + objects
        except DXError as e:
            raise DXFileSystemException(str(e))

    def mkdir(self, path, create_parents=True, **kwargs):
        path = self._strip_protocol(path)

        project_id, _, folder_path = self.dx_path_extractor.extract(path)
        logger.debug(f"Create new folder '{folder_path}' in {project_id}.")

        try:
            return api.project_new_folder(object_id=project_id, input_params={
                                                            "folder": folder_path,
                                                            "parents": create_parents})
        except DXError as e:
            raise DXFileSystemException(f"{str(e)}")

    def mkdirs(self, path, exist_ok=True, **kwargs):
        if not exist_ok and self.isdir(path=path):
            raise DXFileSystemException("ResourceExists: The folder in url {url} alread exists")

        path = self._strip_protocol(path)

        project_id, _, folder_path = self.dx_path_extractor.extract(path)
        logger.debug(f"Create new folder '{folder_path}' in {project_id}.")

        try:
            return api.project_new_folder(object_id=project_id, input_params={
                                                            "folder": folder_path,
                                                            "parents": True})
        except DXError as e:
            raise DXFileSystemException(f"{str(e)}")

    def find(self, path, maxdepth=None, withdirs=False, detail=False, **kwargs):
        """
        When reading parquet file using pyarrow engine, pyarrow will call fs.find function
        Modify the key of result to adapt our format project_id:file_id
        Reference: https://github.com/apache/arrow/blob/3bdbd0d34cdfe6f34e1c2bf80df472faccdff3c0/python/pyarrow/fs.py#L355

        List all files below path.

        Like posix ``find`` command without conditions

        Parameters
        ----------
        path : str
        maxdepth: int or None
            If not None, the maximum number of levels to descend
        withdirs: bool
            Whether to include directory paths in the output. This is True
            when used by glob, but users usually only want files.
        kwargs are passed to ``ls``.
        """
        # TODO: allow equivalent of -name parameter
        path = self._strip_protocol(path)
        out = dict()
        for _, dirs, files in self.walk(path, maxdepth, detail=True, **kwargs):
            if withdirs:
                files.update(dirs)

            def update_data_object(item: tuple) -> tuple:
                """Add size key if the item type is directory

                Param item is tuple because of PEP-3113 which removed Tuple Unpacking

                :param item: (key, value) of each item in files
                :type item: tuple
                :return: (key, value)
                :rtype: tuple
                """
                key, value = item
                if not value.get('size') and value.get('type') == 'directory':
                    # XVG-7669: To make it compatible with the upstream File System wrappers like PyArrow
                    # which get the "size" attribute of the file/directory item
                    value['size'] = 0
                return (value['name'], value)

            _files = dict(map(update_data_object, files.items()))
            out.update(_files)

        if not out and self.isfile(path):
            # walk works on directories, but find should also return [path]
            # when path happens to be a file
            out[path] = {}
        names = sorted(out)
        if not detail:
            return names
        else:
            project, _ = path.split(":")
            return {f"{project}:{name}": out[name] for name in names}

    def rename_folder(self, path: str, new_name: str):
        path = self._strip_protocol(path)
        project_id, _, folder_path = self.dx_path_extractor.extract(path=path)
        api.project_rename_folder(project_id, input_params={
            "folder": folder_path,
            "name": new_name
        })

    def remove_files_in_folder(self, path: str):
        objects = self.ls(path=path, detail=True)
        if len(objects) == 0:
            return
        # only remove file
        object_ids = [obj["id"] for obj in objects if obj["type"] == "file"]
        proj_id = objects[0]['project']
        api.project_remove_objects(proj_id, input_params={"objects": object_ids})


class DXBufferedFile(AbstractBufferedFile):

    part_min = 5 * 2**20
    part_max = 5 * 2**30

    def __init__(self,
                 fs,
                 path: str,
                 mode: str = "rb",
                 block_size: int = 5 * 2**20,
                 cache_type: str ="readahead",
                 autocommit: bool = True,
                 cache_options: dict = None):
        self.dx_path_extractor = DXPathExtractor()
        self.project_id, file_id, self.fullpath = self.dx_path_extractor.extract(path, mode=mode)

        if "r" in mode:
            if not self.dx_path_extractor.is_dx_file_id(file_id):
                raise DXFileSystemException("FileNotFound: Cannot find any file matching { original path: '%s', extracted project: '%s', extracted file_id: '%s' }" \
                                    % (path, self.project_id, file_id ))

            self.dxfile: Union[DXFile, None] = DXFile(file_id, project=self.project_id) if file_id else None

            if self.dxfile and self.dxfile._get_state() != "closed":
                raise DXFileSystemException("NotSupportedError: Reading an open file is not supported.")

            self.details = fs.info(path)
            self.size = self.details["size"]
        if "w" in mode:
            if not self.fullpath:
                raise DXFileSystemException(f"ValueError: Unsupported upload with format of this path {path}")

        super().__init__(
            fs,
            path,
            mode,
            block_size,
            cache_type=cache_type,
            autocommit=autocommit,
            cache_options=cache_options,
        )

    def _upload_chunk(self, final=False):
        logger.debug(
            f"Upload for {self}, final={final}, loc={self.loc}, buffer loc={self.buffer.tell()}"
        )
        self.buffer.seek(0)
        (data0, data1) = (None, self.buffer.read(self.blocksize))

        while data1:
            (data0, data1) = (data1, self.buffer.read(self.blocksize))
            data1_size = len(data1)

            if 0 < data1_size < self.blocksize:
                remainder = data0 + data1
                remainder_size = self.blocksize + data1_size

                if remainder_size <= self.part_max:
                    (data0, data1) = (remainder, None)
                else:
                    partition = remainder_size // 2
                    (data0, data1) = (remainder[:partition], remainder[partition:])

            try:
                logger.debug(f"Upload chunk with length {len(data0)}")
                self.dx_handler.write(data=data0)
            except PermissionDenied as e:
                raise DXFileSystemException(f"PermissionDenied: {e}")


        if final:
            logger.debug(f"Complete upload for {self}")
            self.dx_handler.flush()
            try:
                self.dx_handler.wait_until_parts_uploaded()
            except DXError:
                raise DXFileSystemException("File {} was not uploaded correctly!".format(self.dx_handler.name))
            self.dx_handler.close()
            self.dx_handler.wait_on_close()
            self.dx_handler = None

        return not final

    def _initiate_upload(self):
        """Create remote file/upload"""
        logger.debug("Initiate upload for %s" % self.fullpath)

        folder = os.path.dirname(self.fullpath)
        filename = os.path.basename(self.fullpath)

        try:
            self.dx_handler = new_dxfile(name=filename,
                                     folder=folder,
                                     project=self.project_id,
                                     parents=True,
                                     mode="a")

            self.dx_handler._ensure_write_bufsize()
            self.dx_handler._num_bytes_transmitted = 0

            if not self.fs.storage_options.get("allow_duplicate_filenames"):
                t = threading.Thread(target=self.remove_duplicate_filenames, args=(filename,
                                                                         folder,
                                                                         self.project_id,
                                                                         self.dx_handler.get_id()))
                t.start()
        except PermissionDenied as e:
            raise DXFileSystemException(f"PermissionDenied: {e}")

    def _fetch_range(self, start, end):
        """Get the specified set of bytes from remote"""
        logger.debug(f"Fetch data in range: {start}-{end}")
        logger.debug(f"Get the specified set of bytes from {start} to {end}")
        self.dxfile.seek(offset=start)
        return self.dxfile._read2(end - start)

    def remove_duplicate_filenames(self, filename: str, folder: str, project_id: str, exclude_dxid: str):
        logger.debug(f"Remove the duplicate filenames {filename} in {folder} excluding {exclude_dxid}")
        objects = dxpy.find_data_objects(classname="file",
                                        name=filename,
                                        folder=folder,
                                        project=project_id,
                                        visibility="either",
                                        recurse=False,)


        # to make sure that do not remove the writing file
        file_ids = [obj["id"] for obj in objects if obj["id"] != exclude_dxid]
        if len(file_ids) > 0:
            try:
                api.project_remove_objects(project_id, input_params={"objects": file_ids, "force": True})
                logger.debug(f"Removed: {file_ids}")
            except DXError as e:
                logger.debug(f"DXFileSystemException: {e}")

class DXBufferedFileOnRay(DXBufferedFile):
    def _upload_chunk(self, final=False):
        logger.debug(
            f"Upload for {self}, final={final}, loc={self.loc}, buffer loc={self.buffer.tell()}"
        )
        self.buffer.seek(0)
        data = self.buffer.read()

        storage_options = self.fs.storage_options

        is_last_partition = storage_options.get("n_partitions") - 1 == storage_options.get("partition_idx")

        # to make sure DXFile writes only one part
        # In DXFile, if _write_buffer_size_hint is less than length of data, it will write to multiple parts
        self.dx_handler._write_buffer_size_hint = len(data)

        desc = self.dx_handler.describe(fields={"parts": True})
        parts = desc.get("parts", {})

        # write to the next part
        self.dx_handler._cur_part = len(parts) + 1
        self.dx_handler._num_uploaded_parts = self.dx_handler._cur_part

        if len(data) > 0:
            # because DXFile is required to have at least 5MB for each part (except last part)
            # we remove the file when writing any parts (except last) that is less than 5Mb
            if not is_last_partition and len(data) < 5 * 2**20:
                self.dx_handler._num_uploaded_parts = 0 # to upload empty byte before closing
                self.dx_handler.close()
                self.dx_handler.wait_on_close()
                self.dx_handler.remove()
                raise DXFileSystemException("InvalidState: Each part (except last) must be at least 5 MB")

            self.dx_handler.write(data=data)
            self.dx_handler.flush()

        if final:
            try:
                self.dx_handler.wait_until_parts_uploaded()
            except DXError:
                raise DXFileSystemException("File {} was not uploaded correctly!".format(self.dx_handler.name))
            # close file if it's last partition

            if is_last_partition:
                self.dx_handler.close()
                self.dx_handler.wait_on_close()
                self.dx_handler = None

        return not final

    def _initiate_upload(self):
        """Create remote file/upload"""
        logger.debug("Initiate upload for %s" % self)

        storage_options = self.fs.storage_options
        # marker_id is passed from DXPandasOnRayIO
        marker_id = storage_options.get("marker_id")

        folder = os.path.dirname(self.fullpath)
        filename = os.path.basename(self.fullpath)

        # get DXFile using marker_id
        existing_file = dxpy.find_one_data_object(name=filename,
                                                 folder=folder,
                                                 project=self.project_id,
                                                 properties={"marker_id": marker_id},
                                                 recurse=False,
                                                 zero_ok=True)
        if existing_file:
            self.dx_handler = DXFile(existing_file["id"],
                                     project=existing_file["project"],
                                     mode="a")
            return

        try:
            # create new file for writing
            self.dx_handler = new_dxfile(name=filename,
                                        folder=folder,
                                        project=self.project_id,
                                        parents=True,
                                        mode="w")

            self.dx_handler.set_properties({"marker_id": marker_id})

            # check file exists for first partition
            if storage_options.get("partition_idx") == 0 and not storage_options.get("allow_duplicate_filenames"):
                t = threading.Thread(target=self.remove_duplicate_filenames, args=(filename,
                                                                         folder,
                                                                         self.project_id,
                                                                         self.dx_handler.get_id()))
                t.start()
        except PermissionDenied as e:
            raise DXFileSystemException(f"PermissionDenied: {e}")

class _DXSingleton(type):
    cacheable = True
    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls._instances = {}
        cls._pid = os.getpid()

    def __call__(cls, *args: Any, **kwargs: Any):
        token = tokenize(
            cls, cls._pid, *args,  **kwargs
        )

        if os.getpid() != cls._pid:
            logger.debug("Clear instances because of different PIDs.")
            cls._instances.clear()
            cls._pid = os.getpid()

        if cls.cacheable and token in cls._instances:
            logger.debug(f"Reuse instance by token {token}")
            cls._latest = token
            return cls._instances[token]
        else:
            logger.debug(f"Initialize new instance with args {args} and kwargs {kwargs}")
            obj = super().__call__(*args, **kwargs)

            if cls.cacheable:
                cls._latest = token
                cls._instances[token] = obj

            return obj

class DXPathExtractor(metaclass=_DXSingleton):
    root_marker = "/"
    cacheable = True # this class can be cached, instances reused
    project_cacheable = True # project name can be cached

    def __init__(self) -> None:
        self._cache = {}

    def clear_cache(self):
        self._cache.clear()

    def get_project_id(self, id_or_path: str) -> str:
        if self.project_cacheable and id_or_path in self._cache:
            project_id = self._cache[id_or_path]
            logger.debug(f"Found project id {project_id} in cache")
            return project_id

        if self.is_dx_project_id(id_or_path):
            return id_or_path

        logger.debug(f"{id_or_path} is not DXProject ID. Try to find DXProject with name '{id_or_path}'")

        dx_proj = dxpy.find_one_project(name=id_or_path, zero_ok=True, level="VIEW")
        if dx_proj is None:
            raise DXFileSystemException(f"ProjectNotFound: There is no project with name '{id_or_path}'")

        if self.project_cacheable:
            logger.debug(f"Cache project name {id_or_path}: ", id_or_path)
            self._cache[id_or_path] = dx_proj["id"]

        return dx_proj["id"]

    def is_dx_project_id(self, project_id: str) -> bool:
        try:
            dxpy.verify_string_dxid(project_id, expected_classes="project")
            return True
        except DXError as e:
            logger.debug(f"{project_id} is not a DXProject ID")
            return False

    def is_dx_file_id(self, file_id: str) -> bool:
        try:
            dxpy.verify_string_dxid(file_id, expected_classes="file")
            return True
        except DXError as e:
            logger.debug(f"{file_id} is not a DXFile ID")
            return False

    def get_file_id(self, id_or_path: str, project_id: str = None) -> str:
        if self.is_dx_file_id(id_or_path):
            return id_or_path

        logger.debug(f"{id_or_path} is not DXFile ID. Try to find DXFile with name '{id_or_path}' in {project_id}")

        id_or_path = id_or_path or self.root_marker

        folder = os.path.dirname(id_or_path)
        if not folder.startswith("/"):
            raise DXFileSystemException("ValueError: The folder path should start with '/'")

        filename = os.path.basename(id_or_path)
        if not filename:
            return None

        # check if dxfile exists by name and project
        dxfile_desc = None
        dxfiles = dxpy.find_data_objects(classname="file",
                                            name=filename,
                                            folder=folder,
                                            project=project_id,
                                            describe=True,
                                            recurse=False,
                                            visibility="either")
        for file in dxfiles:
            file_desc = file["describe"]
            if dxfile_desc is None or file_desc["created"] > dxfile_desc["created"]:
                dxfile_desc = file_desc

        if dxfile_desc is None:
            return None

        return dxfile_desc["id"]

    def extract(self, path: str, mode: Union[str, None] = None) -> Tuple[str, str, str]:
        logger.debug(f"Extract info from {path}")

        project_id = None
        file_id = None
        fullpath = None

        file_info = path.split(":")
        # DX id format
        # project-xxx:file-yyyy
        if len(file_info) == 2:
            project_id_or_name, file_or_folder_path = file_info

            project_id = self.get_project_id(id_or_path=project_id_or_name)

            if mode != None and ("w" in mode or "a" in mode):
                pass
            else:
                file_id = self.get_file_id(id_or_path=file_or_folder_path, project_id=project_id)

            # if not file id, assign fullpath to origin path
            if not self.is_dx_file_id(file_or_folder_path):
                fullpath = file_or_folder_path
        else:
            file_or_folder_path = file_info[0]
            if self.is_dx_file_id(file_id=file_or_folder_path):
                file_id = file_or_folder_path
                # find dx project based on dx file id
                dxfile = DXFile(file_or_folder_path)
                dxfile_desc = dxfile.describe()
                project_id = dxfile_desc["project"]

        if not project_id:
            raise DXFileSystemException(f"ProjectNotFound: There is no project with path '{path}'")

        # should remove "/"" at the end if fullpath is not root
        # for case ls on root e.g dxfs.ls("dnanexus://project-xxx:/")
        # for case read file e.g dxfs.ls("dnanexus://project-xxx:/path/to/file.csv/")
        if fullpath and fullpath != self.root_marker:
            fullpath = fullpath.rstrip("/")

        return project_id, file_id, fullpath
