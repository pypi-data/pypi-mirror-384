from django.contrib.auth.models import User
from w.services.abstract_model_service import AbstractModelService
from w import exceptions


class UserService(AbstractModelService):
    _model = User

    @classmethod
    def get_or_create(cls, **attrs):
        # noinspection PyUnresolvedReferences
        try:
            return cls._model.objects.get(username=attrs.get("username"))
        except cls._model.DoesNotExist:
            return cls.create(**attrs)

    @classmethod
    def create(cls, **attrs) -> User:
        return User.objects.create_user(**attrs)

    @classmethod
    def update(cls, instance: User, **attrs):
        password = attrs.pop("password") if "password" in attrs else None
        instance = super().update(instance, **attrs)
        if password:
            instance.set_password(password)
            instance.save()
        return instance

    @classmethod
    def add_group(cls, user: User, group_id):
        user.groups.add(group_id)
        return user

    @classmethod
    def remove_group(cls, user: User, group_id):
        user.groups.remove(group_id)
        return user

    @classmethod
    def clear_groups(cls, user: User):
        user.groups.clear()
        return user

    @classmethod
    def get_by_email(cls, email):
        """
        Retrieve user by its email

        Returns:
            User
        """
        return cls._model.objects.get(email=email)

    @classmethod
    def check_by_email(cls, email):
        """
        Check user exists by its email

        if found return user else raise NotFoundError

        Raises
            NotFoundError
        """
        # noinspection PyUnresolvedReferences
        try:
            return cls.get_by_email(email)
        except cls._model.DoesNotExist:
            raise exceptions.NotFoundError(f"user not found (email={email})")
