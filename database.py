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
            added_date TEXT NOT NULL
        )
    """)

    # Portfolio-Tabelle sicherstellen
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            name TEXT NOT NULL,
            isin TEXT NOT NULL,
            wkn TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            buy_price REAL NOT NULL,
            currency TEXT NOT NULL,
            buy_date TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
    print("✅ Datenbank & Tabellen wurden aktualisiert!")
