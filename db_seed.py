import sqlite3
from datetime import datetime

DB_PATH = "data/portfolio.db"

def seed_database():
    """Befüllt die Datenbank mit initialen Dividendenaktien-Testdaten."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Testdaten für Dividendenaktien
    test_data = [
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Realty Income", "US7561091049", "https://www.realtyincome.com", 
            45.2, 58.5, 75.0, 7.9, 4.7, 7.9, 12, 25, 30, 0.9, 80, 75, 4.2, 5.1, 1, 5, 5, 85
        ),
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Höegh Autoliners", "NO0010936035", "https://www.hoeghautoliners.com", 
            2.8, 63.5, 68.7, 7.8, 9.2, 12.3, 4, 5, 10, 0.85, 70, 65, 6.5, 7.0, 1, 4, 5, 80
        ),
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Microsoft", "US5949181045", "https://www.microsoft.com", 
            2900.0, 400.5, 415.0, 12.1, 0.8, 15.2, 4, 19, 30, 0.95, 35, 30, 8.5, 9.2, 0, 5, 5, 95
        ),
    ]

    # SQL-Query für das Einfügen der Testdaten
    cursor.executemany("""
        INSERT INTO dividend_stocks (
            last_updated, stock_name, isin, link, market_cap, stock_price, ath_price, annual_return,
            dividend_yield, total_10y_return, dividends_per_year, increasing_since, no_cut_since, 
            dividend_stability, payout_ratio_profit, payout_ratio_cashflow, avg_div_growth_5y, 
            avg_div_growth_10y, special_dividends, future_viability, business_model_future, score
        ) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, test_data)

    conn.commit()
    conn.close()
    print("✅ Testdaten erfolgreich in die Datenbank eingetragen.")

if __name__ == "__main__":
    seed_database()
