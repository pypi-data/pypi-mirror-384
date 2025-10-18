# Works with drf.backends.jwt_authenticate and djangrestframeword_simplejwt
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from w.drf import viewsets


class JwtViewset(viewsets.ViewSet):
    serializers = {"default": TokenRefreshSerializer}
    permission_classes = (HasAPIKey,)

    @action(methods=["post"], detail=False)
    def refresh(self, request):
        """
        Refresh token via HttpOnly Cookie

        add to urls.py:
            router.register(r"auth", JwtViewset, basename="jwt_auth")
        """
        cookie_name = getattr(settings, "JWT_AUTH_COOKIE", None)
        if not cookie_name:
            raise RuntimeError("Refresh needs JWT_AUTH_COOKIE")

        serializer = self.get_serializer(
            data={"refresh": request.COOKIES.get(cookie_name)}
        )
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        return Response(serializer.validated_data, status=status.HTTP_200_OK)
