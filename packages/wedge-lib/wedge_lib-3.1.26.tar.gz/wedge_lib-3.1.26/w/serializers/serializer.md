## Common Serializer

Ce serializer est basé sur Serpy. Cette documentation suppose donc une bonne connaisance
de Serpy. Documentation: https://serpy.readthedocs.io/en/latest/

## ORM optimization

Le serializer a été conçu pour fonctionner spécifiquement avec l’ORM Django. 

Cependant, il reste le pb d’optimisation du QuerySet qui va permettre de limiter le nombre de requête à la DB pour serialiser les données.

Le serializer offre la méthode `get_optimized_queryset()`. Cette méthode va optimiser automatiquement le QuerySet nécessaire à la sérialisation complète afin de rendre beaucoup plus performant la récupération des données.

Pour ce faire, il est nécessaire de renseigner le model Django correspondant à la sérialisation (voir exemple).

Cependant, il possible que `get_optimized_queryset()` ne puisse détecter l'optimisation à faire, notamment dans le cas de l'utilisation de `serializer.MethodField`.

Dans ce cas, il faut préciser via 2 méthodes le champs et son serializer:
- `_foreign_keys`
- `_many2many`

ex:

 ```python
from typing import Type
from django.db import models
from w.serializers import serializer

## MODELS

class ProductionCompany(models.Model):
    name = models.CharField()

class Singer(models.Model):
    name = models.CharField()
    production_company = ProductionCompany()

class Album(models.Model):
    name = models.CharField()
    singer = models.ForeignKey(Singer)

class Track(models.Model):
    rank = models.IntegerField()
    name = models.CharField()
    album = models.ForeignKey(Album, related_name="tracks")

## SERIALIZER

class ProductionCompanySerializer(serializer.SerpySerializer):
    class Meta:
        model = ProductionCompany
        
    name = serializer.Field()

class SingerSerializer(serializer.SerpySerializer):
    class Meta:
        model = Singer
        
    name = serializer.Field()
    production_company = ProductionCompanySerializer()


class TrackSerializer(serializer.SerpySerializer):
    class Meta:
        model = Track
        
    rank = serializer.IntField()
    name = serializer.Field()

class AlbumSerializer(serializer.SerpySerializer):
    class Meta:
        model = Album

    name = serializer.Field()
    singer = SingerSerializer()
    tracks = serializer.ManyToManyField(serializer=TrackSerializer)
    
class Album2Serializer(serializer.SerpySerializer):
    class Meta:
        model = Album

    name = serializer.Field()
    singer = serializer.MethodField()
    tracks = serializer.MethodField()
    
    @classmethod
    def _foreign_keys(cls) -> dict[str, Type[serializer.SerpySerializer]]:
        return {"singer": SingerSerializer}
    
    @classmethod
    def _many2many(cls) -> dict[str, Type[serializer.SerpySerializer]]:
        return {"tracks": TrackSerializer}
    
# AlbumSerializer == Album2Serializer

## USAGE

# cet exemple 
qs = SingerSerializer.get_optimized_queryset(Singer.objects)
serialized = SingerSerializer(qs).data

# est équivalent à
qs = Singer.objects.select_related("production_company")
serialized = SingerSerializer(qs).data

# cet exemple 
qs = AlbumSerializer.get_optimized_queryset(Album.objects)
serialized = AlbumSerializer(qs).data

# est équivalent à
qs = Album.objects.select_related("singer__production_company").prefetch_related("tracks")
serialized = SingerSerializer(qs).data
```


