import sys
from pathlib import Path
import importlib.util

# Add parent directory to path to import existing modules
sys.path.append(str(Path(__file__).parent.parent))

import requests
from langchain_core.messages import HumanMessage, SystemMessage
from llm.llm import get_llm

# Handle import of config.config - works even when config is the main module
try:
    from config.config import settings
except (ImportError, ModuleNotFoundError):
    # Fallback: import config module directly if config is the main module
    config_path = Path(__file__).parent.parent / "config" / "config.py"
    spec = importlib.util.spec_from_file_location("config_config", config_path)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    settings = config_module.settings


def news_agent(query: str) -> str:
    """
    Fetches real-time news from NewsAPI and produces
    a highly professional, real-world summary using an LLM.
    """

    api_key = settings.NEWS_API_KEY
    if not api_key:
        return "❌ News API key is missing. Please configure NEWS_API_KEY."

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "sortBy": "publishedAt",
        "pageSize": 7,
        "language": "en",
        "apiKey": api_key
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        # If request failed (status code error)
        if response.status_code != 200:
            return f"❌ API Request Failed ({response.status_code}): {response.text}"

        data = response.json()

        # NewsAPI-specific error handling
        if data.get("status") != "ok":
            return f"❌ NewsAPI Error: {data.get('message', 'Unknown error')}"

        articles = data.get("articles", [])

        if not articles:
            return f"📭 No recent news found for **{query}**."

        # Only take the top 3 strongest articles
        articles = articles[:3]

        # Formatting
        formatted = []
        for a in articles:
            title = a.get("title", "No Title")
            source = a.get("source", {}).get("name", "Unknown Source")
            published = a.get("publishedAt", "")[:10]
            description = a.get("description", "No description available.")
            url = a.get("url", "#")

            formatted.append(
                f"### 📰 {title}\n"
                f"**Source:** {source} | **Date:** {published}\n\n"
                f"{description}\n"
                f"[Read Full Article]({url})\n"
                f"---\n"
            )

        raw_news = "\n".join(formatted)

        # LLM summary instructions
        prompt = f"""
You are a highly skilled real-world news analyst. 
Provide:
- A clear, neutral summary
- Key events in bullet points
- Political, economic, and social impact
- Risks or opportunities
- A concluding insight

Here are the top latest articles for: **{query}**

{raw_news}
"""

        summary = get_llm().invoke([
            SystemMessage(content="Respond as a professional senior news analyst with accurate, objective insights."),
            HumanMessage(content=prompt)
        ])

        return (
            f"## 🔍 Latest Real-World Analysis on: **{query}**\n\n"
            f"{summary.content}"
        )

    except requests.exceptions.Timeout:
        return "⏳ Request timed out. Please try again."

    except requests.exceptions.RequestException as e:
        return f"❌ Network Error: {str(e)}"

    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"
