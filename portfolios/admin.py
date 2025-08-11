from django.contrib import admin
from .models import Asset, Portfolio, AssetPrice, PortfolioWeight, PortfolioHolding, Transaction

admin.site.register(Asset)
admin.site.register(Portfolio)
admin.site.register(AssetPrice)
admin.site.register(PortfolioWeight)
admin.site.register(PortfolioHolding)
admin.site.register(Transaction)
