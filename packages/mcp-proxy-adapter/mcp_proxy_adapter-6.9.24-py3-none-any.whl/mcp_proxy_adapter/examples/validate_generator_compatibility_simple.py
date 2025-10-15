#!/usr/bin/env python3
"""
Simple compatibility test between config generator and validator.
Tests only the structure and required fields, not file existence or certificate validity.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp_proxy_adapter.core.config_validator import ConfigValidator
from mcp_proxy_adapter.examples.config_builder import generate_complete_config


def test_generator_validator_structure():
    """Test that generated configs have the correct structure."""
    print("🔍 Testing Generator-Validator Structure Compatibility")
    print("=" * 60)
    
    # Test basic HTTP configuration
    print("\n📋 Testing: HTTP Basic Configuration")
    print("-" * 40)
    
    try:
        # Generate configuration
        print("  🔧 Generating configuration...")
        config = generate_complete_config(host="localhost", port=8080)
        
        # Check required sections exist
        required_sections = ["server", "logging", "commands", "debug", "ssl", "security", "roles", "proxy_registration"]
        missing_sections = []
        
        for section in required_sections:
            if section not in config:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"  ❌ FAIL - Missing sections: {missing_sections}")
            return False
        
        # Check server section
        server_required = ["host", "port", "protocol", "debug", "log_level"]
        server_missing = [key for key in server_required if key not in config["server"]]
        
        if server_missing:
            print(f"  ❌ FAIL - Server section missing keys: {server_missing}")
            return False
        
        # Check protocol is HTTP
        if config["server"]["protocol"] != "http":
            print(f"  ❌ FAIL - Expected protocol 'http', got '{config['server']['protocol']}'")
            return False
        
        # Check SSL is disabled
        if config["ssl"]["enabled"] != False:
            print(f"  ❌ FAIL - Expected SSL disabled, got {config['ssl']['enabled']}")
            return False
        
        # Check security is disabled
        if config["security"]["enabled"] != False:
            print(f"  ❌ FAIL - Expected security disabled, got {config['security']['enabled']}")
            return False
        
        # Check roles is disabled
        if config["roles"]["enabled"] != False:
            print(f"  ❌ FAIL - Expected roles disabled, got {config['roles']['enabled']}")
            return False
        
        # Check proxy registration is disabled
        if config["proxy_registration"]["enabled"] != False:
            print(f"  ❌ FAIL - Expected proxy registration disabled, got {config['proxy_registration']['enabled']}")
            return False
        
        print("  ✅ PASS - All required sections and fields present")
        print("  ✅ PASS - All features correctly disabled")
        print("  ✅ PASS - Protocol correctly set to HTTP")
        
        return True
        
    except Exception as e:
        print(f"  💥 EXCEPTION: {str(e)}")
        return False


def test_config_modification():
    """Test that we can modify generated configs for different scenarios."""
    print("\n📋 Testing: Configuration Modification")
    print("-" * 40)
    
    try:
        # Generate base config
        config = generate_complete_config(host="localhost", port=8080)
        
        # Test 1: Enable HTTPS
        print("  🔧 Testing HTTPS modification...")
        config["server"]["protocol"] = "https"
        config["ssl"]["enabled"] = True
        
        if config["server"]["protocol"] != "https":
            print("  ❌ FAIL - Could not change protocol to HTTPS")
            return False
        
        if config["ssl"]["enabled"] != True:
            print("  ❌ FAIL - Could not enable SSL")
            return False
        
        print("  ✅ PASS - HTTPS modification successful")
        
        # Test 2: Enable security
        print("  🔧 Testing security modification...")
        config["security"]["enabled"] = True
        config["security"]["tokens"] = {"test_token": {"permissions": ["*"]}}
        
        if config["security"]["enabled"] != True:
            print("  ❌ FAIL - Could not enable security")
            return False
        
        if "tokens" not in config["security"]:
            print("  ❌ FAIL - Could not add tokens")
            return False
        
        print("  ✅ PASS - Security modification successful")
        
        # Test 3: Enable roles
        print("  🔧 Testing roles modification...")
        config["roles"]["enabled"] = True
        config["roles"]["config_file"] = "./test_roles.json"
        
        if config["roles"]["enabled"] != True:
            print("  ❌ FAIL - Could not enable roles")
            return False
        
        if config["roles"]["config_file"] != "./test_roles.json":
            print("  ❌ FAIL - Could not set roles config file")
            return False
        
        print("  ✅ PASS - Roles modification successful")
        
        return True
        
    except Exception as e:
        print(f"  💥 EXCEPTION: {str(e)}")
        return False


def test_validator_accepts_generated_config():
    """Test that validator accepts the basic generated config without file checks."""
    print("\n📋 Testing: Validator Accepts Generated Config")
    print("-" * 40)
    
    try:
        # Generate config
        config = generate_complete_config(host="localhost", port=8080)
        
        # Create a mock validator that doesn't check files
        class MockValidator(ConfigValidator):
            def _validate_file_existence(self):
                """Skip file existence checks for testing."""
                pass
            
            def _validate_certificate_file(self, cert_file, section, key):
                """Skip certificate validation for testing."""
                pass
            
            def _validate_key_file(self, key_file, section, key):
                """Skip key validation for testing."""
                pass
            
            def _validate_ca_certificate_file(self, ca_cert_file, section, key):
                """Skip CA certificate validation for testing."""
                pass
        
        # Validate with mock validator
        validator = MockValidator()
        validator.config_data = config
        results = validator.validate_config()
        
        errors = [r for r in results if r.level == "error"]
        warnings = [r for r in results if r.level == "warning"]
        
        if len(errors) > 0:
            print(f"  ❌ FAIL - {len(errors)} validation errors:")
            for error in errors[:3]:
                print(f"    • {error.message}")
            return False
        
        print(f"  ✅ PASS - No validation errors ({len(warnings)} warnings)")
        return True
        
    except Exception as e:
        print(f"  💥 EXCEPTION: {str(e)}")
        return False


def main():
    """Main test function."""
    print("🚀 Generator-Validator Structure Compatibility Test")
    print("=" * 70)
    
    tests = [
        ("Structure Test", test_generator_validator_structure),
        ("Modification Test", test_config_modification),
        ("Validator Acceptance Test", test_validator_accepts_generated_config)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  💥 Test failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("🎯 FINAL RESULTS")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Generator and validator are structurally compatible.")
        return 0
    else:
        print(f"\n❌ {total - passed} tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
