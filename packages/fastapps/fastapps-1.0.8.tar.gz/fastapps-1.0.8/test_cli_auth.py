"""
Test script for CLI auth features.
Tests the generate_tool_code function and CLI logic.
"""

import sys
from pathlib import Path

# Add FastApps to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("FastApps CLI Auth Features - Test Suite")
print("=" * 70)

# Test 1: Import CLI functions
print("\n[TEST 1] Testing CLI imports...")
try:
    from fastapps.cli.commands.create import generate_tool_code
    print("✓ generate_tool_code imported")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Generate code with --auth
print("\n[TEST 2] Testing --auth flag...")
try:
    code = generate_tool_code(
        class_name="TestWidget",
        identifier="test-widget",
        title="Test Widget",
        auth_type="required",
        scopes=["user", "read:data"]
    )
    
    # Verify code includes correct elements
    assert "from fastapps import BaseWidget, ConfigDict, auth_required, UserContext" in code, "Should import auth_required and UserContext"
    assert '@auth_required(scopes=["user", "read:data"])' in code, "Should have decorator with scopes"
    assert 'description = "Requires authentication (user, read:data)"' in code, "Should have description"
    assert "if user and user.is_authenticated:" in code, "Should check authentication"
    assert "user.claims" in code, "Should access user claims"
    assert "user.subject" in code, "Should access user subject"
    assert "user.scopes" in code, "Should access user scopes"
    
    print("✓ Generated code with @auth_required")
    print("  - Correct imports")
    print("  - Decorator with scopes")
    print("  - User context handling")
    
except Exception as e:
    print(f"✗ --auth test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Generate code with --public
print("\n[TEST 3] Testing --public flag...")
try:
    code = generate_tool_code(
        class_name="PublicWidget",
        identifier="public-widget",
        title="Public Widget",
        auth_type="none",
        scopes=None
    )
    
    assert "from fastapps import BaseWidget, ConfigDict, no_auth" in code, "Should import no_auth"
    assert "UserContext" not in code, "Should not import UserContext for public widgets"
    assert "@no_auth" in code, "Should have @no_auth decorator"
    assert 'description = "Public widget - no authentication required"' in code, "Should have public description"
    assert "if user and user.is_authenticated:" not in code, "Should not check auth for simple public widgets"
    
    print("✓ Generated code with @no_auth")
    print("  - Correct imports (no UserContext)")
    print("  - @no_auth decorator")
    print("  - Simple execute body")
    
except Exception as e:
    print(f"✗ --public test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Generate code with --optional-auth
print("\n[TEST 4] Testing --optional-auth flag...")
try:
    code = generate_tool_code(
        class_name="FlexibleWidget",
        identifier="flexible-widget",
        title="Flexible Widget",
        auth_type="optional",
        scopes=["user"]
    )
    
    assert "from fastapps import BaseWidget, ConfigDict, optional_auth, UserContext" in code, "Should import optional_auth and UserContext"
    assert '@optional_auth(scopes=["user"])' in code, "Should have decorator with scopes"
    assert 'description = "Supports both authenticated and anonymous access"' in code, "Should have optional description"
    assert "if user and user.is_authenticated:" in code, "Should check authentication"
    
    print("✓ Generated code with @optional_auth")
    print("  - Correct imports")
    print("  - Decorator with scopes")
    print("  - Conditional auth handling")
    
except Exception as e:
    print(f"✗ --optional-auth test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Generate code without auth (default)
print("\n[TEST 5] Testing default (no auth flags)...")
try:
    code = generate_tool_code(
        class_name="BasicWidget",
        identifier="basic-widget",
        title="Basic Widget",
        auth_type=None,
        scopes=None
    )
    
    assert "# from fastapps import auth_required, no_auth, optional_auth, UserContext" in code, "Should have commented auth imports"
    assert "# @auth_required(scopes=[" in code, "Should have commented decorator examples"
    assert "# @no_auth" in code, "Should have @no_auth example"
    assert "# @optional_auth(scopes=[" in code, "Should have @optional_auth example"
    assert "# if user and user.is_authenticated:" in code, "Should have commented user handling"
    
    print("✓ Generated code without auth flags")
    print("  - Commented import examples")
    print("  - Commented decorator examples")
    print("  - Commented user handling examples")
    
except Exception as e:
    print(f"✗ Default test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Scopes formatting
print("\n[TEST 6] Testing scopes formatting...")
try:
    # Test with multiple scopes
    code1 = generate_tool_code("Test", "test", "Test", "required", ["user", "read:data", "write:data"])
    assert '@auth_required(scopes=["user", "read:data", "write:data"])' in code1, "Should format multiple scopes"
    print("✓ Multiple scopes formatted correctly")
    
    # Test with single scope
    code2 = generate_tool_code("Test", "test", "Test", "required", ["admin"])
    assert '@auth_required(scopes=["admin"])' in code2, "Should format single scope"
    print("✓ Single scope formatted correctly")
    
    # Test with no scopes
    code3 = generate_tool_code("Test", "test", "Test", "required", None)
    assert '@auth_required(scopes=[])' in code3, "Should have empty scopes array"
    print("✓ No scopes formatted correctly")
    
except Exception as e:
    print(f"✗ Scopes formatting test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 7: Verify code structure for all types
print("\n[TEST 7] Verifying code structure...")
try:
    for auth_type, decorator_name in [
        ("required", "@auth_required"),
        ("none", "@no_auth"),
        ("optional", "@optional_auth"),
    ]:
        code = generate_tool_code("Test", "test", "Test", auth_type, ["user"])
        
        # All should have these basic elements
        assert "class TestInput(BaseModel):" in code, f"{auth_type}: Should have Input class"
        assert "class TestTool(BaseWidget):" in code, f"{auth_type}: Should have Tool class"
        assert 'identifier = "test"' in code, f"{auth_type}: Should have identifier"
        assert 'title = "Test"' in code, f"{auth_type}: Should have title"
        assert "async def execute" in code, f"{auth_type}: Should have execute method"
        assert "widget_csp" in code, f"{auth_type}: Should have CSP config"
        
        print(f"✓ {auth_type}: All required elements present")
    
except Exception as e:
    print(f"✗ Structure test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 8: Check execute signature
print("\n[TEST 8] Testing execute signature...")
try:
    code = generate_tool_code("Test", "test", "Test", "required", ["user"])
    
    # Should have all three parameters
    assert "async def execute(self, input_data: TestInput, context=None, user=None)" in code, \
        "Should have correct execute signature with user parameter"
    
    print("✓ Execute signature includes user parameter")
    
except Exception as e:
    print(f"✗ Execute signature test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Final summary
print("\n" + "=" * 70)
print("Test Summary")
print("=" * 70)
print("""
✓ generate_tool_code function works
✓ --auth flag generates correct code
✓ --public flag generates correct code
✓ --optional-auth flag generates correct code
✓ Default (no flags) includes commented examples
✓ Scopes formatted correctly
✓ All code structures valid
✓ Execute signature includes user parameter

All CLI tests PASSED! ✓

CLI Commands Ready:
  fastapps create name --auth --scopes s1,s2
  fastapps create name --public
  fastapps create name --optional-auth --scopes s1
  fastapps auth-info

Documentation:
  - CLI_COMMANDS_UPDATED.md - Complete reference
  - CLI_EXAMPLES.md - Usage examples
  - CLI_UPDATE_SUMMARY.md - Update summary
""")
print("=" * 70)

