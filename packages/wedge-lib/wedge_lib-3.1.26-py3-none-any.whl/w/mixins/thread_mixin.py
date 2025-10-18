import threading


class ThreadMixin:
    _lock: threading.Lock = threading.Lock()

    @classmethod
    def _get_current_thread_id(cls):
        return threading.currentThread().ident

    @classmethod
    def _list_active_thread_ids(cls):
        return [t.ident for t in threading.enumerate()]
