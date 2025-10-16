import sqlite3
import os
import importlib.resources as pkg_resources
from pathlib import Path
from marketflow.market_information import MarketInformation
import marketflow.__data__


class DBManager():
    
    def __init__(self):
        super().__init__()
        self.db_path = os.path.join(os.path.dirname(__file__), '__data__', 'database.db')
        self.__open_db__()

        # Table des marchés
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS market (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shortname TEXT UNIQUE,
                fullname TEXT,
                description TEXT,
                official_url TEXT,
                created_at TEXT,
                data_url TEXT
            )
        """)

        # Table des tickers
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ticker (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market_id INTEGER,
                type TEXT,
                symbol TEXT,
                full_symbol TEXT,
                description TEXT,
                country TEXT,
                FOREIGN KEY (market_id) REFERENCES market(id)
            )
        """)
        
        
        #self.delete_table(table=["market"])
        self.conn.commit()
        self.__close_db__()

    def __addmarket_to_local_db__(self, market: MarketInformation):
        """
        Add or update a market entry in the local database.

        - If the market does not exist (based on its shortname), a new record is inserted.
        - If the market already exists, its information is updated.

        Args:
            market (MarketInformation): Market object containing metadata such as
                shortname, fullname, description, official_url, created_at, and data_url.
        """        
        self.__open_db__()
        
        self.cursor.execute("SELECT * FROM market WHERE shortname = ?",(market.short_name,))
        existing_market = self.cursor.fetchone()
        
        if existing_market == None:
            self.cursor.execute(
                """
                INSERT OR IGNORE INTO market (shortname,fullname,description,official_url,created_at,data_url)
                VALUES (?,?,?,?,?,?)
                """,
                (market.short_name,market.full_name,market.description,market.official_url,market.created_at,market.data_url,)
            )
        else:
            
            self.cursor.execute(
                """
                UPDATE market SET shortname = ?,fullname = ?,description = ?,official_url = ?,created_at = ?,data_url = ? WHERE id = ?
                """,
                (market.short_name,market.full_name,market.description,market.official_url,market.created_at,market.data_url,int(existing_market[0]),)
            )
        self.conn.commit()
        
        self.__close_db__()

    def __remove_market__(self, market: MarketInformation):
        """
        Remove a market entry from the local database.

        Args:
            market (MarketInformation): The market object to be deleted, identified by its shortname.
        """
        self.__open_db__()
        self.cursor.execute("DELETE FROM market WHERE shorname = ?",market.short_name)
        self.conn.commit()
        self.__close_db__()
        

    def __market_list__(self):
        """
        Retrieve the list of all market shortnames stored in the database.

        Returns:
            list[str]: A sorted list of market shortnames.
        """
        market_list = []
        self.__open_db__()
        self.cursor.execute("SELECT shortname FROM market ORDER BY shortname ASC")
        rows = self.cursor.fetchall()
        self.__close_db__()
        if rows:
            market_list = [market[0] for market in rows]
        return market_list
    
    def __get_markets__(self):
        """
        Retrieve all market entries from the database with basic information.

        Returns:
            list[tuple]: A list of tuples containing market details:
                (id, shortname, fullname, official_url, created_at).
        """
        self.__open_db__()
        self.cursor.execute("SELECT id, shortname,fullname,official_url,created_at FROM market ORDER BY shortname ASC")
        rows = self.cursor.fetchall()
        self.__close_db__()
        return rows

    def __add_tickers__(self, shortname: str, type: str, symbol: str, full_symbol: str, description: str, country: str):
        """
        Add or update a ticker for a given market.

        - If the market exists and the ticker is not found, a new ticker is inserted.
        - If the ticker already exists, its details are updated.

        Args:
            shortname (str): Shortname of the associated market.
            type (str): Type of ticker (e.g., stock, bond, index).
            symbol (str): The ticker symbol.
            full_symbol (str): The full ticker symbol.
            description (str): A short description of the ticker.
            country (str): Country code where the ticker is listed.
        """
        self.__open_db__()
        self.cursor.execute("SELECT id FROM market WHERE shortname = ?",(shortname,))
        market_obj = self.cursor.fetchone()
        
        if market_obj: # market exist
            market_id = int(market_obj[0])
            self.cursor.execute("SELECT t.id, t.symbol FROM ticker t JOIN market m ON m.id = t.market_id WHERE m.shortname = ? AND t.symbol = ?",(shortname,symbol,))
            ticker_obj = self.cursor.fetchone()
            
            if ticker_obj == None:
                self.cursor.execute(
                    """
                    INSERT OR IGNORE INTO ticker (market_id,type,symbol,full_symbol,description,country) VALUES (?,?,?,?,?,?)
                    """,
                    (market_id,type,symbol,full_symbol,description,country,)
                )
            else:
                ticker_id = int(ticker_obj[0])
                self.cursor.execute(
                    """
                    UPDATE ticker SET market_id = ?, type = ?, symbol = ?,full_symbol = ?,description = ?,country = ? WHERE id = ?
                    """,
                    (market_id,type,symbol,full_symbol,description,country,ticker_id,)
                )
            # print("Database updated successfully.")
            self.conn.commit()
        self.__close_db__()
    
    
    def __get_tickers__(self, market_shortname: str):
        """
        Retrieve all tickers for a given market.

        Args:
            market_shortname (str): Shortname of the market.

        Returns:
            list[tuple]: A list of tuples containing ticker details:
                (id, market_id, symbol, full_symbol, description, country).
        """
        self.__open_db__()
        self.cursor.execute("SELECT id FROM market WHERE shortname = ?",(market_shortname,))
        market_obj = self.cursor.fetchone()
        rows = None
        
        if market_obj: # market exist
            market_id = int(market_obj[0])
            self.cursor.execute("""
                SELECT id, market_id, symbol, full_symbol, description, country
                FROM ticker WHERE market_id = ? ORDER BY symbol ASC
            """, (market_id,))
            rows = self.cursor.fetchall()
            
        self.__close_db__()
        return rows

    
    def __ticker_list__(self, market_shortname: str,type: str = "all"):
        
        """
        Retrieve the list of ticker symbols for a given market.

        Args:
            market_shortname (str): Shortname of the market.

        Returns:
            list[str]: A sorted list of ticker symbols for the specified market.
        """
        self.__open_db__()
        ticker_list = []
        self.cursor.execute("SELECT id FROM market WHERE shortname = ?",(market_shortname,))
        market_obj = self.cursor.fetchone()
        
        if market_obj != None: # market exist
            market_id = int(market_obj[0])
            
            if type == "all":
                self.cursor.execute(f"""
                    SELECT symbol FROM ticker WHERE market_id = ? ORDER BY country ASC
                """, (market_id,))
            else:
                self.cursor.execute(f"""
                    SELECT symbol FROM ticker WHERE market_id = ? AND type = ? ORDER BY country ASC
                """, (market_id,type,))
                
            rows = self.cursor.fetchall()
            if rows:
                ticker_list = [row[0] for row in rows]
        
        self.__close_db__()
        return ticker_list
    
    
    def __full_version_ticker_list__(self, market_shortname: str):
        """
        Retrieve the list of native ticker symbols for a given market.

        Args:
            market_shortname (str): Shortname of the market.

        Returns:
            list[str]: A sorted list of ticker symbols for the specified market.
        """
        self.__open_db__()
        ticker_list = []
        self.cursor.execute("SELECT id FROM market WHERE shortname = ?",(market_shortname,))
        market_obj = self.cursor.fetchone()
        
        if market_obj: # market exist
            market_id = int(market_obj[0])
            self.cursor.execute("""
                SELECT full_symbol FROM ticker WHERE market_id = ? ORDER BY symbol ASC
            """, (market_id,))
            
            rows = self.cursor.fetchall()
            if rows:
                ticker_list = [row[0] for row in rows]
        
        self.__close_db__()
        return ticker_list
        
        
    def __open_db__(self):
        """
        Open a connection to the SQLite database and initialize the cursor.
        """
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
    def __close_db__(self):
        """
        Close the current connection to the SQLite database.
        """
        self.conn.close()
        
    def __delete_table__(self, tables: list):
        """
        Delete all rows from one or more tables in the database.

        Args:
            tables (list[str]): List of table names to be cleared.
        """
        self.__open_db__()
        for tab in tables:
            self.cursor.execute(f"DROP TABLE {tab}")
        self.conn.commit()
        self.__close_db__()
        
