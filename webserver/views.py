from django.http import JsonResponse
from django.views import View


class HealthCkeckView(View):
    def get(self, request):
        return JsonResponse({"status": "ok"})
