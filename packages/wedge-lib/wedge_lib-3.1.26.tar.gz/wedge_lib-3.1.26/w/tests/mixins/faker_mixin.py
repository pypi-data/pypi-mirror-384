import factory


class FakerMixin:
    @classmethod
    def faker(cls, provider, **kwargs):
        """
        Wrapper for 'faker' values.

        Args:
            provider(str): the name of the Faker field
            **kwargs: provider params
        """
        return factory.Faker(provider, **kwargs).generate()

    @classmethod
    def fake_str(cls, length) -> str:
        """Generate random str of length characters"""
        return cls.faker("pystr", min_chars=length, max_chars=length)
