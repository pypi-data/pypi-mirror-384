from fsspec_dnanexus.core import DXFileSystemException, DXBufferedFileOnRay, DXBufferedFile

FILECLASS_DICT = {
    "DXBufferedFileOnRay": DXBufferedFileOnRay, 
    "DXBufferedFile": DXBufferedFile
}

MINIMUM_MODIN_VERSION = "0.23.0"

def get_n_partitions(df) -> int:
    from modin.pandas import DataFrame
    try:
        assert type(df) == DataFrame, "`df` must be modin.pandas.DataFrame"
        return len(df._query_compiler._modin_frame._partitions)
    except AssertionError as ae:
        raise DXFileSystemException(ae)
    

