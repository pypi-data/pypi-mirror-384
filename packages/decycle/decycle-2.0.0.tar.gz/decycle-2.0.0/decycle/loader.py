import ast
from types import ModuleType
from importlib.abc import Loader
from .proxy import LazyProxy
from .decorators import wrap_functions


class CircularImportLoader(Loader):
    def __init__(self, spec):
        self.spec = spec

    def exec_module(self, module: ModuleType):
        filename = self.spec.origin

        # is python obj?
        if not filename.endswith(".py"):
            self.spec.loader.exec_module(module)
            return

        with open(filename, "r") as f:
            source = f.read()

        tree = ast.parse(source, filename)
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                obj_name = node.name
                if not hasattr(module, obj_name):
                    setattr(module, obj_name, LazyProxy(module.__name__, obj_name))

        code = compile(tree, filename, "exec")
        exec(code, module.__dict__)

        wrap_functions(module)
