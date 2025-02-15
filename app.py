from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime
import plotly.graph_objects as go
import yfinance as yf

app = Flask(__name__)

# Absoluter Pfad zur Datenbank im `data/`-Ordner
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "portfolio.db")

# Funktion für eine sichere DB-Verbindung mit absolutem Pfad
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Startseite
@app.route("/")
def home():
    return render_template("home.html")

# Watchlist anzeigen
@app.route("/watchlist")
def watchlist():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, ticker, isin, wkn FROM watchlist")
    stocks = cursor.fetchall()
    conn.close()
    return render_template("watchlist.html", watchlist=stocks)

# Portfolio anzeigen
@app.route("/portfolio")
def portfolio():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM portfolio")
    stocks = cursor.fetchall()
    conn.close()
    return render_template("portfolio.html", portfolio=stocks)

# Aktienkauf hinzufügen
@app.route("/add_purchase/<ticker>", methods=["GET", "POST"])
def add_purchase(ticker):
    if request.method == "POST":
        quantity = request.form["quantity"]
        price = request.form["price"]
        purchase_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO portfolio (ticker, quantity, price, purchase_date)
            VALUES (?, ?, ?, ?)
        """, (ticker, quantity, price, purchase_date))
        conn.commit()
        conn.close()

        return redirect(url_for("watchlist"))

    return render_template("add_purchase.html", ticker=ticker)

# Aktienverkauf hinzufügen
@app.route("/add_sale/<ticker>", methods=["GET", "POST"])
def add_sale(ticker):
    if request.method == "POST":
        quantity = request.form["quantity"]
        price = request.form["price"]
        sale_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sales (ticker, quantity, price, sale_date)
            VALUES (?, ?, ?, ?)
        """, (ticker, quantity, price, sale_date))
        conn.commit()
        conn.close()

        return redirect(url_for("watchlist"))

    return render_template("add_sale.html", ticker=ticker)

# Aktien zur Watchlist hinzufügen
@app.route("/add_watchlist", methods=["GET", "POST"])
def add_watchlist():
    if request.method == "POST":
        name = request.form["name"]
        ticker = request.form["ticker"]
        isin = request.form["isin"]
        wkn = request.form["wkn"]
        added_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO watchlist (name, ticker, isin, wkn, added_date)
            VALUES (?, ?, ?, ?, ?)
        """, (name, ticker, isin, wkn, added_date))
        conn.commit()
        conn.close()

        return redirect(url_for("watchlist"))

    return render_template("add_watchlist.html")

# Aktien-Detailseite
@app.route("/detail/<ticker>")
def detail(ticker):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Hole die allgemeinen Aktieninformationen
    cursor.execute("SELECT * FROM watchlist WHERE ticker = ?", (ticker,))
    stock = cursor.fetchone()

    # Hole die Kaufdaten
    cursor.execute("SELECT * FROM portfolio WHERE ticker = ?", (ticker,))
    purchases = cursor.fetchall()

    conn.close()

    # Aktienkursdaten abrufen
    stock_data = yf.Ticker(ticker).history(period="1y")

    # Plotly-Chart erstellen
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data["Close"], mode="lines", name="Kursverlauf"))

    fig.update_layout(
        title=f"{ticker} - Kursverlauf",
        xaxis_title="Datum",
        yaxis_title="Preis",
        template="plotly_dark",
        margin=dict(l=10, r=10, t=50, b=50),
    )

    plotly_chart = fig.to_html(full_html=False)

    return render_template("detail.html", stock=stock, purchases=purchases, plotly_chart=plotly_chart)

# App starten
if __name__ == "__main__":
    app.run(debug=True)
