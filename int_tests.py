"""
Integration tests for the API server with visual feedback and summary stats
"""

############
# Thinking
# 🤔🤔🤔🤠
# Need to add more verbosity without going overboard:
# 1. Add more emojis for different test types
# 2. Include visual command-line art/borders
# 3. Add summary statistics at the end
# 4. Keep the fixed endpoint approach (/api/metrics for protected tests)
# 5. Add progress indicators and more detailed test info
# 6. Track test results for summary generation
#</thinking>
###########

import unittest
import json
import requests
import config
import time
import sys
from termcolor import colored
from utils import generate_token, store_token, redis_client

# Base URL for API requests
BASE_URL = f"http://localhost:{config.API_PORT}"

# Enhanced emoji indicators
EMOJI_SUCCESS = "✅"
EMOJI_FAILURE = "❌"
EMOJI_INFO = "ℹ️"
EMOJI_SERVER = "🖥️"
EMOJI_AUTH = "🔐"
EMOJI_DB = "🗄️"
EMOJI_API = "🌐"
EMOJI_USER = "👤"
EMOJI_TEST = "🧪"
EMOJI_TIME = "⏱️"
EMOJI_PRIVACY = "🔒"
EMOJI_ROCKET = "🚀"
EMOJI_SECURITY = "🛡️"

# Command line art elements
BOX_TOP = "┏" + "━" * 70 + "┓"
BOX_BOTTOM = "┗" + "━" * 70 + "┛"
BOX_LINE = "┃"
SEPARATOR = "─" * 72

class TestStats:
    """Track test statistics for summary reporting"""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.start_time = None
        self.end_time = None
        self.test_results = []
    
    def add_result(self, test_name, result, duration):
        self.test_results.append({
            "name": test_name,
            "result": result,
            "duration": duration
        })
        self.total += 1
        if result == "PASS":
            self.passed += 1
        elif result == "FAIL":
            self.failed += 1
        elif result == "SKIP":
            self.skipped += 1
    
    def print_summary(self):
        if not self.start_time or not self.end_time:
            return
            
        total_time = self.end_time - self.start_time
        
        print(f"\n{BOX_TOP}")
        print(f"{BOX_LINE} {EMOJI_ROCKET} {colored('TEST SUMMARY', 'cyan', attrs=['bold'])} {' ' * 54}{BOX_LINE}")
        print(f"{BOX_LINE}{' ' * 70}{BOX_LINE}")
        print(f"{BOX_LINE} Total Tests: {colored(self.total, 'white', attrs=['bold'])} {' ' * 55}{BOX_LINE}")
        print(f"{BOX_LINE} Passed:      {colored(self.passed, 'green', attrs=['bold'])} {' ' * 55}{BOX_LINE}")
        print(f"{BOX_LINE} Failed:      {colored(self.failed, 'red', attrs=['bold'])} {' ' * 55}{BOX_LINE}")
        print(f"{BOX_LINE} Skipped:     {colored(self.skipped, 'yellow', attrs=['bold'])} {' ' * 55}{BOX_LINE}")
        print(f"{BOX_LINE} Total Time:  {colored(f'{total_time:.2f}s', 'blue', attrs=['bold'])} {' ' * 51}{BOX_LINE}")
        print(f"{BOX_LINE}{' ' * 70}{BOX_LINE}")
        
        # Show performance stats
        print(f"{BOX_LINE} {EMOJI_TIME} {colored('TEST PERFORMANCE', 'cyan', attrs=['bold'])} {' ' * 50}{BOX_LINE}")
        print(f"{BOX_LINE}{' ' * 70}{BOX_LINE}")
        
        # Sort tests by duration
        sorted_results = sorted(self.test_results, key=lambda x: x["duration"], reverse=True)
        for i, test in enumerate(sorted_results[:5]):
            name = test["name"][:40].ljust(40)
            result_color = "green" if test["result"] == "PASS" else "red"
            result_text = colored(f"{test['result']}", result_color)
            duration = colored(f"{test['duration']:.3f}s", "blue")
            print(f"{BOX_LINE} {i+1}. {name} {result_text} {duration} {' ' * (18 - len(test['result']))}{BOX_LINE}")
            
        print(f"{BOX_BOTTOM}")

# Global stats tracker
test_stats = TestStats()

class APIIntegrationTests(unittest.TestCase):
    """Test cases for API server endpoints with visual feedback"""
    
    @classmethod
    def setUpClass(cls):
        """Setup test environment once before all tests"""
        test_stats.start_time = time.time()
        
        print(f"\n{BOX_TOP}")
        print(f"{BOX_LINE} {EMOJI_ROCKET} {colored('API INTEGRATION TESTS', 'cyan', attrs=['bold'])} {' ' * 50}{BOX_LINE}")
        print(f"{BOX_BOTTOM}")
        
        # Create a test user and token
        cls.test_username = "testuser"
        cls.test_token = generate_token()
        store_token(cls.test_username, cls.test_token, expires_in=3600)
        print(f"{EMOJI_AUTH} Created test token for user: {colored(cls.test_username, 'cyan')}")
        
        # Headers for authenticated requests
        cls.auth_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cls.test_token}"
        }
        
        # Headers for unauthenticated requests
        cls.headers = {
            "Content-Type": "application/json"
        }
        
        # Check server availability
        cls._wait_for_server()
    
    @classmethod
    def _wait_for_server(cls):
        """Wait for the server to be ready"""
        print(f"{EMOJI_SERVER} Checking server availability...")
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                response = requests.get(f"{BASE_URL}/ping", timeout=3)
                if response.status_code == 200:
                    print(f"{EMOJI_SUCCESS} Server is ready and responding")
                    return
                    
            except requests.RequestException:
                pass
            
            print(f"{EMOJI_INFO} Waiting for server to start... (attempt {retry_count+1}/{max_retries})")
            time.sleep(2)
            retry_count += 1
            
        print(f"{EMOJI_FAILURE} Server not available after {max_retries} attempts")
        sys.exit(1)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        # Remove test user token
        redis_client.delete(f"auth_token:{cls.test_token}")
        print(f"{EMOJI_AUTH} Removed test token for user: {colored(cls.test_username, 'cyan')}")
        
        test_stats.end_time = time.time()
        test_stats.print_summary()
    
    def setUp(self):
        """Setup before each test"""
        self.test_name = self.id().split('.')[-1]
        self.start_time = time.time()
        print(f"\n{EMOJI_TEST} Running: {colored(self.test_name, 'cyan')}")
    
    def tearDown(self):
        """Cleanup after each test"""
        duration = time.time() - self.start_time
        result = getattr(self, '_outcome').result
        
        # Check if test passed
        if len(result.failures) == 0 and len(result.errors) == 0:
            for failure in result.failures:
                if self == failure[0]:
                    status = "FAIL"
                    break
            else:
                for error in result.errors:
                    if self == error[0]:
                        status = "ERROR"
                        break
                else:
                    status = "PASS"
        else:
            # Check if this specific test has failed or errored
            for failure in result.failures:
                if self == failure[0]:
                    status = "FAIL"
                    break
            else:
                for error in result.errors:
                    if self == error[0]:
                        status = "ERROR"
                        break
                else:
                    status = "PASS"
        
        # Simplified approach to check if the test passed
        if status == "PASS":
            print(f"{EMOJI_SUCCESS} {colored('PASSED', 'green')} {self.test_name} in {duration:.3f}s")
        else:
            print(f"{EMOJI_FAILURE} {colored('FAILED', 'red')} {self.test_name} in {duration:.3f}s")
        
        test_stats.add_result(self.test_name, "PASS" if status == "PASS" else "FAIL", duration)
    
    def make_request(self, method, endpoint, headers=None, data=None, expected_status=200, description=None):
        """Make an HTTP request with informative logging"""
        url = f"{BASE_URL}{endpoint}"
        
        if description:
            print(f"{EMOJI_INFO} {description}")
        
        print(f"{EMOJI_API} {method.upper()} {url}")
        
        try:
            start = time.time()
            if method.lower() == 'get':
                response = requests.get(url, headers=headers, timeout=5)
            elif method.lower() == 'post':
                response = requests.post(url, headers=headers, data=json.dumps(data) if data else None, timeout=5)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            duration = time.time() - start
            
            status_color = 'green' if response.status_code == expected_status else 'red'
            print(f"{EMOJI_INFO} Response: HTTP {colored(response.status_code, status_color)} in {duration:.3f}s")
            
            return response
        except requests.RequestException as e:
            print(f"{EMOJI_FAILURE} Request error: {str(e)}")
            self.fail(f"Request error: {str(e)}")
    
    def test_ping(self):
        """Test the ping endpoint"""
        print(f"{EMOJI_SERVER} Testing server heartbeat...")
        response = requests.get(f"{BASE_URL}/ping")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "ok")
    
    def test_health(self):
        """Test the health endpoint"""
        response = self.make_request('GET', '/health', description="Checking API health status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        print(f"{EMOJI_INFO} Health status: {colored(data['status'], 'green')}")
    
    def test_login_endpoint(self):
        """Test the login endpoint"""
        payload = {
            "username": "testuser",
            "password": "password123"
        }
        response = self.make_request(
            'POST', 
            '/auth/login', 
            headers=self.headers, 
            data=payload,
            description="Testing user authentication flow"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("token", data)
        print(f"{EMOJI_AUTH} Successfully obtained authentication token")
    
    def test_register_endpoint(self):
        """Test the register endpoint"""
        unique_timestamp = int(time.time())
        test_username = f"newuser_{unique_timestamp}"
        
        payload = {
            "username": test_username,
            "password": "password123",
            "email": f"test_{unique_timestamp}@example.com"
        }
        response = self.make_request(
            'POST', 
            '/auth/register', 
            headers=self.headers, 
            data=payload,
            description=f"Testing user registration for '{test_username}'"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("success", data)
        print(f"{EMOJI_USER} User '{test_username}' successfully registered")
    
    def test_protected_endpoint_with_token(self):
        """Test accessing a protected endpoint with a valid token"""
        response = self.make_request(
            'GET', 
            '/api/metrics', 
            headers=self.auth_headers,
            description="Testing protected endpoint access WITH valid token"
        )
        self.assertEqual(response.status_code, 200)
        print(f"{EMOJI_SECURITY} Protected access successfully granted with valid token")
    
    def test_protected_endpoint_without_token(self):
        """Test accessing a protected endpoint without a token"""
        response = self.make_request(
            'GET', 
            '/api/metrics', 
            headers=self.headers,
            expected_status=401,
            description="Testing protected endpoint access WITHOUT token"
        )
        self.assertEqual(response.status_code, 401)
        print(f"{EMOJI_SECURITY} Protected access correctly denied without token")
    
    def test_query_endpoint(self):
        """Test the query endpoint"""
        payload = {
            "query_type": "full",
            "time_range": {
                "start": int(time.time()) - 86400,  # 1 day ago
                "end": int(time.time())
            },
            "filters": {},
            "limit": 10,
            "offset": 0
        }
        response = self.make_request(
            'POST', 
            '/api/query', 
            headers=self.auth_headers, 
            data=payload,
            description="Testing standard data query functionality"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("results", data)
        print(f"{EMOJI_DB} Query returned {colored(len(data['results']), 'cyan')} results")
    
    def test_secure_query_endpoint(self):
        """Test the secure query endpoint"""
        payload = {
            "query_type": "full",
            "time_range": {
                "start": int(time.time()) - 86400,
                "end": int(time.time())
            },
            "query_filters": {},
            "fields_to_redact": getattr(config, "REDACT_FIELDS", ["pii", "sensitive"]),
            "numeric_fields": ["count", "value"],
            "epsilon": getattr(config, "DEFAULT_EPSILON", 0.1),
            "sensitivity": getattr(config, "DEFAULT_SENSITIVITY", 1.0)
        }
        response = self.make_request(
            'POST', 
            '/api/secure-query', 
            headers=self.auth_headers, 
            data=payload,
            description="Testing privacy-enhanced secure query"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("results", data)
        print(f"{EMOJI_PRIVACY} Secure query returned privacy-protected data")
    
    def test_privacy_health_endpoint(self):
        """Test the privacy services health endpoint"""
        response = self.make_request(
            'GET', 
            '/api/privacy-services/health',
            description="Checking privacy services health"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        print(f"{EMOJI_PRIVACY} Privacy services status: {colored(data['status'], 'green')}")
    
    def test_user_info_endpoint(self):
        """Test getting user info with valid token"""
        response = self.make_request(
            'GET', 
            f'/api/users/{self.test_username}', 
            headers=self.auth_headers,
            description=f"Retrieving user profile for '{self.test_username}'"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["username"], self.test_username)
        print(f"{EMOJI_USER} Successfully retrieved user profile")
    
    def test_metrics_endpoint(self):
        """Test the metrics endpoint"""
        response = self.make_request(
            'GET', 
            '/api/metrics', 
            headers=self.auth_headers,
            description="Retrieving system metrics"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("metrics", data)
        print(f"{EMOJI_TIME} Successfully retrieved {colored(len(data['metrics']), 'cyan')} metrics")

if __name__ == "__main__":
    print(f"\n{EMOJI_ROCKET} {colored('Launching API Integration Tests', 'magenta', attrs=['bold'])}")
    unittest.main(verbosity=0)