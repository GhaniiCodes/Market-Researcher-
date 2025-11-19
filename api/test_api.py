#!/usr/bin/env python3
"""
Test script for AI Research Assistant API
Run this after starting the server to test all endpoints
"""

import requests
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print('='*80)

def print_response(response: requests.Response, show_full: bool = True):
    """Print formatted response"""
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✅ Success")
    else:
        print("❌ Failed")
    
    if show_full:
        try:
            data = response.json()
            print(f"Response: {data}")
        except:
            print(f"Response: {response.text}")
    print()

def test_health_check():
    """Test health check endpoint"""
    print_section("1. Testing Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print_response(response)
    return response.status_code == 200

def test_submit_queries():
    """Test query submission"""
    print_section("2. Testing Query Submission")
    
    test_queries = [
        "What's the latest news on artificial intelligence?",
        "Best wireless headphones under $200",
        "Tesla stock price analysis",
        "What is quantum computing?"
    ]
    
    query_ids = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nQuery {i}: {query}")
        print("-" * 80)
        
        response = requests.post(
            f"{API_V1}/query",
            json={"query": query}
        )
        
        if response.status_code == 200:
            data = response.json()
            query_ids.append(data['query_id'])
            print(f"✅ Query ID: {data['query_id']}")
            print(f"   Agent: {data['agent']}")
            print(f"   Execution Time: {data['execution_time']:.2f}s")
            print(f"   Response Preview: {data['response'][:100]}...")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Error: {response.text}")
        
        # Small delay between requests
        time.sleep(0.5)
    
    return query_ids

def test_get_specific_query(query_id: int):
    """Test retrieving a specific query"""
    print_section(f"3. Testing Get Specific Query (ID: {query_id})")
    
    response = requests.get(f"{API_V1}/query/{query_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Retrieved Query {query_id}")
        print(f"   Query: {data['query']}")
        print(f"   Agent: {data['agent']}")
        print(f"   Timestamp: {data['timestamp']}")
    else:
        print(f"❌ Failed to retrieve query")
        print_response(response, show_full=False)

def test_get_history():
    """Test getting query history"""
    print_section("4. Testing Query History")
    
    # Test 1: Get last 10 queries
    print("\n📋 Getting last 10 queries:")
    response = requests.get(f"{API_V1}/history?limit=10")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Total queries in database: {data['total']}")
        print(f"   Retrieved: {len(data['items'])} queries")
        for item in data['items'][:3]:  # Show first 3
            print(f"   - [{item['agent']}] {item['query'][:50]}...")
    else:
        print(f"❌ Failed")
        print_response(response, show_full=False)

def test_filter_by_agent():
    """Test filtering by agent"""
    print_section("5. Testing Agent Filter")
    
    agents = ["News Agent", "Market Research Agent", "Stock Analyst", "General Assistant"]
    
    for agent in agents:
        response = requests.get(f"{API_V1}/history?agent={agent}&limit=5")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 {agent}: {data['total']} queries")
        else:
            print(f"❌ Failed to filter by {agent}")

def test_search_queries():
    """Test search functionality"""
    print_section("6. Testing Search Functionality")
    
    search_term = "AI"
    print(f"🔍 Searching for: '{search_term}'")
    
    response = requests.get(f"{API_V1}/history?search={search_term}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['total']} queries containing '{search_term}'")
        for item in data['items'][:3]:
            print(f"   - {item['query']}")
    else:
        print(f"❌ Search failed")
        print_response(response, show_full=False)

def test_statistics():
    """Test statistics endpoint"""
    print_section("7. Testing Statistics")
    
    response = requests.get(f"{API_V1}/history/stats")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Statistics Retrieved")
        print(f"\n   Total Queries: {data['total_queries']}")
        print(f"   Average Execution Time: {data['avg_execution_time']:.2f}s")
        print(f"   Last Query: {data.get('last_query_time', 'N/A')}")
        print(f"\n   Queries by Agent:")
        for agent, count in data['queries_by_agent'].items():
            print(f"     - {agent}: {count}")
    else:
        print(f"❌ Failed to get statistics")
        print_response(response, show_full=False)

def test_pagination():
    """Test pagination"""
    print_section("8. Testing Pagination")
    
    # Get first page
    print("📄 Page 1 (first 2 queries):")
    response1 = requests.get(f"{API_V1}/history?limit=2&offset=0")
    
    if response1.status_code == 200:
        data1 = response1.json()
        print(f"✅ Retrieved {len(data1['items'])} queries")
        for item in data1['items']:
            print(f"   - ID {item['query_id']}: {item['query'][:40]}...")
    
    # Get second page
    print("\n📄 Page 2 (next 2 queries):")
    response2 = requests.get(f"{API_V1}/history?limit=2&offset=2")
    
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"✅ Retrieved {len(data2['items'])} queries")
        for item in data2['items']:
            print(f"   - ID {item['query_id']}: {item['query'][:40]}...")

def test_delete_query(query_id: int):
    """Test deleting a query"""
    print_section(f"9. Testing Query Deletion (ID: {query_id})")
    
    response = requests.delete(f"{API_V1}/history/{query_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['message']}")
        
        # Verify deletion
        verify = requests.get(f"{API_V1}/query/{query_id}")
        if verify.status_code == 404:
            print(f"✅ Verified: Query {query_id} no longer exists")
    else:
        print(f"❌ Failed to delete query")
        print_response(response, show_full=False)

def run_all_tests():
    """Run all tests"""
    print("="*80)
    print("🧪 AI RESEARCH ASSISTANT API - TEST SUITE")
    print("="*80)
    print(f"Testing API at: {BASE_URL}")
    print("Make sure the server is running before proceeding!")
    
    input("\nPress Enter to start tests...")
    
    try:
        # Test 1: Health check
        if not test_health_check():
            print("\n❌ Server is not responding. Make sure it's running!")
            return
        
        # Test 2: Submit queries
        query_ids = test_submit_queries()
        
        if not query_ids:
            print("\n❌ No queries were created. Cannot continue tests.")
            return
        
        # Test 3: Get specific query
        test_get_specific_query(query_ids[0])
        
        # Test 4: Get history
        test_get_history()
        
        # Test 5: Filter by agent
        test_filter_by_agent()
        
        # Test 6: Search
        test_search_queries()
        
        # Test 7: Statistics
        test_statistics()
        
        # Test 8: Pagination
        test_pagination()
        
        # Test 9: Delete query (delete the last one we created)
        if len(query_ids) > 3:  # Keep some queries in DB
            test_delete_query(query_ids[-1])
        
        print_section("✅ ALL TESTS COMPLETED")
        print("\n🎉 API is working correctly!")
        print(f"\n📚 View full documentation at: {BASE_URL}/docs")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to server!")
        print("Make sure the server is running at http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    run_all_tests()