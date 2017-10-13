from django.core.exceptions import PermissionDenied

ADMIN = 1
DATA_USER = 2
CUSTOMER_SERVICE = 3


def permission_need(perm_list):
    if not isinstance(perm_list, (list, tuple)):
        perm_list = [perm_list]

    def second_func(wrapped_func):
        def third_func(request, *args, **kwargs):
            if request.user.is_authenticated() and request.user.role_id in perm_list:
                return wrapped_func(request, *args, **kwargs)
            else:
                raise PermissionDenied()
        return third_func

    return second_func
