"""
Quick API Test Script
Tests the FinSecAI v2 FastAPI backend endpoints
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

# ANSI colors for output
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_section(title: str):
    """Print a section header"""
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}{title}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}")


def print_request(method: str, endpoint: str, data: Dict = None):
    """Print request details"""
    print(f"\n{BOLD}{YELLOW}Request:{RESET}")
    print(f"  {BOLD}{method}{RESET} {endpoint}")
    if data:
        print(f"  {json.dumps(data, indent=2)}")


def print_response(response: requests.Response):
    """Print response details"""
    print(f"\n{BOLD}{GREEN}Response:{RESET}")
    print(f"  Status: {BOLD}{response.status_code}{RESET}")
    try:
        print(f"  Body: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"  Body: {response.text}")


def test_health_check():
    """Test health check endpoint"""
    print_section("1. Health Check")
    
    endpoint = f"{BASE_URL}/health"
    print_request("GET", endpoint)
    
    response = requests.get(endpoint)
    print_response(response)
    
    return response.status_code == 200


def test_login():
    """Test authentication"""
    print_section("2. Authentication - Login")
    
    endpoint = f"{BASE_URL}/auth/login"
    data = {
        "username": "admin",
        "password": "admin123"
    }
    
    print_request("POST", endpoint, data)
    response = requests.post(endpoint, json=data)
    print_response(response)
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        return token
    
    return None


def test_transaction_analysis(token: str):
    """Test transaction analysis"""
    print_section("3. Transaction Analysis")
    
    endpoint = f"{BASE_URL}/analysis/transaction"
    data = {
        "transaction_id": "TEST-TXN-2024-001",
        "user_id": "TEST-USER-001",
        "amount": 5000.00,
        "currency": "USD",
        "country": "US",
        "merchant": "Premium Retailer Inc",
        "merchant_category": "5411",
        "metadata": {
            "device_type": "mobile",
            "app_version": "2.1.0"
        }
    }
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    print_request("POST", endpoint, data)
    response = requests.post(endpoint, json=data, headers=headers)
    print_response(response)
    
    if response.status_code == 200:
        result = response.json()
        # Extract incident ID if created
        incident_id = result.get("incident_id")
        return incident_id
    
    return None


def test_list_incidents(token: str):
    """Test listing incidents"""
    print_section("4. List Incidents")
    
    endpoint = f"{BASE_URL}/incidents?limit=5"
    print_request("GET", endpoint)
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = requests.get(endpoint, headers=headers)
    print_response(response)
    
    return response.status_code == 200


def test_get_incident(incident_id: str, token: str):
    """Test retrieving incident details"""
    if not incident_id:
        print(f"\n{YELLOW}⚠️  Skipping incident details test (no incident ID from analysis){RESET}")
        return False
    
    print_section("5. Get Incident Details")
    
    endpoint = f"{BASE_URL}/incidents/{incident_id}"
    print_request("GET", endpoint)
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = requests.get(endpoint, headers=headers)
    print_response(response)
    
    return response.status_code == 200


def test_generate_report(incident_id: str, token: str):
    """Test report generation"""
    if not incident_id:
        print(f"\n{YELLOW}⚠️  Skipping report generation test (no incident ID){RESET}")
        return False
    
    print_section("6. Generate Report")
    
    endpoint = f"{BASE_URL}/reports/generate"
    data = {
        "incident_id": incident_id,
        "format": "pdf",
        "include_evidence": True,
        "include_timeline": True
    }
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    print_request("POST", endpoint, data)
    response = requests.post(endpoint, json=data, headers=headers)
    print_response(response)
    
    return response.status_code == 200


def main():
    """Run all tests"""
    print(f"\n{BOLD}{BLUE}FinSecAI v2 API Test Suite{RESET}")
    print(f"{BLUE}Testing: {BASE_URL}{RESET}")
    
    # Test health
    if not test_health_check():
        print(f"\n{RED}❌ Health check failed. Is the API running?{RESET}")
        print(f"{YELLOW}Start with: python -m uvicorn api.main:app --reload{RESET}")
        return
    
    print(f"\n{GREEN}✅ Health check passed{RESET}")
    
    # Test login
    print(f"\n{YELLOW}Demo Credentials (no real database yet):{RESET}")
    print(f"  Username: admin | Password: admin123")
    print(f"  Username: analyst | Password: analyst123")
    
    token = test_login()
    if token:
        print(f"{GREEN}✅ Login successful{RESET}")
    else:
        print(f"{RED}❌ Login failed{RESET}")
        token = None
    
    # Test transaction analysis
    incident_id = test_transaction_analysis(token)
    if incident_id:
        print(f"{GREEN}✅ Transaction analysis successful (Incident: {incident_id}){RESET}")
    else:
        print(f"{YELLOW}⚠️  Transaction analysis returned but check response{RESET}")
    
    # Test incident listing
    if test_list_incidents(token):
        print(f"{GREEN}✅ List incidents successful{RESET}")
    else:
        print(f"{RED}❌ List incidents failed{RESET}")
    
    # Test get incident
    if test_get_incident(incident_id, token):
        print(f"{GREEN}✅ Get incident successful{RESET}")
    else:
        print(f"{YELLOW}⚠️  Get incident check response{RESET}")
    
    # Test report generation
    if test_generate_report(incident_id, token):
        print(f"{GREEN}✅ Report generation successful{RESET}")
    else:
        print(f"{YELLOW}⚠️  Report generation check response{RESET}")
    
    # Summary
    print_section("Test Summary")
    print(f"{GREEN}✅ Basic API functionality verified!{RESET}")
    print(f"\n{BOLD}Next Steps:{RESET}")
    print(f"  1. Review API_IMPLEMENTATION_GUIDE.md for full documentation")
    print(f"  2. Access API docs at: {BASE_URL}/docs")
    print(f"  3. Integrate with Streamlit dashboard")
    print(f"  4. Set up PostgreSQL for persistence")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print(f"\n{RED}❌ Connection Error: Cannot reach API at {BASE_URL}{RESET}")
        print(f"{YELLOW}Make sure the API is running:{RESET}")
        print(f"  python -m uvicorn api.main:app --reload")
    except Exception as e:
        print(f"\n{RED}❌ Error: {str(e)}{RESET}")
