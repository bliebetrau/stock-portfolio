from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime
import yfinance as yf
import requests_cache
import plotly.graph_objects as go
import pandas as pd

app = Flask(__name__)

DB_PATH = "data/portfolio.db"

# ✅ Cache für `yfinance`, um unnötige Anfragen zu vermeiden (30 Minuten Cache)
session = requests_cache.CachedSession('yfinance_cache', expire_after=1800)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/portfolio")
def portfolio():
    return render_template("index.html")

@app.route("/watchlist")
def watchlist():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, ticker, wkn, isin, added_date FROM watchlist")
    stocks = cursor.fetchall()
    conn.close()

    return render_template("watchlist.html", stocks=stocks)

@app.route("/add_watchlist", methods=["GET", "POST"])
def add_watchlist():
    error = None

    if request.method == "POST":
        ticker = request.form.get("ticker", "").strip().upper()
        wkn = request.form.get("wkn", "").strip()
        isin = request.form.get("isin", "").strip()
        name = request.form.get("name", "").strip()

        if not (ticker or wkn or isin):
            error = "Bitte mindestens einen Identifikator (Ticker, WKN oder ISIN) eingeben!"
        elif not name:
            error = "Bitte einen Namen für die Aktie eingeben!"
        else:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            added_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO watchlist (name, ticker, isin, wkn, added_date)
                VALUES (?, ?, ?, ?, ?)
            """, (name, ticker, isin, wkn, added_date))
            conn.commit()
            conn.close()
            return redirect(url_for("watchlist"))

    return render_template("add_watchlist.html", error=error)

@app.route("/detail/<ticker>")
def detail(ticker):
    stock = yf.Ticker(ticker, session=session)

    selected_period = request.args.get("period", "6mo")
    selected_indicator = request.args.get("indicator", "None")

    try:
        info = stock.info
        chart_url = f"https://finance.yahoo.com/chart/{ticker}"

        df = stock.history(period=selected_period)
        df.reset_index(inplace=True)

        if selected_indicator == "SMA":
            df["SMA_20"] = df["Close"].rolling(window=20, min_periods=1).mean()
        elif selected_indicator == "EMA":
            df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()

        chart_html = generate_plotly_chart(df, ticker, selected_indicator)

        all_time_high = df["Close"].max()

        stock_data = {
            "name": info.get("longName", "Unbekannt"),
            "ticker": ticker,
            "isin": info.get("isin", "N/A"),
            "wkn": info.get("symbol", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": f"{info.get('marketCap', 'N/A'):,}" if info.get("marketCap") else "N/A",
            "52w_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "52w_low": info.get("fiftyTwoWeekLow", "N/A"),
            "all_time_high": all_time_high,
            "dividend_yield": info.get("dividendYield", "N/A"),
            "dividend_rate": info.get("dividendRate", "N/A"),
            "chart_url": chart_url,
            "chart_html": chart_html,
            "selected_period": selected_period,
            "selected_indicator": selected_indicator
        }
    except Exception as e:
        stock_data = {"error": f"Fehler beim Abrufen der Daten: {e}"}

    return render_template("detail.html", stock=stock_data)

def generate_plotly_chart(df, ticker, indicator):
    fig = go.Figure()

    # Standard Linienchart für den Kursverlauf
    fig.add_trace(go.Scatter(x=df["Date"], y=df["Close"], mode="lines", name="Schlusskurs"))

    if indicator == "SMA":
        fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA_20"], mode="lines", name="SMA (20 Tage)"))
    elif indicator == "EMA":
        fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA_20"], mode="lines", name="EMA (20 Tage)"))

    y_min = df["Close"].min() * 0.98
    y_max = df["Close"].max() * 1.02

    fig.update_layout(
        title=f"Aktienkurs von {ticker}",
        xaxis_title="Datum",
        yaxis_title="Preis",
        xaxis_rangeslider_visible=True,
        yaxis=dict(range=[y_min, y_max])
    )

    return fig.to_html(full_html=False)

if __name__ == "__main__":
    print("✅ Flask-App startet auf http://127.0.0.1:5001/")
    app.run(debug=True, host="0.0.0.0", port=5001)
