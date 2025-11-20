import sys
from pathlib import Path
import importlib.util

# Add parent directory to path to import existing modules
sys.path.append(str(Path(__file__).parent.parent))

from langchain_groq import ChatGroq

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

llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model="llama-3.3-70b-versatile",
    temperature=0.1,
    max_tokens=1024,
)

def get_llm():
    return llm