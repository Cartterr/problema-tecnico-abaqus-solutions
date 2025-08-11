from django.db import models
from decimal import Decimal


class Asset(models.Model):
    symbol = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.symbol


class Portfolio(models.Model):
    name = models.CharField(max_length=50)
    initial_value = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('1000000000'))

    def __str__(self):
        return self.name


class AssetPrice(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    date = models.DateField()
    price = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        unique_together = ['asset', 'date']


class PortfolioWeight(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=8, decimal_places=6)

    class Meta:
        unique_together = ['portfolio', 'asset']


class PortfolioHolding(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    date = models.DateField()
    quantity = models.DecimalField(max_digits=15, decimal_places=6)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    weight = models.DecimalField(max_digits=8, decimal_places=6)

    class Meta:
        unique_together = ['portfolio', 'asset', 'date']


class Transaction(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    date = models.DateField()
    transaction_type = models.CharField(max_length=10, choices=[('BUY', 'Buy'), ('SELL', 'Sell')])
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    quantity = models.DecimalField(max_digits=15, decimal_places=6)
