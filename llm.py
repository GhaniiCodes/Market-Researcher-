from langchain_groq import ChatGroq
from config import settings

llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model="llama-3.3-70b-versatile",
    temperature=0.1,
    max_tokens=1024,
)

def get_llm():
    return llm