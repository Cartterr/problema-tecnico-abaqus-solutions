import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)
assets = ['EEUU', 'Europa', 'Japon', 'China', 'Brasil', 'India', 'Rusia', 'Australia', 'Canada', 'Mexico', 'Chile', 'Argentina', 'Colombia', 'Peru', 'Oro', 'Plata', 'Petroleo']
weights_data = {
    'A': [''] + assets,
    'B': ['Asset'] + assets,
    'C': ['Portfolio 1'] + list(np.random.dirichlet(np.ones(17))),
    'D': ['Portfolio 2'] + list(np.random.dirichlet(np.ones(17)))
}
start_date = datetime(2022, 2, 15)
end_date = datetime(2023, 2, 16)
dates = []
current_date = start_date
while current_date <= end_date:
    dates.append(current_date)
    current_date += timedelta(days=1)
prices_data = {'Date': dates}
initial_prices = np.random.uniform(50, 500, len(assets))
for i, asset in enumerate(assets):
    prices = [initial_prices[i]]
    for _ in range(len(dates) - 1):
        change = np.random.normal(0, 0.02)
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 1))
    prices_data[asset] = prices
weights_df = pd.DataFrame(weights_data)
prices_df = pd.DataFrame(prices_data)
with pd.ExcelWriter('data/datos.xlsx') as writer:
    weights_df.to_excel(writer, sheet_name='Weights', index=False)
    prices_df.to_excel(writer, sheet_name='Precios', index=False)
print("Fake data created successfully in data/datos.xlsx")
