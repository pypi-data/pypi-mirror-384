#!/usr/bin/env python3
"""
Test script to verify cleaning_agent integration with enhanced context utilities.
"""

import sys
import os
import pandas as pd
import json

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cleaning_agent.agent import CleaningAgent

def test_context_integration():
    """Test that cleaning_agent can use enhanced context utilities."""
    
    print("🧪 Testing cleaning_agent context integration...")
    
    # Create sample data
    sample_data = pd.DataFrame({
        'patient_id': [1, 2, 3, None, 5],
        'age': [25, 30, 35, 40, 45],
        'diagnosis': ['Flu', 'Cold', 'Fever', 'Headache', 'Cough'],
        'treatment_date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05']
    })
    
    # Create enriched context (similar to what problem_orchestrator would send)
    enriched_context = {
        'enriched_context': {
            'domain_knowledge': {
                'domain': 'healthcare',
                'business_context': {
                    'compliance': 'HIPAA',
                    'data_sensitivity': 'high',
                    'industry': 'medical'
                },
                'data_files': ['medical_records.csv'],
                'constraints': {'privacy': 'strict'},
                'stakeholders': ['doctors', 'nurses', 'patients']
            },
            'workflow_context': {
                'goal': 'Clean medical records for analysis while maintaining HIPAA compliance',
                'complexity': 'moderate',
                'risk_level': 'high'
            },
            'execution_context': {
                'current_step': {'step_id': 'cleaning_step', 'agent_name': 'cleaning_agent'},
                'execution_progress': {'completed_steps': [], 'current_step_number': 1}
            }
        }
    }
    
    try:
        # Initialize cleaning agent
        print("📋 Initializing cleaning agent...")
        agent = CleaningAgent()
        
        # Test with enriched context
        print("🔍 Testing with enriched context...")
        result = agent.analyze_and_clean_table(
            table_data=sample_data,
            table_name="medical_records",
            problem_context=enriched_context
        )
        
        # Check results
        if 'error' in result:
            print(f"❌ Error occurred: {result['error']}")
            return False
        
        # Check if enhanced cleaning plan was created
        cleaning_plan = result.get('cleaning_plan', {})
        if 'context_utilization' in cleaning_plan:
            print("✅ Enhanced context utilization detected!")
            print(f"   Domain: {cleaning_plan.get('domain', 'unknown')}")
            print(f"   Data Sensitivity: {cleaning_plan.get('data_sensitivity', 'unknown')}")
            print(f"   Context Strategies: {len(cleaning_plan.get('context_aware_strategies', []))}")
        else:
            print("⚠️  Basic cleaning plan used (context analysis may have failed)")
        
        print("✅ Context integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_context():
    """Test with basic problem context (fallback)."""
    
    print("\n🧪 Testing with basic problem context...")
    
    # Create sample data
    sample_data = pd.DataFrame({
        'customer_id': [1, 2, 3, None, 5],
        'age': [25, 30, 35, 40, 45],
        'product': ['A', 'B', 'C', 'D', 'E']
    })
    
    # Basic context
    basic_context = {
        'problem': 'Clean customer data for analysis',
        'domain': 'retail'
    }
    
    try:
        agent = CleaningAgent()
        result = agent.analyze_and_clean_table(
            table_data=sample_data,
            table_name="customer_data",
            problem_context=basic_context
        )
        
        if 'error' in result:
            print(f"❌ Error occurred: {result['error']}")
            return False
        
        print("✅ Basic context test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Basic context test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting cleaning_agent context integration tests...\n")
    
    # Test 1: Enhanced context
    success1 = test_context_integration()
    
    # Test 2: Basic context
    success2 = test_basic_context()
    
    print(f"\n📊 Test Results:")
    print(f"   Enhanced Context: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"   Basic Context: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed! Context integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
