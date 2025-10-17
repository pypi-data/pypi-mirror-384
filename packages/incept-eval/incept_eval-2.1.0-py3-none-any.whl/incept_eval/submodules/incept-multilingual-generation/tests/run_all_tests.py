#!/usr/bin/env python3
"""
Run all module tests and analyze results
"""

import sys
import os
import subprocess
import time

def run_test(test_file):
    """Run a single test file and capture output"""
    print(f"\n{'='*80}")
    print(f"RUNNING: {test_file}")
    print(f"{'='*80}")
    
    try:
        start_time = time.time()
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=300)
        end_time = time.time()
        
        duration = end_time - start_time
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return {
            'file': test_file,
            'success': result.returncode == 0,
            'duration': duration,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            'file': test_file,
            'success': False,
            'duration': 300,
            'stdout': '',
            'stderr': 'Test timed out after 300 seconds'
        }
    except Exception as e:
        return {
            'file': test_file,
            'success': False,
            'duration': 0,
            'stdout': '',
            'stderr': str(e)
        }

def analyze_results(results):
    """Analyze test results and provide summary"""
    print(f"\n{'='*80}")
    print("TEST ANALYSIS SUMMARY")
    print(f"{'='*80}")
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    failed_tests = total_tests - successful_tests
    total_time = sum(r['duration'] for r in results)
    
    print(f"📊 OVERALL RESULTS:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Successful: {successful_tests} ✅")
    print(f"   Failed: {failed_tests} ❌")
    print(f"   Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    print(f"   Total Time: {total_time:.2f}s")
    print(f"   Average Time: {total_time/total_tests:.2f}s per test")
    
    print(f"\n📈 INDIVIDUAL TEST PERFORMANCE:")
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        module_name = result['file'].replace('test_module_', 'Module ').replace('.py', '')
        print(f"   {module_name}: {status} ({result['duration']:.2f}s)")
        
        if not result['success']:
            print(f"      Error: {result['stderr']}")
    
    print(f"\n🔍 KEY INSIGHTS:")
    
    # Performance analysis
    fastest = min(results, key=lambda x: x['duration'])
    slowest = max(results, key=lambda x: x['duration'])
    print(f"   Fastest: {fastest['file']} ({fastest['duration']:.2f}s)")
    print(f"   Slowest: {slowest['file']} ({slowest['duration']:.2f}s)")
    
    # Error analysis
    if failed_tests > 0:
        print(f"\n❌ FAILED TESTS ANALYSIS:")
        for result in results:
            if not result['success']:
                print(f"   {result['file']}:")
                print(f"      Error: {result['stderr'][:200]}...")
    
    # Success analysis
    if successful_tests > 0:
        print(f"\n✅ SUCCESSFUL TESTS:")
        for result in results:
            if result['success']:
                # Count occurrences of SUCCESS in output
                success_count = result['stdout'].count('SUCCESS:')
                error_count = result['stdout'].count('ERROR:')
                print(f"   {result['file']}: {success_count} successes, {error_count} errors")

def main():
    """Run all tests and analyze results"""
    
    # Change to the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    test_files = [
        'test_module_1.py',
        'test_module_2.py', 
        'test_module_3.py',
        'test_module_4.py',
        'test_module_5.py'
    ]
    
    print("🚀 STARTING MODULE TESTING SUITE")
    print(f"Found {len(test_files)} test files")
    
    results = []
    for test_file in test_files:
        if os.path.exists(test_file):
            result = run_test(test_file)
            results.append(result)
        else:
            print(f"⚠️  Test file not found: {test_file}")
            results.append({
                'file': test_file,
                'success': False,
                'duration': 0,
                'stdout': '',
                'stderr': 'Test file not found'
            })
    
    analyze_results(results)
    
    print(f"\n{'='*80}")
    print("MODULE TESTING COMPLETE")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()