from w.serializers import serializer
from w.tests.fixtures.datasets.django_app import dtf_models


class CitySerializer(serializer.SerpySerializer):
    class Meta:
        model = dtf_models.City

    id = serializer.IntField()
    name = serializer.Field()


class AuthorSerializer(serializer.SerpySerializer):
    class Meta:
        model = dtf_models.Author

    id = serializer.IntField()
    firstname = serializer.Field()
    lastname = serializer.Field()
    birth_city = CitySerializer()


class SeriesSerializer(serializer.SerpySerializer):
    class Meta:
        model = dtf_models.Series

    id = serializer.IntField()
    name = serializer.Field()


class DepartmentSerializer(serializer.SerpySerializer):
    class Meta:
        model = dtf_models.Department

    id = serializer.IntField()
    name = serializer.Field()


class BookSerializer(serializer.SerpySerializer):
    class Meta:
        model = dtf_models.Book

    id = serializer.IntField()
    name = serializer.Field()
    author = AuthorSerializer()
    series = SeriesSerializer(serializer.SerpySerializer, required=False)
    departments = serializer.ManyToManyField(serializer=DepartmentSerializer)


class CharacterNoBooksSerializer(serializer.SerpySerializer):
    class Meta:
        model = dtf_models.Character

    id = serializer.IntField()
    firstname = serializer.Field()
    lastname = serializer.Field()


class CharacterSerializer(CharacterNoBooksSerializer):
    class Meta:
        model = dtf_models.Character

    list_books = serializer.ManyToManyField(serializer=BookSerializer, attr="books")


class One2OneCitySerializer(serializer.SerpySerializer):
    class Meta:
        model = dtf_models.One2OneCity

    id = serializer.IntField()
    is_one2one = serializer.BoolField()


class CityOne2OneSerializer(CitySerializer):
    one2one = serializer.MethodField()

    def get_one2one(self, o):
        if hasattr(o, "one2one"):
            return One2OneCitySerializer(o.one2one).data

    @classmethod
    def _foreign_keys(cls) -> dict:
        return {"one2one": One2OneCitySerializer}


class CharacterHiddenMany2ManySerializer(CharacterNoBooksSerializer):
    class Meta:
        model = dtf_models.Character

    list_books = serializer.MethodField()

    def get_list_books(self, o):
        if o and o.books.exists():
            return BookSerializer(o.books.all(), many=True).data
        return []

    @classmethod
    def _many2many(cls) -> dict:
        return {"books": BookSerializer}
