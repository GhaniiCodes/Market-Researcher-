import requests
from langchain_core.messages import HumanMessage, SystemMessage
from llm import get_llm
from config import settings

def news_agent(query: str) -> str:
    api_key = settings.NEWS_API_KEY
    if not api_key:
        return "News API key not configured."

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "sortBy": "publishedAt",
        "pageSize": 5,
        "language": "en",
        "apiKey": api_key
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") != "ok":
            return f"NewsAPI Error: {data.get('message', 'Unknown error')}"

        articles = data.get("articles", [])[:3]
        if not articles:
            return "No recent news articles found."

        formatted = []
        for a in articles:
            formatted.append(
                f"**{a['title']}**\n"
                f"_Source: {a['source']['name']}_ | Published: {a['publishedAt'][:10]}\n"
                f"{a.get('description', '')[:200]}{'...' if a.get('description', '') else ''}\n"
                f"[Read more]({a['url']})\n"
            )

        raw_news = "\n".join(formatted)

        summary = get_llm().invoke([
            SystemMessage(content="You are a professional news analyst. Summarize clearly and objectively."),
            HumanMessage(content=f"Summarize the latest news for: {query}\n\n{raw_news}")
        ])

        return f"### Latest News on: {query}\n\n{summary.content}"

    except Exception as e:
        return f"Failed to fetch news: {str(e)}"