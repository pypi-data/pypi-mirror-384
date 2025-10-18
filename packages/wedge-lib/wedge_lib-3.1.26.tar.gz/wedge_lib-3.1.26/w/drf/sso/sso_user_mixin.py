import copy
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction

from w.services.technical.dict_service import DictService
from w.services.technical.list_service import ListService
from w.services.technical.sso_service import SsoService


class SsoUserMixin:
    _sso2django_remapping = {
        "email": "email",
        "username": "username",
        "firstName": "first_name",
        "lastName": "last_name",
    }

    @classmethod
    def remap_sso2django_user(cls, sso_data):
        return DictService.remap_keys(sso_data, cls._sso2django_remapping)

    @classmethod
    def _update_auth_user(cls, user, data):
        return cls.get_user_service().update(user, **data)

    @classmethod
    def _create_auth_user(cls, user_data):
        data = DictService.keep_keys(
            user_data, ["username", "email", "first_name", "last_name", "password"]
        )
        return cls.get_user_service().create(**data)

    @classmethod
    def create_from_sso(cls, uuid, user_data) -> User:
        """Create user (Django) and sso user from sso"""
        data = copy.deepcopy(user_data)
        if "password" not in user_data:
            data["password"] = str(uuid4())
        user = cls._create_auth_user(data)
        return cls.create(sso_uuid=uuid, user=user, list_apps=user_data["list_apps"])

    @classmethod
    def update_from_sso(cls, user, user_data):
        with transaction.atomic():
            list_apps = user_data.pop("list_apps")
            if ListService.are_different(user.list_apps, list_apps):
                cls.update(user, list_apps=list_apps)
            cls._update_auth_user(user.user, user_data)
        return user

    @classmethod
    def create_or_update_by_uuid(cls, uuid, user_data):
        """
        Create or update Django user from SSO server
        Args:
            uuid: sso uid
            user_data: {
                "username": "example",
                "first_name": "Example",
                "last_name": "Example",
                "email": "email@fake.com"
            }

        Returns:
            user(User), created(Bool)
        """
        qs = cls._model.objects.filter(sso_uuid=uuid)
        if qs.exists():
            return cls.update_from_sso(qs.first(), user_data), False
        return cls.create_from_sso(uuid, user_data), True

    @classmethod
    def get_by_uuid(cls, uuid):
        return cls._model.objects.get(sso_uuid=uuid)

    @classmethod
    def get_by_uuid_if_exist(cls, uuid):
        qs = cls._model.objects.filter(sso_uuid=uuid)
        if qs.exists():
            return qs.first()
        return None

    @classmethod
    def get_or_create_sso_user(
        cls, user: User, password: str, list_apps: list
    ) -> (dict, bool):
        attrs = DictService.keep_keys(
            cls.get_user_service().to_dict(user),
            ["email", "username", "first_name", "last_name"],
        )
        client_roles = {app: [f"{app}"] for app in list_apps}
        return SsoService.get_or_create_user(
            {**attrs, "password": password, "client_roles": client_roles}
        )

    @classmethod
    def require_update_user_password(
        cls,
        user_id,
        client_id=settings.SSO["CLIENT_ID"],
        lifespan=None,
        redirect_uri=None,
    ):
        return SsoService.require_update_password(
            user_id=user_id,
            client_id=client_id,
            lifespan=lifespan,
            redirect_uri=redirect_uri,
        )

    @classmethod
    def get_user_service(cls):  # pragma: no cover
        """get UserService on Django User model"""
        raise RuntimeError("need to be implemented")
