from django.db import models

from w.django.models import AbstractSsoUser


class Example(models.Model):
    attribute_one = models.CharField(max_length=50)
    attribute_two = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.attribute_one}/{self.attribute_two}"


class FkOne(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name}"


class FkTwo(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name}"


class ExampleWithFks(models.Model):
    name = models.CharField(max_length=50)
    fk_one = models.ForeignKey(FkOne, on_delete=models.CASCADE)
    fk_two = models.ForeignKey(FkTwo, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.fk_one}/{self.fk_two})"


class InternalDependencyOne(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name}"


class InternalDependencyTwo(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name}"


class ExampleWithInternalDependencies(models.Model):
    name = models.CharField(max_length=50)
    internal_one = models.ForeignKey(InternalDependencyOne, on_delete=models.CASCADE)
    internal_two = models.ForeignKey(InternalDependencyTwo, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.internal_one}/{self.internal_two})"


class SsoUser(AbstractSsoUser):
    pass
