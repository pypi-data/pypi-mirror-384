from abc import ABC

from django.conf import settings
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from w import exceptions
from w.drf.viewsets import ViewSet

from w.services.technical.models.tpl_models import TplSettings
from w.services.technical.tpl_service import TplService


class AbstractCypressViewSet(ViewSet, ABC):  # pragma: no cover
    permission_classes = [permissions.AllowAny]
    lookup_field = "tpl_name"
    app = None

    @action(detail=True, methods=["get"])
    def load(self, request, tpl_name: str):
        if settings.DJANGO_ENV != "cypress":
            raise exceptions.BadRequestError("Cypress env should be used")
        tpl_settings = TplSettings(
            **settings.DATABASES.get("default"),
            app=self.app,
            tpl_name=tpl_name,
        )
        with TplService.session(tpl_settings):
            TplService.load(settings.DATABASES.get("default").get("NAME"))
        return Response(status=status.HTTP_204_NO_CONTENT)
