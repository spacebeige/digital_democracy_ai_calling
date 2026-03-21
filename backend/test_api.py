"""
Test Script for Ticketing API
Run this after starting the FastAPI server to test all endpoints
"""
import requests
import json
from typing import Any

BASE_URL = "http://localhost:8000"

# ANSI color codes for terminal output
HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKCYAN = '\033[96m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'


def print_section(title: str) -> None:
    """Print a formatted section header"""
    print(f"\n{BOLD}{HEADER}{'='*70}{ENDC}")
    print(f"{BOLD}{HEADER}{title:^70}{ENDC}")
    print(f"{BOLD}{HEADER}{'='*70}{ENDC}\n")


def print_success(message: str) -> None:
    """Print success message"""
    print(f"{OKGREEN}✅ {message}{ENDC}")


def print_error(message: str) -> None:
    """Print error message"""
    print(f"{FAIL}❌ {message}{ENDC}")


def print_info(message: str) -> None:
    """Print info message"""
    print(f"{OKCYAN}ℹ️  {message}{ENDC}")


def print_request(method: str, endpoint: str, data: dict = None) -> None:
    """Print request details"""
    print(f"{BOLD}{OKBLUE}{method} {endpoint}{ENDC}")
    if data:
        print(f"Body: {json.dumps(data, indent=2)}")


def print_response(response: requests.Response) -> None:
    """Print response details"""
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")


def print_warning(message: str) -> None:
    """Print warning message"""
    print(f"{WARNING}⚠️  {message}{ENDC}")


def test_health_check() -> bool:
    """Test health check endpoint"""
    print_section("1️⃣  Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        print_request("GET", "/")
        print_response(response)
        
        if response.status_code == 200:
            print_success("Health check passed!")
            return True
        else:
            print_error("Health check failed!")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_create_ticket() -> dict | None:
    """Test ticket creation"""
    print_section("2️⃣  Create Ticket")
    
    try:
        data = {
            "issue": "Major flood in market area",
            "location": "Central Market",
            "priority": "HIGH"
        }
        
        response = requests.post(f"{BASE_URL}/ticket/create", json=data)
        print_request("POST", "/ticket/create", data)
        print_response(response)
        
        if response.status_code == 200:
            print_success("Ticket created successfully!")
            return response.json()
        else:
            print_error("Failed to create ticket!")
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None


def test_create_ticket_auto_priority() -> dict | None:
    """Test ticket creation with auto-detected priority"""
    print_section("3️⃣  Create Ticket with Auto-Detected Priority")
    
    try:
        data = {
            "issue": "There is garbage pile on the street",
            "location": "Old Town"
        }
        
        response = requests.post(f"{BASE_URL}/ticket/create", json=data)
        print_request("POST", "/ticket/create", data)
        print_response(response)
        
        if response.status_code == 200:
            print_success("Ticket created with auto-detected priority!")
            return response.json()
        else:
            print_error("Failed to create ticket!")
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None


def test_get_all_tickets() -> bool:
    """Test getting all tickets"""
    print_section("4️⃣  Get All Tickets")
    
    try:
        response = requests.get(f"{BASE_URL}/tickets")
        print_request("GET", "/tickets")
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Retrieved {data.get('total_count', 0)} tickets!")
            return True
        else:
            print_error("Failed to get tickets!")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_get_single_ticket(ticket_id: str) -> bool:
    """Test getting a single ticket"""
    print_section("5️⃣  Get Single Ticket")
    
    try:
        response = requests.get(f"{BASE_URL}/ticket/{ticket_id}")
        print_request("GET", f"/ticket/{ticket_id}")
        print_response(response)
        
        if response.status_code == 200:
            print_success(f"Retrieved ticket {ticket_id}!")
            return True
        else:
            print_error("Failed to get ticket!")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_valid_status_transition(ticket_id: str) -> bool:
    """Test valid status transition"""
    print_section("6️⃣  Valid Status Transition (OPEN → ASSIGNED)")
    
    try:
        data = {"status": "ASSIGNED"}
        
        response = requests.put(f"{BASE_URL}/ticket/{ticket_id}/status", json=data)
        print_request("PUT", f"/ticket/{ticket_id}/status", data)
        print_response(response)
        
        if response.status_code == 200:
            print_success("Status updated successfully!")
            return True
        else:
            print_error("Failed to update status!")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_invalid_status_transition(ticket_id: str) -> bool:
    """Test invalid status transition"""
    print_section("7️⃣  Invalid Status Transition (ASSIGNED → CLOSED)")
    
    try:
        data = {"status": "CLOSED"}
        
        response = requests.put(f"{BASE_URL}/ticket/{ticket_id}/status", json=data)
        print_request("PUT", f"/ticket/{ticket_id}/status", data)
        print_response(response)
        
        if response.status_code == 400:
            print_success("Invalid transition correctly rejected!")
            return True
        else:
            print_warning("Expected 400 status code!")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_workflow_transitions(ticket_id: str) -> bool:
    """Test complete state machine workflow"""
    print_section("8️⃣  Complete Workflow Transitions")
    
    transitions = [
        ("ASSIGNED", "IN_PROGRESS"),
        ("IN_PROGRESS", "RESOLVED"),
        ("RESOLVED", "CLOSED")
    ]
    
    all_passed = True
    
    for from_status, to_status in transitions:
        try:
            data = {"status": to_status}
            response = requests.put(f"{BASE_URL}/ticket/{ticket_id}/status", json=data)
            
            print_info(f"Transition: {from_status} → {to_status}")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print_success(f"✓ {from_status} → {to_status}")
            else:
                print_error(f"✗ {from_status} → {to_status}")
                all_passed = False
        except Exception as e:
            print_error(f"Error in transition {from_status} → {to_status}: {e}")
            all_passed = False
    
    return all_passed


def test_analytics() -> bool:
    """Test analytics endpoint"""
    print_section("9️⃣  Analytics (Tickets by Location)")
    
    try:
        response = requests.get(f"{BASE_URL}/analytics")
        print_request("GET", "/analytics")
        print_response(response)
        
        if response.status_code == 200:
            print_success("Analytics retrieved successfully!")
            return True
        else:
            print_error("Failed to get analytics!")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def print_summary(results: dict) -> None:
    """Print test summary"""
    print_section("📊 Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = f"{OKGREEN}✓{ENDC}" if result else f"{FAIL}✗{ENDC}"
        print(f"{status} {test}")
    
    print(f"\nTotal: {BOLD}{passed}/{total} tests passed{ENDC}\n")
    
    if passed == total:
        print(f"{OKGREEN}🎉 All tests passed!{ENDC}\n")
    else:
        print(f"{WARNING}⚠️  Some tests failed!{ENDC}\n")


def main():
    """Main test runner"""
    print(f"\n{BOLD}{OKBLUE}🎫 Ticketing System API Test Suite{ENDC}\n")
    
    results = {}
    
    # Test health check
    results["Health Check"] = test_health_check()
    
    if not results["Health Check"]:
        print_error("Cannot proceed - server is not running!")
        print_info("Start the server with: uvicorn app.main:app --reload")
        return
    
    # Test ticket creation
    ticket1 = test_create_ticket()
    results["Create Ticket"] = ticket1 is not None
    
    if not ticket1:
        print_error("Cannot proceed - ticket creation failed!")
        return
    
    ticket_id = ticket1["ticket_id"]
    
    # Test auto-priority detection
    ticket2 = test_create_ticket_auto_priority()
    results["Auto-Priority Detection"] = ticket2 is not None
    
    # Test getting all tickets
    results["Get All Tickets"] = test_get_all_tickets()
    
    # Test getting single ticket
    results["Get Single Ticket"] = test_get_single_ticket(ticket_id)
    
    # Test valid transition
    results["Valid Transition"] = test_valid_status_transition(ticket_id)
    
    # Test invalid transition
    results["Invalid Transition"] = test_invalid_status_transition(ticket_id)
    
    # Test workflow
    results["Complete Workflow"] = test_workflow_transitions(ticket_id)
    
    # Test analytics
    results["Analytics"] = test_analytics()
    
    # Print summary
    print_summary(results)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{WARNING}Tests interrupted by user{ENDC}\n")
    except Exception as e:
        print_error(f"Unexpected error: {e}")
