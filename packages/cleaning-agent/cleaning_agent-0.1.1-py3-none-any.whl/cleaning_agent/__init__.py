"""
Cleaning Agent - Intelligent data cleaning for automated data quality improvement.

This package provides an AI-powered data cleaning agent that can:
- Automatically detect data quality issues
- Suggest and apply cleaning strategies
- Handle various data types and formats
- Integrate with LLM models for intelligent cleaning decisions
- Provide detailed cleaning reports and recommendations

Example usage:
    from cleaning_agent import CleaningAgent
    
    agent = CleaningAgent(model_name="gpt-4")
    cleaned_data = agent.clean_data(data, goal="improve data quality")
"""

__version__ = "0.1.0"
__author__ = "StepFunction AI"
__email__ = "team@stepfunction.ai"

from .agent import CleaningAgent
from .config import CleaningConfig
from .models import CleaningRequest, CleaningResponse, CleaningStrategy, DataFrameColumnStats
from .utils import DataQualityAnalyzer, CleaningValidator

__all__ = [
    "CleaningAgent",
    "CleaningConfig", 
    "CleaningRequest",
    "CleaningResponse",
    "CleaningStrategy",
    "DataQualityAnalyzer",
    "CleaningValidator",
    "DataFrameColumnStats",
]
