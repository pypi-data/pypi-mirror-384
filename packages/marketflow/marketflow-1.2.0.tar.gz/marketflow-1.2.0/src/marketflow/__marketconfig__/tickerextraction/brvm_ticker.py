from bs4 import BeautifulSoup
import requests
from marketflow.__db_manager__ import DBManager


db_manager = DBManager()

def __get_tickers__(market_shortname="BRVM"):
    """
    Retrieve ticker information (indexes and shares) for a given market.

    The function attempts two steps:
    
    1. **Fetch from the web**  
       - Scrapes ticker information from `https://www.sikafinance.com/` using BeautifulSoup.  
       - Extracts both ticker symbol and description from the HTML select element `#dpShares`.  
       - Splits tickers into two categories:  
         - INDEXES: Tickers starting with "BRVM".
         - SHARES: Regular company tickers (excluding "BRVM" and "SIKA"). 
       - Saves the extracted tickers into the local database.  
       - Prints both categories in a formatted table.

    2. **Fallback to local database**  
       - If the web request fails, attempts to load tickers stored locally.  
       - Applies the same separation into INDEXES and SHARES.  
       - Prints both categories in a formatted table.

    Args:
        market_shortname (str, optional): Shortname of the market. Default is `"BRVM"`.

    Returns:
        list[list]: A list containing two sublists:  
            - [0]: INDEXES tickers, each row as `[id, market_id, symbol, description, country]`.  
            - [1]: SHARES tickers, each row as `[id, market_id, symbol, description, country]`.

    Raises:
        Exception: If both web scraping and local database access fail.

    Notes:
        - The output is also printed in the console using `tabulate`.  
        - Web scraping depends on the structure of `sikafinance.com`; changes on the website may break this method.  
        - Local database must already be populated with valid ticker data for the fallback to work.
    """
    url = "https://www.sikafinance.com/"
    all_tables = []

    # Étape 1 : tenter de récupérer via Internet
    try:
        response = requests.get(url=url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, features="html.parser")
        options = soup.select("#dpShares option")

        values = []
        for opt in options:
            val = opt.get("value").strip()
            text = opt.get_text(strip=True)
            if val:  # éviter l'option vide "Choisir une valeur"
                val_split = val.split(".")
                if len(val_split) == 2:
                    values.append(["","",val_split[0],val, text, val_split[1].upper()])
                else:
                    values.append(["","",val_split[0],val, text, ""])

        sorted_table = sorted(values, key=lambda x: x[2])

        # Séparer INDEXES et SHARES
        indexes = [row for row in sorted_table if row[2].startswith("BRVM")]
        shares = [row for row in sorted_table if not (row[2].startswith("BRVM") or row[2].startswith("SIKA"))]

        all_tables.append(indexes)
        all_tables.append(shares)

        # # Sauvegarde dans la DB
        for row in indexes:
            db_manager.__add_tickers__(market_shortname, "INDEX", row[2], row[3], row[4], row[5])
        for row in shares:
            db_manager.__add_tickers__(market_shortname, "SHARE", row[2], row[3], row[4], row[5])

        return all_tables

    except Exception as e:
        print(f"[WARN] Web retrieval failure.")

    # Étape 2 : tenter de récupérer dans la DB locale
    try:
        sorted_table = db_manager.__get_tickers__(market_shortname=market_shortname)

        if sorted_table:
            indexes = [row for row in sorted_table if row[2].startswith("BRVM")]
            shares = [row for row in sorted_table if not (row[2].startswith("BRVM") or row[2].startswith("SIKA"))]

            all_tables.append(indexes)
            all_tables.append(shares)

        return all_tables

    except Exception as e:
        print(f"[ERROR] Unable to retrieve tickers.")
        return []


# __get_tickers__()