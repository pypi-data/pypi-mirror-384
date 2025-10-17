
import unittest
import pandas as pd
from unittest.mock import MagicMock, patch
from cleaning_agent.agent import CleaningAgent
import pytest 
class TestLLMDrivenCleaning(unittest.TestCase):

    def setUp(self):
        self.agent = CleaningAgent()

    def test_execute_llm_driven_cleaning_cycle_success(self):
        # Sample data with issues
        sample_data = pd.DataFrame({
            'patient_id': [1, 2, 3, None, 5],
            'age': [25, 30, 35, 40, 45],
            'diagnosis': ['Flu', 'Cold', 'Fever', 'Headache', 'Cough'],
            'treatment_date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05']
        })
        goal = "Clean the patient data. Fill missing patient_id with the mean of the column."

        # Execute the cleaning cycle
        cleaned_df = self.agent.execute_llm_driven_cleaning_cycle(sample_data, goal)

        # Assertions
        self.assertIsNotNone(cleaned_df)
        self.assertFalse(cleaned_df['patient_id'].isnull().any())
        self.assertNotEqual(sample_data.to_string(), cleaned_df.to_string())
        print("✅ Test passed: LLM-driven cleaning cycle completed successfully.")

if __name__ == '__main__':
    pytest.main([__file__])   
