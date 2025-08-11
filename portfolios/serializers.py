from rest_framework import serializers
from .models import PortfolioHolding


class PortfolioHoldingSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.symbol', read_only=True)
    portfolio_name = serializers.CharField(source='portfolio.name', read_only=True)

    class Meta:
        model = PortfolioHolding
        fields = ['date', 'asset_name', 'portfolio_name', 'quantity', 'amount', 'weight']


class PortfolioValueSerializer(serializers.Serializer):
    date = serializers.DateField()
    portfolio_name = serializers.CharField()
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2)
