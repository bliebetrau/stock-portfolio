from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import os
from datetime import datetime
import plotly.graph_objects as go
import yfinance as yf
import requests  # <-- MUSS DA SEIN!
from bs4 import BeautifulSoup
from routes.portfolio import portfolio  # Import der Portfolio-Route


app = Flask(__name__)

app.register_blueprint(portfolio)

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
    return render_template("index.html")

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

@app.route("/add_trade/<trade_type>/<ticker>", methods=["GET", "POST"])
def add_trade(trade_type, ticker):
    conn = sqlite3.connect("data/portfolio.db")
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM watchlist WHERE ticker = ?", (ticker,))
    stock = cursor.fetchone()
    name = stock[0] if stock else ""

    if request.method == "POST":
        date = request.form.get("date")
        shares = int(request.form.get("shares"))
        price_per_share = float(request.form.get("price_per_share"))
        currency = request.form.get("currency")
        fees = float(request.form.get("fees"))
        taxes = float(request.form.get("taxes", 0)) if trade_type == "sell" else 0
        total_price = shares * price_per_share
        total_cost = total_price + fees + taxes
        notes = request.form.get("notes")

        cursor.execute("""
            INSERT INTO trades (ticker, name, date, type, shares, price_per_share, currency, total_price, fees, taxes, total_cost, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (ticker, name, date, trade_type, shares, price_per_share, currency, total_price, fees, taxes, total_cost, notes))

        conn.commit()
        conn.close()

        return redirect(url_for("portfolio"))

    conn.close()
    return render_template("add_trade.html", trade_type=trade_type, ticker=ticker, name=name)

@app.route("/watchlist_data")
def watchlist_data():
    conn = sqlite3.connect("data/portfolio.db")
    cursor = conn.cursor()
    cursor.execute("SELECT ticker, name FROM watchlist")
    stocks = cursor.fetchall()
    conn.close()
    
    return jsonify([{"ticker": row[0], "name": row[1]} for row in stocks])

@app.route("/add_watchlist", methods=["GET", "POST"])
def add_watchlist():
    if request.method == "GET":
        return render_template("add_watchlist.html")  # Zeigt das Formular an

    # Formulardaten abrufen
    ticker = request.form.get("ticker")
    name = request.form.get("name")
    isin = request.form.get("isin")
    wkn = request.form.get("wkn")
    notes = request.form.get("notes")

    if not ticker or not name:
        return jsonify({"error": "Ticker und Name sind erforderlich!"}), 400

    conn = sqlite3.connect("data/portfolio.db")
    cursor = conn.cursor()

    try:
        # **Prüfen, ob die Aktie mit WKN oder Ticker schon existiert**
        cursor.execute("SELECT * FROM watchlist WHERE ticker = ? OR wkn = ?", (ticker, wkn))
        existing_stock = cursor.fetchone()

        if existing_stock:
            return jsonify({"error": "Diese Aktie ist bereits in der Watchlist!"}), 400

        # **Falls nicht vorhanden, speichern**
        cursor.execute("""
            INSERT INTO watchlist (ticker, name, isin, wkn, added_date, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (ticker, name, isin, wkn, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), notes))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for("watchlist"))

    except sqlite3.Error as e:
        cursor.close()
        conn.close()
        return jsonify({"error": f"Fehler beim Speichern: {e}"}), 500


@app.route("/get_isin")
def get_isin():
    ticker = request.args.get("ticker")
    if not ticker:
        return jsonify({"error": "Kein Ticker angegeben."}), 400

    try:
        stock = yf.Ticker(ticker)
        isin = stock.isin  # ISIN abrufen
        return jsonify({"isin": isin if isin else ""})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/search_ticker", methods=["GET"])
def search_ticker():
    company_name = request.args.get("company_name")

    if not company_name:
        return jsonify([])

    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={company_name}&lang=en-US&region=US"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        # Jetzt ALLE verfügbaren Aktien ausgeben
        results = [
            {
                "name": stock.get("shortname"),
                "ticker": stock.get("symbol"),
                "exchange": stock.get("exchange"),
                "type": stock.get("quoteType", "Unknown")  # Zeigt an, ob es ein Stock, ETF etc. ist
            }
            for stock in data.get("quotes", []) if stock.get("symbol")
        ]

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500



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
