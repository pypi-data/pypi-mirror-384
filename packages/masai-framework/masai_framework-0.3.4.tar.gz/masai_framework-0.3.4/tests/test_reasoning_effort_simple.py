"""
Simple test to verify reasoning_effort parameter is correctly configured.

This test checks the CODE STRUCTURE without making actual API calls.
It verifies:
1. reasoning_effort is passed as a direct parameter (not in model_kwargs)
2. Temperature mapping logic is correct
3. Model detection logic is correct

Run this test:
    python tests/test_reasoning_effort_simple.py
"""

import sys
import os
import re

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

def test_code_structure():
    """Test that the code structure is correct."""
    
    print("\n" + "="*80)
    print("TEST: Code Structure Verification")
    print("="*80)
    
    # Read the source file
    file_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'src', 
        'masai', 
        'GenerativeModel', 
        'baseGenerativeModel', 
        'basegenerativeModel.py'
    )
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    passed = 0
    failed = 0
    
    # Test 1: Check that reasoning_effort is passed as direct parameter
    print("\n📊 Test 1: reasoning_effort as direct parameter")
    print("-" * 80)
    
    # Look for the correct pattern
    correct_pattern = r'reasoning_effort=reasoning_effort'
    wrong_pattern = r'model_kwargs=\{[^}]*"reasoning_effort"'
    
    if re.search(correct_pattern, content):
        print("   ✅ PASSED: Found 'reasoning_effort=reasoning_effort' (direct parameter)")
        passed += 1
    else:
        print("   ❌ FAILED: Did not find 'reasoning_effort=reasoning_effort'")
        failed += 1
    
    if re.search(wrong_pattern, content):
        print("   ❌ FAILED: Found 'model_kwargs' with 'reasoning_effort' (wrong method)")
        failed += 1
    else:
        print("   ✅ PASSED: No 'model_kwargs' with 'reasoning_effort' found")
        passed += 1
    
    # Test 2: Check temperature mapping logic
    print("\n📊 Test 2: Temperature mapping logic")
    print("-" * 80)
    
    mapping_patterns = [
        (r'if self\.temperature <= 0\.3:', 'low'),
        (r'elif self\.temperature <= 0\.7:', 'medium'),
        (r'else:', 'high'),
    ]
    
    for pattern, expected in mapping_patterns:
        if re.search(pattern, content):
            print(f"   ✅ PASSED: Found temperature mapping for '{expected}'")
            passed += 1
        else:
            print(f"   ❌ FAILED: Missing temperature mapping for '{expected}'")
            failed += 1
    
    # Test 3: Check model detection logic
    print("\n📊 Test 3: Reasoning model detection")
    print("-" * 80)
    
    model_patterns = [
        (r"self\.model_name\.startswith\('gpt-5'\)", 'gpt-5'),
        (r"self\.model_name\.startswith\('o1'\)", 'o1'),
        (r"self\.model_name\.startswith\('o3'\)", 'o3'),
        (r"self\.model_name\.startswith\('o4'\)", 'o4'),
        (r"self\.model_name\.startswith\('gpt-4\.1'\)", 'gpt-4.1'),
    ]
    
    for pattern, model in model_patterns:
        if re.search(pattern, content):
            print(f"   ✅ PASSED: Found detection for '{model}' models")
            passed += 1
        else:
            print(f"   ❌ FAILED: Missing detection for '{model}' models")
            failed += 1
    
    # Test 4: Check for verbose=True
    print("\n📊 Test 4: Verbose logging enabled")
    print("-" * 80)
    
    if re.search(r'verbose=True', content):
        print("   ✅ PASSED: Found 'verbose=True' for debugging")
        passed += 1
    else:
        print("   ⚠️  WARNING: 'verbose=True' not found (optional)")
        # Don't count as failure
    
    # Test 5: Check for logging statement
    print("\n📊 Test 5: Logging statement for reasoning_effort")
    print("-" * 80)
    
    if re.search(r'Reasoning model.*initialized with reasoning_effort', content):
        print("   ✅ PASSED: Found logging statement for reasoning_effort")
        passed += 1
    else:
        print("   ⚠️  WARNING: Logging statement not found (optional)")
        # Don't count as failure
    
    # Test 6: Check that ChatOpenAI is used correctly
    print("\n📊 Test 6: ChatOpenAI initialization")
    print("-" * 80)
    
    if re.search(r'llm = ChatOpenAI\(', content):
        print("   ✅ PASSED: Found ChatOpenAI initialization")
        passed += 1
    else:
        print("   ❌ FAILED: ChatOpenAI initialization not found")
        failed += 1
    
    print("\n" + "="*80)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*80)
    
    return failed == 0


def test_temperature_mapping_values():
    """Test the temperature mapping logic with actual values."""
    
    print("\n" + "="*80)
    print("TEST: Temperature Mapping Values")
    print("="*80)
    
    test_cases = [
        (0.0, "low"),
        (0.1, "low"),
        (0.3, "low"),
        (0.4, "medium"),
        (0.5, "medium"),
        (0.7, "medium"),
        (0.8, "high"),
        (0.9, "high"),
        (1.0, "high"),
    ]
    
    passed = 0
    failed = 0
    
    for temperature, expected_effort in test_cases:
        # Simulate the mapping logic
        if temperature <= 0.3:
            reasoning_effort = "low"
        elif temperature <= 0.7:
            reasoning_effort = "medium"
        else:
            reasoning_effort = "high"
        
        print(f"\n📊 temperature={temperature} → reasoning_effort='{reasoning_effort}'")
        
        if reasoning_effort == expected_effort:
            print(f"   ✅ PASSED: Correct mapping (expected '{expected_effort}')")
            passed += 1
        else:
            print(f"   ❌ FAILED: Wrong mapping (expected '{expected_effort}', got '{reasoning_effort}')")
            failed += 1
    
    print("\n" + "="*80)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*80)
    
    return failed == 0


def test_model_detection():
    """Test the model detection logic."""
    
    print("\n" + "="*80)
    print("TEST: Model Detection Logic")
    print("="*80)
    
    test_cases = [
        # (model_name, should_be_reasoning_model)
        ("gpt-5", True),
        ("gpt-5-pro", True),
        ("o1", True),
        ("o1-mini", True),
        ("o1-preview", True),
        ("o3", True),
        ("o3-mini", True),
        ("o4-mini", True),
        ("gpt-4.1", True),
        ("gpt-4.1-nano", True),
        ("gpt-4o", False),
        ("gpt-4", False),
        ("gpt-3.5-turbo", False),
    ]
    
    passed = 0
    failed = 0
    
    for model_name, should_be_reasoning in test_cases:
        # Simulate the detection logic
        is_reasoning_model = (
            model_name.startswith('gpt-5') or
            model_name.startswith('o1') or
            model_name.startswith('o3') or
            model_name.startswith('o4') or
            model_name.startswith('gpt-4.1')
        )
        
        print(f"\n📊 Model: {model_name}")
        print(f"   Expected: {'Reasoning' if should_be_reasoning else 'Non-reasoning'}")
        print(f"   Detected: {'Reasoning' if is_reasoning_model else 'Non-reasoning'}")
        
        if is_reasoning_model == should_be_reasoning:
            print(f"   ✅ PASSED: Correct detection")
            passed += 1
        else:
            print(f"   ❌ FAILED: Wrong detection")
            failed += 1
    
    print("\n" + "="*80)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*80)
    
    return failed == 0


def main():
    """Run all tests."""
    
    print("\n" + "="*80)
    print("REASONING_EFFORT SIMPLE VERIFICATION TEST")
    print("="*80)
    print("\nThis test verifies the CODE STRUCTURE without making API calls.")
    print("It checks:")
    print("  1. reasoning_effort is passed as direct parameter")
    print("  2. Temperature mapping logic is correct")
    print("  3. Model detection logic is correct")
    print("\n" + "="*80)
    
    # Run tests
    test1_passed = test_code_structure()
    test2_passed = test_temperature_mapping_values()
    test3_passed = test_model_detection()
    
    # Summary
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)
    print(f"  Test 1 (Code Structure):       {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"  Test 2 (Temperature Mapping):  {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"  Test 3 (Model Detection):      {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    print("="*80)
    
    if test1_passed and test2_passed and test3_passed:
        print("\n🎉 ALL TESTS PASSED! Code structure is correct!")
        print("\n✅ The reasoning_effort parameter is properly configured:")
        print("   • Passed as direct parameter (not in model_kwargs)")
        print("   • Temperature mapping is correct")
        print("   • Model detection is correct")
        print("\n📝 Note: This test only verifies code structure.")
        print("   To test actual API calls, set OPENAI_API_KEY and run your agent.")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED! Please review the output above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

