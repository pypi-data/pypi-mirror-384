"""
Configuration management for the Cleaning Agent.
"""

import os
from typing import Dict, Any, Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field


class CleaningConfig(BaseSettings):
    """Configuration for the Cleaning Agent."""
    
    # Model configuration - now uses sfn_blueprint's centralized approach
    model_name: str = Field(os.getenv("LLM_MODEL", "gpt-4.1-mini"), description="LLM model to use for cleaning decisions (auto = let sfn_blueprint choose)")
    model_api_key: Optional[str] = Field(os.getenv("LLM_API_KEY", ""), description="API key for the LLM model (handled by sfn_blueprint)")
    model_temperature: float = Field(default=0.1, description="Temperature for LLM responses (handled by sfn_blueprint)")
    model_max_tokens: int = Field(default=2000, description="Maximum tokens for LLM responses (handled by sfn_blueprint)")
    
    # AI Provider configuration - centralized settings
    ai_provider: str = Field(default="openai", description="AI provider to use (openai, anthropic, cortex)")
    ai_task_type: str = Field(default="suggestions_generator", description="Task type for AI requests")
    
    # Cleaning configuration
    max_rows_per_batch: int = Field(default=10000, description="Maximum rows to process in one batch")
    enable_parallel_processing: bool = Field(default=True, description="Enable parallel data processing")
    cleaning_strategy: str = Field(default="auto", description="Cleaning strategy: auto, conservative, aggressive")
    handle_outliers: bool = Field(default=True, description="Enable outlier detection and handling")
    
    # Data quality thresholds
    min_data_quality_score: float = Field(default=0.7, description="Minimum acceptable data quality score")
    max_missing_percentage: float = Field(default=0.3, description="Maximum acceptable missing data percentage")
    max_duplicate_percentage: float = Field(default=0.1, description="Maximum acceptable duplicate data percentage")
    
    # Output configuration
    output_format: str = Field(default="csv", description="Output format: csv, xlsx, json, parquet")
    include_cleaning_report: bool = Field(default=True, description="Include detailed cleaning report")
    backup_original_data: bool = Field(default=True, description="Backup original data before cleaning")
    
    # Logging configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    enable_console_logging: bool = Field(default=True, description="Enable console logging")
    
    # Performance configuration
    cache_enabled: bool = Field(default=True, description="Enable caching for repeated operations")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    
    class Config:
        env_prefix = "CLEANING_AGENT_"
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields to prevent validation errors from Flask app environment variables
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_environment_variables()
    
    def _load_environment_variables(self):
        """Load configuration from environment variables.
        
        Environment variables should be prefixed with CLEANING_AGENT_ followed by the uppercase field name.
        For example, CLEANING_AGENT_MODEL_NAME=test will set model_name="test"
        """
        # First try to get model API key from standard environment variables
        if not self.model_api_key:
            self.model_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("CLEANING_AGENT_MODEL_API_KEY")
        
        # Load other configuration from environment variables
        for field_name, field_info in self.__class__.model_fields.items():
            env_var = f"CLEANING_AGENT_{field_name.upper()}"
            if env_var not in os.environ:
                continue
                
            value = os.environ[env_var]
            field_type = field_info.annotation
            
            # Convert the value to the correct type
            try:
                if field_type == bool:
                    # Handle boolean values (accepts true/false, yes/no, 1/0)
                    if isinstance(value, str):
                        value = value.lower() in ('true', 'yes', '1')
                elif field_type == int:
                    value = int(value)
                elif field_type == float:
                    value = float(value)
                elif field_type == str:
                    value = str(value)
                
                setattr(self, field_name, value)
                
            except (ValueError, TypeError) as e:
                import logging
                logging.warning(
                    f"Failed to set {field_name} from environment variable {env_var}. "
                    f"Expected type {field_type}, got value: {value}. Error: {str(e)}"
                )

    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration for LLM client."""
        return {
            "model_name": self.model_name,
            "api_key": self.model_api_key,
            "temperature": self.model_temperature,
            "max_tokens": self.model_max_tokens,
        }
    
    def get_cleaning_config(self) -> Dict[str, Any]:
        """Get cleaning configuration."""
        return {
            "max_rows_per_batch": self.max_rows_per_batch,
            "enable_parallel_processing": self.enable_parallel_processing,
            "cleaning_strategy": self.cleaning_strategy,
            "min_data_quality_score": self.min_data_quality_score,
            "max_missing_percentage": self.max_missing_percentage,
            "max_duplicate_percentage": self.max_duplicate_percentage,
        }
    
    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration."""
        return {
            "output_format": self.output_format,
            "include_cleaning_report": self.include_cleaning_report,
            "backup_original_data": self.backup_original_data,
        }


def get_config() -> CleaningConfig:
    """Get the default configuration instance."""
    return CleaningConfig()


def get_config_from_env() -> CleaningConfig:
    """Get configuration from environment variables."""
    return CleaningConfig()
