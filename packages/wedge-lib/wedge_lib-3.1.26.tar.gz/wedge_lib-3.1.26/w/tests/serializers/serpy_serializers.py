from w.test_utils.serializers.serpy_serializers import (
    RequestResponseSerializer as RequestResponseSerializerOk,
    MailOutboxSerializer as MailOutboxSerializerOk,
    UserSsoNoAuthUserTestSerializer as UserSsoNoAuthUserTestSerializerOk,
    UserSsoTestSerializer as UserSsoTestSerializerOk,
    UserWithSsoUserTestSerializer as UserWithSsoUserTestSerializerOk,
)


# deprecated
class RequestResponseSerializer(RequestResponseSerializerOk):
    """deprecated"""

    pass


# deprecated
class MailOutboxSerializer(MailOutboxSerializerOk):
    """deprecated"""

    pass


# deprecated
class UserSsoNoAuthUserTestSerializer(UserSsoNoAuthUserTestSerializerOk):
    """deprecated"""

    pass


# deprecated
class UserSsoTestSerializer(UserSsoTestSerializerOk):
    """deprecated"""

    pass


# deprecated
class UserWithSsoUserTestSerializer(UserWithSsoUserTestSerializerOk):
    """deprecated"""

    pass
