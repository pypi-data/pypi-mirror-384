# Modify Modin's Factories to read and write parquet and csv files on DNAnexus platform
# References:
# 1. Override PandasOnRay to pass storage_options to fsspec for writing feature
#   https://github.com/modin-project/modin/blob/master/modin/core/execution/ray/implementations/pandas_on_ray/io/io.py#L46
# 2. Override ParquetDispatcher for reading single parquet file
#   https://github.com/modin-project/modin/blob/master/modin/core/io/column_stores/parquet_dispatcher.py#L302

import os
from fsspec_dnanexus.core import DXFileSystemException
from fsspec_dnanexus.utils import MINIMUM_MODIN_VERSION

def provision_dx_on_ray():
    from modin import set_execution, __version__
    from packaging import version

    if version.parse(__version__) < version.parse(MINIMUM_MODIN_VERSION):
        raise DXFileSystemException(f"The version of Modin is too low. You need at least {MINIMUM_MODIN_VERSION} but you have {__version__}.")

    from modin.config import StorageFormat
    from modin.core.execution.dispatching.factories import factories

    from .dxpandas_on_ray import DXPandasOnRayFactory
    factories.DxpandasOnRayFactory = DXPandasOnRayFactory
    StorageFormat.add_option("Dxpandas")

    set_execution(storage_format="Dxpandas")

def provision_dx_on_python():
    from modin import set_execution, __version__
    from packaging import version

    if version.parse(__version__) < version.parse(MINIMUM_MODIN_VERSION):
        raise DXFileSystemException(f"The version of Modin is too low. You need at least {MINIMUM_MODIN_VERSION} but you have {__version__}.")

    from modin.config import StorageFormat
    from modin.core.execution.dispatching.factories import factories

    from .dxpandas_on_python import DXPandasOnPythonFactory
    factories.DxpandasOnPythonFactory = DXPandasOnPythonFactory
    StorageFormat.add_option("Dxpandas")

    set_execution(storage_format="Dxpandas")
    
    # set modin engin to python
    os.environ["MODIN_ENGINE"] = "python"

