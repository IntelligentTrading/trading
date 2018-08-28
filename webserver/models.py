from django.db import models
import jsonfield


class User(models.Model):
    api_key = models.TextField(db_index=True, max_length=32, unique=True)
    date_created = models.DateTimeField()


class Statistics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    data = jsonfield.JSONField()
