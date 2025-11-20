import sys
from pathlib import Path

# Add parent directory to path to import existing modules
sys.path.append(str(Path(__file__).parent.parent))

import yfinance as yf
from langchain_core.messages import HumanMessage, SystemMessage
from llm.llm import get_llm

def extract_symbol(query: str) -> str:
    query_upper = query.upper()
    common_tickers = {
        "APPLE": "AAPL", "TESLA": "TSLA", "GOOGLE": "GOOGL", "MICROSOFT": "MSFT",
        "AMAZON": "AMZN", "NVIDIA": "NVDA", "META": "META", "NETFLIX": "NFLX"
    }
    for word in query_upper.split():
        if word in common_tickers:
            return common_tickers[word]
        if len(word) <= 5 and word.replace(".", "").isalnum():
            return word  # assume it's a ticker
    return "AAPL"  # default

def stock_agent(query: str) -> str:
    symbol = extract_symbol(query)
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        price = info.get("currentPrice") or info.get("regularMarketPrice", "N/A")
        change = info.get("regularMarketChange", 0)
        change_pct = info.get("regularMarketChangePercent", 0)
        volume = info.get("volume", 0)
        market_cap = info.get("marketCap")
        day_high = info.get("dayHigh")
        day_low = info.get("dayLow")
        name = info.get("longName") or info.get("shortName", symbol)

        stats = f"""
**{name} ({symbol})**
• Current Price: ${price:.2f}
• Change: {change:+.2f} ({change_pct:+.2f}%)
• Day Range: ${day_low:.2f} - ${day_high:.2f}
• Volume: {volume:,}
• Market Cap: ${market_cap / 1e9:.2f}B
        """.strip()

        analysis = get_llm().invoke([
            SystemMessage(content="You are a professional stock analyst. Give concise, insightful analysis based on current price and momentum."),
            HumanMessage(content=f"Current data for {symbol}:\n{stats}\n\nQuery: {query}\n\nProvide brief outlook.")
        ])

        return f"### Stock Analysis: {symbol}\n{stats}\n\n**Insight:**\n{analysis.content}"

    except Exception as e:
        return f"Could not fetch stock data for {symbol}: {str(e)}"