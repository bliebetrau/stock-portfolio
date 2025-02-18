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
    """Listet alle Dividendenaktien aus der Datenbank auf."""
    print("⚡ Route /dividend-stocks/ aufgerufen")  # Debugging-Ausgabe
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, stock_name, isin, market_cap, stock_price, dividend_yield, increasing_since, score FROM dividend_stocks")
    stocks = cursor.fetchall()
    conn.close()
    #print(f"📊 Anzahl gefundener Aktien: {len(stocks)}")  # Debugging-Ausgabe
    return render_template("dividend_stocks.html", stocks=stocks)

@bp.route("/add", methods=["GET", "POST"])
def add_dividend_stock():
    """Fügt eine neue Dividendenaktie hinzu – manuell per Formular oder durch CSV-Upload."""
    if request.method == "POST":
        try:
            stock_name = request.form.get("stock_name", "").strip()
            isin = request.form.get("isin", "").strip()
            link = request.form.get("link", "").strip()
            market_cap = float(request.form.get("market_cap", 0) or 0)
            stock_price = float(request.form.get("stock_price", 0) or 0)
            dividend_yield = float(request.form.get("dividend_yield", 0) or 0)
            increasing_since = int(request.form.get("increasing_since", 0) or 0)
            no_cut_since = int(request.form.get("no_cut_since", 0) or 0)
            payout_ratio_profit = float(request.form.get("payout_ratio_profit", 0) or 0)
            payout_ratio_cashflow = float(request.form.get("payout_ratio_cashflow", 0) or 0)
            avg_div_growth_5y = float(request.form.get("avg_div_growth_5y", 0) or 0)
            avg_div_growth_10y = float(request.form.get("avg_div_growth_10y", 0) or 0)
            special_dividends = int(request.form.get("special_dividends", 0) or 0)
            future_viability = int(request.form.get("future_viability", 0) or 0)
            business_model_future = int(request.form.get("business_model_future", 0) or 0)
            score = float(request.form.get("score", 0) or 0)

            last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Debugging: Zeige die Werte im Terminal an
            print(f"📥 Speichere Aktie: {stock_name} ({isin}) mit Score {score}")

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO dividend_stocks (
                    last_updated, stock_name, isin, link, market_cap, stock_price, dividend_yield, 
                    increasing_since, no_cut_since, payout_ratio_profit, payout_ratio_cashflow, 
                    avg_div_growth_5y, avg_div_growth_10y, special_dividends, 
                    future_viability, business_model_future, score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                last_updated, stock_name, isin, link, market_cap, stock_price, dividend_yield, 
                increasing_since, no_cut_since, payout_ratio_profit, payout_ratio_cashflow, 
                avg_div_growth_5y, avg_div_growth_10y, special_dividends, 
                future_viability, business_model_future, score
            ))
            conn.commit()
            conn.close()
            
            flash("✅ Aktie erfolgreich gespeichert!", "success")
            return redirect(url_for("dividend_stocks.list_dividend_stocks"))  # Fix: Zurück zur Übersicht

        except sqlite3.IntegrityError:
            flash("⚠️ Fehler: ISIN bereits vorhanden!", "danger")
        except Exception as e:
            flash(f"⚠️ Fehler beim Speichern: {str(e)}", "danger")
            print(f"❌ Fehler beim Speichern: {e}")  # Debugging im Terminal

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
        return render_template("dividend_stocks_add.html", form_data={})  # Bleibt auf der Seite!

    file = request.files["file"]
    if file.filename == "":
        flash("⚠️ Keine Datei ausgewählt!", "danger")
        return render_template("dividend_stocks_add.html", form_data={})  # Bleibt auf der Seite!

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # CSV-Daten auslesen
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            data = next(reader, None)  # Nur die erste Zeile lesen

        if not data:
            flash("⚠️ CSV-Datei war leer!", "danger")
            return render_template("dividend_stocks_add.html", form_data={})  # Bleibt auf der Seite!

        print(f"📥 CSV-Daten geladen: {data}")  # Debugging im Terminal

        # WICHTIG: Daten an das Formular übergeben
        return render_template("dividend_stocks_add.html", form_data=dict(data))  # KEIN REDIRECT!

    flash("⚠️ Ungültige Datei. Bitte eine CSV-Datei hochladen!", "danger")
    return render_template("dividend_stocks_add.html", form_data={})  # Bleibt auf der Seite!
