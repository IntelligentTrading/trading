import ujson as json
from functools import wraps

from django.http.response import HttpResponse
from django.utils.decorators import method_decorator

from webserver.models import User


@method_decorator
def with_valid_api_key(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        api_key = json.loads(request.body).get("api_key", None)
        try:
            request.user = User.objects.get(api_key=api_key)
        except User.DoesNotExist:
            return HttpResponse(
                json.dumps({"status": "Not authorized"}),
                content_type="application/json", status=401)
        return view_func(request, *args, **kwargs)
    return _wrapped_view
