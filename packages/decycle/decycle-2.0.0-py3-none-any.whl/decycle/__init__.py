import sys
import os
from .finder import _finder_instance


def install():
    """Init decycling. Useless for external calling"""
    if _finder_instance not in sys.meta_path:
        sys.meta_path.insert(0, _finder_instance)


def uninstall():
    """Uninstall decycling"""
    if _finder_instance in sys.meta_path:
        sys.meta_path.remove(_finder_instance)


def add_project_root(path):
    """
        Now imagine. You designed the framework poorly. Call
        ```python
        import decycle

        decycle.add_project_root(os.path.dirname(__file__))
        ```
    at the root (in your framework's __init__.py) and decycle will fix all the cyclic imports
    """
    _finder_instance.add_root(os.path.abspath(path))


install()

__all__ = ["install", "uninstall", "add_project_root"]
