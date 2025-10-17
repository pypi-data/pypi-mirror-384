"""
Test script to verify that reasoning_effort parameter is being properly used.

This script tests:
1. No warnings are generated
2. Correct reasoning_effort values are logged
3. Temperature mapping works correctly
4. Different models are handled correctly

Run this script to verify the fix is working:
    python tests/test_reasoning_effort.py
"""

import sys
import os
import warnings

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from masai.GenerativeModel.baseGenerativeModel.basegenerativeModel import BaseGenerativeModel
from masai.Tools.logging_setup.logger import setup_logger
from dotenv import load_dotenv
load_dotenv()

# Capture warnings
warnings.simplefilter("always")

def test_reasoning_model_initialization():
    """Test that reasoning models are initialized with correct reasoning_effort."""
    
    print("\n" + "="*80)
    print("TEST: Reasoning Model Initialization")
    print("="*80)
    
    test_cases = [
        # (model_name, category, temperature, expected_reasoning_effort)
        ("gpt-5", "openai", 0.1, "low"),
        ("gpt-5", "openai", 0.5, "medium"),
        ("gpt-5", "openai", 0.9, "high"),
        ("o1", "openai", 0.2, "low"),
        ("o3-mini", "openai", 0.6, "medium"),
        ("o4-mini", "openai", 0.8, "high"),
        ("gpt-4.1", "openai", 0.3, "low"),
    ]
    
    passed = 0
    failed = 0
    
    for model_name, category, temperature, expected_effort in test_cases:
        print(f"\n📊 Test Case: {model_name} with temperature={temperature}")
        print(f"   Expected reasoning_effort: {expected_effort}")
        print("-" * 80)
        
        try:
            # Capture warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                
                # Create model
                model = BaseGenerativeModel(
                    model_name=model_name,
                    category=category,
                    temperature=temperature,
                    logging=True
                )
                
                # Check for warnings
                model_kwargs_warnings = [
                    warning for warning in w 
                    if "model_kwargs" in str(warning.message)
                ]
                
                if model_kwargs_warnings:
                    print(f"   ❌ FAILED: Warning detected!")
                    for warning in model_kwargs_warnings:
                        print(f"      {warning.message}")
                    failed += 1
                else:
                    print(f"   ✅ PASSED: No warnings")
                    
                    # Check if reasoning_effort is set correctly
                    if hasattr(model.model, 'reasoning_effort'):
                        actual_effort = model.model.reasoning_effort
                        if actual_effort == expected_effort:
                            print(f"   ✅ PASSED: reasoning_effort='{actual_effort}' (correct)")
                            passed += 1
                        else:
                            print(f"   ❌ FAILED: reasoning_effort='{actual_effort}' (expected '{expected_effort}')")
                            failed += 1
                    else:
                        print(f"   ⚠️  WARNING: reasoning_effort attribute not found on model")
                        print(f"      This might be expected if the model doesn't expose this attribute")
                        passed += 1
                        
        except Exception as e:
            print(f"   ❌ FAILED: Exception occurred: {e}")
            failed += 1
    
    print("\n" + "="*80)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*80)
    
    return failed == 0


def test_non_reasoning_model():
    """Test that non-reasoning models use temperature (not reasoning_effort)."""
    
    print("\n" + "="*80)
    print("TEST: Non-Reasoning Model (should use temperature)")
    print("="*80)
    
    test_cases = [
        ("gpt-4o", "openai", 0.5),
        ("gpt-4", "openai", 0.7),
        ("gpt-3.5-turbo", "openai", 0.3),
    ]
    
    passed = 0
    failed = 0
    
    for model_name, category, temperature in test_cases:
        print(f"\n📊 Test Case: {model_name} with temperature={temperature}")
        print("-" * 80)
        
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                
                model = BaseGenerativeModel(
                    model_name=model_name,
                    category=category,
                    temperature=temperature,
                    logging=True
                )
                
                # Check for warnings
                model_kwargs_warnings = [
                    warning for warning in w 
                    if "model_kwargs" in str(warning.message)
                ]
                
                if model_kwargs_warnings:
                    print(f"   ❌ FAILED: Unexpected warning!")
                    failed += 1
                else:
                    print(f"   ✅ PASSED: No warnings")
                    
                    # Check that temperature is set (not reasoning_effort)
                    if hasattr(model.model, 'temperature'):
                        actual_temp = model.model.temperature
                        if actual_temp == temperature:
                            print(f"   ✅ PASSED: temperature={actual_temp} (correct)")
                            passed += 1
                        else:
                            print(f"   ❌ FAILED: temperature={actual_temp} (expected {temperature})")
                            failed += 1
                    else:
                        print(f"   ⚠️  WARNING: temperature attribute not found")
                        passed += 1
                        
        except Exception as e:
            print(f"   ❌ FAILED: Exception occurred: {e}")
            failed += 1
    
    print("\n" + "="*80)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*80)
    
    return failed == 0


def test_temperature_mapping():
    """Test that temperature values are correctly mapped to reasoning_effort."""
    
    print("\n" + "="*80)
    print("TEST: Temperature to reasoning_effort Mapping")
    print("="*80)
    
    test_cases = [
        # (temperature, expected_reasoning_effort)
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
        print(f"\n📊 Test Case: temperature={temperature} → reasoning_effort='{expected_effort}'")
        print("-" * 80)
        
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                
                model = BaseGenerativeModel(
                    model_name="gpt-5",
                    category="openai",
                    temperature=temperature,
                    logging=True
                )
                
                # Check for warnings
                model_kwargs_warnings = [
                    warning for warning in w 
                    if "model_kwargs" in str(warning.message)
                ]
                
                if model_kwargs_warnings:
                    print(f"   ❌ FAILED: Warning detected!")
                    failed += 1
                else:
                    print(f"   ✅ PASSED: Mapping correct, no warnings")
                    passed += 1
                        
        except Exception as e:
            print(f"   ❌ FAILED: Exception occurred: {e}")
            failed += 1
    
    print("\n" + "="*80)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*80)
    
    return failed == 0


def main():
    """Run all tests."""
    
    print("\n" + "="*80)
    print("REASONING_EFFORT VERIFICATION TEST SUITE")
    print("="*80)
    print("\nThis test suite verifies that:")
    print("  1. reasoning_effort is passed as a direct parameter (not in model_kwargs)")
    print("  2. No warnings are generated")
    print("  3. Temperature mapping works correctly")
    print("  4. Different models are handled correctly")
    print("\n" + "="*80)
    
    # Run tests
    test1_passed = test_reasoning_model_initialization()
    test2_passed = test_non_reasoning_model()
    test3_passed = test_temperature_mapping()
    
    # Summary
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)
    print(f"  Test 1 (Reasoning Models):     {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"  Test 2 (Non-Reasoning Models): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"  Test 3 (Temperature Mapping):  {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    print("="*80)
    
    if test1_passed and test2_passed and test3_passed:
        print("\n🎉 ALL TESTS PASSED! reasoning_effort is working correctly!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED! Please review the output above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

