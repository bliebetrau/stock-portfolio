import sqlite3

DB_PATH = "data/portfolio.db"

def create_tables():
    """Erstellt oder aktualisiert die notwendigen Tabellen für die Watchlist und das Portfolio."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Watchlist-Tabelle neu erstellen
    cursor.execute("DROP TABLE IF EXISTS watchlist")  # Alte Tabelle löschen
    cursor.execute("""
        CREATE TABLE watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            isin TEXT UNIQUE,
            wkn TEXT UNIQUE,
            notes TEXT,
            added_date TEXT NOT NULL
        )
    """)

    # Tabelle für Trades
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            type TEXT CHECK( type IN ('buy', 'sell') ) NOT NULL,
            shares INTEGER NOT NULL,
            price_per_share REAL NOT NULL,
            currency TEXT NOT NULL,
            total_price REAL NOT NULL,
            fees REAL DEFAULT 0,
            taxes REAL DEFAULT 0,
            total_cost REAL NOT NULL,
            notes TEXT
        );
    """)

       # Neue Tabelle für Dividendenaktien hinzufügen
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dividend_stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_updated TEXT NOT NULL,
            stock_name TEXT NOT NULL,
            isin TEXT UNIQUE NOT NULL,
            link TEXT,
            market_cap REAL,
            stock_price REAL,
            ath_price REAL,
            annual_return REAL,
            dividend_yield REAL,
            total_10y_return REAL,
            dividends_per_year INTEGER,
            increasing_since INTEGER,
            no_cut_since INTEGER,
            dividend_stability REAL,
            payout_ratio_profit REAL,
            payout_ratio_cashflow REAL,
            avg_div_growth_5y REAL,
            avg_div_growth_10y REAL,
            special_dividends INTEGER,
            future_viability INTEGER,
            business_model_future INTEGER,
            score REAL
        );
    """)


    conn.commit()
    conn.close()

def update_portfolio_view():
    """Erstellt oder aktualisiert die Portfolio-View mit aggregierten Daten."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Falls die View bereits existiert, löschen wir sie zuerst
    cursor.execute("DROP VIEW IF EXISTS portfolio_view")

   # Neue Portfolio-View erstellen (mit aktuellen Kursdaten)
    cursor.execute("""
        CREATE VIEW portfolio_view AS
        SELECT
            w.ticker AS ticker,
            w.name AS name,
            w.isin AS isin,
            w.wkn AS wkn,
            COALESCE(SUM(CASE WHEN t.type = 'buy' THEN t.shares ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN t.type = 'sell' THEN t.shares ELSE 0 END), 0) AS total_shares,
            CASE 
                WHEN SUM(CASE WHEN t.type = 'buy' THEN t.shares ELSE 0 END) > 0 
                THEN SUM(CASE WHEN t.type = 'buy' THEN t.total_cost ELSE 0 END) /
                    SUM(CASE WHEN t.type = 'buy' THEN t.shares ELSE 0 END)
                ELSE NULL
            END AS avg_buy_price,
            COALESCE(SUM(CASE WHEN t.type = 'buy' THEN t.total_cost ELSE 0 END), 0) AS total_invested,
            MAX(t.currency) AS currency
        FROM watchlist w
        LEFT JOIN trades t ON w.ticker = t.ticker
        GROUP BY w.ticker, w.name, w.isin, w.wkn
        HAVING total_shares > 0;

    """)


    conn.commit()
    conn.close()
    print("✅ Portfolio-View wurde erfolgreich aktualisiert!")

if __name__ == "__main__":
    create_tables()
    update_portfolio_view()
    print("✅ Datenbank & Portfolio-View wurden aktualisiert!")
