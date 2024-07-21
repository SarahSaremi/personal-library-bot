from django.db import models


class Book(models.Model):
    title = models.CharField(max_length=200)
    writer = models.CharField(max_length=100)
    translator = models.CharField(max_length=100, null=True, blank=True)
    borrower = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.title
