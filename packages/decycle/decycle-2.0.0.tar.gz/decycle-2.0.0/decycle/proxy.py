import sys


class LazyProxy:
    def __init__(self, module_name, obj_name):
        self.__module_name = module_name
        self.__obj_name = obj_name
        self.__real_obj = None

    def _load_real_obj(self):
        if self.__real_obj is None:
            module = sys.modules.get(self.__module_name)
            if module is None:
                raise ImportError(f"Module {self.__module_name} not found.")

            real_obj = getattr(module, self.__obj_name)

            if real_obj is self:
                raise AttributeError(
                    f"'{self.__obj_name}' is not fully initialized yet due to a circular import. "
                    f"Cannot resolve attribute."
                )

            self.__real_obj = real_obj
        return self.__real_obj

    def __call__(self, *args, **kwargs):
        return self._load_real_obj()(*args, **kwargs)

    def __getattr__(self, name):
        if name in ("__deepcopy__", "__copy__"):
            return getattr(self._load_real_obj(), name)

        try:
            return getattr(self._load_real_obj(), name)
        except AttributeError as e:
            raise AttributeError(
                f"Could not resolve attribute '{name}' on '{self.__obj_name}' from module '{self.__module_name}'. Original error: {e}"
            ) from e

    def __repr__(self):
        if self.__real_obj is not None:
            return repr(self.__real_obj)
        return f"<LazyProxy for '{self.__module_name}.{self.__obj_name}'>"
