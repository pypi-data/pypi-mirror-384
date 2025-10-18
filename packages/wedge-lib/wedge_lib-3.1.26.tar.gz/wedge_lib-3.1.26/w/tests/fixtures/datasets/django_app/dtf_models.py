from django.db import models

from w.django.models import AbstractCreatedUpdatedModel


class City(models.Model):
    name = models.CharField(max_length=128)


class Author(models.Model):
    firstname = models.CharField(max_length=50)
    lastname = models.CharField(max_length=50)
    birth_city = models.ForeignKey(
        City, on_delete=models.CASCADE, related_name="authors", blank=True, null=True
    )


class Series(models.Model):
    name = models.CharField(max_length=128)


class Department(models.Model):
    name = models.CharField(max_length=128)


class Book(models.Model):
    name = models.CharField(max_length=128)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books")
    series = models.ForeignKey(
        Series, on_delete=models.CASCADE, related_name="books", blank=True, null=True
    )
    departments = models.ManyToManyField(Department, related_name="department")


class Character(models.Model):
    firstname = models.CharField(max_length=50)
    lastname = models.CharField(max_length=50)
    books = models.ManyToManyField(Book, related_name="characters")


class AutoNowModel(AbstractCreatedUpdatedModel):
    pass


class One2OneCity(models.Model):
    city = models.OneToOneField(City, on_delete=models.CASCADE, related_name="one2one")
    is_one2one = models.BooleanField(default=True)
