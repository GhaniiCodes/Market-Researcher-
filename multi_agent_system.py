import os
import requests
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

# --------------------------------------------------------------
# CONFIGURATION
# --------------------------------------------------------------
load_dotenv(r"D:\BAVE AI\Market-Researcher-\.env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment")

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.3-70b-versatile",
    temperature=0,
)

# --------------------------------------------------------------
# AGENT 1: NEWS AGENT (Uses News API)
# --------------------------------------------------------------
def news_agent(query: str) -> str:
    """Fetches latest news using News API."""
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return "❌ News API key not configured"

    url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&pageSize=3&apiKey={api_key}"
    
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        if data.get("status") != "ok":
            return f"❌ NewsAPI error: {data.get('message', 'unknown')}"

        articles = []
        for a in data["articles"][:3]:
            articles.append(
                f"**{a.get('title','N/A')}**\n"
                f"_Source: {a.get('source',{}).get('name','N/A')}_\n"
                f"{a.get('description','')[:200]}...\n"
                f"[Read more]({a.get('url','#')})\n"
            )
        
        news_data = "\n".join(articles) if articles else "No articles found."
        
        # Use LLM to summarize
        summary = llm.invoke([
            SystemMessage(content="You are a news specialist. Summarize the news clearly and professionally."),
            HumanMessage(content=f"News data:\n{news_data}\n\nSummarize this for the query: {query}")
        ])
        
        return summary.content
        
    except Exception as e:
        return f"❌ News fetch error: {e}"


# --------------------------------------------------------------
# AGENT 2: MARKET RESEARCH AGENT (Uses RapidAPI E-commerce APIs)
# --------------------------------------------------------------
def market_agent(query: str) -> str:
    """Provides product research using real e-commerce APIs."""
    
    rapidapi_key = os.getenv("RAPIDAPI_KEY")
    if not rapidapi_key:
        return "❌ RapidAPI key not configured. Add RAPIDAPI_KEY to .env file"
    
    try:
        # Using Real-Time Amazon Data API
        url = "https://real-time-amazon-data.p.rapidapi.com/search"
        
        headers = {
            "X-RapidAPI-Key": rapidapi_key,
            "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
        }
        
        params = {
            "query": query,
            "page": "1",
            "country": "US",
            "sort_by": "RELEVANCE",
            "product_condition": "ALL"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        data = response.json()
        
        if data.get("status") != "OK" or not data.get("data", {}).get("products"):
            return f"❌ No products found for: {query}"
        
        # Get top 3 products
        products = data["data"]["products"][:3]
        product_data = []
        
        for idx, p in enumerate(products, 1):
            product_info = f"""
**Product {idx}: {p.get('product_title', 'N/A')}**
- Price: {p.get('product_price', 'N/A')}
- Rating: {p.get('product_star_rating', 'N/A')} ({p.get('product_num_ratings', 0)} reviews)
- URL: {p.get('product_url', 'N/A')}
"""
            product_data.append(product_info)
        
        product_summary = "\n".join(product_data)
        
        # Use LLM to analyze
        analysis = llm.invoke([
            SystemMessage(content="You are a product research expert. Provide detailed analysis of products including pricing, features, ratings, and recommendations."),
            HumanMessage(content=f"User query: {query}\n\nProduct data:\n{product_summary}\n\nProvide a comprehensive market research response with comparisons and recommendations.")
        ])
        
        return analysis.content
        
    except Exception as e:
        return f"❌ Market research error: {e}"


# --------------------------------------------------------------
# AGENT 3: STOCK AGENT (Uses yfinance API)
# --------------------------------------------------------------
def stock_agent(query: str) -> str:
    """Fetches real-time stock data using yfinance."""
    
    try:
        import yfinance as yf
        
        # Extract stock symbol from query
        words = query.upper().split()
        symbol = next((w for w in words if w in ["AAPL", "TSLA", "GOOGL", "MSFT", "AMZN"]), "AAPL")
        
        ticker = yf.Ticker(symbol)
        info = ticker.info

        price = info.get("currentPrice") or info.get("regularMarketPrice") or "N/A"
        change = info.get("regularMarketChange") or "N/A"
        change_pct = info.get("regularMarketChangePercent") or "N/A"
        day_high = info.get("dayHigh") or "N/A"
        day_low = info.get("dayLow") or "N/A"
        volume = info.get("volume") or "N/A"
        market_cap = info.get("marketCap") or "N/A"

        stock_data = f"""
Stock: {symbol}
Current Price: ${price}
Change: {change} ({change_pct:+.2f}%)
Day Range: ${day_low} — ${day_high}
Volume: {volume:,}
Market Cap: ${market_cap}
"""
        
        # Use LLM to analyze
        analysis = llm.invoke([
            SystemMessage(content="You are a financial analyst. Provide stock analysis with key metrics and brief outlook."),
            HumanMessage(content=f"Stock data:\n{stock_data}\n\nProvide analysis for: {query}")
        ])
        
        return analysis.content
        
    except Exception as e:
        return f"❌ Stock data error: {e}"


# --------------------------------------------------------------
# AGENT 4: SUPERVISOR (Routes to appropriate agent)
# --------------------------------------------------------------
def supervisor_agent(query: str) -> dict:
    """Routes query to the appropriate specialist agent and returns response."""
    
    # Ask LLM to route the query
    routing_prompt = f"""You are a routing supervisor. Analyze the user query and respond with ONLY ONE of these words:
    
- news (for news, articles, headlines, current events)
- market (for products, prices, features, shopping, buying)
- stock (for stocks, trading, financial markets, ticker symbols)

Query: {query}

Respond with only one word (news, market, or stock):"""

    try:
        route_response = llm.invoke([
            SystemMessage(content="You are a routing expert. Reply with only one word."),
            HumanMessage(content=routing_prompt)
        ])
        
        route = route_response.content.strip().lower()
        
        # Route to appropriate agent
        if "news" in route:
            agent_name = "News Agent"
            response = news_agent(query)
        elif "market" in route:
            agent_name = "Market Research Agent"
            response = market_agent(query)
        elif "stock" in route:
            agent_name = "Stock Agent"
            response = stock_agent(query)
        else:
            # Fallback: keyword-based routing
            q = query.lower()
            if any(w in q for w in ["news", "article", "latest", "headlines"]):
                agent_name = "News Agent"
                response = news_agent(query)
            elif any(w in q for w in ["price", "product", "iphone", "buy", "feature"]):
                agent_name = "Market Research Agent"
                response = market_agent(query)
            else:
                agent_name = "Stock Agent"
                response = stock_agent(query)
        
        return {
            "agent": agent_name,
            "response": response,
            "query": query
        }
        
    except Exception as e:
        return {
            "agent": "Error",
            "response": f"❌ System error: {e}",
            "query": query
        }


# --------------------------------------------------------------
# MAIN RUNNER
# --------------------------------------------------------------
def run_agent_system(query: str):
    """Main entry point - routes and executes query."""
    result = supervisor_agent(query)
    return result


# --------------------------------------------------------------
# TEST
# --------------------------------------------------------------
if __name__ == "__main__":
    test_queries = [
        "What's the latest news about artificial intelligence?",
        "Tell me about the iPhone 15 price and features",
        "What's the current stock price of Apple (AAPL)?",
    ]

    for query in test_queries:
        print("\n" + "=" * 70)
        print(f"QUERY: {query}")
        print("=" * 70)
        
        result = run_agent_system(query)
        
        print(f"\n🤖 AGENT: {result['agent']}")
        print("-" * 70)
        print(f"\n{result['response']}")
        print("\n")