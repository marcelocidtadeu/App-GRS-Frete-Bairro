#!/usr/bin/env python3
"""
Backend API Testing for Excel Processing Application
Tests Intelipost configuration, CEP processing, and history endpoints
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class ExcelProcessorAPITester:
    def __init__(self, base_url="https://logistics-assist-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test_name": name,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    Details: {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")
        print()

    def test_api_health(self) -> bool:
        """Test if API is accessible"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            success = response.status_code in [200, 404]  # 404 is OK for root endpoint
            self.log_test(
                "API Health Check", 
                success, 
                f"Status: {response.status_code}",
                {"status_code": response.status_code}
            )
            return success
        except Exception as e:
            self.log_test("API Health Check", False, f"Connection error: {str(e)}")
            return False

    def test_get_intelipost_config_empty(self) -> bool:
        """Test getting Intelipost config when none exists"""
        try:
            response = requests.get(f"{self.api_base}/config/intelipost", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                # Should return configured: false when no config exists
                expected_structure = "configured" in data
                success = success and expected_structure
                
            self.log_test(
                "Get Intelipost Config (Empty)", 
                success, 
                f"Status: {response.status_code}, Has 'configured' field: {expected_structure if success else 'N/A'}",
                response.json() if success else response.text
            )
            return success
        except Exception as e:
            self.log_test("Get Intelipost Config (Empty)", False, f"Error: {str(e)}")
            return False

    def test_save_intelipost_config(self) -> bool:
        """Test saving Intelipost configuration"""
        try:
            config_data = {
                "api_key_intelipost": "test_api_key_12345",
                "sobrepreco_padrao": 135.0
            }
            
            response = requests.post(
                f"{self.api_base}/config/intelipost", 
                json=config_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_message = "message" in data
                has_id = "id" in data
                success = success and has_message and has_id
                
            self.log_test(
                "Save Intelipost Config", 
                success, 
                f"Status: {response.status_code}, Has message: {has_message if success else 'N/A'}, Has ID: {has_id if success else 'N/A'}",
                response.json() if success else response.text
            )
            return success
        except Exception as e:
            self.log_test("Save Intelipost Config", False, f"Error: {str(e)}")
            return False

    def test_get_intelipost_config_saved(self) -> bool:
        """Test getting Intelipost config after saving"""
        try:
            response = requests.get(f"{self.api_base}/config/intelipost", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                is_configured = data.get("configured", False)
                has_masked_key = "api_key_masked" in data
                has_sobrepreco = "sobrepreco_padrao" in data
                
                success = success and is_configured and has_masked_key and has_sobrepreco
                
            self.log_test(
                "Get Intelipost Config (Saved)", 
                success, 
                f"Status: {response.status_code}, Configured: {is_configured if success else 'N/A'}, Has masked key: {has_masked_key if success else 'N/A'}",
                response.json() if success else response.text
            )
            return success
        except Exception as e:
            self.log_test("Get Intelipost Config (Saved)", False, f"Error: {str(e)}")
            return False

    def test_get_history_empty(self) -> bool:
        """Test getting processing history"""
        try:
            response = requests.get(f"{self.api_base}/history", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_history_field = "history" in data
                history_is_list = isinstance(data.get("history"), list)
                
                success = success and has_history_field and history_is_list
                
            self.log_test(
                "Get Processing History", 
                success, 
                f"Status: {response.status_code}, Has history field: {has_history_field if success else 'N/A'}, History is list: {history_is_list if success else 'N/A'}",
                {"history_count": len(data.get("history", [])) if success else 0}
            )
            return success
        except Exception as e:
            self.log_test("Get Processing History", False, f"Error: {str(e)}")
            return False

    def test_cotacao_process_no_file(self) -> bool:
        """Test cotacao processing endpoint without file (should fail)"""
        try:
            response = requests.post(f"{self.api_base}/cotacao/process", timeout=10)
            # Should return 422 (validation error) for missing file
            success = response.status_code == 422
            
            self.log_test(
                "Cotacao Process (No File)", 
                success, 
                f"Status: {response.status_code} (Expected 422 for missing file)",
                {"status_code": response.status_code}
            )
            return success
        except Exception as e:
            self.log_test("Cotacao Process (No File)", False, f"Error: {str(e)}")
            return False

    def test_cep_process_no_file(self) -> bool:
        """Test CEP processing endpoint without file (should fail)"""
        try:
            response = requests.post(f"{self.api_base}/cep/process", timeout=10)
            # Should return 422 (validation error) for missing file
            success = response.status_code == 422
            
            self.log_test(
                "CEP Process (No File)", 
                success, 
                f"Status: {response.status_code} (Expected 422 for missing file)",
                {"status_code": response.status_code}
            )
            return success
        except Exception as e:
            self.log_test("CEP Process (No File)", False, f"Error: {str(e)}")
            return False

    def test_invalid_endpoints(self) -> bool:
        """Test invalid endpoints return 404"""
        try:
            response = requests.get(f"{self.api_base}/invalid/endpoint", timeout=10)
            success = response.status_code == 404
            
            self.log_test(
                "Invalid Endpoint (404)", 
                success, 
                f"Status: {response.status_code} (Expected 404)",
                {"status_code": response.status_code}
            )
            return success
        except Exception as e:
            self.log_test("Invalid Endpoint (404)", False, f"Error: {str(e)}")
            return False

    def test_cors_headers(self) -> bool:
        """Test CORS headers are present"""
        try:
            response = requests.options(f"{self.api_base}/config/intelipost", timeout=10)
            success = response.status_code in [200, 204]
            
            # Check for CORS headers
            has_cors = "access-control-allow-origin" in response.headers
            
            self.log_test(
                "CORS Headers", 
                success and has_cors, 
                f"Status: {response.status_code}, Has CORS: {has_cors}",
                {"cors_origin": response.headers.get("access-control-allow-origin", "Not found")}
            )
            return success and has_cors
        except Exception as e:
            self.log_test("CORS Headers", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all backend tests"""
        print("🚀 Starting Backend API Tests for Excel Processor Application")
        print("=" * 60)
        
        # Test sequence
        tests = [
            self.test_api_health,
            self.test_get_intelipost_config_empty,
            self.test_save_intelipost_config,
            self.test_get_intelipost_config_saved,
            self.test_get_history_empty,
            self.test_cotacao_process_no_file,
            self.test_cep_process_no_file,
            self.test_invalid_endpoints,
            self.test_cors_headers
        ]
        
        for test in tests:
            test()
        
        # Summary
        print("=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
        else:
            print("⚠️  Some tests failed. Check details above.")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": success_rate,
            "test_results": self.test_results
        }

def main():
    """Main test execution"""
    tester = ExcelProcessorAPITester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if results["passed_tests"] == results["total_tests"] else 1

if __name__ == "__main__":
    sys.exit(main())