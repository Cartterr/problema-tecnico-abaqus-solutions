import os
import sys
import django
from decimal import Decimal
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio_management.settings')
django.setup()

from portfolios.etl import PortfolioETL
from portfolios.models import Portfolio, Asset, PortfolioHolding, AssetPrice, Transaction

def safe_load_data(excel_file):
    print("🔄 Iniciando carga segura de datos...")

    try:
        etl = PortfolioETL(excel_file)
        print("📊 Cargando datos básicos...")
        etl.load_data()
        print("✅ Datos básicos cargados correctamente")

        initial_price = AssetPrice.objects.order_by('date').first()
        if initial_price:
            fecha_inicial = initial_price.date
            p1 = Portfolio.objects.get(name='Portfolio 1')
            holdings_ini = PortfolioHolding.objects.filter(portfolio=p1, date=fecha_inicial)
            total_ini = sum(h.amount for h in holdings_ini)
            print(f"📅 Fecha inicial: {fecha_inicial}")
            print(f"💰 Portafolio 1 V0: ${total_ini:,.2f}")

            for h in holdings_ini.order_by('asset__symbol')[:5]:
                print(f"   {h.asset.symbol}: cantidad={h.quantity} monto=${h.amount:,.2f} peso={h.weight:.6f}")

        print("\n💱 Procesando transacción (esto puede tomar unos minutos)...")
        try:
            etl.process_transaction(
                'Portfolio 1',
                'EEUU',
                Decimal('200000000'),
                'Europa',
                Decimal('200000000'),
                datetime(2022, 5, 15).date()
            )
            print("✅ Transacción procesada correctamente")
        except Exception as e:
            print(f"❌ Error en transacción: {e}")
            print("   Los datos básicos están cargados, pero la transacción falló")
            return False

        fecha_tx = datetime(2022, 5, 15).date()
        holdings_tx = PortfolioHolding.objects.filter(portfolio=p1, date=fecha_tx)
        if holdings_tx.exists():
            total_tx = sum(h.amount for h in holdings_tx)
            print(f"📅 Fecha transacción: {fecha_tx}")
            print(f"💰 Valor después de transacción: ${total_tx:,.2f}")

        return True

    except Exception as e:
        print(f"❌ Error crítico durante carga: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/safe_load_data.py <archivo_excel>")
        sys.exit(1)

    excel_file = sys.argv[1]
    if not os.path.exists(excel_file):
        print(f"❌ Archivo no encontrado: {excel_file}")
        sys.exit(1)

    success = safe_load_data(excel_file)
    if success:
        print("\n🎉 ¡Carga completada exitosamente!")
        print("   Puedes ejecutar: python scripts/start_server.py")
    else:
        print("\n⚠️ Carga completada con errores")
        print("   Algunos datos pueden estar disponibles")
        print("   Revisa los logs arriba para más detalles")
