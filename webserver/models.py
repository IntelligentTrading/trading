from django.db import models


class User(models.Model):
    api_key = models.TextField(db_index=True, max_length=32, unique=True)
    date_created = models.DateTimeField()


class Statistics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mid_market_price = models.FloatField()
    average_exec_price = models.FloatField()
    volume = models.FloatField()
    pair = models.CharField(max_length=10)
    fee = models.FloatField()
    action = models.CharField(max_length=4, choices=[("buy", "buy"),
                                                     ("sell", "sell")])
