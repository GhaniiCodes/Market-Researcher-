import sys
from pathlib import Path

# Add parent directory to path to import existing modules
sys.path.append(str(Path(__file__).parent.parent))

from langchain_core.messages import HumanMessage
from llm.llm import get_llm
from agents.news_agent import news_agent
from agents.market_agent import market_agent
from agents.stock_agent import stock_agent

def general_agent(query: str) -> str:
    """Handles queries that don't fit into specialized categories."""
    try:
        # Use the LLM for a direct, general answer
        response = get_llm().invoke([
            HumanMessage(content=f"Answer the following query clearly and concisely: {query}")
        ])
        return f"### General Knowledge Response\n\n{response.content}"
    except Exception as e:
        return f"General LLM failed: {str(e)}"

def supervisor_agent(query: str) -> dict:
    routing_prompt = f"""
You are an intelligent router. Classify the user query into ONE category:

- news → latest news, headlines, events, AI developments
- market → products, prices, features, buying, reviews, Amazon
- stock → stock price, AAPL, TSLA, market cap, trading
- general → anything else (e.g., definitions, explanations, history, simple facts)

Query: {query}

Respond with ONLY one word: news, market, stock, or general
"""
    try:
        route = get_llm().invoke([HumanMessage(content=routing_prompt)]).content.strip().lower()

        if "news" in route:
            response = news_agent(query)
            agent = "News Agent"
        elif "market" in route:
            response = market_agent(query)
            agent = "Market Research Agent"
        elif "stock" in route:
            response = stock_agent(query)
            agent = "Stock Analyst"
        else:
            # Fallback for "general" or any unclassified/irrelevant response
            response = general_agent(query)
            agent = "General Assistant"

        return {"agent": agent, "response": response, "query": query}

    except Exception as e:
        return {"agent": "Error", "response": f"System error: {e}", "query": query}