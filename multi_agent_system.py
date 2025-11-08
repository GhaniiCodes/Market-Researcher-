import os
import requests
from datetime import datetime
from typing import Literal

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, MessagesState, START, END 
from langchain_core.tools import tool

# --------------------------------------------------------------
# 1. CONFIGURATION
# --------------------------------------------------------------
load_dotenv(r"D:\BAVE AI\Market-Researcher-\.env")   # <-- adjust if needed

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment")

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# --------------------------------------------------------------
# 2. LLM
# --------------------------------------------------------------
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=GROQ_MODEL,
    temperature=0,
)

# --------------------------------------------------------------
# 3. TOOLS
# --------------------------------------------------------------

@tool
def search_news(query: str) -> str:
    """Search the latest news articles (requires NEWS_API_KEY)."""
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return "News API key not configured – set NEWS_API_KEY in .env"

    url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&pageSize=5&apiKey={api_key}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data.get("status") != "ok":
            return f"NewsAPI error: {data.get('message', 'unknown')}"

        articles = []
        for a in data["articles"][:3]:
            articles.append(
                f"**{a.get('title','N/A')}**\n"
                f"_Source: {a.get('source',{}).get('name','N/A')}_\n"
                f"{a.get('description','')[:200]}...\n"
                f"[Read more]({a.get('url','#')})\n"
            )
        return "\n".join(articles) or "No articles found."
    except Exception as e:
        return f"News fetch error: {e}"


@tool
def get_product_info(product_name: str) -> str:
    """Demo product info (replace with real e-commerce API in prod)."""
    return f"""
**Product:** {product_name}
**Average Price:** $1,199.00
**Rating:** 4.7/5 stars
**Availability:** In Stock

**Key Features:**
- A17 Pro chip
- 48 MP Main camera
- USB-C charging
- Dynamic Island
- Aerospace-grade aluminum

*Demo data – integrate Amazon/eBay API for production.*
"""


@tool
def get_stock_market_data(symbol: str) -> str:
    """REAL-TIME stock data via yfinance."""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol.strip().upper())
        info = ticker.info

        # Pull the most useful fields
        price = info.get("currentPrice") or info.get("regularMarketPrice") or "N/A"
        change = info.get("regularMarketChange") or "N/A"
        change_pct = info.get("regularMarketChangePercent") or "N/A"
        day_high = info.get("dayHigh") or "N/A"
        day_low = info.get("dayLow") or "N/A"
        volume = info.get("volume") or "N/A"
        market_cap = info.get("marketCap") or "N/A"
        pe = info.get("trailingPE") or "N/A"

        # Human-readable formatting
        def fmt(num):
            if isinstance(num, (int, float)):
                if num >= 1e9:
                    return f"${num/1e9:.2f}B"
                if num >= 1e6:
                    return f"${num/1e6:.2f}M"
                return f"${num:,.2f}"
            return str(num)

        return f"""
**Stock:** {symbol.upper()}
**Current Price:** {fmt(price)}
**Change:** {fmt(change)} ({change_pct:+.2f}%)  
**Day Range:** {fmt(day_low)} – {fmt(day_high)}
**Volume:** {volume:,}
**Market Cap:** {fmt(market_cap)}
**P/E Ratio:** {pe if pe != 'N/A' else 'N/A'}

*Data from Yahoo Finance (real-time).*
"""
    except Exception as e:
        return f"Stock data error: {e}"


# Bind tools to separate LLM instances (so each agent sees only its tool)
news_llm = llm.bind_tools([search_news])
market_llm = llm.bind_tools([get_product_info])
stock_llm = llm.bind_tools([get_stock_market_data])

# --------------------------------------------------------------
# 4. STATE
# --------------------------------------------------------------
class AgentState(MessagesState):
    next: str = "supervisor"   # default


# --------------------------------------------------------------
# 5. AGENT NODE FACTORY (handles tool call + final summary)
# --------------------------------------------------------------
def make_agent_node(llm_with_tool, system_prompt, tool_name):
    def node(state: AgentState):
        msgs = state["messages"]
        user_msg = msgs[-1]

        # 1. Ask LLM (may return tool call)
        resp = llm_with_tool.invoke([SystemMessage(content=system_prompt), user_msg])

        # 2. If tool call → execute → ask LLM to summarize
        if resp.tool_calls:
            tc = resp.tool_calls[0]
            if tc["name"] == tool_name:
                raw = globals()[tool_name].invoke(tc["args"])
                summary = llm.invoke([
                    SystemMessage(content=system_prompt),
                    user_msg,
                    AIMessage(content=f"Tool result:\n{raw}"),
                    HumanMessage(content="Give a concise, professional summary of the tool result.")
                ])
                return {"messages": [AIMessage(content=summary.content)], "next": END}

        # 3. No tool call → just return LLM answer
        return {"messages": [resp], "next": END}

    return node


news_agent_node = make_agent_node(
    news_llm,
    "You are a news specialist. Use the **search_news** tool to fetch the top 3 articles. Summarize clearly.",
    "search_news"
)

market_agent_node = make_agent_node(
    market_llm,
    "You are a product-research expert. Use **get_product_info** and provide pricing, features, and a short comparison.",
    "get_product_info"
)

stock_agent_node = make_agent_node(
    stock_llm,
    "You are a financial analyst. Use **get_stock_market_data** to give price, change, key metrics, and a brief outlook.",
    "get_stock_market_data"
)

# --------------------------------------------------------------
# 6. SUPERVISOR (routes once, then finishes)
# --------------------------------------------------------------
def supervisor_node(state: AgentState):
    # If any AI message already exists → we are done
    if any(isinstance(m, AIMessage) for m in state["messages"]):
        return {"next": END}

    query = state["messages"][-1].content

    prompt = f"""Route the user query to **exactly one** agent. Reply with ONLY the agent name:

- news_agent
- market_research_agent  
- stock_agent

Query: {query}

Answer with only the agent name (no punctuation, no extra text)."""

    try:
        resp = llm.invoke([SystemMessage(content=prompt)])
        route = resp.content.strip().lower()

        if "news" in route:
            return {"next": "news_agent"}
        if "market" in route or "product" in route or "iphone" in route:
            return {"next": "market_research_agent"}
        if "stock" in route or "aapl" in route:
            return {"next": "stock_agent"}

        # ---- fallback keyword routing ----
        q = query.lower()
        if any(w in q for w in ["news", "article", "latest", "headlines"]):
            return {"next": "news_agent"}
        if any(w in q for w in ["price", "feature", "iphone", "laptop", "buy"]):
            return {"next": "market_research_agent"}
        if any(w in q for w in ["stock", "aapl", "tesla", "nasdaq", "price of"]):
            return {"next": "stock_agent"}

        return {"next": "news_agent"}   # safe default
    except Exception as e:
        print(f"Supervisor error: {e}")
        return {"next": END}


# --------------------------------------------------------------
# 7. BUILD GRAPH
# --------------------------------------------------------------
def create_workflow():
    workflow = StateGraph(AgentState)

    # nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("news_agent", news_agent_node)
    workflow.add_node("market_research_agent", market_agent_node)
    workflow.add_node("stock_agent", stock_agent_node)

    # start → supervisor
    workflow.add_edge(START, "supervisor")

    # supervisor → chosen agent (conditional)
    workflow.add_conditional_edges(
        "supervisor",
        lambda s: s["next"],
        {
            "news_agent": "news_agent",
            "market_research_agent": "market_research_agent",
            "stock_agent": "stock_agent",
            END: END,
        },
    )

    # every agent → END
    workflow.add_edge("news_agent", END)
    workflow.add_edge("market_research_agent", END)
    workflow.add_edge("stock_agent", END)

    return workflow.compile()


# --------------------------------------------------------------
# 8. RUNNER
# --------------------------------------------------------------
def run_agent_system(query: str):
    try:
        graph = create_workflow()
        result = graph.invoke(
            {"messages": [HumanMessage(content=query)]},
            config={"recursion_limit": 50},   # safety net
        )
        return result["messages"]
    except Exception as e:
        import traceback
        traceback.print_exc()
        return [AIMessage(content=f"System error: {e}")]


# --------------------------------------------------------------
# 9. QUICK TEST (run the file directly)
# --------------------------------------------------------------
if __name__ == "__main__":
    tests = [
        "What's the latest news about artificial intelligence?",
        "Tell me about the iPhone 15 price and features",
        "What's the current stock price of Apple (AAPL)?",
    ]

    for q in tests:
        print("\n" + "=" * 70)
        print(f"QUERY: {q}")
        print("=" * 70)
        msgs = run_agent_system(q)
        for m in msgs:
            if m.type == "ai":
                print("\nAI RESPONSE:\n" + m.content)