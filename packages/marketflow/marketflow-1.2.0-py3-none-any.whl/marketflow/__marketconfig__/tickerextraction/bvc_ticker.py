from marketflow.market_information import MarketInformation
from marketflow.market_registry import MarketRegistry
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import requests, certifi
from tabulate import tabulate

from marketflow.__db_manager__ import DBManager

db_manager = DBManager()



def __get_tickers__(market_shortname="BVC"):
    url_share = "https://www.casablanca-bourse.com/en/instruments"
    tickers_headers = ["ID","ID Market","Symbols","Description","Country Code"]

    try:
        #driver = webdriver.Chrome()
        response = requests.get(url=url_share, timeout=10, verify=False)
        response.raise_for_status()
        print(f"[INFO] HTTP {response.status_code}")
        
        soup = BeautifulSoup(response.text, "html.parser")

        # On cible uniquement la liste des tickers
        options = soup.find_all("option")
        
        values = []
        for opt in options:
            label = opt.text.strip()
            val = opt.get("value")

            # ignorer les en-têtes ou entrées vides
            if not val or val.lower() in ["issuers"]:
                continue

            # Ajouter comme ticker + description identiques
            values.append(["", market_shortname, val, label, "MA"])

        # Trier par symbole
        sorted_table = sorted(values, key=lambda x: x[2])

        # Debug : aperçu
        for row in sorted_table[:10]:
            print(row)

        return sorted_table

    except Exception as e:
        print(f"[ERROR] {e}")
        return []

# Exemple d’appel
tickers = __get_tickers__()
print(tickers)