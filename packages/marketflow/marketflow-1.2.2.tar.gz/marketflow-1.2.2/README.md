# Asset Management Package

Access to African, American, European and Asian open market data for financial analysis, scientific study and to provide a decision-making basis to investors.

## Installation

You can install this package using pip:

```bash
pip install marketflow
```

## How to use marketflow

Import requirements 

```bash
from marketflow.market_registry import MarketRegistry
from marketflow.market_ticker import MarketTickers
from marketflow.market_data import MarketData
```

Or simply with 

```bash
from marketflow import MarketRegistry, MarketTickers, MarketData
```

Initialize the registry (to manage cache / stored data)

```bash
register = MarketRegistry()
# register.purge()   # Uncomment to clear existing registry data
```

Get available tickers for market (Ex : BRVM)

```bash
tickers = MarketTickers()
brvm_tickers = tickers.getTickers("BRVM")
print(brvm_tickers)
```

Download market data (example: BRVM, ticker BNBC.ci)
```bash
data = MarketData()
brvm_data = data.getData("BRVM", "all")
boab_data = data.getData("BRVM", "BOAB")
bicc_data = data.getData("BRVM", "BICC")
print(brvm_data.head())
```