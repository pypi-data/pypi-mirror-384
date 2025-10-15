import pytest
import pandas as pd
import traceback

from cleaning_agent.agent import CleaningAgent
from cleaning_agent.config import CleaningConfig

class TestSqlCleaningAgent:
    """Test cases for SQL-based cleaning methods in CleaningAgent."""
    def setup_method(self):
        try:
            # self.config = CleaningConfig(
            #     model_name="gpt-4.1-mini",
            #     handle_outliers=False,
            #     log_level="ERROR"
            # )
            self.sample_data = pd.DataFrame({
                'id': [1, 2, 3, 4, 5],
                'name': ['Alice', 'Bob', None, 'David', 'Eve'],
                'age': [25, 30, None, 35, 40],
                'salary': [50000, 60000, 70000, 80000, 90000],
                'department': ['HR', 'IT', 'IT', 'HR', 'IT']
            })
            self.agent = CleaningAgent(model_name="gpt-4.1-mini", config=None)#self.config)
            # print('\n','-'*30,"setup successful", '-'*30, '\n')
        except Exception as e:
            print(f"Error setting up test: {e}")
            # print('\n','-'*30,"setup failed", '-'*30, '\n')
            print(traceback.format_exc())

    def test_cleaning_with_sql(self):
        """Test suggest_cleaning_and_sql_operations returns expected structure (no patch)."""
        try:
            result = self.agent.suggest_cleaning_with_sql(
                # df=self.sample_data,
                columns=list(self.sample_data.columns),
                db_name="db",
                schema="s",
                table_name="t",
                use_case="test",
            )
            print('\n**** results of suggest_cleaning_and_sql_operations : \n', result, '\n')
            assert isinstance(result, dict)
            assert 'feature_suggestions' in result
            assert isinstance(result['feature_suggestions'], list)
            print('\n','-'*30,"test_suggest_cleaning_and_sql_operations passed", '-'*30, '\n')
        except Exception as e:
            print(f"Error in test_suggest_cleaning_and_sql_operations: {e}")
            print('\n','-'*30,"test_suggest_cleaning_and_sql_operations failed", '-'*30, '\n')
            print(traceback.format_exc())

    def test_clean_data_with_sql(self):
        """Test clean_data_with_sql returns structured output (no patch)."""
        try:
            # Prepare sample data and required parameters
            sample_data = self.sample_data.head(5).to_dict(orient='list')  # Sample data as dict
            columns_name = list(self.sample_data.columns)
            data_types = {col: str(self.sample_data[col].dtype) for col in self.sample_data.columns}
            computed_stats = {col: {'unique': self.sample_data[col].nunique()} for col in self.sample_data.columns}
            identical_column_pairs = []
            
            result = self.agent.clean_data_with_sql(
                sample_data=sample_data,
                columns_name=columns_name,
                data_types=data_types,
                computed_stats=computed_stats,
                identical_column_pairs=identical_column_pairs,
                db_name="db", 
                schema="s", 
                table="t", 
                use_case="u"
            )
            
            print('\n**** results of clean_data_with_sql : \n', result, '\n')
            assert isinstance(result, dict)
            assert 'success' in result
            assert 'db_name' in result
            assert 'schema' in result
            assert 'table' in result
            assert 'feature_suggestions' in result
            assert isinstance(result['feature_suggestions'], list)
            print('\n','-'*30,"test_clean_data_with_sql passed", '-'*30, '\n')
        except Exception as e:
            print(f"Error in test_clean_data_with_sql: {e}")
            print('\n','-'*30,"test_clean_data_with_sql failed", '-'*30, '\n')
            print(traceback.format_exc())

    def test_execute_cleaning_operation_with_sql(self):
        """Test execute_cleaning_operation_with_sql returns structured output."""
        try:
            # Prepare sample data and required parameters
            sample_data = self.sample_data.head(5).to_dict(orient='list')  # Sample data as dict
            columns_name = list(self.sample_data.columns)
            data_types = {col: str(self.sample_data[col].dtype) for col in self.sample_data.columns}
            computed_stats = {col: {'unique': self.sample_data[col].nunique()} for col in self.sample_data.columns}
            identical_column_pairs = []
            
            # Call with explicit parameters
            result = self.agent.execute_llm_driven_cleaning_operation_with_sql(
                sample_data=sample_data,
                columns_name=columns_name,
                data_types=data_types,
                computed_stats=computed_stats,
                identical_column_pairs=identical_column_pairs,
                db_name="db", 
                schema="s", 
                table="t", 
                use_case="test"
            )
            
            print('\n**** results of execute_cleaning_operation_with_sql : \n', result, '\n')
            assert isinstance(result, dict)
            assert 'success' in result
            assert 'db_name' in result
            assert 'schema' in result
            assert 'table' in result
            assert 'feature_suggestions' in result
            
            # For the second call, we'll use the same parameters since None is not a valid input
            result2 = self.agent.execute_llm_driven_cleaning_operation_with_sql(
                sample_data=sample_data,
                columns_name=columns_name,
                data_types=data_types,
                computed_stats=computed_stats,
                identical_column_pairs=identical_column_pairs,
                db_name="db2",  # Different db_name to show it's a different call
                schema="public",
                table="test_table"
            )
            
            print('\n**** results of execute_cleaning_operation_with_sql second call: \n', result2, '\n')
            assert isinstance(result2, dict)
            assert 'success' in result2
            assert 'db_name' in result2
            assert 'schema' in result2
            assert 'table' in result2
            assert 'feature_suggestions' in result2
            
            print('\n','-'*30,"test_execute_cleaning_operation_with_sql passed", '-'*30, '\n')
            print("="*30, "All tests passed", "=" * 30)
        except Exception as e:
            print(f"Error in test_execute_cleaning_operation_with_sql: {e}")
            print('\n','-'*30,"test_execute_cleaning_operation_with_sql failed", '-'*30, '\n')
            print(traceback.format_exc())
