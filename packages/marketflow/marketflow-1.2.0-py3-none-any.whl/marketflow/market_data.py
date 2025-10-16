from marketflow.market_information import MarketInformation
from marketflow.market_registry import MarketRegistry
from marketflow.__db_manager__ import DBManager
from bs4 import BeautifulSoup
from datetime import datetime,timedelta
from tabulate import tabulate
import requests
import numpy as np
import pandas as pd

# specific link
from marketflow.__marketconfig__.dataextraction import brvm_data

class MarketData:
    """
    A class to manage market tickers and extract historical data from supported APIs.

    Attributes:
        db_manager (DBManager): Database manager used to access market and ticker metadata.
    """

    def __init__(self):
        self.db_manager = DBManager()
                
    def getData(self, market, symbols="all", period: str = 'daily',
                start_date=(datetime.today() - timedelta(100)).strftime("%Y-%m-%d"),
                end_date=datetime.today().strftime("%Y-%m-%d"),
                output_type=0):
        """
        Retrieve historical data for a given market and a list of symbols.

        Args:
            market (str): Shortname of the market (e.g., "BRVM").
            symbols (list[str], optional): List of ticker symbols to fetch.
            period (str, optional): Frequency of data. Supported values: 'daily', 'weekly', 'monthly', 'yearly'.
            start_date (str, optional): Start date (format: 'YYYY-MM-DD'). Default is 100 days before today.
            end_date (str, optional): End date (format: 'YYYY-MM-DD'). Default is today.
            output_type (int, optional): Reserved for formatting output (not fully implemented).

        Returns:
            MarketDataOutput: An object containing row-based and column-based DataFrames of extracted data.

        Raises:
            ValueError: If the market or period is not supported.
        """

        try:
            output = None
            
            if type(symbols) == str:
                symbols = symbols.toupper()
            if type(symbols) == list:
                symbols = [symbol.upper() for symbol in symbols]
            
            if market in self.db_manager.__market_list__():
                
                if market.upper() == "BRVM":
                    output = brvm_data.__get_brvm_data__(market_shortname=market,symbols = symbols,period = period,start_date = start_date,end_date = end_date)
                else:
                    raise ValueError(f"This market {market} is not supported yet.")
            else:
                raise ValueError(f"[Error] The defined market '{market}' is not part of those configured")
            
        except Exception as e:
            print("Check if you have an active internet connection.")
        finally:
            return output

