"""
Utility classes for the Cleaning Agent.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Callable
import pandas as pd
import numpy as np
import io
import contextlib
import traceback
import sys
import json
import warnings
import types 

from .models import DataQualityIssue, DataQualityMetrics, DataFrameProfile, DataFrameColumnStats

import json
from typing import Any, Dict, List

def extract_sample_data_sql_cleaning(df: pd.DataFrame, sample_rows: int = 5) -> Dict[str, List[Any]]:
    """
    Extract sample data from a DataFrame for prompt input.
    Returns a dict of column -> list of sample values.
    """
    sample = df.head(sample_rows)
    return {col: sample[col].tolist() for col in sample.columns}

def validate_llm_json_output_sql_cleaning(llm_response: str) -> Any:
    """
    Validate and parse an LLM response expected to be a JSON object or array.
    Returns parsed JSON or raises ValueError.
    """
    try:
        # Remove markdown code block markers if present
        # print('\n\nllm_response_: ', llm_response, type(llm_response))

        cleaned = llm_response.strip()
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        if cleaned.startswith('```'):
            cleaned = cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        return json.loads(cleaned)
    except Exception as e:
        print(traceback.format_exc()[:500])
        raise ValueError(f"Invalid LLM JSON output: {e}")

def extract_dataframe_profile(df: pd.DataFrame, sample_size: int = 5) -> DataFrameProfile:
    """
    Extracts profile information from a pandas DataFrame including:
    - sample_rows (as string)
    - columns (list)
    - data_types (dict)
    - computed_stats (dict of DataFrameColumnStats)
    - identical_column_pairs (list of tuples)
    Handles errors gracefully, logs them, and returns a DataFrameProfile.
    """
    logger = logging.getLogger(__name__)
    error_log = []
    sample_rows = ''
    columns = []
    data_types = {}
    computed_stats = {}
    identical_column_pairs = []

    # Sample Rows
    try:
        sample_rows = df.head(sample_size).to_string()
    except Exception as e:
        logger.error(f"Failed to extract sample rows: {e}")
        error_log.append(f"sample_rows: {str(e)}")
        sample_rows = ''

    # Columns
    try:
        columns = list(df.columns)
    except Exception as e:
        logger.error(f"Failed to extract columns: {e}")
        error_log.append(f"columns: {str(e)}")
        columns = []

    # Data Types
    try:
        data_types = df.dtypes.astype(str).to_dict()
    except Exception as e:
        logger.error(f"Failed to extract data types: {e}")
        error_log.append(f"data_types: {str(e)}")
        data_types = {}

    # Computed Stats
    for col in columns:
        try:
            series = df[col]
            null_fraction = float(series.isnull().mean()) if series.size > 0 else None
            distinct_count = int(series.nunique(dropna=True))
            mean = float(series.mean()) if pd.api.types.is_numeric_dtype(series) else None
            std = float(series.std()) if pd.api.types.is_numeric_dtype(series) else None
            min_val = float(series.min()) if pd.api.types.is_numeric_dtype(series) else None
            max_val = float(series.max()) if pd.api.types.is_numeric_dtype(series) else None
            computed_stats[col] = DataFrameColumnStats(
                column_name=col,
                null_fraction=null_fraction,
                distinct_count=distinct_count,
                mean=mean,
                std=std,
                min_val=min_val,
                max_val=max_val
            )
        except Exception as e:
            logger.error(f"Failed to compute stats for column {col}: {e}")
            error_log.append(f"computed_stats[{col}]: {str(e)}")
            computed_stats[col] = DataFrameColumnStats(column_name=col)

    # Identical Column Pairs
    try:
        n = len(columns)
        for i in range(n):
            for j in range(i+1, n):
                try:
                    if df[columns[i]].equals(df[columns[j]]):
                        identical_column_pairs.append((columns[i], columns[j]))
                except Exception as e:
                    logger.warning(f"Failed to compare columns {columns[i]} and {columns[j]}: {e}")
    except Exception as e:
        logger.error(f"Failed to find identical column pairs: {e}")
        error_log.append(f"identical_column_pairs: {str(e)}")
        identical_column_pairs = []

    return DataFrameProfile(
        sample_rows=sample_rows,
        columns=columns,
        data_types=data_types,
        computed_stats=computed_stats,
        identical_column_pairs=identical_column_pairs,
        error_log=error_log
    )

class DataQualityAnalyzer:
    """Analyzes data quality and detects issues."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_data_quality(self, df: pd.DataFrame) -> DataQualityMetrics:
        """Analyze the quality of the provided DataFrame."""
        try:
            total_rows, total_columns = df.shape
            
            # Calculate missing values
            # print('\ndf', df.head(1), df.columns, df.dtypes, df.shape, type(df))
            missing_values = df.isnull().sum().to_dict()
            # print('\n\n\nmissing_values1', missing_values, type(missing_values))
            missing_percentage = {col: (missing_values[col] / total_rows) * 100 for col in missing_values}
            # print('\nmissing_percentage1', missing_percentage, type(missing_percentage))
            
            # Calculate duplicates
            duplicate_rows = df.duplicated().sum()
            # print('\nduplicate_rows1', duplicate_rows, type(duplicate_rows))
            duplicate_percentage = (duplicate_rows / total_rows) * 100 if total_rows > 0 else 0
            # print('\nduplicate_percentage1', duplicate_percentage, type(duplicate_percentage))
            
            # Get data types
            data_types = df.dtypes.astype(str).to_dict()
            # print('\ndata_types1', data_types, type(data_types))
            
            # Calculate unique values per column
            unique_values = {col: df[col].nunique() for col in df.columns}
            # print('\nunique_values1', unique_values, type(unique_values))
            
            # Calculate overall quality score
            quality_score = self._calculate_quality_score(
                missing_percentage, duplicate_percentage, data_types, unique_values, total_rows
            )
            # print('\nquality_score1', quality_score, type(quality_score))

            return DataQualityMetrics(
                total_rows=total_rows,
                total_columns=total_columns,
                missing_values=missing_values,
                missing_percentage=missing_percentage,
                duplicate_rows=int(duplicate_rows),
                duplicate_percentage=duplicate_percentage,
                data_types=data_types,
                unique_values=unique_values,
                quality_score=quality_score
            )
            
        except Exception as e:
            self.logger.error(f"Failed to analyze data quality: {e}")
            # Return default metrics
            return DataQualityMetrics(
                total_rows=0,
                total_columns=0,
                missing_values={},
                missing_percentage={},
                duplicate_rows=0,
                duplicate_percentage=0.0,
                data_types={},
                unique_values={},
                quality_score=0.0
            )
    
    def _calculate_quality_score(
        self,
        missing_percentage: Dict[str, float],
        duplicate_percentage: float,
        data_types: Dict[str, str],
        unique_values: Dict[str, int],
        total_rows: int
    ) -> float:
        """Calculate overall data quality score."""
        try:
            # Missing values penalty (0-30 points)
            avg_missing = np.mean(list(missing_percentage.values())) if missing_percentage else 0
            missing_score = max(0, 30 - (avg_missing * 0.3))
            
            # Duplicate penalty (0-20 points)
            duplicate_score = max(0, 20 - (duplicate_percentage * 0.2))
            
            # Data type consistency (0-25 points)
            type_score = 25  # Assume good for now
            
            # Uniqueness score (0-25 points)
            if total_rows > 0:
                avg_uniqueness = np.mean([unique_values[col] / total_rows for col in unique_values if total_rows > 0])
                uniqueness_score = min(25, avg_uniqueness * 25)
            else:
                uniqueness_score = 0
            
            total_score = missing_score + duplicate_score + type_score + uniqueness_score
            return min(100, max(0, total_score)) / 100  # Normalize to 0-1
            
        except Exception as e:
            self.logger.error(f"Failed to calculate quality score: {e}")
            return 0.5  # Default score
    
    def detect_issues(self, df: pd.DataFrame, quality_metrics: DataQualityMetrics) -> List[DataQualityIssue]:
        """Detect data quality issues based on the metrics."""
        issues = []
        
        try:
            # Missing values issues
            for column, missing_pct in quality_metrics.missing_percentage.items():
                if missing_pct > 20:  # More than 20% missing
                    issues.append(DataQualityIssue(
                        issue_type="missing_values",
                        severity="high" if missing_pct > 50 else "medium",
                        description=f"Column '{column}' has {missing_pct:.1f}% missing values",
                        affected_columns=[column],
                        affected_rows=int(quality_metrics.missing_values[column]),
                        suggested_fixes=[
                            "Consider removing rows with missing values",
                            "Use imputation strategies",
                            "Investigate why values are missing"
                        ]
                    ))
            
            # Duplicate rows issues
            if quality_metrics.duplicate_percentage > 5:
                issues.append(DataQualityIssue(
                    issue_type="duplicate_rows",
                    severity="medium" if quality_metrics.duplicate_percentage > 20 else "low",
                    description=f"Dataset has {quality_metrics.duplicate_percentage:.1f}% duplicate rows",
                    affected_columns=[],
                    affected_rows=quality_metrics.duplicate_rows,
                    suggested_fixes=[
                        "Remove duplicate rows",
                        "Investigate source of duplicates",
                        "Consider keeping only unique records"
                    ]
                ))
            
            # Data type issues
            for column, dtype in quality_metrics.data_types.items():
                if dtype == 'object' and quality_metrics.unique_values[column] < quality_metrics.total_rows * 0.1:
                    # Low cardinality object columns might be categorical
                    issues.append(DataQualityIssue(
                        issue_type="data_type_inconsistency",
                        severity="low", # ToDo -add criteria for severity
                        description=f"Column '{column}' might be categorical but is stored as object",
                        affected_columns=[column],
                        affected_rows=quality_metrics.total_rows,
                        suggested_fixes=[
                            "Convert to categorical type",
                            "Review data type assignment"
                        ]
                    ))
            
            # Outlier detection for numerical columns
            for column in df.columns:
                if df[column].dtype in ['int64', 'float64']:
                    outliers = self._detect_outliers(df[column])
                    if outliers > 0:
                        issues.append(DataQualityIssue(
                            issue_type="outliers",
                            severity="low",  # ToDo -add criteria for severity
                            description=f"Column '{column}' has {outliers} potential outliers",
                            affected_columns=[column],
                            affected_rows=outliers,
                            suggested_fixes=[
                                "Investigate outliers for validity",
                                "Consider outlier handling strategies",
                                "Use robust statistical methods"
                            ]
                        ))
            
        except Exception as e:
            self.logger.error(f"Failed to detect issues: {e}")
        
        return issues
    
    def _detect_outliers(self, series: pd.Series) -> int:
        """Detect outliers in a numerical series using IQR method."""
        try:
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = ((series < lower_bound) | (series > upper_bound)).sum()
            return int(outliers)
        except Exception:
            return 0

class CleaningValidator:
    """Validates cleaned data and provides quality assessment."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_cleaned_data(self, cleaned_df: pd.DataFrame, original_metrics: DataQualityMetrics) -> Any:
        """Validate the cleaned data and return validation results."""
        try:
            # Create a simple validation result object
            class ValidationResult:
                def __init__(self, final_quality_score: float, validation_passed: bool, issues: List[str]):
                    self.final_quality_score = final_quality_score
                    self.validation_passed = validation_passed
                    self.issues = issues
            
            # Analyze cleaned data
            analyzer = DataQualityAnalyzer()
            cleaned_metrics = analyzer.analyze_data_quality(cleaned_df)
            
            # Check for improvements
            improvement = cleaned_metrics.quality_score - original_metrics.quality_score
            validation_passed = improvement >= 0
            
            # Collect any new issues
            issues = []
            if cleaned_metrics.quality_score < original_metrics.quality_score:
                issues.append("Data quality decreased after cleaning")
            
            if cleaned_metrics.total_rows < original_metrics.total_rows * 0.8:
                issues.append("Too many rows were removed during cleaning")
            
            return ValidationResult(
                final_quality_score=cleaned_metrics.quality_score,
                validation_passed=validation_passed,
                issues=issues
            )
            
        except Exception as e:
            self.logger.error(f"Failed to validate cleaned data: {e}")
            # Return default validation result
            class DefaultValidationResult:
                def __init__(self):
                    self.final_quality_score = 0.5
                    self.validation_passed = False
                    self.issues = ["Validation failed due to error"]
            
            return DefaultValidationResult()
    
    def generate_validation_report(self, original_df: pd.DataFrame, cleaned_df: pd.DataFrame) -> Dict[str, Any]:
        """Generate a comprehensive validation report."""
        try:
            report = {
                "validation_summary": {
                    "original_rows": len(original_df),
                    "cleaned_rows": len(cleaned_df),
                    "rows_removed": len(original_df) - len(cleaned_df),
                    "removal_percentage": ((len(original_df) - len(cleaned_df)) / len(original_df)) * 100 if len(original_df) > 0 else 0
                },
                "data_integrity": {
                    "columns_preserved": len(cleaned_df.columns) == len(original_df.columns),
                    "data_types_preserved": self._check_data_type_preservation(original_df, cleaned_df),
                    "key_relationships": self._check_key_relationships(original_df, cleaned_df)
                },
                "quality_improvements": {
                    "missing_values_reduced": self._check_missing_values_improvement(original_df, cleaned_df),
                    "duplicates_removed": self._check_duplicates_removal(original_df, cleaned_df),
                    "data_consistency": self._check_data_consistency(cleaned_df)
                }
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate validation report: {e}")
            return {"error": str(e)}
    
    def _check_data_type_preservation(self, original_df: pd.DataFrame, cleaned_df: pd.DataFrame) -> bool:
        """Check if data types were preserved during cleaning."""
        try:
            original_dtypes = set(original_df.dtypes.astype(str))
            cleaned_dtypes = set(cleaned_df.dtypes.astype(str))
            return len(original_dtypes - cleaned_dtypes) == 0
        except Exception:
            return False
    
    def _check_key_relationships(self, original_df: pd.DataFrame, cleaned_df: pd.DataFrame) -> bool:
        """Check if key relationships were preserved."""
        try:
            # Simple check: if we have the same columns, assume relationships are preserved
            return set(original_df.columns) == set(cleaned_df.columns)
        except Exception:
            return False
    
    def _check_missing_values_improvement(self, original_df: pd.DataFrame, cleaned_df: pd.DataFrame) -> bool:
        """Check if missing values were reduced."""
        try:
            original_missing = original_df.isnull().sum().sum()
            cleaned_missing = cleaned_df.isnull().sum().sum()
            return cleaned_missing <= original_missing
        except Exception:
            return False
    
    def _check_duplicates_removal(self, original_df: pd.DataFrame, cleaned_df: pd.DataFrame) -> bool:
        """Check if duplicates were removed."""
        try:
            original_duplicates = original_df.duplicated().sum()
            cleaned_duplicates = cleaned_df.duplicated().sum()
            return cleaned_duplicates <= original_duplicates
        except Exception:
            return False
    
    def _check_data_consistency(self, cleaned_df: pd.DataFrame) -> bool:
        """Check data consistency in cleaned DataFrame."""
        try:
            # Check for any remaining obvious inconsistencies
            for column in cleaned_df.columns:
                if cleaned_df[column].dtype == 'object':
                    # Check for mixed case in string columns
                    if cleaned_df[column].str.len().nunique() > 1:
                        return False
            return True
        except Exception:
            return False

class CodeExecutor:
    """
    Executes Python code in a controlled environment.
    NOTE: This is not sandboxed and is not safe for production use with untrusted code.
    """
    def __init__(self, globals_dict: Optional[Dict[str, Any]] = None, locals_dict: Optional[Dict[str, Any]] = None):
        self.globals = globals_dict if globals_dict is not None else {}
        self.locals = locals_dict if locals_dict is not None else {}

    def _serialize_locals(self, local_scope: Dict[str, Any]) -> Dict[str, Any]:
        """Safely serialize the local scope to prevent issues with un-serializable types."""
        serialized_scope = {}
        for key, value in local_scope.items():
            if key.startswith("__"): continue # Ignore built-in variables
            if isinstance(value, (types.ModuleType, types.FunctionType)): continue
            
            try:
                # Attempt to serialize, fallback to string representation
                json.dumps(value) 
                serialized_scope[key] = value
            except (TypeError, OverflowError):
                if isinstance(value, pd.DataFrame):
                    # For DataFrames, provide a summary instead of full data
                    serialized_scope[key] = f"DataFrame(shape={value.shape}, columns={value.columns.tolist()})"
                else:
                    serialized_scope[key] = str(value)

        return serialized_scope

    def execute(self, code: str) -> Dict[str, Any]:
        """
        Executes the code and returns the output, error, and local variables.
        This version provides a detailed traceback on exceptions.
        """
        stdout = io.StringIO()
        stderr = io.StringIO()
        
        try:
            # We keep the redirectors to capture non-fatal output and print statements
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore")
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    exec(code, self.globals, self.locals)

            error_output = stderr.getvalue()
            if error_output:
                return {"output": stdout.getvalue(), "error": error_output, "locals": self.locals}
            
            return {"output": stdout.getvalue(), "error": None, "locals": self.locals}
        
        except Exception:
            # --- ENHANCED TRACEBACK GENERATION ---
            exc_type, exc_value, exc_traceback = sys.exc_info()
            
            # Split the generated code into a list of lines
            code_lines = code.split('\n')
            
            # Format the traceback to be more readable and informative
            formatted_traceback_lines = []
            tb_frames = traceback.extract_tb(exc_traceback)
            
            formatted_traceback_lines.append("Traceback (most recent call last):")
            for frame in tb_frames:
                # For each frame in the traceback, add filename and function info
                formatted_traceback_lines.append(f'  File "{frame.filename}", line {frame.lineno}, in {frame.name}')
                
                # This is the key part: If the error is in our generated code...
                if frame.filename == "<string>" and 1 <= frame.lineno <= len(code_lines):
                    # ...add the actual line of code that failed.
                    line_of_code = code_lines[frame.lineno - 1]
                    formatted_traceback_lines.append(f"    -> {line_of_code.strip()}")

            # Add the final exception message
            formatted_traceback_lines.append(f"{exc_type.__name__}: {exc_value}")
            
            rich_error_message = "\n".join(formatted_traceback_lines)

            return {"output": stdout.getvalue(), "error": rich_error_message, "locals": self.locals}

class LLMCodeValidator:
    """Uses an LLM to iteratively validate and fix Python code."""
    def __init__(self, executor: CodeExecutor, llm_client: str, llm_provider: str, model: str):
        self.executor = executor
        self.llm_client = llm_client
        self.llm_provider = llm_provider
        self.model = model

    def _extract_python_code(self, llm_response: str) -> str:
        """Extracts Python code from an LLM response, handling markdown code blocks."""
        if "```python" in llm_response:
            return llm_response.split("```python\n")[1].split("```")[0].strip()
        elif "```" in llm_response:
            return llm_response.split("```\n")[1].split("```")[0].strip()
        return llm_response.strip()

    def run_with_validation(self, goal, df_head_str, code: str, user_prompt_template: Callable, system_prompt: Optional[str] = None, max_retries: int = 2) -> Dict[str, Any]:
        """Runs code, and if it fails, asks an LLM to fix it based on the error."""
        current_code = code
        for attempt in range(max_retries + 1):
            result = self.executor.execute(current_code)
            
            if result["error"] is None:
                return result  # Success
            
            if attempt >= max_retries:
                break # ToDo - Max retries exceeded, return the last error

            # Prepare prompt for the LLM to fix the code
            error_feedback = result["error"]
            print("-------------------------------------------------")
            print("Error feedback for LLM:", error_feedback)
            print("-------------------------------------------------")
            user_prompt = user_prompt_template(goal=goal, df_head_str=df_head_str, code=current_code, error=error_feedback)
            messages = [{"role": "user", "content": user_prompt}]
            if system_prompt:
                messages.insert(0, {"role": "system", "content": system_prompt})
            
            # Call LLM to get the corrected code
            response, _ = self.llm_client.route_to(
                self.llm_provider,
                configuration={"messages": messages},
                model=self.model
            )
            
            current_code = self._extract_python_code(response)

        return {"output": "", "error": f"Max retries exceeded. Last error: {result.get('error', 'Unknown')}", "locals": {}}
