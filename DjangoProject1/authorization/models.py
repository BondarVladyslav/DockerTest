from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE , related_name='additional_data')
    bio = models.TextField(blank=True, null=True)
    favourite_books = models.ManyToManyField('books.Book', related_name='favourite_books', blank=True)
    finished_books = models.ManyToManyField('books.Book', related_name='finished_books', blank=True)
    def __str__(self):
        return self.user.username