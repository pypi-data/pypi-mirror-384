from marketflow.__db_manager__ import DBManager
from tabulate import tabulate


# specific link
from marketflow.__marketconfig__.tickerextraction import brvm_ticker



class MarketTickersOutput:
    """
    A container class for storing ticker information of a specific market.

    Attributes:
        ticker_database (list[tuple]): Detailed ticker information retrieved from the database,
            typically including fields such as ID, market ID, symbol, description, and country code.
    """
    
    def __init__(self, ticker_database,index_ticker_list = [], share_ticker_list = [], bonds_ticker_list = []):
        self.share_ticker_list = share_ticker_list
        self.index_ticker_list = index_ticker_list
        self.bonds_ticker_list = bonds_ticker_list
        self.ticker_list = self.index_ticker_list + self.share_ticker_list + self.bonds_ticker_list
        self.ticker_database = ticker_database
        self.index_ticker_database = [row[:3] + row[4:] for row in self.ticker_database[0]]
        self.share_ticker_database = [row[:3] + row[4:] for row in self.ticker_database[1]]
        
        self.tickers_headers = ["ID","ID Market","Symbol","Description","Country Code"]
        self.seperator = ", "
        
    def __str__(self):
        return(
            "======= ALL TICKERS =======\n"
            f"{self.seperator.join(self.ticker_list)}.\n\n"
            "1 - INDEXES *\n"
            f"{tabulate(self.index_ticker_database, self.tickers_headers, tablefmt="fancy_grid")}\n"
            "2 - SHARES **\n"
            f"{tabulate(self.share_ticker_database, self.tickers_headers, tablefmt="fancy_grid")}\n"
        )


class MarketTickers:
    """
    A class to manage and retrieve ticker information for financial markets.

    Attributes:
        tickers_headers (list[str]): Column headers used to describe ticker information.
        db_manager (DBManager): Database manager to query stored market and ticker metadata.
    """
    def __init__(self):
        self.db_manager = DBManager()
        # for market in self.db_manager.__market_list__():
        #     self.getTickers(market=market)



    def ticker_list(self,market):
        """
        Retrieve ticker list for a given market.
        
        Args:
            market (str): The shortname of the market.
        """
        try:
            output = []
            if self.db_manager.__ticker_list__(market_shortname=market) == None:
                self.getTickers(market=market)
            output = self.db_manager.__ticker_list__(market_shortname=market)
        except Exception as e:
            print("Check if you have an active internet connection.")
        finally:
            return(output)
        
        
    def getTickers(self, market):
        """
        Retrieve ticker information for a given market.

        If the market exists in the local database and is supported,
        the method returns both:
            - A simple list of ticker symbols.
            - A detailed representation of each ticker from the database.

        Args:
            market (str): The shortname of the market (e.g., "BRVM").

        Returns:
            MarketTickersOutput: An object containing:
                - ticker_list: List of ticker symbols.
                - ticker_database: Detailed database entries for the tickers.

        Raises:
            ValueError: If the market is not supported or not found in the local database.

        Notes:
            Currently, only the BRVM market is supported.
        """

        try:
            output = {}
            
            if market in self.db_manager.__market_list__():
                if market.upper() == "BRVM":
                    output = MarketTickersOutput(
                        ticker_database= brvm_ticker.__get_tickers__(market_shortname=market),
                        index_ticker_list = self.db_manager.__ticker_list__(market_shortname=market,type="INDEX"),
                        share_ticker_list = self.db_manager.__ticker_list__(market_shortname=market,type="SHARE")
                    )
                    
                    
                else:
                    raise ValueError(f"This market {market} is not supported yet.")
    
            else:
                raise ValueError(f"[Error] the defined market '{market}' is not part of those configured")
            
            
            return output
        except Exception as e:
            print("Check if you have an active internet connection.")
            #print(e)
        
        
    def __full_ticker_list__(self,market):
        """
        Retrieve ticker list for a given market.
        
        Args:
            market (str): The shortname of the market.
        """
        try:
            output = []
            if self.db_manager.__full_version_ticker_list__(market_shortname=market) == None:
                self.getTickers(market=market)
                
            output = self.db_manager.__full_version_ticker_list__(market_shortname=market)
        except Exception as e:
            print("Check if you have an active internet connection.")
        finally:
            return(output)