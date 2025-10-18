import factory
from w.django.models import Reference


class ReferenceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Reference

    code = factory.lazy_attribute(lambda o: o.label.upper())
    label = factory.Sequence(lambda n: f"reference_{n}")
