from abc import ABC


class AbstractService(ABC):
    """
    Ensure only one instance can be created, kind of singleton pattern
    """

    def __new__(cls, *args, **kwargs):
        raise RuntimeError("%s should not be instantiated" % cls)  # pragma: no cover

    @classmethod
    def clear(cls):  # pragma: no cover
        pass  # is like an abstract class method

    @classmethod
    def _is_initialized(cls) -> bool:  # pragma: no cover (todo one day)
        return True

    @classmethod
    def _check_is_initialized(cls):
        """
        Check service is initialized

        Returns:
            None

        Raises:
            RuntimeError
        """
        if cls._is_initialized():
            return None

        raise RuntimeError(f"Service {cls.__name__} must be initialized first")

    @classmethod
    def get_patch_target(cls, method_name=None, relative=False) -> str:
        """
        Get patch target to easily patch/mock the service
        """
        import inspect

        module = None
        for k, v in inspect.getmembers(cls):
            if k == "__module__":
                module = v
                break

        target = f"{module}" if relative else f"{module}.{cls.__name__}"
        if method_name:
            return f"{target}.{method_name}"
        return target  # pragma: no cover (todo one day)
