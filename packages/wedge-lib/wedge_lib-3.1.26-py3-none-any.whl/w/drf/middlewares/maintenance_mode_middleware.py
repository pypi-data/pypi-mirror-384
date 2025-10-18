from django.http import JsonResponse
from rest_framework import status

from w.services.technical.maintenance_mode_service import MaintenanceModeService


class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if MaintenanceModeService.is_on():
            return JsonResponse(
                data={"status": "site in maintenance"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return self.get_response(request)
