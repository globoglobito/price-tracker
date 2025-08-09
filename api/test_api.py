#!/usr/bin/env python3
"""
Test script for the Price Tracker Search API
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_endpoints():
    """Test health check endpoints"""
    print("🧪 Testing health endpoints...")
    
    # Test root endpoint
    response = requests.get(f"{BASE_URL}/")
    print(f"✅ Root endpoint: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Test health endpoint
    response = requests.get(f"{BASE_URL}/health")
    print(f"✅ Health endpoint: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    print()

def test_search_endpoints():
    """Test search CRUD endpoints"""
    print("🧪 Testing search endpoints...")
    
    # Test initial state
    response = requests.get(f"{BASE_URL}/searches")
    print(f"✅ List searches (initial): {response.status_code}")
    initial_data = response.json()
    print(f"   Total searches: {initial_data['total']}")
    print(f"   Active searches: {initial_data['active_count']}")
    
    # Test creating a search
    new_search = {
        "search_term": "Selmer Mark VI",
        "website": "ebay",
        "is_active": True
    }
    
    response = requests.post(f"{BASE_URL}/searches", json=new_search)
    print(f"✅ Create search: {response.status_code}")
    if response.status_code == 201:
        created_search = response.json()
        search_id = created_search['id']
        print(f"   Created search ID: {search_id}")
        print(f"   Search term: {created_search['search_term']}")
        print(f"   Website: {created_search['website']}")
        
        # Test getting the specific search
        response = requests.get(f"{BASE_URL}/searches/{search_id}")
        print(f"✅ Get search by ID: {response.status_code}")
        
        # Test updating the search
        update_data = {"is_active": False}
        response = requests.put(f"{BASE_URL}/searches/{search_id}", json=update_data)
        print(f"✅ Update search: {response.status_code}")
        
        # Test toggle endpoint
        response = requests.patch(f"{BASE_URL}/searches/{search_id}/toggle")
        print(f"✅ Toggle search status: {response.status_code}")
        
        # Test list searches after changes
        response = requests.get(f"{BASE_URL}/searches")
        print(f"✅ List searches (after changes): {response.status_code}")
        updated_data = response.json()
        print(f"   Total searches: {updated_data['total']}")
        print(f"   Active searches: {updated_data['active_count']}")
        
        # Test creating duplicate (should fail)
        response = requests.post(f"{BASE_URL}/searches", json=new_search)
        print(f"✅ Create duplicate search: {response.status_code} (should be 409)")
        
        # Test deleting the search
        response = requests.delete(f"{BASE_URL}/searches/{search_id}")
        print(f"✅ Delete search: {response.status_code}")
        
        # Verify deletion
        response = requests.get(f"{BASE_URL}/searches/{search_id}")
        print(f"✅ Get deleted search: {response.status_code} (should be 404)")
    
    print()

def test_error_handling():
    """Test error handling"""
    print("🧪 Testing error handling...")
    
    # Test getting non-existent search
    response = requests.get(f"{BASE_URL}/searches/99999")
    print(f"✅ Get non-existent search: {response.status_code} (should be 404)")
    
    # Test updating non-existent search
    response = requests.put(f"{BASE_URL}/searches/99999", json={"is_active": False})
    print(f"✅ Update non-existent search: {response.status_code} (should be 404)")
    
    # Test deleting non-existent search
    response = requests.delete(f"{BASE_URL}/searches/99999")
    print(f"✅ Delete non-existent search: {response.status_code} (should be 404)")
    
    print()

def main():
    """Main test function"""
    print("🚀 Starting Price Tracker Search API Tests")
    print("=" * 50)
    
    try:
        test_health_endpoints()
        test_search_endpoints()
        test_error_handling()
        
        print("🎉 All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running on http://localhost:8000")
        print("   Start the server with: python api/main.py")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    main() 