from supervisor import supervisor_agent

def run_query(query: str):
    print(f"\n{'='*80}")
    print(f"QUERY: {query}")
    print('='*80)
    
    result = supervisor_agent(query)
    
    print(f"\nAGENT → {result['agent']}")
    print(f"\n{result['response']}")
    print("\n" + "─"*80)

def main():
    print("="*80)
    print("🤖 AI RESEARCH ASSISTANT")
    print("="*80)
    print("\nAvailable agents:")
    print("  📰 News Agent - Latest news, headlines, events")
    print("  🛒 Market Agent - Product research, prices, reviews")
    print("  📈 Stock Agent - Stock prices, analysis, forecasts")
    print("  🧠 General Assistant - Definitions, explanations, non-specialized queries") # UPDATED LINE
    print("\nType 'quit' or 'exit' to stop")
    print("="*80)
    
    while True:
        try:
            # Get user input
            query = input("\n💬 Enter your query: ").strip()
            
            # Check for exit commands
            if query.lower() in ['quit', 'exit', 'q', 'bye']:
                print("\n👋 Goodbye!")
                break
            
            # Skip empty queries
            if not query:
                print("⚠️  Please enter a valid query")
                continue
            
            # Process the query
            run_query(query)
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again...")

if __name__ == "__main__":
    main()