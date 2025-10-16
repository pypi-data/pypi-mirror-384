import threading
from types import FunctionType, ModuleType
from .recursion_preventer import RecursiveCallPreventer


def wrap_functions(module: ModuleType):
    for name, obj in list(module.__dict__.items()):
        if isinstance(obj, FunctionType) and obj.__module__ == module.__name__:
            wrapped_func = RecursiveCallPreventer(obj)
            setattr(module, name, wrapped_func)
