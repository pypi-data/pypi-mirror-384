"""
Data models for the Cleaning Agent.
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
import pandas as pd

class SqlCleaningSuggestion(BaseModel):
    """Model for a single feature suggestion (SQL)."""
    operation_name: str = Field(..., description="Name of the suggested feature")
    sql_query: str = Field(..., description="SQL query for the feature transformation")
    explanation: str = Field(..., description="Explanation of the feature suggestion")

class SqlCleaningOperationMapping(BaseModel):
    """Model for a single UI operation mapped from a feature suggestion."""
    operation_type: str = Field(..., description="Type of the operation (e.g., filter, transform)")
    parameters: Dict[str, Any] = Field(..., description="Parameters for the operation")
    original_feature_name: Optional[str] = Field(None, description="Name of the original feature suggestion")
    original_sql_query: Optional[str] = Field(None, description="SQL query of the original feature suggestion")
    original_explanation: Optional[str] = Field(None, description="Explanation of the original feature suggestion")


class CleaningRequest(BaseModel):
    """Request model for data cleaning operations."""
    
    data: Any = Field(..., description="Input data to be cleaned (DataFrame, dict, or file path)")
    goal: str = Field(..., description="Cleaning goal or objective")
    cleaning_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional cleaning parameters")
    data_source: Optional[str] = Field(default=None, description="Source of the data")
    user_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict, description="User-specific cleaning preferences")
    
    class Config:
        arbitrary_types_allowed = True


class CleaningStrategy(BaseModel):
    """Model for cleaning strategy configuration."""
    
    strategy_name: str = Field(..., description="Name of the cleaning strategy")
    description: str = Field(..., description="Description of the strategy")
    applicable_issues: List[str] = Field(..., description="Data quality issues this strategy addresses")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in this strategy")
    estimated_impact: str = Field(..., description="Estimated impact on data quality")
    implementation_complexity: str = Field(..., description="Complexity of implementation: low, medium, high")
    
    class Config:
        use_enum_values = True


class DataQualityIssue(BaseModel):
    """Model for data quality issues."""
    
    issue_type: str = Field(..., description="Type of data quality issue")
    severity: str = Field(..., description="Severity: low, medium, high, critical")
    description: str = Field(..., description="Description of the issue")
    affected_columns: List[str] = Field(default_factory=list, description="Columns affected by this issue")
    affected_rows: Optional[int] = Field(default=None, description="Number of rows affected")
    suggested_fixes: List[str] = Field(default_factory=list, description="Suggested fixes for this issue")


class CleaningOperation(BaseModel):
    """Model for individual cleaning operations."""
    
    operation_id: str = Field(..., description="Unique identifier for the operation")
    operation_type: str = Field(..., description="Type of cleaning operation")
    description: str = Field(..., description="Description of what the operation does")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters used for the operation")
    status: str = Field(default="pending", description="Status: pending, in_progress, completed, failed")
    start_time: Optional[datetime] = Field(default=None, description="When the operation started")
    end_time: Optional[datetime] = Field(default=None, description="When the operation completed")
    rows_affected: Optional[int] = Field(default=None, description="Number of rows affected by this operation")
    error_message: Optional[str] = Field(default=None, description="Error message if operation failed")


class CleaningReport(BaseModel):
    """Model for cleaning operation reports."""
    
    report_id: str = Field(..., description="Unique identifier for the report")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the report was generated")
    data_summary: Dict[str, Any] = Field(..., description="Summary of the data before and after cleaning")
    issues_detected: List[DataQualityIssue] = Field(default_factory=list, description="Data quality issues detected")
    cleaning_operations: List[CleaningOperation] = Field(default_factory=list, description="Cleaning operations performed")
    quality_metrics: Dict[str, float] = Field(..., description="Data quality metrics before and after cleaning")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for further improvements")
    execution_time: Optional[float] = Field(default=None, description="Total execution time in seconds")


class CleaningResponse(BaseModel):
    """Response model for data cleaning operations."""
    
    success: bool = Field(..., description="Whether the cleaning operation was successful")
    cleaned_data: Optional[Any] = Field(default=None, description="Cleaned data output")
    report: Optional[CleaningReport] = Field(default=None, description="Detailed cleaning report")
    message: str = Field(..., description="Human-readable message about the operation")
    errors: List[str] = Field(default_factory=list, description="List of errors if operation failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the operation")
    
    class Config:
        arbitrary_types_allowed = True


class DataQualityMetrics(BaseModel):
    """Model for data quality metrics."""
    
    total_rows: int = Field(..., description="Total number of rows")
    total_columns: int = Field(..., description="Total number of columns")
    missing_values: Dict[str, int] = Field(..., description="Missing values per column")
    missing_percentage: Dict[str, float] = Field(..., description="Missing values percentage per column")
    duplicate_rows: int = Field(..., description="Number of duplicate rows")
    duplicate_percentage: float = Field(..., description="Percentage of duplicate rows")
    data_types: Dict[str, str] = Field(..., description="Data types of each column")
    unique_values: Dict[str, int] = Field(..., description="Number of unique values per column")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall data quality score")


class CleaningParameters(BaseModel):
    """Model for cleaning operation parameters."""
    
    handle_missing_values: bool = Field(default=True, description="Whether to handle missing values")
    remove_duplicates: bool = Field(default=True, description="Whether to remove duplicate rows")
    standardize_data_types: bool = Field(default=True, description="Whether to standardize data types")
    handle_outliers: bool = Field(default=False, description="Whether to handle outliers")
    normalize_text: bool = Field(default=False, description="Whether to normalize text data")
    custom_rules: List[Dict[str, Any]] = Field(default_factory=list, description="Custom cleaning rules")
    preserve_original: bool = Field(default=True, description="Whether to preserve original data")
    
    class Config:
        use_enum_values = True


def serialize_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """Serialize pandas DataFrame to dictionary."""
    return {
        "data": df.to_dict(orient="records"),
        "columns": df.columns.tolist(),
        "index": df.index.tolist(),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "shape": df.shape,
        "memory_usage": df.memory_usage(deep=True).sum()
    }


def deserialize_dataframe(data: Dict[str, Any]) -> pd.DataFrame:
    """Deserialize dictionary to pandas DataFrame."""
    df = pd.DataFrame(data["data"], columns=data["columns"])
    if "index" in data and data["index"]:
        df.index = data["index"]
    return df


class DataFrameColumnStats(BaseModel):
    """Statistics for a single DataFrame column."""
    column_name: str
    null_fraction: Optional[float] = None
    distinct_count: Optional[int] = None
    mean: Optional[float] = None
    std: Optional[float] = None
    min_val: Optional[float] = None
    max_val: Optional[float] = None

class DataFrameProfile(BaseModel):
    """Profile summary of a pandas DataFrame for cleaning/analysis."""
    sample_rows: str
    columns: List[str] = []
    data_types: Dict[str, str] = {}
    computed_stats: Dict[str, DataFrameColumnStats] = {}
    identical_column_pairs: List[Tuple[str, str]] = []
    error_log: List[str] = []
