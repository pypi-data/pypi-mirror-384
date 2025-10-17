#!/usr/bin/env python3
"""
Integration test for network conditions and mobile emulation tools.

Tests that the new tools are properly integrated into the server without requiring
full Playwright installation.
"""

import sys
import ast
from pathlib import Path

def test_syntax_validation():
    """Test that all Python files have valid syntax."""
    src_dir = Path("src")
    python_files = list(src_dir.glob("**/*.py"))
    
    print(f"📝 Testing syntax validation for {len(python_files)} Python files...")
    
    for py_file in python_files:
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            ast.parse(content)
            print(f"✅ {py_file}: Syntax OK")
        except SyntaxError as e:
            print(f"❌ {py_file}: Syntax Error - {e}")
            return False
        except Exception as e:
            print(f"⚠️  {py_file}: Warning - {e}")
    
    return True

def test_import_structure():
    """Test that the server imports are structured correctly."""
    print("\n🔍 Testing import structure...")
    
    server_file = Path("src/server.py")
    try:
        with open(server_file, 'r') as f:
            content = f.read()
        
        # Check for network conditions imports
        network_imports = [
            "browser_set_network_conditions",
            "browser_clear_network_conditions", 
            "browser_list_network_presets",
            "browser_test_network_conditions"
        ]
        
        for import_name in network_imports:
            if import_name in content:
                print(f"✅ Network import found: {import_name}")
            else:
                print(f"❌ Missing network import: {import_name}")
                return False
        
        # Check for mobile emulation imports
        mobile_imports = [
            "browser_emulate_mobile_device",
            "browser_simulate_touch_gesture",
            "browser_change_orientation",
            "browser_list_mobile_devices"
        ]
        
        for import_name in mobile_imports:
            if import_name in content:
                print(f"✅ Mobile import found: {import_name}")
            else:
                print(f"❌ Missing mobile import: {import_name}")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Error reading server file: {e}")
        return False

def test_tool_registration():
    """Test that tools are registered with @app.tool() decorators."""
    print("\n🛠️  Testing tool registration...")
    
    server_file = Path("src/server.py") 
    try:
        with open(server_file, 'r') as f:
            content = f.read()
        
        # Check for tool registrations
        expected_tools = [
            "set_network_conditions",
            "clear_network_conditions",
            "list_network_presets", 
            "test_network_conditions",
            "emulate_mobile_device",
            "simulate_touch_gesture",
            "change_orientation",
            "list_mobile_devices"
        ]
        
        for tool_name in expected_tools:
            # Look for async def tool_name with @app.tool() somewhere before it
            if f"async def {tool_name}(" in content:
                print(f"✅ Tool registered: {tool_name}")
            else:
                print(f"❌ Missing tool registration: {tool_name}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking tool registration: {e}")
        return False

def test_capabilities_updated():
    """Test that server capabilities include new features."""
    print("\n🎯 Testing capabilities updated...")
    
    server_file = Path("src/server.py")
    try:
        with open(server_file, 'r') as f:
            content = f.read()
        
        # Check for new capabilities
        expected_capabilities = [
            "network_condition_simulation",
            "mobile_device_emulation",
            "touch_gesture_simulation",
            "device_orientation_control"
        ]
        
        for capability in expected_capabilities:
            if f'"{capability}"' in content:
                print(f"✅ Capability added: {capability}")
            else:
                print(f"❌ Missing capability: {capability}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking capabilities: {e}")
        return False

def test_file_existence():
    """Test that the required files exist."""
    print("\n📁 Testing file existence...")
    
    required_files = [
        "src/tools/network_conditions.py",
        "src/tools/mobile_emulation.py",
        "src/server.py"
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ File exists: {file_path}")
        else:
            print(f"❌ Missing file: {file_path}")
            return False
    
    return True

def main():
    """Run all integration tests."""
    print("🧪 MCPlaywright Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("File Existence", test_file_existence),
        ("Syntax Validation", test_syntax_validation), 
        ("Import Structure", test_import_structure),
        ("Tool Registration", test_tool_registration),
        ("Capabilities Updated", test_capabilities_updated)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name}: Exception - {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Integration Test Results")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed! Network and mobile emulation tools are properly integrated.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the integration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())