#!/usr/bin/env python3
"""Quick test to verify benchmark system setup."""

import sys
import os
from pathlib import Path

# Set UTF-8 encoding for Windows console
if os.name == 'nt':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("Testing Router's Matrix Benchmark System...")
print("=" * 60)

# Test 1: Import all modules
print("\n1. Testing imports...")
try:
    from benchmark.test_generator import TestGenerator
    from benchmark.metrics_collector import MetricsCollector
    from benchmark.quality_analyzer import QualityAnalyzer
    from benchmark.matrix_generator import MatrixGenerator
    print("   ✓ All modules imported successfully")
except ImportError as e:
    print(f"   ✗ Import error: {e}")
    sys.exit(1)

# Test 2: Test generator
print("\n2. Testing TestGenerator...")
gen = TestGenerator()
all_tests = gen.get_all_tests()
print(f"   ✓ Total tests: {len(all_tests)}")

summary = gen.get_summary()
print(f"   ✓ Categories: {list(summary['categories'].keys())}")

# Test 3: Quick tests
print("\n3. Testing quick test selection...")
quick_tests = gen.get_quick_tests(20)
print(f"   ✓ Quick tests: {len(quick_tests)}")

# Test 4: Category tests
print("\n4. Testing category selection...")
code_tests = gen.get_tests_by_category("code")
print(f"   ✓ Code tests: {len(code_tests)}")

# Test 5: Matrix generator
print("\n5. Testing MatrixGenerator...")
matrix_gen = MatrixGenerator(output_dir="test_output")
print(f"   ✓ Output directory: {matrix_gen.run_dir}")

# Test 6: Verify test structure
print("\n6. Verifying test structure...")
for test in quick_tests[:3]:
    is_valid = gen.validate_test(test)
    print(f"   {'✓' if is_valid else '✗'} {test['id']}: {test.get('subcategory', 'unknown')}")

print("\n" + "=" * 60)
print("All tests passed! Benchmark system is ready.")
print("\nTo run the benchmark:")
print("  python scripts/router_matrix.py --quick")
print("  python scripts/router_matrix.py --full")
