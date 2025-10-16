from tabulate import tabulate
from marketflow.market_information import MarketInformation
from marketflow.__db_manager__ import DBManager

class MarketRegistry():
    """
    A class to manage multiple markets.
    """
    def __init__(self):
        self.markets = []
        self.version = "v1.1.1"
        self.db_manager = DBManager()
        self.__setup_market__()
        

    def __setup_market__(self):

        # add market
        self.__addmarket__(MarketInformation("BRVM", "Bourse Régionale des Valeurs Mobilières (BRVM)",
                                                "The BRVM (Regional Stock Exchange) is a fully electronic and integrated financial market shared by the eight member states of the West African Economic and Monetary Union (WAEMU): Benin, Burkina Faso, Côte d’Ivoire, Guinea-Bissau, Mali, Niger, Senegal, and Togo. Headquartered in Abidjan, it provides a unified platform for listing, trading, and settlement of securities across the region.",
                                                "https://www.brvm.org/","December 18, 1996"))

        self.__addmarket__(MarketInformation("BVC", "Bourse de Valeurs de Casablanca / Casablanca Stock Exchange (CSE)",
                                                "The Casablanca Stock Exchange (CSE) is Morocco’s principal financial market, located in Casablanca and established in 1929. It is one of the largest and most dynamic stock exchanges in Africa, second only to the Johannesburg Stock Exchange. The CSE operates two main markets: the Central Market for regular trading and the Block Trade Market for large transactions. It features modern infrastructure, including an electronic trading platform and a central securities depository (Maroclear). The exchange lists over 70 companies and tracks performance through indices like MASI (Moroccan All Shares Index) and MSI20.", 
                                                "https://www.casablanca-bourse.com/","November 7, 1929"))

        self.__addmarket__(MarketInformation("NGX", "Nigerian Stock Exchange",
                                                "Bourse du Nigéria", "https://www.nse.com.ng/","September 15, 1960"))


    def __addmarket__(self, market: MarketInformation):
        """Add a new market to the registry."""
        self.markets.append(market)
        self.db_manager.__addmarket_to_local_db__(market=market)
            
        
    def market_list(self):
        """List market to the registry."""
        list_market = []
        full_market_name = self.db_manager.__market_list__()
        if full_market_name:
            list_market = [market for market in full_market_name]
            return list_market

    def show_all(self):
        """Display all registered markets."""
        print(f"======= WELCOME TO MARKETFLOW PyEdition {self.version} (R) =======\n")
        print(f"Note : Currently {len(self.markets)} markets are configured on MarketFlow.\n")
        print("=== AVAILABLE STOCK MARKETS ===")
        for idx, market in enumerate(self.markets, start=1):
            print(f"ID : {idx}")
            print(market)
            print("-" * 40)
            
    def describe(self):
        """Describe all registered markets."""
        print(f"======= WELCOME TO MARKETFLOW PyEdition {self.version} (R) =======\n")
        print(f"Note : Currently {len(self.markets)} markets are configured on MarketFlow.\n")
        print("=== AVAILABLE STOCK MARKETS ===")
        
        table = self.db_manager.__get_markets__()
        if table:     
            headers = ["ID","Shortname","Fullname","Official URL","Creation date"]
            print(tabulate(table,headers=headers,tablefmt="fancy_grid"))
            
    def purge(self):
        """Delete all from locale database."""
        
        self.db_manager.__delete_table__(["market","ticker"])
        # self.db_manager.__init__()
        # self.__setup_market__()
        