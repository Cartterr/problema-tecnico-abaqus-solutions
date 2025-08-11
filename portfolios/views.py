from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render
from django.db.models import Sum
from .models import PortfolioHolding, Asset, Portfolio, AssetPrice, Transaction
from .serializers import PortfolioHoldingSerializer
from datetime import datetime
import socket
import subprocess


@api_view(['GET'])
def portfolio_weights(request):
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    holdings = PortfolioHolding.objects.all()
    if fecha_inicio:
        holdings = holdings.filter(date__gte=datetime.strptime(fecha_inicio, '%Y-%m-%d').date())
    if fecha_fin:
        holdings = holdings.filter(date__lte=datetime.strptime(fecha_fin, '%Y-%m-%d').date())
    serializer = PortfolioHoldingSerializer(holdings, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def portfolio_values(request):
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    holdings = PortfolioHolding.objects.values('date', 'portfolio__name').annotate(
        total_value=Sum('amount')
    ).order_by('date', 'portfolio__name')
    if fecha_inicio:
        holdings = holdings.filter(date__gte=datetime.strptime(fecha_inicio, '%Y-%m-%d').date())
    if fecha_fin:
        holdings = holdings.filter(date__lte=datetime.strptime(fecha_fin, '%Y-%m-%d').date())
    data = [
        {
            'date': item['date'],
            'portfolio_name': item['portfolio__name'],
            'total_value': item['total_value']
        }
        for item in holdings
    ]
    return Response(data)


def dashboard(request):
    return render(request, 'dashboard.html')


@api_view(['GET'])
def test_data(request):
    try:
        assets_count = Asset.objects.count()
        portfolios_count = Portfolio.objects.count()
        holdings_count = PortfolioHolding.objects.count()
        prices_count = AssetPrice.objects.count()
        transactions_count = Transaction.objects.count()

        message = f"Assets: {assets_count}, Portfolios: {portfolios_count}, Holdings: {holdings_count}, Prices: {prices_count}, Transactions: {transactions_count}"

        if assets_count > 0 and holdings_count > 0:
            return Response({
                'success': True,
                'message': message,
                'details': {
                    'assets': assets_count,
                    'portfolios': portfolios_count,
                    'holdings': holdings_count,
                    'prices': prices_count,
                    'transactions': transactions_count
                }
            })
        else:
            return Response({
                'success': False,
                'message': f"Datos incompletos: {message}"
            })
    except Exception as e:
        return Response({
            'success': False,
            'message': f"Error verificando datos: {str(e)}"
        })


@api_view(['GET'])
def test_ports(request):
    def check_port(port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result != 0

    test_ports = [8000, 8080, 3000, 5000, 8888, 9000]
    available_ports = [port for port in test_ports if check_port(port)]

    current_port = request.get_port() if hasattr(request, 'get_port') else 'unknown'

    return Response({
        'message': f"Puerto actual: {current_port}",
        'available_ports': available_ports,
        'total_checked': len(test_ports)
    })
