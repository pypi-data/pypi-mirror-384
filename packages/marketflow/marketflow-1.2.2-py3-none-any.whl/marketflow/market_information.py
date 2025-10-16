
"""
Fondamental market Class
"""

class MarketInformation:
    """
    A class to represent a financial market.

    Params:
        short_name (str): A short identifier for the data source.
        full_name (str): The complete name of the data source.
        description (str): A brief explanation of the data source or its purpose.
        official_url (str): The official website or reference link.
        created_at (str): The creation date of the data source or record.
        data_url (str): The direct URL for accessing or downloading the data.
    """
    
    def __init__(self, short_name = "", full_name = "",description = "",official_url = "",created_at = "",data_url = ""):
        # These are instance variables
        self.short_name = short_name
        self.full_name = full_name
        self.description = description
        self.official_url = official_url
        self.created_at = created_at
        self.data_url = data_url

    def __str__(self):
        return (
            f"Shortname   : {self.short_name}\n"
            f"Fullname    : {self.full_name}\n"
            f"Description : {self.description}\n"
            f"Official URL: {self.official_url}\n"
            f"Created at  : {self.created_at}\n"
        )

    def show(self):
        """Prints the market info nicely."""
        print(self.__str__())

