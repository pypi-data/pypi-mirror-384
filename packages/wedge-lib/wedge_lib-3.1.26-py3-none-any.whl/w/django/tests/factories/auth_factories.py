import factory
from django.contrib.auth import models

# crypted version of testtest
crypted = "argon2$argon2i$v=19$m=512,t=2,p=2$TXFvZTQ3RnVBQUV1$MIzwaXUe6yRwxm5zdTDmDg"


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.User

    username = factory.sequence(lambda n: f"user_{n}")
    first_name = factory.LazyAttribute(lambda o: f"{o.username[:20]}_firstname")
    last_name = factory.LazyAttribute(lambda o: f"{o.username}_lastname")
    email = factory.LazyAttribute(lambda o: f"{o.username}@test.com")

    password = crypted
    is_active = True

    is_staff = False
    is_superuser = False


class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Group

    name = factory.Sequence(lambda n: f"group_{n}")


class PermissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Permission

    name = factory.Sequence(lambda n: f"permission_{n}")
    content_type = factory.Iterator(models.ContentType.objects.all())
    codename = factory.lazy_attribute(
        lambda o: f"{o.content_type.model}_{o.name.lower().replace(' ', '_')}"
    )
