from django.core.management.base import BaseCommand
from portfolios.etl import PortfolioETL
from datetime import datetime
from decimal import Decimal
from portfolios.models import Portfolio, AssetPrice, PortfolioHolding


class Command(BaseCommand):
    help = 'Load portfolio data from Excel file'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Path to Excel file')

    def handle(self, *args, **options):
        excel_file = options['excel_file']
        etl = PortfolioETL(excel_file)
        self.stdout.write('Cargando datos...')
        etl.load_data()
        self.stdout.write(self.style.SUCCESS('Datos cargados correctamente'))
        initial_price = AssetPrice.objects.order_by('date').first()
        if initial_price:
            fecha_inicial = initial_price.date
            p1 = Portfolio.objects.get(name='Portfolio 1')
            holdings_ini = PortfolioHolding.objects.filter(portfolio=p1, date=fecha_inicial)
            total_ini = sum(h.amount for h in holdings_ini)
            self.stdout.write(f"Fecha inicial: {fecha_inicial}")
            self.stdout.write(f"Portafolio 1 V0 calculado: {total_ini}")
            for h in holdings_ini.order_by('asset__symbol')[:5]:
                self.stdout.write(f"{h.asset.symbol}: cantidad={h.quantity} monto={h.amount} weight={h.weight}")
        self.stdout.write('Procesando transacción...')
        etl.process_transaction(
            'Portfolio 1',
            'EEUU',
            Decimal('200000000'),
            'Europa',
            Decimal('200000000'),
            datetime(2022, 5, 15).date()
        )
        self.stdout.write(self.style.SUCCESS('Transacción procesada correctamente'))
        fecha_tx = datetime(2022, 5, 15).date()
        p1 = Portfolio.objects.get(name='Portfolio 1')
        holdings_tx = PortfolioHolding.objects.filter(portfolio=p1, date=fecha_tx)
        total_tx = sum(h.amount for h in holdings_tx)
        self.stdout.write(f"Fecha transacción: {fecha_tx} Vt: {total_tx}")
        for h in holdings_tx.order_by('asset__symbol')[:5]:
            self.stdout.write(f"{h.asset.symbol}: cantidad={h.quantity} monto={h.amount} weight={h.weight}")
