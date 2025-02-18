import sqlite3
from datetime import datetime

DB_PATH = "data/portfolio.db"

def seed_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Testdaten für Watchlist
    cursor.execute("INSERT INTO watchlist (ticker, name, isin, wkn, added_date, notes) VALUES (?, ?, ?, ?, ?, ?)",
                   ("AAPL", "Apple Inc.", "US0378331005", "865985", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Wachstumsaktie"))

    cursor.execute("INSERT INTO watchlist (ticker, name, isin, wkn, added_date, notes) VALUES (?, ?, ?, ?, ?, ?)",
                   ("MSFT", "Microsoft Corporation", "US5949181045", "870747", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Langfristiges Investment"))

    # Testdaten für Trades
    cursor.execute("INSERT INTO trades (ticker, name, date, type, shares, price_per_share, currency, total_price, fees, total_cost, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   ("AAPL", "Apple Inc.", "2025-02-16", "buy", 10, 145.50, "USD", 1455.00, 5.00, 1460.00, "Testkauf"))

    cursor.execute("INSERT INTO trades (ticker, name, date, type, shares, price_per_share, currency, total_price, fees, total_cost, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   ("MSFT", "Microsoft Corporation", "2025-02-16", "buy", 5, 320.00, "USD", 1600.00, 3.00, 1597.00, "Teilverkauf"))

    # Testdaten für Dividendenaktien
    cursor.execute("INSERT INTO dividend_stocks (last_updated, stock_name, isin, link, market_cap, stock_price, dividend_yield, total_return_10y, increasing_since, no_cut_since, dividend_stability, payout_ratio_profit, avg_div_growth_5y, avg_div_growth_10y, future_viability, business_model_future, score) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Realty Income", "US7561091049", "https://www.realtyincome.com", 45.2, 58.5, 4.7, 7.9, 25, 30, 90, 80, 4.2, 5.1, 5, 5, 85))

    conn.commit()
    conn.close()
    print("✅ Testdaten erfolgreich eingefügt.")

if __name__ == "__main__":
    seed_database()
