import feedparser
import requests
from bs4 import BeautifulSoup
from flask import Blueprint, jsonify

aggregate_news_bp = Blueprint("aggregate_news", __name__)

# ✅ Yahoo Finance RSS Feed abrufen
YAHOO_RSS_URL = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"

@aggregate_news_bp.route("/yahoo_news/<ticker>")
def yahoo_rss_news(ticker):
    try:
        feed_url = YAHOO_RSS_URL.format(ticker=ticker)
        feed = feedparser.parse(feed_url)
        
        if not feed.entries:
            return jsonify({"source": "Yahoo Finance RSS", "news": [], "error": "Keine News gefunden"}), 200

        formatted_news = [
            {"title": entry.title, "link": entry.link, "summary": entry.summary}
            for entry in feed.entries[:5]
        ]

        return jsonify({"source": "Yahoo Finance RSS", "news": formatted_news})

    except Exception as e:
        return jsonify({"source": "Yahoo Finance RSS", "error": str(e)}), 500


# ✅ Mapping für MarketScreener
TICKER_TO_MARKETSCREENER = {
    "O": "REALTY-INCOME-CORPORATION-13868",
    "AAPL": "APPLE-INC-4849",
    "TSLA": "TESLA-INC-6344548",
}

@aggregate_news_bp.route("/marketscreener_news/<ticker>")
def marketscreener_news(ticker):
    try:
        if ticker not in TICKER_TO_MARKETSCREENER:
            return jsonify({"source": "MarketScreener", "news": [], "error": f"Kein Mapping für Ticker {ticker} gefunden"}), 400

        market_id = TICKER_TO_MARKETSCREENER[ticker]
        url = f"https://de.marketscreener.com/kurs/aktie/{market_id}/news/"

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return jsonify({"source": "MarketScreener", "news": [], "error": "Fehler beim Abrufen der News"}), 500

        soup = BeautifulSoup(response.text, "html.parser")
        news_items = soup.select(".table.table--small.table--hover.table--bordered.table--fixed tbody tr")

        news_list = []
        for item in news_items[:5]:  
            title_element = item.find("a", class_="txt-- txt-overflow-2 link link--no-underline my-5 my-m-0 txt-m-inline")
            if title_element:
                title = title_element.text.strip()
                link = "https://de.marketscreener.com" + title_element["href"]
                news_list.append({"title": title, "link": link})

        return jsonify({"source": "MarketScreener", "news": news_list})

    except Exception as e:
        return jsonify({"source": "MarketScreener", "error": str(e)}), 500


# ✅ Tagesschau News Scraper
TAGESSCHAU_NEWS_URL = "https://www.tagesschau.de/wirtschaft/boersenkurse/realty-income-aktie-899744/"

@aggregate_news_bp.route("/tagesschau_news")
def tagesschau_news():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(TAGESSCHAU_NEWS_URL, headers=headers)

        if response.status_code != 200:
            return jsonify({"source": "Tagesschau", "news": [], "error": "Fehler beim Abrufen der News"}), 500

        soup = BeautifulSoup(response.text, "html.parser")
        news_items = soup.select(".list_news ul li")

        news_list = []
        for item in news_items[:5]:  
            title_element = item.find("span", class_="title")
            link_element = item.get("onclick")
            summary_element = item.find("span", class_="content")

            if title_element and link_element:
                title = title_element.text.strip()
                link = link_element.replace("top.location.href='", "").replace("';", "").strip()
                summary = summary_element.text.strip() if summary_element else ""

                news_list.append({"title": title, "link": link, "summary": summary})

        return jsonify({"source": "Tagesschau", "news": news_list})

    except Exception as e:
        return jsonify({"source": "Tagesschau", "error": str(e)}), 500
