import requests
from bs4 import BeautifulSoup

def extract_stock_info(url):
    """Holt den Ticker, ISIN, WKN und Namen aus einer Aktien-URL."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Fehler werfen, falls die Seite nicht geladen wird
        soup = BeautifulSoup(response.text, "html.parser")

        # Beispiel für Yahoo Finance (Anpassen je nach Quelle)
        name_tag = soup.find("h1")
        if name_tag:
            full_name = name_tag.text
            if "(" in full_name:
                name, ticker = full_name.rsplit(" (", 1)
                ticker = ticker.strip(")")
            else:
                name = full_name
                ticker = "UNKNOWN"

        # Dummy-Werte für ISIN & WKN (müssen je nach Quelle angepasst werden)
        isin = "ISIN_NICHT_GEFUNDEN"
        wkn = "WKN_NICHT_GEFUNDEN"

        return {"ticker": ticker, "name": name.strip(), "isin": isin, "wkn": wkn}

    except Exception as e:
        return {"error": f"Fehler beim Abrufen der Daten: {e}"}
