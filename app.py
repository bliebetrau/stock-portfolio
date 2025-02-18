from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import os
from datetime import datetime
import plotly.graph_objects as go
import yfinance as yf
import requests  # <-- MUSS DA SEIN!
from bs4 import BeautifulSoup
from routes.portfolio import portfolio  # Import der Portfolio-Route
from routes.aggregate_news import aggregate_news_bp
from routes.dividend_stocks import bp as dividend_stocks_bp


app = Flask(__name__)

# Setzt einen geheimen Schlüssel für Session-Support
app.config['SECRET_KEY'] = os.urandom(24)

app.config['DEBUG'] = True  # Debug-Modus aktivieren



app.register_blueprint(dividend_stocks_bp)
app.register_blueprint(portfolio)
app.register_blueprint(aggregate_news_bp)

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

@app.route("/add_trade/<ticker>/<trade_type>", methods=["GET", "POST"])
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

    # Hole die allgemeinen Aktieninformationen aus der Watchlist
    cursor.execute("SELECT * FROM watchlist WHERE ticker = ?", (ticker,))
    stock = cursor.fetchone()
    conn.close()

    if not stock:
        return "Aktie nicht gefunden", 404

    # 📌 Yahoo Finance Daten abrufen
    try:
        stock_data = yf.Ticker(ticker)
        hist_data = stock_data.history(period="1y")

        # ✅ NEU: Aktuellen Kurs & ATH abrufen
        current_price = stock_data.info.get("regularMarketPrice", "N/A")
        all_time_high = max(hist_data["Close"]) if not hist_data.empty else "N/A"

    except Exception as e:
        print("Fehler beim Abrufen der Yahoo Finance Daten:", e)
        current_price = "N/A"
        all_time_high = "N/A"
        hist_data = None

    # 📌 Detailseite mit Kurs und ATH rendern
    return render_template(
        "detail.html",
        stock=stock,
        current_price=current_price,
        all_time_high=all_time_high,
    )


@app.route("/api/get_chart_data")
def get_chart_data():
    ticker = request.args.get("ticker")
    period = request.args.get("period", "1y")  # Standard: 1 Jahr

    if not ticker:
        return jsonify({"error": "Kein Ticker angegeben"}), 400

    # 🚀 Mapping für Intraday-Intervalle
    period_mapping = {
        "1d": ("1d", "5m"),   # 1 Tag → 5-Minuten-Kerzen
        "5d": ("5d", "5m"),   # ✅ Fix: 5 Tage auch mit 5-Minuten-Kerzen holen
        "1mo": ("1mo", "1h"), 
        "3mo": ("3mo", "1d"), 
        "6mo": ("6mo", "1d"), 
        "1y": ("1y", "1d"), 
        "2y": ("2y", "1d"), 
        "5y": ("5y", "1wk"), 
        "10y": ("10y", "1mo"), 
        "ytd": ("ytd", "1d"),
        "max": ("max", "1mo")
    }


    period, interval = period_mapping.get(period, ("1y", "1d"))

    print(f"🟢 API-Request: Ticker={ticker}, Zeitraum={period}, Interval={interval}")

    try:
        stock = yf.Ticker(ticker)
        hist_data = stock.history(period=period, interval=interval)

        if hist_data.empty:
            print(f"🔴 Keine Kursdaten für {ticker} mit Zeitraum {period}")
            return jsonify({"error": "Keine Kursdaten gefunden"}), 404

        print(f"✅ {len(hist_data)} Kursdaten erhalten für {ticker} ({period}, {interval})")

        dates = hist_data.index.strftime("%Y-%m-%d %H:%M:%S").tolist()
        prices = hist_data["Close"].tolist()

        return jsonify({
            "dates": dates,
            "prices": prices
        })

    except Exception as e:
        print(f"🔥 Fehler: {e}")
        return jsonify({"error": str(e)}), 500

# App starten
if __name__ == "__main__":
    #print(app.url_map)
    app.run(debug=True)
