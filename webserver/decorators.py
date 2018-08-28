from functools import wraps

from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied

from webserver.models import User


@method_decorator
def with_valid_api_key(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'api_key' not in request.data:
            raise PermissionDenied
        api_key = request.data.pop('api_key')
        try:
            request.user = User.objects.get(api_key=api_key)
        except User.DoesNotExist:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped_view
