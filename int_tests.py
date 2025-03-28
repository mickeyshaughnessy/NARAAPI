#!/usr/bin/env python3
import json,sys,os,time,random, string, requests
from datetime import datetime, timedelta

############
# thinking
# Rewrite the tests to be simpler and standalone:
# 1. Remove unittest framework
# 2. Use simple assertions with custom error messages
# 3. Create a simple test runner that reports success/failure
# 4. Keep the same test coverage but with simpler structure
# </thinking>
###########

# Configuration
BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000/api')
API_KEY = os.environ.get('API_KEY', 'test_api_key')
TEST_NUMBER = '4155551234'  # Test phone number for SMS/call tests

# Test status tracking
tests_run = 0
tests_passed = 0
tests_failed = 0
created_resources = {}  # Keep track of resources to clean up

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Helper functions
def random_string(length=10):
    """Generate a random string for test data"""
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))

def create_auth_headers():
    """Create headers with authentication"""
    return {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }

def assert_equals(actual, expected, message=None):
    """Assert that actual equals expected"""
    global tests_run, tests_passed, tests_failed
    tests_run += 1
    
    if actual == expected:
        tests_passed += 1
        return True
    else:
        tests_failed += 1
        error_msg = message or f"Expected {expected}, got {actual}"
        print(f"{RED}FAIL: {error_msg}{RESET}")
        return False

def assert_true(condition, message=None):
    """Assert that condition is True"""
    global tests_run, tests_passed, tests_failed
    tests_run += 1
    
    if condition:
        tests_passed += 1
        return True
    else:
        tests_failed += 1
        error_msg = message or "Assertion failed"
        print(f"{RED}FAIL: {error_msg}{RESET}")
        return False

def assert_in(item, container, message=None):
    """Assert that item is in container"""
    global tests_run, tests_passed, tests_failed
    tests_run += 1
    
    if item in container:
        tests_passed += 1
        return True
    else:
        tests_failed += 1
        error_msg = message or f"Expected {item} to be in {container}"
        print(f"{RED}FAIL: {error_msg}{RESET}")
        return False

def assert_is_instance(obj, cls, message=None):
    """Assert that obj is an instance of cls"""
    global tests_run, tests_passed, tests_failed
    tests_run += 1
    
    if isinstance(obj, cls):
        tests_passed += 1
        return True
    else:
        tests_failed += 1
        error_msg = message or f"Expected object of type {cls.__name__}, got {type(obj).__name__}"
        print(f"{RED}FAIL: {error_msg}{RESET}")
        return False

def run_test(test_func, *args, **kwargs):
    """Run a test function and report success/failure"""
    global tests_run, tests_passed, tests_failed
    
    test_name = test_func.__name__
    print(f"\n{BOLD}Running test: {test_name}{RESET}")
    
    start_time = time.time()
    
    try:
        test_func(*args, **kwargs)
        elapsed = time.time() - start_time
        print(f"{GREEN}PASS: {test_name} ({elapsed:.2f}s){RESET}")
    except AssertionError as e:
        elapsed = time.time() - start_time
        tests_failed += 1
        print(f"{RED}FAIL: {test_name} - {str(e)} ({elapsed:.2f}s){RESET}")
    except Exception as e:
        elapsed = time.time() - start_time
        tests_failed += 1
        print(f"{RED}ERROR: {test_name} - {type(e).__name__}: {str(e)} ({elapsed:.2f}s){RESET}")

def cleanup_resources():
    """Clean up any resources created during tests"""
    headers = create_auth_headers()
    
    print(f"\n{YELLOW}Cleaning up created resources...{RESET}")
    
    for resource_type, resource_ids in created_resources.items():
        for resource_id in resource_ids:
            try:
                response = requests.delete(
                    f"{BASE_URL}/{resource_type}/{resource_id}",
                    headers=headers
                )
                if response.status_code == 204:
                    print(f"Deleted {resource_type}/{resource_id}")
                else:
                    print(f"Failed to delete {resource_type}/{resource_id}: {response.status_code}")
            except Exception as e:
                print(f"Error cleaning up {resource_type}/{resource_id}: {e}")

def add_resource_for_cleanup(resource_type, resource_id):
    """Add a resource to be cleaned up after tests"""
    if resource_type not in created_resources:
        created_resources[resource_type] = []
    created_resources[resource_type].append(resource_id)

#############################################################
# Tests
#############################################################

def test_health_check():
    """Test API health check endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    assert_equals(response.status_code, 200, "Health check should return 200")
    data = response.json()
    assert_equals(data['status'], 'ok', "Health check status should be 'ok'")

def test_unauthorized_access():
    """Test unauthorized access is properly rejected"""
    # Try without auth headers
    response = requests.get(f"{BASE_URL}/contacts")
    assert_equals(response.status_code, 401, "Unauthorized request should return 401")
    
    # Try with invalid API key
    invalid_headers = {
        'Authorization': 'Bearer invalid_key',
        'Content-Type': 'application/json'
    }
    response = requests.get(f"{BASE_URL}/contacts", headers=invalid_headers)
    assert_equals(response.status_code, 401, "Invalid API key should return 401")

def test_crud_operations():
    """Test Create, Read, Update, Delete operations"""
    headers = create_auth_headers()
    
    # CREATE
    contact_data = {
        'name': f'Test Contact {random_string()}',
        'number': f'555{random.randint(1000000, 9999999)}',
        'email': f'{random_string()}@example.com'
    }
    
    create_response = requests.post(
        f"{BASE_URL}/contacts",
        headers=headers,
        json=contact_data
    )
    assert_equals(create_response.status_code, 201, "Contact creation should return 201")
    created_contact = create_response.json()
    assert_in('id', created_contact, "Created contact should have an ID")
    
    # Store for cleanup
    contact_id = created_contact['id']
    add_resource_for_cleanup('contacts', contact_id)
    
    # READ
    read_response = requests.get(
        f"{BASE_URL}/contacts/{contact_id}",
        headers=headers
    )
    assert_equals(read_response.status_code, 200, "Contact retrieval should return 200")
    retrieved_contact = read_response.json()
    assert_equals(retrieved_contact['name'], contact_data['name'], "Retrieved contact name should match")
    assert_equals(retrieved_contact['number'], contact_data['number'], "Retrieved contact number should match")
    
    # UPDATE
    update_data = {
        'name': f'Updated {contact_data["name"]}',
        'notes': 'Added during test'
    }
    update_response = requests.put(
        f"{BASE_URL}/contacts/{contact_id}",
        headers=headers,
        json=update_data
    )
    assert_equals(update_response.status_code, 200, "Contact update should return 200")
    updated_contact = update_response.json()
    assert_equals(updated_contact['name'], update_data['name'], "Updated contact name should match")
    assert_equals(updated_contact['notes'], update_data['notes'], "Updated contact notes should match")
    
    # LIST
    list_response = requests.get(
        f"{BASE_URL}/contacts",
        headers=headers
    )
    assert_equals(list_response.status_code, 200, "Contacts list should return 200")
    contacts_list = list_response.json()
    assert_is_instance(contacts_list, list, "Contacts should be returned as a list")
    contact_ids = [c['id'] for c in contacts_list]
    assert_in(contact_id, contact_ids, "Created contact should be in the list")
    
    # DELETE
    delete_response = requests.delete(
        f"{BASE_URL}/contacts/{contact_id}",
        headers=headers
    )
    assert_equals(delete_response.status_code, 204, "Contact deletion should return 204")
    
    # Verify deleted
    get_deleted_response = requests.get(
        f"{BASE_URL}/contacts/{contact_id}",
        headers=headers
    )
    assert_equals(get_deleted_response.status_code, 404, "Deleted contact should return 404")
    
    # Remove from cleanup since we already deleted it
    if 'contacts' in created_resources and contact_id in created_resources['contacts']:
        created_resources['contacts'].remove(contact_id)

def test_not_found():
    """Test proper 404 response for non-existent resources"""
    headers = create_auth_headers()
    
    response = requests.get(
        f"{BASE_URL}/contacts/non_existent_id",
        headers=headers
    )
    assert_equals(response.status_code, 404, "Non-existent contact should return 404")
    
    response = requests.get(
        f"{BASE_URL}/non_existent_endpoint",
        headers=headers
    )
    assert_equals(response.status_code, 404, "Non-existent endpoint should return 404")

def test_validation_errors():
    """Test validation errors are properly returned"""
    headers = create_auth_headers()
    
    # Missing required field
    contact_data = {
        'email': f'{random_string()}@example.com'
        # Missing 'name' and 'number' which are required
    }
    
    response = requests.post(
        f"{BASE_URL}/contacts",
        headers=headers,
        json=contact_data
    )
    assert_equals(response.status_code, 400, "Invalid contact data should return 400")
    error_data = response.json()
    assert_in('errors', error_data, "Error response should contain 'errors' field")
    
    # Invalid data type
    contact_data = {
        'name': 'Test Contact',
        'number': 'not-a-number',  # Should be numeric
        'email': f'{random_string()}@example.com'
    }
    
    response = requests.post(
        f"{BASE_URL}/contacts",
        headers=headers,
        json=contact_data
    )
    assert_equals(response.status_code, 400, "Invalid number format should return 400")
    error_data = response.json()
    assert_in('errors', error_data, "Error response should contain 'errors' field")

def test_contact_search():
    """Test searching contacts"""
    headers = create_auth_headers()
    
    # Create test contacts
    unique_name = f'Searchable {random_string()}'
    contacts_data = [
        {
            'name': unique_name,
            'number': f'555{random.randint(1000000, 9999999)}',
            'email': f'{random_string()}@example.com'
        },
        {
            'name': f'Another {unique_name}',
            'number': f'555{random.randint(1000000, 9999999)}',
            'email': f'{random_string()}@example.com'
        },
        {
            'name': 'Unrelated Contact',
            'number': f'555{random.randint(1000000, 9999999)}',
            'email': f'{random_string()}@example.com'
        }
    ]
    
    created_ids = []
    for contact_data in contacts_data:
        response = requests.post(
            f"{BASE_URL}/contacts",
            headers=headers,
            json=contact_data
        )
        assert_equals(response.status_code, 201, "Contact creation should return 201")
        created_contact = response.json()
        created_ids.append(created_contact['id'])
        add_resource_for_cleanup('contacts', created_contact['id'])
    
    # Search by name
    search_response = requests.get(
        f"{BASE_URL}/contacts/search?query={unique_name}",
        headers=headers
    )
    assert_equals(search_response.status_code, 200, "Contact search should return 200")
    search_results = search_response.json()
    assert_is_instance(search_results, list, "Search results should be a list")
    assert_equals(len(search_results), 2, "Search should find exactly 2 matching contacts")
    
    # Search by number (using the first contact's number)
    first_contact_number = contacts_data[0]['number']
    search_response = requests.get(
        f"{BASE_URL}/contacts/search?query={first_contact_number}",
        headers=headers
    )
    assert_equals(search_response.status_code, 200, "Contact number search should return 200")
    search_results = search_response.json()
    assert_is_instance(search_results, list, "Search results should be a list")
    assert_equals(len(search_results), 1, "Search by number should find exactly 1 contact")

def test_send_sms():
    """Test sending an SMS"""
    headers = create_auth_headers()
    
    sms_data = {
        'to': TEST_NUMBER,
        'message': f'Test message {random_string()}',
        'from': 'TEST'
    }
    
    response = requests.post(
        f"{BASE_URL}/sms/send",
        headers=headers,
        json=sms_data
    )
    assert_equals(response.status_code, 200, "SMS send should return 200")
    result = response.json()
    assert_in('id', result, "SMS response should contain message ID")
    assert_in('status', result, "SMS response should contain status")
    
    # Store for verification
    sms_id = result['id']
    add_resource_for_cleanup('sms', sms_id)
    
    # Verify SMS was sent
    status_response = requests.get(
        f"{BASE_URL}/sms/{sms_id}",
        headers=headers
    )
    assert_equals(status_response.status_code, 200, "SMS status check should return 200")
    status_data = status_response.json()
    assert_equals(status_data['to'], sms_data['to'], "SMS recipient should match")
    assert_equals(status_data['message'], sms_data['message'], "SMS message should match")

def test_sms_history():
    """Test retrieving SMS history"""
    headers = create_auth_headers()
    
    # Send a test message first
    sms_data = {
        'to': TEST_NUMBER,
        'message': f'History test {random_string()}',
        'from': 'TEST'
    }
    
    send_response = requests.post(
        f"{BASE_URL}/sms/send",
        headers=headers,
        json=sms_data
    )
    assert_equals(send_response.status_code, 200, "SMS send should return 200")
    sms_id = send_response.json()['id']
    add_resource_for_cleanup('sms', sms_id)
    
    # Get history
    history_response = requests.get(
        f"{BASE_URL}/sms/history",
        headers=headers
    )
    assert_equals(history_response.status_code, 200, "SMS history should return 200")
    history_data = history_response.json()
    assert_is_instance(history_data, list, "SMS history should be a list")
    
    # Check if our test message is in the history
    found = False
    for message in history_data:
        if message.get('id') == sms_id:
            found = True
            assert_equals(message['to'], sms_data['to'], "SMS recipient should match")
            assert_equals(message['message'], sms_data['message'], "SMS message should match")
            break
    assert_true(found, "Test message not found in SMS history")
    
    # Test filtering by date range
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    filtered_response = requests.get(
        f"{BASE_URL}/sms/history?from={yesterday}&to={tomorrow}",
        headers=headers
    )
    assert_equals(filtered_response.status_code, 200, "Filtered SMS history should return 200")
    filtered_data = filtered_response.json()
    assert_is_instance(filtered_data, list, "Filtered SMS history should be a list")

def test_make_call():
    """Test making an outbound call"""
    headers = create_auth_headers()
    
    call_data = {
        'to': TEST_NUMBER,
        'from': 'TEST',
        'callback_url': 'https://example.com/callback'
    }
    
    response = requests.post(
        f"{BASE_URL}/calls/make",
        headers=headers,
        json=call_data
    )
    assert_equals(response.status_code, 200, "Call initiation should return 200")
    result = response.json()
    assert_in('id', result, "Call response should contain ID")
    assert_in('status', result, "Call response should contain status")
    
    # Store for verification
    call_id = result['id']
    add_resource_for_cleanup('calls', call_id)
    
    # Verify call was initiated
    status_response = requests.get(
        f"{BASE_URL}/calls/{call_id}",
        headers=headers
    )
    assert_equals(status_response.status_code, 200, "Call status check should return 200")
    status_data = status_response.json()
    assert_equals(status_data['to'], call_data['to'], "Call recipient should match")

def test_carrier_lookup():
    """Test carrier lookup for a phone number"""
    headers = create_auth_headers()
    test_number = TEST_NUMBER
    
    response = requests.get(
        f"{BASE_URL}/carrier/lookup?number={test_number}",
        headers=headers
    )
    assert_equals(response.status_code, 200, "Carrier lookup should return 200")
    lookup_data = response.json()
    assert_in('carrier', lookup_data, "Lookup should contain carrier info")
    assert_in('carrier_type', lookup_data, "Lookup should contain carrier type")
    assert_in('number', lookup_data, "Lookup should contain number")
    assert_equals(lookup_data['number'], test_number, "Lookup number should match request")

def test_carrier_bulk_lookup():
    """Test bulk carrier lookup for multiple numbers"""
    headers = create_auth_headers()
    
    test_numbers = [
        f'555{random.randint(1000000, 9999999)}',
        f'555{random.randint(1000000, 9999999)}',
        f'555{random.randint(1000000, 9999999)}'
    ]
    
    bulk_data = {
        'numbers': test_numbers
    }
    
    response = requests.post(
        f"{BASE_URL}/carrier/bulk-lookup",
        headers=headers,
        json=bulk_data
    )
    assert_equals(response.status_code, 200, "Bulk carrier lookup should return 200")
    results = response.json()
    assert_in('results', results, "Bulk lookup should contain results")
    assert_equals(len(results['results']), len(test_numbers), "Should have results for all numbers")
    
    for number_data in results['results']:
        assert_in('number', number_data, "Each result should contain the number")
        assert_in('carrier', number_data, "Each result should contain carrier info")
        assert_in('carrier_type', number_data, "Each result should contain carrier type")
        assert_in(number_data['number'], test_numbers, "Result number should be in request")

def test_spam_check():
    """Test checking if a number is spam"""
    headers = create_auth_headers()
    
    # Test known spam number
    spam_number = '9009001234'  # Example known spam number
    
    response = requests.get(
        f"{BASE_URL}/spam-filter/check?number={spam_number}",
        headers=headers
    )
    assert_equals(response.status_code, 200, "Spam check should return 200")
    result = response.json()
    assert_in('is_spam', result, "Response should indicate if number is spam")
    assert_in('confidence', result, "Response should include confidence level")
    assert_in('details', result, "Response should include details")
    
    # Test non-spam number
    non_spam_number = TEST_NUMBER
    
    response = requests.get(
        f"{BASE_URL}/spam-filter/check?number={non_spam_number}",
        headers=headers
    )
    assert_equals(response.status_code, 200, "Spam check should return 200")
    result = response.json()
    assert_in('is_spam', result, "Response should indicate if number is spam")

def test_report_spam():
    """Test reporting a number as spam"""
    headers = create_auth_headers()
    
    report_data = {
        'number': f'555{random.randint(1000000, 9999999)}',
        'reason': 'Test spam report',
        'evidence': 'Message content was unsolicited advertising'
    }
    
    response = requests.post(
        f"{BASE_URL}/spam-filter/report",
        headers=headers,
        json=report_data
    )
    assert_equals(response.status_code, 200, "Spam report should return 200")
    result = response.json()
    assert_in('success', result, "Response should indicate success")
    assert_true(result['success'], "Report should be successful")
    assert_in('report_id', result, "Response should include report ID")
    
    # Verify the report was recorded
    report_id = result['report_id']
    verification_response = requests.get(
        f"{BASE_URL}/spam-filter/reports",
        headers=headers
    )
    assert_equals(verification_response.status_code, 200, "Reports list should return 200")
    reports = verification_response.json()
    
    found = False
    for report in reports:
        if report.get('id') == report_id:
            found = True
            assert_equals(report['number'], report_data['number'], "Report number should match")
            assert_equals(report['reason'], report_data['reason'], "Report reason should match")
            break
    assert_true(found, "Spam report not found in reports list")

def test_spam_rules_management():
    """Test managing custom spam filtering rules"""
    headers = create_auth_headers()
    
    # Create a custom rule
    rule_data = {
        'name': f'Test Rule {random_string()}',
        'pattern': f'pattern_{random_string()}',
        'action': 'block',
        'priority': random.randint(1, 10)
    }
    
    create_response = requests.post(
        f"{BASE_URL}/spam-filter/rules",
        headers=headers,
        json=rule_data
    )
    assert_equals(create_response.status_code, 201, "Rule creation should return 201")
    created_rule = create_response.json()
    assert_in('id', created_rule, "Created rule should have an ID")
    rule_id = created_rule['id']
    add_resource_for_cleanup('spam-filter/rules', rule_id)
    
    # Get the rule
    get_response = requests.get(
        f"{BASE_URL}/spam-filter/rules/{rule_id}",
        headers=headers
    )
    assert_equals(get_response.status_code, 200, "Rule retrieval should return 200")
    rule = get_response.json()
    assert_equals(rule['name'], rule_data['name'], "Rule name should match")
    assert_equals(rule['pattern'], rule_data['pattern'], "Rule pattern should match")
    
    # Update the rule
    update_data = {
        'name': f'Updated {rule_data["name"]}',
        'action': 'flag'
    }
    update_response = requests.put(
        f"{BASE_URL}/spam-filter/rules/{rule_id}",
        headers=headers,
        json=update_data
    )
    assert_equals(update_response.status_code, 200, "Rule update should return 200")
    updated_rule = update_response.json()
    assert_equals(updated_rule['name'], update_data['name'], "Updated rule name should match")
    assert_equals(updated_rule['action'], update_data['action'], "Updated rule action should match")
    
    # List all rules
    list_response = requests.get(
        f"{BASE_URL}/spam-filter/rules",
        headers=headers
    )
    assert_equals(list_response.status_code, 200, "Rules list should return 200")
    rules = list_response.json()
    assert_is_instance(rules, list, "Rules should be returned as a list")
    rule_ids = [r['id'] for r in rules]
    assert_in(rule_id, rule_ids, "Created rule should be in the list")
    
    # Delete the rule
    delete_response = requests.delete(
        f"{BASE_URL}/spam-filter/rules/{rule_id}",
        headers=headers
    )
    assert_equals(delete_response.status_code, 204, "Rule deletion should return 204")
    
    # Check it's deleted
    get_deleted_response = requests.get(
        f"{BASE_URL}/spam-filter/rules/{rule_id}",
        headers=headers
    )
    assert_equals(get_deleted_response.status_code, 404, "Deleted rule should return 404")
    
    # Remove from cleanup list since we already deleted it
    if 'spam-filter/rules' in created_resources and rule_id in created_resources['spam-filter/rules']:
        created_resources['spam-filter/rules'].remove(rule_id)

def run_all_tests():
    """Run all integration tests"""
    print(f"{BOLD}Starting API Integration Tests{RESET}")
    print(f"API Base URL: {BASE_URL}")
    
    start_time = time.time()
    
    # Generic API Tests
    run_test(test_health_check)
    run_test(test_unauthorized_access)
    run_test(test_crud_operations)
    run_test(test_not_found)
    run_test(test_validation_errors)
    
    # Contacts API Tests
    run_test(test_contact_search)
    
    # SMS API Tests
    run_test(test_send_sms)
    run_test(test_sms_history)
    
    # Call API Tests
    run_test(test_make_call)
    
    # Carrier API Tests
    run_test(test_carrier_lookup)
    run_test(test_carrier_bulk_lookup)
    
    # Spam Filter API Tests
    run_test(test_spam_check)
    run_test(test_report_spam)
    run_test(test_spam_rules_management)
    
    # Clean up
    cleanup_resources()
    
    # Print summary
    elapsed = time.time() - start_time
    print(f"\n{BOLD}Test Summary:{RESET}")
    print(f"Ran {tests_run} tests in {elapsed:.2f} seconds")
    print(f"{GREEN}Passed: {tests_passed}{RESET}")
    if tests_failed > 0:
        print(f"{RED}Failed: {tests_failed}{RESET}")
        return False
    else:
        print(f"{GREEN}All tests passed!{RESET}")
        return True

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
