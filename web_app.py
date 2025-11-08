import streamlit as st
import os
from multi_agent_system import run_agent_system, create_workflow
from langchain_core.messages import HumanMessage
import time

# Page configuration
st.set_page_config(
    page_title="Multi-Agent AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .agent-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #1E88E5;
        color: white;
        border-radius: 5px;
        padding: 0.5rem;
    }
    .message-container {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #E3F2FD;
        border-left: 4px solid #1E88E5;
    }
    .agent-message {
        background-color: #F5F5F5;
        border-left: 4px solid #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_configured" not in st.session_state:
    st.session_state.api_configured = False

# Sidebar for API configuration
with st.sidebar:
    st.title("⚙️ Configuration")
    
    st.markdown("### API Keys")
    groq_api_key = st.text_input(
        "Groq API Key", 
        type="password", 
        value=os.getenv("GROQ_API_KEY", ""),
        help="Required: Get your key from https://console.groq.com"
    )
    news_api_key = st.text_input(
        "News API Key", 
        type="password", 
        value=os.getenv("NEWS_API_KEY", ""),
        help="Optional: Get your key from https://newsapi.org"
    )
    
    if st.button("Save API Keys"):
        if groq_api_key:
            os.environ["GROQ_API_KEY"] = groq_api_key
            if news_api_key:
                os.environ["NEWS_API_KEY"] = news_api_key
            st.session_state.api_configured = True
            st.success("✅ API Keys saved!")
        else:
            st.error("❌ Groq API Key is required!")
    
    st.markdown("---")
    
    st.markdown("### 🤖 Available Agents")
    
    with st.expander("📰 News Agent"):
        st.write("""
        **Specialization:** News & Current Events
        
        **Capabilities:**
        - Fetch latest news articles
        - Search news by topic
        - Summarize current events
        
        **Example Queries:**
        - "Latest news on AI"
        - "What's happening in tech?"
        """)
    
    with st.expander("🛒 Market Research Agent"):
        st.write("""
        **Specialization:** Product Research
        
        **Capabilities:**
        - Product pricing information
        - Feature comparison
        - Market analysis
        
        **Example Queries:**
        - "iPhone 15 price and features"
        - "Best laptops under $1000"
        
        **Note:** Currently using demo data
        """)
    
    with st.expander("📈 Stock Market Agent"):
        st.write("""
        **Specialization:** Financial Data
        
        **Capabilities:**
        - Stock price information
        - Market analysis
        - Trading volume data
        
        **Example Queries:**
        - "AAPL stock price"
        - "Tesla stock analysis"
        
        **Note:** Currently using demo data
        """)
    
    st.markdown("---")
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Main content
st.markdown("<h1 class='main-header'>🤖 Multi-Agent AI Assistant</h1>", unsafe_allow_html=True)

st.markdown("""
<div style='text-align: center; margin-bottom: 2rem;'>
    <p style='font-size: 1.2rem; color: #666;'>
        Powered by LangGraph & Groq | News 📰 | Market Research 🛒 | Stocks 📈
    </p>
</div>
""", unsafe_allow_html=True)

# Check API configuration
if not os.getenv("GROQ_API_KEY"):
    st.warning("⚠️ Please configure your Groq API key in the sidebar to use the assistant.")

# Quick action buttons
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📰 Latest AI News"):
        st.session_state.sample_query = "What's the latest news about artificial intelligence?"

with col2:
    if st.button("🛒 iPhone 15 Info"):
        st.session_state.sample_query = "Tell me about iPhone 15 price and features"

with col3:
    if st.button("📈 Apple Stock"):
        st.session_state.sample_query = "What's the current stock price of Apple (AAPL)?"

# Display chat messages
st.markdown("### 💬 Conversation")

chat_container = st.container()

with chat_container:
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class='message-container user-message'>
                <strong>👤 You:</strong><br>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            agent_name = message.get('agent', 'Assistant')
            content = message["content"]
            st.markdown(f"""
            <div class='message-container agent-message'>
                <strong>🤖 {agent_name}:</strong><br>
                {content}
            </div>
            """, unsafe_allow_html=True)

# Chat input
st.markdown("---")

# Handle sample query
if "sample_query" in st.session_state:
    query = st.session_state.sample_query
    del st.session_state.sample_query
else:
    query = st.chat_input("Ask about news, products, or stocks...")

if query:
    if not os.getenv("GROQ_API_KEY"):
        st.error("⚠️ Please configure your Groq API key in the sidebar first!")
    else:
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user",
            "content": query
        })
        
        # Show processing message
        with st.spinner("🔄 Agents are processing your query..."):
            try:
                # Run the multi-agent system
                graph = create_workflow()
                result = graph.invoke({
                    "messages": [HumanMessage(content=query)]
                })
                
                # Extract agent responses
                agent_responded = False
                for msg in result["messages"]:
                    if msg.type == "ai" and msg != result["messages"][0]:  # Skip the query itself
                        # Determine which agent responded
                        agent_name = "Assistant"
                        content = msg.content
                        
                        # Try to identify agent from content or metadata
                        if "news" in content.lower() or "article" in content.lower():
                            agent_name = "News Agent"
                        elif "product" in content.lower() or "price" in content.lower():
                            agent_name = "Market Research Agent"
                        elif "stock" in content.lower() or "market" in content.lower():
                            agent_name = "Stock Agent"
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "agent": agent_name,
                            "content": content
                        })
                        agent_responded = True
                
                if not agent_responded:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "agent": "System",
                        "content": "I processed your query but couldn't generate a response. Please try rephrasing your question."
                    })
                
                # Rerun to show new messages
                st.rerun()
                
            except ValueError as ve:
                st.error(f"❌ Configuration Error: {str(ve)}")
                st.info("💡 Make sure your Groq API key is valid.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("💡 Make sure your API keys are valid and you have internet connection.")
                # Add error message to chat
                st.session_state.messages.append({
                    "role": "assistant",
                    "agent": "System",
                    "content": f"Error occurred: {str(e)}"
                })

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>Built with ❤️ using LangChain, LangGraph, and Streamlit</p>
    <p style='font-size: 0.9rem;'>Supervisor Agent orchestrates News, Market Research, and Stock agents</p>
</div>
""", unsafe_allow_html=True)

# Display system info in expander
with st.expander("ℹ️ System Information"):
    st.markdown("""
    ### How it works:
    
    1. **Supervisor Agent** analyzes your query
    2. Routes to the appropriate specialist agent:
       - **News Agent** for current events and articles
       - **Market Research Agent** for product information
       - **Stock Agent** for financial data
    3. Specialist agent processes the request using its tools
    4. Results are returned to you with source attribution
    
    ### Architecture:
    - **Framework:** LangGraph (LangChain)
    - **LLM Provider:** Groq (llama-3.1-70b)
    - **Agent Pattern:** Supervisor with specialized sub-agents
    - **Tools:** News API, Product APIs (demo), Stock Market APIs (demo)
    
    ### Setup:
    1. Get a Groq API key from https://console.groq.com
    2. (Optional) Get a News API key from https://newsapi.org
    3. Enter keys in the sidebar
    4. Start chatting!
    
    ### Note:
    Product and Stock data are currently using demo responses. 
    Integrate real APIs for production use.
    """)