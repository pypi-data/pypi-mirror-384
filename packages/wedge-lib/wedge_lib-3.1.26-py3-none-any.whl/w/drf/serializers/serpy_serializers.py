from django.contrib.auth import models

from w.serializers import serializer


class ReferenceSerializer(serializer.SerpySerializer):
    code = serializer.StrField()
    label = serializer.StrField()


class I18nReferenceSerializer(ReferenceSerializer):
    label = serializer.TranslateField()


class GroupSerializer(serializer.SerpySerializer):
    class Meta:
        model = models.Group

    id = serializer.IntField()
    name = serializer.Field()


class UserSerializer(serializer.SerpySerializer):
    class Meta:
        model = models.User

    id = serializer.IntField()
    username = serializer.Field()
    first_name = serializer.Field()
    last_name = serializer.Field()
    email = serializer.Field()
    is_active = serializer.BoolField()


class UserWithGroupsSerializer(UserSerializer):
    groups = serializer.MethodField()

    def get_groups(self, o):  # pragma: no cover (todo one day)
        if o.groups and o.groups.exists():
            return GroupSerializer(o.groups.all().order_by("id"), many=True).data
        return []


class UserWithOneGroupSerializer(UserSerializer):
    group = serializer.ManyToFirstField(serializer=GroupSerializer, attr="groups")


class UserWithDateSerializer(UserSerializer):
    date_joined = serializer.DateField()
