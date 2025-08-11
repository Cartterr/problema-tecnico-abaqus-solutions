import pandas as pd
from decimal import Decimal
from datetime import datetime
from django.db import transaction as db_transaction
from tqdm import tqdm
from .models import Asset, Portfolio, AssetPrice, PortfolioWeight, PortfolioHolding, Transaction


class PortfolioETL:
    def __init__(self, excel_file_path):
        self.excel_file_path = excel_file_path

    def load_data(self):
        print('Leyendo planilla...')
        weights_df = pd.read_excel(self.excel_file_path, sheet_name='Weights')
        prices_df = pd.read_excel(self.excel_file_path, sheet_name='Precios')
        print('Cargando activos y pesos...')
        self.load_assets_and_weights(weights_df)
        print('Cargando precios...')
        self.load_prices(prices_df)
        print('Calculando holdings...')
        self.calculate_holdings()
        print('Holdings calculados')

    def load_assets_and_weights(self, weights_df):
        Portfolio.objects.get_or_create(name='Portfolio 1')
        Portfolio.objects.get_or_create(name='Portfolio 2')
        created_weights = 0
        for index, row in weights_df.iterrows():
            symbol = row.get('B')
            w1 = row.get('C')
            w2 = row.get('D')
            if isinstance(symbol, str) and symbol and symbol != 'Asset':
                asset, _ = Asset.objects.get_or_create(symbol=symbol, defaults={'name': symbol})
                if pd.notna(w1) and isinstance(w1, (int, float)):
                    _, created = PortfolioWeight.objects.get_or_create(
                        portfolio=Portfolio.objects.get(name='Portfolio 1'),
                        asset=asset,
                        defaults={'weight': Decimal(str(w1))}
                    )
                    if created:
                        created_weights += 1
                if pd.notna(w2) and isinstance(w2, (int, float)):
                    _, created = PortfolioWeight.objects.get_or_create(
                        portfolio=Portfolio.objects.get(name='Portfolio 2'),
                        asset=asset,
                        defaults={'weight': Decimal(str(w2))}
                    )
                    if created:
                        created_weights += 1
        print(f"Activos: {Asset.objects.count()} Pesos creados: {created_weights}")

    def load_prices(self, prices_df):
        prices_df.columns = prices_df.columns.astype(str)
        date_column = prices_df.columns[0]
        inserted = 0
        for index, row in prices_df.iterrows():
            if pd.notna(row[date_column]):
                date = pd.to_datetime(row[date_column]).date()
                for col in prices_df.columns[1:]:
                    val = row[col]
                    if pd.notna(val) and isinstance(val, (int, float)):
                        try:
                            asset = Asset.objects.get(symbol=col)
                            _, created = AssetPrice.objects.get_or_create(
                                asset=asset,
                                date=date,
                                defaults={'price': Decimal(str(val))}
                            )
                            if created:
                                inserted += 1
                        except Asset.DoesNotExist:
                            continue
        print(f"Precios insertados: {inserted}")

    def calculate_holdings(self):
        dates = list(AssetPrice.objects.values_list('date', flat=True).distinct().order_by('date'))
        portfolios = Portfolio.objects.all()
        for portfolio in portfolios:
            print(f"Calculando {portfolio.name}")
            PortfolioHolding.objects.filter(portfolio=portfolio).delete()
            weights = list(PortfolioWeight.objects.filter(portfolio=portfolio).select_related('asset'))
            initial_quantities = {}
            for w in weights:
                initial_price = AssetPrice.objects.filter(asset=w.asset).order_by('date').first()
                if not initial_price:
                    continue
                qty = ((w.weight * portfolio.initial_value) / initial_price.price).quantize(Decimal('0.000001'))
                initial_quantities[w.asset_id] = qty
            asset_ids = list(initial_quantities.keys())
            holdings_to_create = []
            for d in dates:
                prices = AssetPrice.objects.filter(date=d, asset_id__in=asset_ids)
                price_map = {p.asset_id: p.price for p in prices}
                total_value = Decimal('0')
                amounts = {}
                for aid, qty in initial_quantities.items():
                    price = price_map.get(aid)
                    if price is None:
                        continue
                    amt = (Decimal(str(qty)) * Decimal(str(price))).quantize(Decimal('0.01'))
                    amounts[aid] = amt
                    total_value += amt
                if total_value == 0:
                    continue
                for aid, qty in initial_quantities.items():
                    price = price_map.get(aid)
                    if price is None:
                        continue
                    amt = amounts[aid]
                    wgt = (amt / total_value).quantize(Decimal('0.000001'))
                    holdings_to_create.append(PortfolioHolding(
                        portfolio=portfolio,
                        asset_id=aid,
                        date=d,
                        quantity=qty,
                        amount=amt,
                        weight=wgt
                    ))
            if holdings_to_create:
                PortfolioHolding.objects.bulk_create(holdings_to_create, ignore_conflicts=True)

    def process_transaction(self, portfolio_name, sell_asset, sell_amount, buy_asset, buy_amount, transaction_date):
        print('Iniciando transacción...')
        portfolio = Portfolio.objects.get(name=portfolio_name)
        sell_asset_obj = Asset.objects.get(symbol=sell_asset)
        buy_asset_obj = Asset.objects.get(symbol=buy_asset)
        sell_price = AssetPrice.objects.get(asset=sell_asset_obj, date=transaction_date)
        buy_price = AssetPrice.objects.get(asset=buy_asset_obj, date=transaction_date)
        sell_quantity = (sell_amount / sell_price.price).quantize(Decimal('0.000001'))
        buy_quantity = (buy_amount / buy_price.price).quantize(Decimal('0.000001'))
        print(f"Vender {sell_asset}: {sell_amount} -> qty {sell_quantity}")
        print(f"Comprar {buy_asset}: {buy_amount} -> qty {buy_quantity}")
        Transaction.objects.create(portfolio=portfolio, asset=sell_asset_obj, date=transaction_date, transaction_type='SELL', amount=sell_amount, quantity=sell_quantity)
        Transaction.objects.create(portfolio=portfolio, asset=buy_asset_obj, date=transaction_date, transaction_type='BUY', amount=buy_amount, quantity=buy_quantity)
        print('Recalculando holdings posteriores a la transacción...')
        self.recalculate_holdings_after_transaction(portfolio, transaction_date)
        print('Re cálculo de holdings terminado')

    def recalculate_holdings_after_transaction(self, portfolio, transaction_date):
        weights = list(PortfolioWeight.objects.filter(portfolio=portfolio).select_related('asset'))
        initial_quantities = {}
        for w in weights:
            initial_price = AssetPrice.objects.filter(asset=w.asset).order_by('date').first()
            if not initial_price:
                continue
            qty = ((w.weight * portfolio.initial_value) / initial_price.price).quantize(Decimal('0.000001'))
            initial_quantities[w.asset_id] = qty
        txs = Transaction.objects.filter(portfolio=portfolio, date__lte=transaction_date)
        for t in txs:
            current_qty = initial_quantities.get(t.asset_id, Decimal('0'))
            if t.transaction_type == 'BUY':
                new_qty = (current_qty + t.quantity).quantize(Decimal('0.000001'))
                initial_quantities[t.asset_id] = new_qty
            else:
                new_qty = (current_qty - t.quantity).quantize(Decimal('0.000001'))
                if new_qty < 0:
                    new_qty = Decimal('0')
                initial_quantities[t.asset_id] = new_qty
        asset_ids = list(initial_quantities.keys())
        future_dates = list(AssetPrice.objects.filter(asset_id__in=asset_ids, date__gte=transaction_date).values_list('date', flat=True).distinct().order_by('date'))
        print(f"Fechas a recalcular: {len(future_dates)} Activos: {len(asset_ids)}")

        negative_qty_count = 0
        decimal_error_count = 0

        for d in tqdm(future_dates, desc='Fechas', unit='d'):
            prices = AssetPrice.objects.filter(date=d, asset_id__in=asset_ids)
            price_map = {p.asset_id: p.price for p in prices}
            total_value = Decimal('0')
            amounts = {}
            for aid, qty in initial_quantities.items():
                price = price_map.get(aid)
                if price is None:
                    continue
                amt = (Decimal(str(qty)) * Decimal(str(price))).quantize(Decimal('0.01'))
                amounts[aid] = amt
                total_value += amt
            if total_value == 0:
                continue
            for aid, qty in initial_quantities.items():
                price = price_map.get(aid)
                if price is None:
                    continue

                if qty < 0:
                    negative_qty_count += 1
                    continue

                amt = amounts[aid]
                wgt = (amt / total_value).quantize(Decimal('0.000001'))

                try:
                    holding, created = PortfolioHolding.objects.get_or_create(
                        portfolio=portfolio,
                        asset_id=aid,
                        date=d,
                        defaults={
                            'quantity': Decimal(str(qty)).quantize(Decimal('0.000001')),
                            'amount': Decimal(str(amt)).quantize(Decimal('0.01')),
                            'weight': Decimal(str(wgt)).quantize(Decimal('0.000001'))
                        }
                    )
                    if not created:
                        holding.quantity = Decimal(str(qty)).quantize(Decimal('0.000001'))
                        holding.amount = Decimal(str(amt)).quantize(Decimal('0.01'))
                        holding.weight = Decimal(str(wgt)).quantize(Decimal('0.000001'))
                        holding.save()
                except Exception as e:
                    decimal_error_count += 1
                    continue

        if negative_qty_count > 0 or decimal_error_count > 0:
            print(f"\nResumen de errores manejados:")
            if negative_qty_count > 0:
                print(f"  - Cantidades negativas omitidas: {negative_qty_count}")
            if decimal_error_count > 0:
                print(f"  - Errores de precisión decimal: {decimal_error_count}")

    def calculate_portfolio_value_with_transactions(self, portfolio, date):
        total_value = Decimal('0')
        transactions = Transaction.objects.filter(portfolio=portfolio, date__lte=date)
        for asset in Asset.objects.all():
            initial_weight = PortfolioWeight.objects.filter(portfolio=portfolio, asset=asset).first()
            if not initial_weight:
                continue
            initial_price = AssetPrice.objects.filter(asset=asset).order_by('date').first()
            current_price = AssetPrice.objects.filter(asset=asset, date=date).first()
            if not initial_price or not current_price:
                continue
            initial_quantity = (initial_weight.weight * portfolio.initial_value) / initial_price.price
            asset_transactions = transactions.filter(asset=asset)
            for transaction in asset_transactions:
                if transaction.transaction_type == 'BUY':
                    initial_quantity += transaction.quantity
                else:
                    initial_quantity -= transaction.quantity
            amount = initial_quantity * current_price.price
            total_value += amount
        return total_value
