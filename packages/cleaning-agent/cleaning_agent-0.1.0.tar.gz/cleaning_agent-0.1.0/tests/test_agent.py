"""
Tests for the Cleaning Agent.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from cleaning_agent.agent import CleaningAgent
from cleaning_agent.config import CleaningConfig
from cleaning_agent.models import CleaningRequest, CleaningResponse


class TestCleaningAgent:
    """Test cases for the CleaningAgent class."""
    def setup_method(self):
        """Set up test fixtures."""
        self.config = CleaningConfig(
            model_name="gpt-4",
            handle_outliers=False,
            log_level="ERROR"
        )
        
        # Create sample data
        self.sample_data = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', None, 'David', 'Eve'],
            'age': [25, 30, None, 35, 40],
            'salary': [50000, 60000, 70000, 80000, 90000],
            'department': ['HR', 'IT', 'IT', 'HR', 'IT']
        })

        self.agent = CleaningAgent(model_name="gpt-4", config=self.config)
    
    def test_initialization(self):
        """Test agent initialization."""
        assert self.agent.model_name == "gpt-4"
        assert self.agent.config is not None
        assert isinstance(self.agent.config, CleaningConfig)
    
    def test_parse_input_data_dataframe(self):
        """Test parsing DataFrame input."""
        result = self.agent._parse_input_data(self.sample_data)
        assert isinstance(result, pd.DataFrame)
        assert result.shape == self.sample_data.shape
        assert result is not self.sample_data  # Should be a copy
    
    def test_parse_input_data_dict(self):
        """Test parsing dictionary input."""
        print('self.sample_data', self.sample_data, type(self.sample_data))
        data_dict = self.sample_data.to_dict()
        print('data_dict', data_dict, type(data_dict))
        result = self.agent._parse_input_data(data_dict)
        print('result', result, type(result))
        assert isinstance(result, pd.DataFrame)
        assert result.shape == self.sample_data.shape
    
    def test_parse_input_data_invalid(self):
        """Test parsing invalid input."""
        result = self.agent._parse_input_data(123)
        assert result is None
    
    def test_handle_missing_values(self):
        """Test missing value handling."""
        # Create data with missing values
        data_with_missing = pd.DataFrame({
            'numeric': [1, 2, None, 4, 5],
            'categorical': ['A', 'B', None, 'D', 'E']
        })
        
        result = self.agent._handle_missing_values(data_with_missing, {})
        
        # Check that missing values were handled
        assert result['numeric'].isnull().sum() == 0
        assert result['categorical'].isnull().sum() == 0
        
        # Check that numeric column was filled with median
        assert result['numeric'].iloc[2] == 3.0  # median of [1,2,4,5]
        
        # Check that categorical column was filled with mode
        assert result['categorical'].iloc[2] in ['A', 'B', 'D', 'E']
    
    def test_remove_duplicates(self):
        """Test duplicate removal."""
        # Create data with duplicates
        data_with_duplicates = pd.DataFrame({
            'id': [1, 1, 2, 3, 3],
            'name': ['Alice', 'Alice', 'Bob', 'Charlie', 'Charlie']
        })
        
        result = self.agent._remove_duplicates(data_with_duplicates, {})
        
        # Check that duplicates were removed
        assert len(result) == 3
        assert result['id'].nunique() == 3
    
    def test_standardize_data_types(self):
        """Test data type standardization."""
        # Create data with mixed types
        data_mixed_types = pd.DataFrame({
            'numeric_string': ['1', '2', '3'],
            'text': ['A', 'B', 'C']
        })
        
        result = self.agent._standardize_data_types(data_mixed_types, {})
        
        # Check that numeric strings were converted
        assert result['numeric_string'].dtype in ['int64', 'float64']
        # Check that text remains as object
        assert result['text'].dtype == 'object'
    
    def test_generate_cleaning_strategies(self):
        """Test cleaning strategy generation."""
        # Mock quality metrics and issues
        from cleaning_agent.models import DataQualityMetrics, DataQualityIssue
        
        metrics = DataQualityMetrics(
            total_rows=100,
            total_columns=5,
            missing_values={'col1': 20, 'col2': 0},
            missing_percentage={'col1': 20.0, 'col2': 0.0},
            duplicate_rows=5,
            duplicate_percentage=5.0,
            data_types={'col1': 'object', 'col2': 'int64'},
            unique_values={'col1': 10, 'col2': 100},
            quality_score=0.7
        )
        
        issues = [
            DataQualityIssue(
                issue_type="missing_values",
                severity="medium",
                description="Column has missing values",
                affected_columns=['col1'],
                affected_rows=20,
                suggested_fixes=[]
            )
        ]
        
        strategies = self.agent._generate_cleaning_strategies(
            self.sample_data, issues, "improve quality", metrics
        )
        
        assert len(strategies) > 0
        assert any(s.strategy_name == "handle_missing_values" for s in strategies)
        assert any(s.strategy_name == "remove_duplicates" for s in strategies)
    
    def test_apply_cleaning_strategies(self):
        """Test applying cleaning strategies."""
        from cleaning_agent.models import CleaningStrategy
        
        strategies = [
            CleaningStrategy(
                strategy_name="remove_duplicates",
                description="Remove duplicate rows",
                applicable_issues=["duplicates"],
                confidence_score=0.9,
                estimated_impact="high",
                implementation_complexity="low"
            )
        ]
        
        # Create data with duplicates
        data_with_duplicates = pd.DataFrame({
            'id': [1, 1, 2, 3],
            'name': ['Alice', 'Alice', 'Bob', 'Charlie']
        })
        
        cleaned_data, operations = self.agent._apply_cleaning_strategies(
            data_with_duplicates, strategies, {}
        )
        
        assert len(cleaned_data) < len(data_with_duplicates)
        assert len(operations) == 1
        assert operations[0].status == "completed"
    
    def test_clean_data_success(self):
        """Test successful data cleaning."""
        with patch.object(self.agent, '_parse_input_data', return_value=self.sample_data):
            response = self.agent.clean_data(
                self.sample_data,
                "improve data quality",
                {}
            )
            
            assert response.success is True
            assert response.cleaned_data is not None
            assert response.report is not None
            assert "successfully" in response.message.lower()
    
    def test_clean_data_failure(self):
        """Test data cleaning failure."""
        with patch.object(self.agent, '_parse_input_data', return_value=None):
            response = self.agent.clean_data(
                "invalid_data",
                "improve data quality",
                {}
            )
            
            assert response.success is False
            assert "Failed to parse input data" in response.message
    
    def test_get_capabilities(self):
        """Test getting agent capabilities."""
        capabilities = self.agent.get_capabilities()
        
        assert capabilities['agent_name'] == "cleaning_agent"
        assert capabilities['version'] == "0.1.0"
        assert 'missing_value_handling' in capabilities['capabilities']
        assert 'duplicate_removal' in capabilities['capabilities']
        assert 'csv' in capabilities['supported_data_formats']


class TestDataQualityAnalyzer:
    """Test cases for the DataQualityAnalyzer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from cleaning_agent.utils import DataQualityAnalyzer
        self.analyzer = DataQualityAnalyzer()
        
        # Create sample data
        self.sample_data = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', None, 'David', 'Eve'],
            'age': [25, 30, None, 35, 40],
            'salary': [50000, 60000, 70000, 80000, 90000]
        })
    
    def test_analyze_data_quality(self):
        """Test data quality analysis."""
        metrics = self.analyzer.analyze_data_quality(self.sample_data)
        
        assert metrics.total_rows == 5
        assert metrics.total_columns == 4
        assert metrics.missing_values['name'] == 1
        assert metrics.missing_values['age'] == 1
        assert metrics.duplicate_rows == 0
        assert 0 <= metrics.quality_score <= 1
    
    # def test_detect_issues(self):
    #     """Test issue detection."""
    #     metrics = self.analyzer.analyze_data_quality(self.sample_data)
    #     issues = self.analyzer.detect_issues(self.sample_data, metrics)
        
    #     # Should detect missing value issues
    #     missing_issues = [i for i in issues if i.issue_type == "missing_values"]
    #     assert len(missing_issues) > 0
        
    #     # Check issue details
    #     for issue in missing_issues:
    #         assert issue.severity in ["low", "medium", "high", "critical"]
    #         assert len(issue.suggested_fixes) > 0


class TestCleaningValidator:
    """Test cases for the CleaningValidator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from cleaning_agent.utils import CleaningValidator
        self.validator = CleaningValidator()
        
        # Create sample data
        self.original_data = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', None, 'David', 'Eve'],
            'age': [25, 30, None, 35, 40]
        })
        
        self.cleaned_data = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Unknown', 'David', 'Eve'],
            'age': [25, 30, 30, 35, 40]
        })
    
    def test_validate_cleaned_data(self):
        """Test cleaned data validation."""
        from cleaning_agent.models import DataQualityMetrics
        
        original_metrics = DataQualityMetrics(
            total_rows=5,
            total_columns=3,
            missing_values={'id': 0, 'name': 1, 'age': 1},
            missing_percentage={'id': 0.0, 'name': 20.0, 'age': 20.0},
            duplicate_rows=0,
            duplicate_percentage=0.0,
            data_types={'id': 'int64', 'name': 'object', 'age': 'int64'},
            unique_values={'id': 5, 'name': 4, 'age': 4},
            quality_score=0.7
        )
        
        result = self.validator.validate_cleaned_data(self.cleaned_data, original_metrics)
        
        assert hasattr(result, 'final_quality_score')
        assert hasattr(result, 'validation_passed')
        assert hasattr(result, 'issues')
    
    def test_generate_validation_report(self):
        """Test validation report generation."""
        report = self.validator.generate_validation_report(self.original_data, self.cleaned_data)
        
        assert 'validation_summary' in report
        assert 'data_integrity' in report
        assert 'quality_improvements' in report
        
        # Check summary
        assert report['validation_summary']['original_rows'] == 5
        assert report['validation_summary']['cleaned_rows'] == 5
        assert report['validation_summary']['rows_removed'] == 0


if __name__ == "__main__":
    pytest.main([__file__])
