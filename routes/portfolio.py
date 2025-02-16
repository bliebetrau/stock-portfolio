from flask import Blueprint, render_template
import sqlite3
import yfinance as yf

portfolio = Blueprint("portfolio", __name__)

DB_PATH = "data/portfolio.db"

@portfolio.route("/portfolio")
def show_portfolio():
    """Lädt die Portfolio-Daten aus der View und ergänzt sie um aktuelle Kursdaten."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Ergebnisse als Dictionary abrufen
    cursor = conn.cursor()

    # Portfolio-Daten abrufen
    cursor.execute("SELECT * FROM portfolio_view")
    portfolio_data = [dict(row) for row in cursor.fetchall()]  # In Liste von Dictionaries umwandeln

    # Trades-Daten abrufen (sortiert nach Datum absteigend)
    cursor.execute("SELECT * FROM trades ORDER BY date DESC")
    trades_data = [dict(row) for row in cursor.fetchall()]  # In Liste von Dictionaries umwandeln

    conn.close()

    # **Summen-Variablen initialisieren**
    total_invested = 0
    total_market_value = 0
    total_profit_loss_absolute = 0
    total_profit_loss_percentage = 0

    # **API-Daten ergänzen & Summen berechnen**
    for stock in portfolio_data:
        ticker = stock["ticker"]
        try:
            stock_data = yf.Ticker(ticker)
            current_price = stock_data.history(period="1d")["Close"].iloc[-1]  # Letzter Schlusskurs
        except:
            current_price = None

        market_value = (stock["total_shares"] * current_price) if current_price else None
        profit_loss_absolute = (market_value - stock["total_invested"]) if market_value else None
        profit_loss_percentage = ((profit_loss_absolute / stock["total_invested"]) * 100) if profit_loss_absolute else None

        # Berechnete Werte in das Dictionary setzen
        stock["current_price"] = current_price
        stock["market_value"] = market_value
        stock["profit_loss_absolute"] = profit_loss_absolute
        stock["profit_loss_percentage"] = profit_loss_percentage

        # Summen berechnen (nur wenn Werte vorhanden sind)
        if stock["total_invested"]:
            total_invested += stock["total_invested"]
        if market_value:
            total_market_value += market_value
        if profit_loss_absolute:
            total_profit_loss_absolute += profit_loss_absolute

    # **Gesamt-Profit/Verlust in % berechnen**
    if total_invested > 0:
        total_profit_loss_percentage = (total_profit_loss_absolute / total_invested) * 100

    return render_template(
        "portfolio.html",
        portfolio=portfolio_data,
        trades=trades_data,
        total_invested=total_invested,
        total_market_value=total_market_value,
        total_profit_loss_absolute=total_profit_loss_absolute,
        total_profit_loss_percentage=total_profit_loss_percentage,
    )
