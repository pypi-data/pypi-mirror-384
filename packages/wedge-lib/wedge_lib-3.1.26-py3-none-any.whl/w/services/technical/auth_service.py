from w.services.abstract_service import AbstractService


class AuthService(AbstractService):
    @classmethod
    def generate_token(cls):  # pragma: no cover
        # generate unique token
        import uuid

        return uuid.uuid4().hex

    @classmethod
    def generate_random_pwd(cls):
        return cls.generate_token()
