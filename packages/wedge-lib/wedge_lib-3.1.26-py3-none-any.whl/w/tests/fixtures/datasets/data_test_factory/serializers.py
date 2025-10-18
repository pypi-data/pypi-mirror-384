from w.serializers import serializer


class CitySerializer(serializer.SerpySerializer):
    id = serializer.IntField()
    name = serializer.Field()


class AuthorSerializer(serializer.SerpySerializer):
    id = serializer.IntField()
    firstname = serializer.Field()
    lastname = serializer.Field()


class SeriesSerializer(serializer.SerpySerializer):
    id = serializer.IntField()
    name = serializer.Field()


class BookSerializer(serializer.SerpySerializer):
    id = serializer.IntField()
    name = serializer.Field()
    author = AuthorSerializer()
    series = SeriesSerializer(serializer.SerpySerializer, required=False)


class SeriesBooksSerializer(SeriesSerializer):
    books = serializer.ManyToManyField(serializer=BookSerializer)


class CharacterNoBooksSerializer(serializer.SerpySerializer):
    id = serializer.IntField()
    firstname = serializer.Field()
    lastname = serializer.Field()


class CharacterSerializer(CharacterNoBooksSerializer):
    books = serializer.ManyToManyField(serializer=BookSerializer)


class BookCharactersSerializer(BookSerializer):
    characters = serializer.ManyToManyField(serializer=CharacterNoBooksSerializer)


class AutoNowModelSerializer(serializer.SerpySerializer):
    created_at = serializer.DatetimeField()
    updated_at = serializer.DatetimeField()


class One2OneCitySerializer(serializer.SerpySerializer):
    city = CitySerializer()
    is_one2one = serializer.BoolField()
