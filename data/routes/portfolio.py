from flask import Blueprint, render_template
import sqlite3

portfolio = Blueprint("portfolio", __name__)
DB_PATH = "data/portfolio.db"

@portfolio.route("/portfolio")
def show_portfolio():
    """Lädt die Portfolio-Daten aus der View und zeigt sie an."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT ticker, name, isin, wkn, total_shares, avg_buy_price, total_invested FROM portfolio_view")
    portfolio_data = cursor.fetchall()

    conn.close()

    return render_template("portfolio.html", portfolio=portfolio_data)
