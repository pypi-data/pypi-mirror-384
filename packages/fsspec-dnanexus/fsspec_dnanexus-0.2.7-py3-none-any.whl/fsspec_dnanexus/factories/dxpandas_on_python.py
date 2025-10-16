from modin.core.execution.dispatching.factories.factories import BaseFactory
from modin.core.execution.python.implementations.pandas_on_python.io import PandasOnPythonIO

class DXPandasOnPythonIO(PandasOnPythonIO):
    pass

class DXPandasOnPythonFactory(BaseFactory):
    @classmethod
    def prepare(cls):
        cls.io_cls = DXPandasOnPythonIO