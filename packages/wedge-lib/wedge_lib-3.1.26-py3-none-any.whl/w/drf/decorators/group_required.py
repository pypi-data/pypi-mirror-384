from rest_framework.exceptions import PermissionDenied


def group_required(groups):
    """
    Limit api access to list of groups. User must be authenticated too.

    If user do not belongs to one of the groups return 403 permission denied.

    Usage:
        @group_required(("group1", "group2", ...))
        def list(self, request, *args, **kwargs):
            ...
    """

    def decorator(drf_custom_method):
        def _decorator(self, *args, **kwargs):
            if self.request.user.groups.filter(name__in=groups).exists():
                return drf_custom_method(self, *args, **kwargs)
            raise PermissionDenied()

        return _decorator

    return decorator
