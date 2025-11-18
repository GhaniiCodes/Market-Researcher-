import requests
from langchain_core.messages import HumanMessage, SystemMessage
from llm import get_llm
from config import settings

def market_agent(query: str) -> str:
    key = settings.RAPIDAPI_KEY
    if not key:
        return "RapidAPI key not configured."

    url = "https://real-time-amazon-data.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": key,
        "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
    }
    params = {
        "query": query,
        "page": "1",
        "country": "US",
        "sort_by": "RELEVANCE",
        "product_condition": "ALL"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        data = response.json()

        if data.get("status") != "OK" or not data.get("data", {}).get("products"):
            return f"No products found for '{query}' on Amazon."

        products = data["data"]["products"][:4]
        product_lines = []

        for i, p in enumerate(products, 1):
            title = p.get("product_title", "N/A")
            price = p.get("product_price", "N/A")
            rating = p.get("product_star_rating", "N/A")
            reviews = p.get("product_num_ratings", 0)
            url = p.get("product_url", "")

            product_lines.append(
                f"**{i}. {title}**\n"
                f"   • Price: {price}\n"
                f"   • Rating: {rating} stars ({reviews:,} reviews)\n"
                f"   • [View on Amazon]({url})\n"
            )

        raw_data = "\n".join(product_lines)

        analysis = get_llm().invoke([
            SystemMessage(content="You are an expert e-commerce analyst. Compare products, prices, ratings, and give purchase recommendations."),
            HumanMessage(content=f"User wants: {query}\n\nHere are top Amazon results:\n{raw_data}\n\nProvide detailed comparison and recommendation.")
        ])

        return f"### Market Research: {query}\n\n{analysis.content}"

    except Exception as e:
        return f"Market research failed: {str(e)}"