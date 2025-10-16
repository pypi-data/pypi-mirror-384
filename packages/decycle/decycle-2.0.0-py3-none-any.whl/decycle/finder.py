import os
import sys
import importlib.util
from importlib.abc import MetaPathFinder
from .loader import CircularImportLoader
from .utils import get_project_root


class CircularImportFinder(MetaPathFinder):
    def __init__(self):
        self._in_progress = set()
        self.project_roots = {get_project_root()}

    def add_root(self, path):
        if path:
            self.project_roots.add(os.path.abspath(path))

    def _is_in_project(self, path):
        if not path:
            return False
        abs_path = os.path.abspath(path)
        return any(abs_path.startswith(root) for root in self.project_roots)

    def find_spec(self, fullname, path, target=None):
        if fullname in self._in_progress:
            return None

        if fullname in sys.modules or fullname.startswith(("__", "builtins")):
            return None

        self._in_progress.add(fullname)
        try:
            spec = importlib.util.find_spec(fullname, path)
            if not spec or not spec.origin:
                return None

            is_package = spec.origin.endswith("__init__.py")
            is_py_file = spec.origin.endswith(".py")

            if not (is_py_file or is_package):
                return None

            if not self._is_in_project(spec.origin):
                return None

            return importlib.util.spec_from_file_location(
                fullname,
                spec.origin,
                loader=CircularImportLoader(spec),
                submodule_search_locations=spec.submodule_search_locations,
            )
        finally:
            self._in_progress.remove(fullname)


_finder_instance = CircularImportFinder()
