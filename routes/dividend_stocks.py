import csv
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename

DB_PATH = "data/portfolio.db"
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"csv"}

bp = Blueprint("dividend_stocks", __name__, url_prefix="/dividend-stocks")

@bp.route("/")
def list_dividend_stocks():
    """Listet alle Dividendenaktien aus der Datenbank auf und berechnet Scores."""
    print("⚡ Route /dividend-stocks/ aufgerufen")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, stock_name, isin, link, market_cap, stock_price, ath_price, 
               avg_10y_price_gain, dividend_yield, total_10y_return, dividends_per_year, 
               increasing_since, no_cut_since, dividend_stability, payout_ratio_profit, 
               payout_ratio_cashflow, avg_div_growth_5y, avg_div_growth_10y, special_dividends, 
               future_viability, business_model_future 
        FROM dividend_stocks
    """)
    stocks = cursor.fetchall()
    conn.close()

    # Berechnung der Scores für jede Aktie
    stocks_with_scores = []
    for stock in stocks:
        stock_dict = {
            "id": stock[0],
            "stock_name": stock[1],
            "isin": stock[2],
            "link": stock[3],
            "market_cap": stock[4],
            "stock_price": stock[5],
            "ath_price": stock[6],
            "avg_10y_price_gain": stock[7],
            "dividend_yield": stock[8],
            "total_10y_return": stock[9],
            "dividends_per_year": stock[10],
            "increasing_since": stock[11],
            "no_cut_since": stock[12],
            "dividend_stability": stock[13],
            "payout_ratio_profit": stock[14],
            "payout_ratio_cashflow": stock[15],
            "avg_div_growth_5y": stock[16],
            "avg_div_growth_10y": stock[17],
            "special_dividends": stock[18],
            "future_viability": stock[19],
            "business_model_future": stock[20],
        }

        # Score berechnen
        scores, total_score = calculate_individual_scores(stock_dict)
        stock_dict["scores"] = scores
        stock_dict["total_score"] = total_score

        stocks_with_scores.append(stock_dict)

    return render_template("dividend_stocks.html", stocks=stocks_with_scores)


@bp.route("/add", methods=["GET", "POST"])
def add_dividend_stock():
    """Fügt eine neue Dividendenaktie hinzu – manuell per Formular oder durch CSV-Upload."""
    if request.method == "POST":
        print("✅ Formular wurde gesendet")
        try:
            stock_name = request.form.get("stock_name", "").strip()
            isin = request.form.get("isin", "").strip()
            link = request.form.get("link", "").strip()
            market_cap = float(request.form.get("market_cap", 0) or 0)
            stock_price = float(request.form.get("stock_price", 0) or 0)
            ath_price = float(request.form.get("ath_price", 0) or 0)
            avg_10y_price_gain = float(request.form.get("avg_10y_price_gain", 0) or 0)
            dividend_yield = float(request.form.get("dividend_yield", 0) or 0)
            total_10y_return = float(request.form.get("total_10y_return", 0) or 0)
            dividends_per_year = int(request.form.get("dividends_per_year", 0) or 0)
            increasing_since = int(request.form.get("increasing_since", 0) or 0)
            no_cut_since = int(request.form.get("no_cut_since", 0) or 0)
            dividend_stability = float(request.form.get("dividend_stability", 0) or 0)
            payout_ratio_profit = float(request.form.get("payout_ratio_profit", 0) or 0)
            payout_ratio_cashflow = float(request.form.get("payout_ratio_cashflow", 0) or 0)
            avg_div_growth_5y = float(request.form.get("avg_div_growth_5y", 0) or 0)
            avg_div_growth_10y = float(request.form.get("avg_div_growth_10y", 0) or 0)
            special_dividends = int(request.form.get("special_dividends", 0) or 0)
            future_viability = int(request.form.get("future_viability", 0) or 0)
            business_model_future = int(request.form.get("business_model_future", 0) or 0)
            score = float(request.form.get("score", 0) or 0)

            last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Debugging: Werte ausgeben
            print(f"📥 Speichere Aktie: {stock_name} ({isin}) mit Score {score}")

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO dividend_stocks (
                    last_updated, stock_name, isin, link, market_cap, stock_price, ath_price, avg_10y_price_gain, 
                    dividend_yield, total_10y_return, dividends_per_year, increasing_since, no_cut_since, 
                    dividend_stability, payout_ratio_profit, payout_ratio_cashflow, 
                    avg_div_growth_5y, avg_div_growth_10y, special_dividends, 
                    future_viability, business_model_future, score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                last_updated, stock_name, isin, link, market_cap, stock_price, ath_price, avg_10y_price_gain, 
                dividend_yield, total_10y_return, dividends_per_year, increasing_since, no_cut_since, 
                dividend_stability, payout_ratio_profit, payout_ratio_cashflow, 
                avg_div_growth_5y, avg_div_growth_10y, special_dividends, 
                future_viability, business_model_future, score
            ))
            conn.commit()
            conn.close()
            
            flash("✅ Aktie erfolgreich gespeichert!", "success")
            return redirect(url_for("dividend_stocks.list_dividend_stocks"))  

        except sqlite3.IntegrityError:
            flash("⚠️ Fehler: ISIN bereits vorhanden!", "danger")
        except Exception as e:
            flash(f"⚠️ Fehler beim Speichern: {str(e)}", "danger")
            print(f"❌ Fehler beim Speichern: {e}")  

    return render_template("dividend_stocks_add.html")

# Sicherstellen, dass der Upload-Ordner existiert
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Prüft, ob die Datei eine erlaubte Endung hat."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route("/upload", methods=["POST"])
def upload_csv():
    """Verarbeitet den CSV-Upload und füllt das Formular mit den Daten aus der Datei."""
    if "file" not in request.files:
        flash("⚠️ Keine Datei hochgeladen!", "danger")
        return render_template("dividend_stocks_add.html", form_data={})  

    file = request.files["file"]
    if file.filename == "":
        flash("⚠️ Keine Datei ausgewählt!", "danger")
        return render_template("dividend_stocks_add.html", form_data={})  

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # CSV-Daten auslesen
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            data = next(reader, None)  

        if not data:
            flash("⚠️ CSV-Datei war leer!", "danger")
            return render_template("dividend_stocks_add.html", form_data={})  

        print(f"📥 CSV-Daten geladen: {data}")  

        return render_template("dividend_stocks_add.html", form_data=dict(data))  

    flash("⚠️ Ungültige Datei. Bitte eine CSV-Datei hochladen!", "danger")
    return render_template("dividend_stocks_add.html", form_data={})  


def evaluate_metric(value, neg_threshold, neu_threshold, pos_threshold):
    """Hilfsfunktion zur Bewertung einer einzelnen Kennzahl (-1, 0, +1)."""
    if value is None:
        return 0  # Falls kein Wert vorhanden ist, neutral bewerten
    if value < neg_threshold:
        return -1
    elif neu_threshold[0] <= value <= neu_threshold[1]:
        return 0
    elif value > pos_threshold:
        return 1
    return 0  # Falls kein Wert passt

def calculate_individual_scores(stock):
    """
    Berechnet eine individuelle Bewertung für jede Kennzahl (-1, 0, +1).
    Falls eine Kennzahl None ist, wird sie mit 0 ersetzt.
    """

    def safe_value(value, default=0):
        """Hilfsfunktion, um None-Werte mit einem Standardwert zu ersetzen."""
        return float(value) if value is not None else default

    def safe_div(a, b, default=0):
        """Hilfsfunktion für sicheres Dividieren, falls b None oder 0 ist."""
        if b is None or b == 0:
            return default
        return a / b

    # Berechnung des Verhältnisses von aktuellem Kurs zum Allzeithoch
    stock_price = safe_value(stock.get('stock_price'))
    ath_price = safe_value(stock.get('ath_price'))
    stock_price_ath_ratio = safe_div(stock_price, ath_price)

    scores = {
        "market_cap": evaluate_metric(safe_value(stock.get('market_cap')), 2, (2, 10), 10),
        "ath_price": evaluate_metric(stock_price_ath_ratio, 0.9, (0.8, 0.9), 0.8),  # Korrektur hier
        "avg_10y_price_gain": evaluate_metric(safe_value(stock.get('avg_10y_price_gain')), 3, (3, 7), 7),
        "dividend_yield": evaluate_metric(safe_value(stock.get('dividend_yield')), 3, (3, 5), 5),
        "total_10y_return": evaluate_metric(safe_value(stock.get('total_10y_return')), 5, (5, 10), 10),
        "dividends_per_year": evaluate_metric(safe_value(stock.get('dividends_per_year')), 2, (2, 4), 4),
        "increasing_since": evaluate_metric(safe_value(stock.get('increasing_since')), 5, (5, 10), 10),
        "no_cut_since": evaluate_metric(safe_value(stock.get('no_cut_since')), 5, (5, 15), 15),
        "dividend_stability": evaluate_metric(safe_value(stock.get('dividend_stability')), 0.7, (0.7, 0.9), 0.9),
        "payout_ratio_profit": evaluate_metric(safe_value(stock.get('payout_ratio_profit')), 20, (20, 80), 60),
        "payout_ratio_cashflow": evaluate_metric(safe_value(stock.get('payout_ratio_cashflow')), 20, (20, 80), 60),
        "avg_div_growth_5y": evaluate_metric(safe_value(stock.get('avg_div_growth_5y')), 2, (2, 4), 4),
        "avg_div_growth_10y": evaluate_metric(safe_value(stock.get('avg_div_growth_10y')), 2, (2, 4), 4),
        "special_dividends": evaluate_metric(safe_value(stock.get('special_dividends')), 0, (1, 2), 2),
        "future_viability": evaluate_metric(safe_value(stock.get('future_viability')), 3, (3, 4), 5),
        "business_model_future": evaluate_metric(safe_value(stock.get('business_model_future')), 3, (3, 4), 5),
    }

    # Gesamt-Score berechnen (Summe aller Einzelwerte)
    total_score = sum(scores.values())

    return scores, total_score
