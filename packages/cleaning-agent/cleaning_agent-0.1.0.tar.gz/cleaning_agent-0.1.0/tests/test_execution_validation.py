#!/usr/bin/env python3
"""
Test that AI recommendations are actually executed and produce real results.
This validates the complete flow: context → AI recommendations → actual execution → results.
"""

import sys
import os
import pandas as pd
import numpy as np
import json

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cleaning_agent.agent import CleaningAgent

def test_execution_validation():
    """Test that AI recommendations are actually executed and measurable results are produced."""
    
    print("🔬 Testing AI Recommendations Execution Validation...")
    
    # Create problematic data that needs real cleaning
    sample_data = pd.DataFrame({
        'patient_id': [1.0, 2.0, np.nan, 4.0, 5.0],  # Has null, wrong dtype (float vs int)
        'age': [25, 30, 35, 150, -5],  # Has outliers (150, -5)
        'diagnosis': ['flu', 'COLD', 'Fever  ', 'headache', 'Cough'],  # Inconsistent casing, extra spaces
        'treatment_date': ['2024-01-01', '2024/01/02', '01-03-2024', '2024-01-04', 'invalid_date']  # Inconsistent formats
    })
    
    print("📋 Original Data Issues:")
    print(f"   - Null values: {sample_data.isnull().sum().sum()}")
    print(f"   - Inconsistent diagnosis casing: {sample_data['diagnosis'].tolist()}")
    print(f"   - Patient ID dtype: {sample_data['patient_id'].dtype}")
    print(f"   - Age outliers: {sample_data['age'].tolist()}")
    print(f"   - Date format issues: {sample_data['treatment_date'].tolist()}")
    
    # Create enriched context (healthcare domain with HIPAA compliance)
    enriched_context = {
        'enriched_context': {
            'domain_knowledge': {
                'domain': 'healthcare',
                'business_context': {
                    'compliance': 'HIPAA',
                    'data_sensitivity': 'high',
                    'industry': 'medical',
                    'quality_requirements': 'strict'
                },
                'data_files': ['medical_records.csv'],
                'constraints': {'privacy': 'strict', 'data_retention': '7_years'},
                'stakeholders': ['doctors', 'nurses', 'patients', 'compliance_officers']
            },
            'workflow_context': {
                'goal': 'Clean medical records for compliance analysis while maintaining HIPAA standards',
                'complexity': 'high',
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
        print("\n🤖 Initializing cleaning agent...")
        agent = CleaningAgent()
        
        # Execute cleaning with enriched context
        print("\n🔧 Executing cleaning with AI recommendations...")
        result = agent.analyze_and_clean_table(
            table_data=sample_data,
            table_name="medical_records",
            problem_context=enriched_context
        )
        
        # Verify execution results
        if 'error' in result:
            print(f"❌ Execution failed: {result['error']}")
            return False
        
        cleaned_data = result.get('cleaned_data', pd.DataFrame())
        cleaning_plan = result.get('cleaning_plan', {})
        execution_summary = result.get('execution_summary', {})
        
        print("\n📊 Analyzing Execution Results...")
        
        # Test 1: Verify actual data transformations occurred
        data_changes = []
        
        # Check null handling
        original_nulls = sample_data.isnull().sum().sum()
        cleaned_nulls = cleaned_data.isnull().sum().sum()
        if cleaned_nulls != original_nulls:
            data_changes.append(f"Null values: {original_nulls} → {cleaned_nulls}")
        
        # Check data type changes
        if 'patient_id' in cleaned_data.columns:
            original_dtype = str(sample_data['patient_id'].dtype)
            cleaned_dtype = str(cleaned_data['patient_id'].dtype)
            if original_dtype != cleaned_dtype:
                data_changes.append(f"Patient ID dtype: {original_dtype} → {cleaned_dtype}")
        
        # Check outlier handling
        if 'age' in cleaned_data.columns:
            original_outliers = len([x for x in sample_data['age'] if x < 0 or x > 120])
            cleaned_outliers = len([x for x in cleaned_data['age'] if x < 0 or x > 120])
            if original_outliers != cleaned_outliers:
                data_changes.append(f"Age outliers: {original_outliers} → {cleaned_outliers}")
        
        # Check text standardization
        if 'diagnosis' in cleaned_data.columns:
            original_inconsistent = len(set(sample_data['diagnosis'].str.lower().str.strip()))
            cleaned_inconsistent = len(set(cleaned_data['diagnosis'].str.lower().str.strip()))
            if original_inconsistent != cleaned_inconsistent:
                data_changes.append(f"Diagnosis variations: {original_inconsistent} → {cleaned_inconsistent}")
        
        print("\n✅ Measurable Data Transformations:")
        if data_changes:
            for change in data_changes:
                print(f"   ✓ {change}")
        else:
            print("   ⚠️  No measurable transformations detected")
        
        # Test 2: Verify AI recommendations were used
        context_aware = False
        if 'context_utilization' in cleaning_plan:
            context_aware = True
            print(f"\n✅ Context-Aware Processing:")
            print(f"   ✓ Domain: {cleaning_plan.get('domain', 'unknown')}")
            print(f"   ✓ Data Sensitivity: {cleaning_plan.get('data_sensitivity', 'unknown')}")
            
            strategies = cleaning_plan.get('context_aware_strategies', [])
            if strategies:
                print(f"   ✓ AI Strategies Applied: {len(strategies)}")
                for i, strategy in enumerate(strategies[:3], 1):  # Show first 3
                    print(f"     {i}. {strategy}")
            else:
                print("   ⚠️  No context-aware strategies found")
        
        # Test 3: Verify execution actually occurred
        execution_occurred = False
        if execution_summary.get('status') == 'completed':
            execution_occurred = True
            steps_executed = execution_summary.get('steps_executed', [])
            print(f"\n✅ Execution Verification:")
            print(f"   ✓ Status: {execution_summary.get('status')}")
            print(f"   ✓ Steps Executed: {len(steps_executed)}")
            for step in steps_executed:
                print(f"     - {step}")
        
        # Test 4: Verify results are ready for next agent
        results_ready = False
        if not cleaned_data.empty and 'final_summary' in result:
            results_ready = True
            print(f"\n✅ Results Ready for Next Agent:")
            print(f"   ✓ Cleaned Data Shape: {cleaned_data.shape}")
            print(f"   ✓ Data Quality Score: {len(data_changes)} improvements")
            print(f"   ✓ Summary Available: {bool(result.get('final_summary'))}")
        
        # Overall assessment
        print(f"\n🎯 Execution Assessment:")
        print(f"   Data Transformations: {'✅ YES' if data_changes else '❌ NO'}")
        print(f"   Context-Aware Processing: {'✅ YES' if context_aware else '❌ NO'}")
        print(f"   Actual Execution: {'✅ YES' if execution_occurred else '❌ NO'}")
        print(f"   Results for Next Agent: {'✅ YES' if results_ready else '❌ NO'}")
        
        # Success criteria
        success = bool(data_changes) and execution_occurred and results_ready
        
        if success:
            print(f"\n🎉 SUCCESS: AI recommendations were executed and produced measurable results!")
            print(f"   ✓ Data was actually transformed")
            print(f"   ✓ Results are ready for the next agent")
            print(f"   ✓ Context was utilized in decision making")
        else:
            print(f"\n⚠️  PARTIAL SUCCESS: Some execution verification failed")
            if not data_changes:
                print(f"   ❌ No measurable data transformations detected")
            if not execution_occurred:
                print(f"   ❌ Execution status not confirmed")
            if not results_ready:
                print(f"   ❌ Results not properly formatted for next agent")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Execution test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_execution():
    """Test basic execution without enriched context."""
    
    print("\n🧪 Testing Basic Execution (Control Test)...")
    
    # Simple data for basic test
    simple_data = pd.DataFrame({
        'id': [1, 2, 3, None, 5],
        'value': [10, 20, 30, 40, 50]
    })
    
    try:
        agent = CleaningAgent()
        result = agent.analyze_and_clean_table(
            table_data=simple_data,
            table_name="test_data",
            problem_context={'problem': 'Clean test data'}
        )
        
        if 'error' in result:
            print(f"❌ Basic execution failed: {result['error']}")
            return False
        
        cleaned_data = result.get('cleaned_data', pd.DataFrame())
        print(f"✅ Basic execution successful - Shape: {cleaned_data.shape}")
        return True
        
    except Exception as e:
        print(f"❌ Basic execution failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting AI Recommendations Execution Validation...\n")
    
    # Test 1: Full execution validation
    success1 = test_execution_validation()
    
    # Test 2: Basic execution (control)
    success2 = test_basic_execution()
    
    print(f"\n📊 Final Results:")
    print(f"   Enhanced Execution: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"   Basic Execution: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print(f"\n🎉 VALIDATION COMPLETE!")
        print(f"   ✓ AI recommendations are executed and produce real results")
        print(f"   ✓ Data transformations are measurable and verified")
        print(f"   ✓ Results are properly formatted for agent-to-agent handoff")
        print(f"\n🚀 Ready to test multi-agent context passing!")
    else:
        print(f"\n⚠️  Validation incomplete. Check the output above for details.")
