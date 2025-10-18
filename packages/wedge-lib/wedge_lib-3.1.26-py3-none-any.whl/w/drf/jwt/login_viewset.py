from dj_rest_auth.views import LoginView
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey
from w.drf.serializers.serpy_serializers import UserSerializer
from w.services.technical.date_service import DateService
from w.utils import import_path


class LoginViewset(LoginView):
    permission_classes = [HasAPIKey]
    _user_serializer = None

    def get_user_serializer(self):
        if not self._user_serializer:
            klass = None
            serializers = getattr(settings, "REST_AUTH_SERIALIZERS", None)
            if serializers and "W_LOGIN_RESPONSE_SERIALIZER" in serializers:
                klass = serializers["W_LOGIN_RESPONSE_SERIALIZER"]
            self._user_serializer = import_path(klass) if klass else UserSerializer
        return self._user_serializer

    def get_response(self):
        if not getattr(settings, "REST_USE_JWT", False):
            raise RuntimeError("This viewset need REST_USE_JWT=True")

        from rest_framework_simplejwt.settings import api_settings as jwt_settings

        jwt_expiration = DateService.to_datetime() + jwt_settings.ACCESS_TOKEN_LIFETIME
        user_serializer = self.get_user_serializer()
        data = {
            "user": user_serializer(self.user).data,
            "access_token": str(self.access_token),
            "expires": DateService.to_mysql_datetime(jwt_expiration),
        }
        response = Response(data, status=status.HTTP_200_OK)
        cookie_name = getattr(settings, "JWT_AUTH_COOKIE", None)

        if cookie_name:
            cookie_secure = getattr(settings, "JWT_AUTH_SECURE", False)
            cookie_httponly = getattr(settings, "JWT_AUTH_HTTPONLY", True)
            cookie_samesite = getattr(settings, "JWT_AUTH_SAMESITE", "Lax")
            jwt_expiration = (
                DateService.to_datetime() + jwt_settings.REFRESH_TOKEN_LIFETIME
            )
            response.set_cookie(
                cookie_name,
                self.refresh_token,
                expires=jwt_expiration,
                secure=cookie_secure,
                httponly=cookie_httponly,
                samesite=cookie_samesite,
            )
        return response
