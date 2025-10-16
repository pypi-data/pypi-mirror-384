import os
import sys


def get_project_root():
    main_module = sys.modules.get("__main__")
    if main_module and hasattr(main_module, "__file__"):
        return os.path.dirname(os.path.abspath(main_module.__file__))

    return os.getcwd()
