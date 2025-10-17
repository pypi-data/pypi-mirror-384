from marketflow.market_registry import MarketRegistry
from marketflow.market_ticker import MarketTickers
from marketflow.__db_manager__ import DBManager
from bs4 import BeautifulSoup
from datetime import datetime,timedelta
from tabulate import tabulate
import requests
import pandas as pd

db_manager = DBManager()

class MarketDataOutput:
    """
    A container class for storing and displaying extracted market data.

    Attributes:
        market (str): The shortname of the market.
        by_row (pd.DataFrame): Extracted data organized by rows.
        by_col (pd.DataFrame): Extracted data organized by columns.
    """

    def __init__(self,market,by_row,by_col):
        self.market = market
        self.by_row = by_row
        self.by_col = by_col
        
    def __str__(self):
        """
        Format the extracted data as a human-readable string.

        Returns:
            str: A formatted string showing the market name, row-based data, and column-based data.
        """
        return(
            f"\n ### EXTRACT DATA FROM {self.market}"
            f"{"-" * 40}\n"
            "\n1 - Data Extracted - Rows\n"
            f"{self.by_row}"
            "\n2 - Data Extracted - Columns\n"
            f"{self.by_col}"
        )
        
    def show(self):
        """
        Print the formatted extracted data to the console.
        """
        return print(self.__str__())



def __get_brvm_data__(market_shortname="BRVM",
                    symbols ="all",
                    period: str = 'daily',
                    start_date=(datetime.today() - timedelta(100)).strftime("%Y-%m-%d"),
                    end_date=datetime.today().strftime("%Y-%m-%d")):
    """
    Extract historical data for BRVM tickers using the SikaFinance API.

    Args:
        market_shortname (str, optional): Market shortname, default is "BRVM".
        symbols (list[str], optional): List of ticker symbols to extract data for.
        period (str, optional): Frequency of data ('daily', 'weekly', 'monthly', 'yearly').
        start_date (str, optional): Start date of the extraction period ('YYYY-MM-DD').
        end_date (str, optional): End date of the extraction period ('YYYY-MM-DD').

    Returns:
        MarketDataOutput: Object containing extracted data as two DataFrames:
            - by_row: Data organized with one row per observation.
            - by_col: Data organized with one column per ticker.

    Raises:
        ValueError: If the market or period is not supported, or if the date range is invalid.
    """
    
    url = "https://www.sikafinance.com/api/general/GetHistos"
    all_dataframe_row = None
    all_dataframe_col = None
    all_dataframes = None
    
    registry_obj = MarketRegistry()
    ticker_obj = MarketTickers()
    
    
    market_list = registry_obj.market_list()
    real_ticker_list = []
    
    if market_shortname in market_list:
        ticker_obj.getTickers(market=market_shortname)
        real_ticker_list = ticker_obj.__full_ticker_list__(market_shortname)
    else:
        raise ValueError(f"[Error] This market '{market_shortname}' is not supported.")
    
    period_map = {
        'daily': '0',
        'weekly': '7',
        'monthly': '30',
        'yearly': '91'
    }
    
    _range_date = []
    _range_date_full = []
    _start_date = datetime.strptime(start_date,"%Y-%m-%d").date()
    _end_date = datetime.strptime(end_date,"%Y-%m-%d").date()
    
    if not _end_date >= _start_date:
        raise ValueError(f"[Error] Invalid date.")
    else:
        # conversion date range split période by 85 days
        n = 85
        
        val = _start_date
        while val <= _end_date:
            _range_date.append(val.strftime("%Y-%m-%d"))
            if len(_range_date) == 2:
                _range_date_full.append(_range_date)
                _range_date = [val.strftime("%Y-%m-%d")]

            val += timedelta(days=n)
            if not (end_date in _range_date) and val > _end_date:
                val = _end_date
            
    if period in period_map:
        frequency = period_map[period.lower()]
    else:
        raise ValueError(f"[Error] the defined period '{period}' is not supported.")
    
    if type(symbols) == str:
        if symbols.upper() == "ALL":
            symbols = real_ticker_list
    
    first_full_data = True
    for symbol in symbols:
        data_symbol = {}
        first_data = True
        
        full_symbol = [symb for symb in real_ticker_list if symb.startswith(symbol)][0]
        
        if full_symbol in real_ticker_list:

            for row_period in _range_date_full:
                response = requests.post(
                    url = url,
                    json = {
                        "ticker": full_symbol,
                        "datedeb": row_period[0],
                        "datefin": row_period[1],
                        "xperiod": frequency
                    }
                )
                
                #print(post_table.status_code)
                if response.status_code == 200:
                    data_json = response.json()  
                    
                    if 'error' in data_json and data_json['error'] == 'nodata':
                        data_symbol[symbol] = pd.DataFrame()  # DataFrame vide
                        continue
                    else:
                        # ici selon la structure réelle de l'API, souvent data_json['lst'] ou data_json['Data']
                        df = pd.DataFrame(data_json.get('lst', []))
                        
                        if first_data == True:
                            data_symbol[symbol] = df
                            first_data = False
                        else:
                            data_symbol[symbol] = pd.concat([data_symbol[symbol],df],axis=0)
                else:
                    continue
            
            if data_symbol[symbol].shape[0] > 0: 
                                    
                print(f"\u2705 Data extracted for {symbol.split('.')[0]} between {data_symbol[symbol].iloc[0,0]} - {data_symbol[symbol].iloc[-1,0]}")  

                data_symbol_row = pd.DataFrame(data_symbol[symbol])
                data_symbol_col = pd.DataFrame(data_symbol[symbol])
                
                data_symbol_row["Ticker"] = symbol
                data_symbol_col.columns = ["Date"] + [symbol + "." + val for val in data_symbol[symbol].columns.drop("Date")]
                #print(data_symbol_row)
                #
                
                if first_full_data == True: 
                    all_dataframe_row = data_symbol_row
                    all_dataframe_col = data_symbol_col
                    first_full_data = False
                else:
                    all_dataframe_row = pd.concat([all_dataframe_row,data_symbol_row],axis=0)
                    all_dataframe_col = pd.merge(all_dataframe_col,data_symbol_col,how="outer",on="Date")
                    
                all_dataframe_row = all_dataframe_row.drop_duplicates()                
                all_dataframe_col = all_dataframe_col.drop_duplicates()
            else:
                print(f"[Info] No data for {symbol} in the given period.")
        else:
            print(f"This ticker {symbol} is not available.")
            
        if all_dataframe_row.shape[0] > 0:
            all_dataframes = MarketDataOutput(market=market_shortname,by_row=all_dataframe_row,by_col=all_dataframe_col)

    return all_dataframes
