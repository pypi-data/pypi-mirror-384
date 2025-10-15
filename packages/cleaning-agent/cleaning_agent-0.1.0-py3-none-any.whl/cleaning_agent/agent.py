"""
Intelligent Data Cleaning Agent using LLM-driven approach.
"""

import logging
import json
import traceback
import pandas as pd
import numpy as np
import time
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import warnings

# Completely disable ALL pandas warnings
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)
pd.options.mode.chained_assignment = None

from .config import CleaningConfig, get_config
from .models import (
    CleaningRequest, CleaningResponse, CleaningReport, CleaningOperation,
    DataQualityIssue, DataQualityMetrics, CleaningStrategy, CleaningParameters
)
from .utils import DataQualityAnalyzer, CleaningValidator, CodeExecutor, LLMCodeValidator, extract_dataframe_profile
from .constants import (
    SYSTEM_PROMPT_DATA_ANALYSIS,
    SYSTEM_PROMPT_CLEANING_PLAN,
    SYSTEM_PROMPT_CLEANING_SUMMARY,
    format_data_analysis_prompt,
    format_cleaning_plan_prompt,
    format_cleaning_summary_prompt, 
    format_data_analysis_agent_prompt,
    format_data_analysis_agent_code_fixer_prompt,
    format_cleaning_agent_prompt,
    format_cleaning_agent_code_fixer_prompt
)
import sfn_blueprint
from sfn_blueprint import SFNConfigManager, SFNAIHandler, setup_logger
from sfn_blueprint.utils.context_utils import ContextAnalyzer, extract_context_info

class CleaningAgent:
    """
    Intelligent agent for data cleaning and standardization using sfn_blueprint.
    
    Uses LLM to:
    1. Analyze data structure and content
    2. Identify cleaning needs dynamically
    3. Create customized cleaning plans
    4. Execute intelligent data transformations
    """
    def __init__(self, model_name: str = "auto", config: Optional[CleaningConfig] = None):
        """Initialize the Cleaning Agent."""
        self.config = config or get_config()
        # Use sfn_blueprint's centralized model selection instead of hardcoded names
        self.model_name = get_config().model_name
        self.agent_type = "cleaning_agent"
        
        # Set up logging first using sfn_blueprint
        try:
            logger_result = setup_logger(__name__)
            # setup_logger returns (logger, handler) tuple
            if isinstance(logger_result, tuple):
                self.logger = logger_result[0]
            else:
                self.logger = logger_result
        except Exception as e:
            # Fallback to basic logging if sfn_blueprint setup fails
            import logging
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(__name__)
            self.logger.info(f"Using fallback logging due to: {e}")
        
        # Initialize sfn_blueprint components with error handling
        self.llm_handler = None  # Always define llm_handler, even if SFNAIHandler fails
        try:
            self.config_manager = SFNConfigManager()
        except Exception as e:
            self.logger.warning(f"Could not initialize SFNConfigManager: {e}")
            self.config_manager = None
            
        try:
            self.llm_handler = SFNAIHandler()
        except Exception as e:
            self.logger.warning(f"Could not initialize SFNAIHandler: {e}")
            self.llm_handler = None
            
        try:
            self.data_loader = sfn_blueprint.SFNDataLoader()
        except Exception as e:
            self.logger.warning(f"Could not initialize SFNDataLoader: {e}")
            self.data_loader = None
            
        # try:
        #     self.data_processor = sfn_blueprint.SFNDataPostProcessor()
        # except Exception as e:
        #     self.logger.warning(f"Could not initialize SFNDataPostProcessor: {e}")
        #     self.data_processor = None
            
        self.logger.info(f"Cleaning Agent initialized with model: {model_name}")
        
        # Initialize components
        self.quality_analyzer = DataQualityAnalyzer()
        self.validator = CleaningValidator()
    
    def analyze_and_clean_table(self, table_data: pd.DataFrame, table_name: str, 
                              problem_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Intelligently analyze and clean a table using LLM-driven approach with enhanced context awareness.
        
        Args:
            table_data: DataFrame to clean
            table_name: Name of the table
            problem_context: Context about the problem being solved (can include enriched_context)
            
        Returns:
            Dictionary containing cleaned data and comprehensive analysis
        """
        self.logger.info(f"Starting intelligent data cleaning for table: {table_name}")
        
        # Log context information for debugging
        if problem_context:
            if 'enriched_context' in problem_context:
                self.logger.info("Received enriched context from problem_orchestrator")
                # Log key context information   
                enriched = problem_context['enriched_context']
                if hasattr(enriched, 'domain_knowledge') and hasattr(enriched.domain_knowledge, 'domain'):
                    self.logger.info(f"Domain: {enriched.domain_knowledge.domain}")
                if hasattr(enriched, 'workflow_context') and hasattr(enriched.workflow_context, 'goal'):
                    self.logger.info(f"Workflow Goal: {enriched.workflow_context.goal}")
            else:
                self.logger.info("Received basic problem context")
        else:
            self.logger.info("No problem context provided")
        
        try:
            # Step 1: Analyze the data structure and content
            data_analysis = self._analyze_table_structure(table_data, table_name)
            
            # Step 2: Generate cleaning plan using LLM with enhanced context
            cleaning_plan = self._generate_cleaning_plan(data_analysis, problem_context)
            
            # Step 3: Execute the cleaning plan
            cleaned_data, execution_summary = self._execute_cleaning_plan(
                table_data, cleaning_plan, table_name
            )
            
            # Step 4: Generate final summary
            final_summary = self._generate_cleaning_summary(
                data_analysis, cleaning_plan, execution_summary, table_name
            )
            
            return {
                "cleaned_data": cleaned_data,
                "cleaning_plan": cleaning_plan,
                "execution_summary": execution_summary,
                "final_summary": final_summary,
                "data_analysis": data_analysis
            }
            
        except Exception as e:
            error_msg = f"Error in intelligent data cleaning: {str(e)}"
            self.logger.error(error_msg)
            return {
                "error": error_msg,
                "cleaned_data": table_data,  # Return original data on error
                "cleaning_plan": {},
                "execution_summary": {"status": "failed", "error": error_msg}
            }

    def _analyze_table_structure(self, table_data: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """Analyze table structure using LLM via sfn_blueprint."""
        basic_analysis = {
            "table_name": table_name,
            "shape": table_data.shape,
            "columns": list(table_data.columns),
            "dtypes": table_data.dtypes.to_dict(),
            "null_counts": table_data.isnull().sum().to_dict(),
            "sample_data": table_data.head(3).to_dict()
        }
        
        # Try to use LLM analysis if available
        if self.llm_handler is not None:
            try:
                # Use sfn_blueprint's centralized model configuration
                # This automatically selects the best available model and provider
                prompt = format_data_analysis_prompt(
                    table_name=table_name,
                    shape=table_data.shape,
                    columns=list(table_data.columns),
                    data_types=table_data.dtypes.to_dict(),
                    null_counts=table_data.isnull().sum().to_dict(),
                    sample_data=table_data.head(3).to_dict()
                )
                
                # Use sfn_blueprint's centralized approach with supported provider
                # Get the model name from centralized configuration using config values
                model_config = sfn_blueprint.MODEL_CONFIG.get(self.config.ai_task_type, {}).get(self.config.ai_provider, {})
                model_name = model_config.get('model', 'gpt-4o-mini')
                
                response = self.llm_handler.route_to(
                    self.config.ai_provider,  # Use provider from config
                    configuration={
                        "messages": [{"role": "user", "content": prompt}]
                    },
                    model=model_name  # Use the centralized model name
                )
                
                # route_to returns (response, cost_summary) tuple
                if isinstance(response, tuple):
                    llm_response = response[0]
                else:
                    llm_response = response
                
                # Handle the new response format from sfn_blueprint
                if hasattr(llm_response, 'get'):
                    # Try the new format first
                    if 'choices' in llm_response:
                        content = llm_response.get('choices', [{}])[0].get('message', {}).get('content', '')
                    else:
                        # Fallback to direct content access
                        content = llm_response.get('content', str(llm_response))
                else:
                    # If it's not a dict-like object, convert to string
                    content = str(llm_response)
                
                basic_analysis["llm_analysis"] = content
                return basic_analysis
                
            except Exception as e:
                self.logger.warning(f"LLM analysis failed, using basic analysis: {e}")
        else:
            self.logger.info("LLM handler not available, using basic analysis only")
            
        return basic_analysis

    def _generate_cleaning_plan(self, data_analysis: Dict[str, Any], problem_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate cleaning plan using LLM via sfn_blueprint with enhanced context analysis."""
        basic_plan = {
            "cleaning_steps": "Basic cleaning plan: Remove nulls, standardize data types, handle duplicates",
            "generated_at": datetime.now().isoformat()
        }
        
        # Try to use enhanced context analysis if available
        try:
            # Extract structured context information using our new utilities
            if problem_context and isinstance(problem_context, dict):
                # Check if this is enriched context from problem_orchestrator
                if 'enriched_context' in problem_context:
                    enriched_context = problem_context['enriched_context']
                    self.logger.info("Using enriched context from problem_orchestrator")
                    
                    # Extract structured context info
                    context_info = extract_context_info(problem_context)
                    
                    # Get context-aware recommendations for cleaning agent
                    context_analyzer = ContextAnalyzer()
                    recommendations = context_analyzer.get_context_aware_recommendations(context_info, 'cleaning_agent')
                    
                    # Log context utilization
                    context_analyzer.log_context_usage(context_info, 'cleaning_agent', [
                        'domain', 'workflow_goal', 'data_sensitivity', 'compliance_requirements'
                    ])
                    
                    # Use recommendations to enhance the cleaning plan
                    enhanced_plan = self._create_enhanced_cleaning_plan(data_analysis, context_info, recommendations)
                    return enhanced_plan
                    
                else:
                    # Basic problem context - use existing logic
                    self.logger.info("Using basic problem context")
                    return self._generate_basic_cleaning_plan(data_analysis, problem_context)
            else:
                # No context provided - use basic plan
                self.logger.info("No problem context provided, using basic cleaning plan")
                return basic_plan
                
        except Exception as e:
            self.logger.warning(f"Enhanced context analysis failed: {e}")
            # Fallback to basic plan generation
            return self._generate_basic_cleaning_plan(data_analysis, problem_context)
    
    def _create_enhanced_cleaning_plan(self, data_analysis: Dict[str, Any], context_info: Any, recommendations: Any) -> Dict[str, Any]:
        """Create enhanced cleaning plan using context-aware recommendations."""
        try:
            # Extract domain-specific information
            domain = getattr(context_info, 'domain', 'unknown')
            data_sensitivity = getattr(context_info, 'data_sensitivity', 'medium')
            compliance_requirements = getattr(context_info, 'compliance_requirements', [])
            
            # Create domain-specific cleaning strategies
            cleaning_strategies = []
            
            # Add data processing recommendations
            if hasattr(recommendations, 'data_processing'):
                cleaning_strategies.extend(recommendations.data_processing)
            
            # Add quality check recommendations
            if hasattr(recommendations, 'quality_checks'):
                cleaning_strategies.extend(recommendations.quality_checks)
            
            # Add compliance measures
            if hasattr(recommendations, 'compliance_measures'):
                cleaning_strategies.extend(recommendations.compliance_measures)
            
            # Create enhanced plan
            enhanced_plan = {
                "cleaning_steps": f"Enhanced cleaning plan for {domain} domain",
                "domain": domain,
                "data_sensitivity": data_sensitivity,
                "compliance_requirements": compliance_requirements,
                "context_aware_strategies": cleaning_strategies,
                "data_analysis": data_analysis,
                "generated_at": datetime.now().isoformat(),
                "context_utilization": "Used enriched context for intelligent cleaning decisions"
            }
            
            self.logger.info(f"Created enhanced cleaning plan for {domain} domain with {len(cleaning_strategies)} strategies")
            return enhanced_plan
            
        except Exception as e:
            self.logger.error(f"Error creating enhanced cleaning plan: {e}")
            # Return basic plan on error
            return {
                "cleaning_steps": "Basic cleaning plan due to context analysis error",
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
    
    def _generate_basic_cleaning_plan(self, data_analysis: Dict[str, Any], problem_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate basic cleaning plan using LLM via sfn_blueprint."""
        basic_plan = {
            "cleaning_steps": "Basic cleaning plan: Remove nulls, standardize data types, handle duplicates",
            "generated_at": datetime.now().isoformat()
        }
        
        # Try to use LLM planning if available
        if self.llm_handler is not None:
            try:
                context_info = f"Problem Context: {problem_context}" if problem_context else "No specific problem context provided"
                
                prompt = format_cleaning_plan_prompt(
                    data_analysis=data_analysis,
                    context_info=context_info
                )
                
                # Use sfn_blueprint's centralized approach with supported provider
                # Get the model name from centralized configuration using config values
                model_config = sfn_blueprint.MODEL_CONFIG.get(self.config.ai_task_type, {}).get(self.config.ai_provider, {})
                model_name = model_config.get('model', 'gpt-4o-mini')
                
                response = self.llm_handler.route_to(
                    self.config.ai_provider,  # Use provider from config
                    configuration={
                        "messages": [{"role": "user", "content": prompt}]
                    },
                    model=model_name  # Use the centralized model name
                )
                
                # route_to returns (response, cost_summary) tuple
                if isinstance(response, tuple):
                    llm_response = response[0]
                else:
                    llm_response = response
                
                # Handle the new response format from sfn_blueprint
                if hasattr(llm_response, 'get'):
                    # Try the new format first
                    if 'choices' in llm_response:
                        content = llm_response.get('choices', [{}])[0].get('message', {}).get('content', '')
                    else:
                        # Fallback to direct content access
                        content = llm_response.get('content', str(llm_response))
                else:
                    # If it's not a dict-like object, convert to string
                    content = str(llm_response)
                
                return {
                    "cleaning_steps": content,
                    "generated_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.warning(f"LLM plan generation failed: {e}")
        else:
            self.logger.info("LLM handler not available, using basic cleaning plan")
            
        return basic_plan

    def _execute_cleaning_plan(self, table_data: pd.DataFrame, cleaning_plan: Dict[str, Any], table_name: str) -> tuple:
        """Execute the cleaning plan on the data."""
        try:
            # For now, implement basic cleaning based on common patterns
            # In the future, this could parse LLM-generated plans and execute them
            cleaned_data = table_data.copy()
            execution_summary = {"steps_executed": [], "errors": []}
            
            # Basic cleaning operations
            for col in cleaned_data.columns:
                if cleaned_data[col].dtype == 'object':
                    # Handle string columns
                    cleaned_data[col] = cleaned_data[col].astype(str).str.strip()
                    cleaned_data[col] = cleaned_data[col].replace('', np.nan)
                
                # Handle numeric columns
                if pd.api.types.is_numeric_dtype(cleaned_data[col]):
                    # Remove outliers using IQR method
                    Q1 = cleaned_data[col].quantile(0.25)
                    Q3 = cleaned_data[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    cleaned_data[col] = cleaned_data[col].clip(lower_bound, upper_bound)
            
            execution_summary["steps_executed"].append("Basic data cleaning applied")
            execution_summary["status"] = "completed"
            
            return cleaned_data, execution_summary
            
        except Exception as e:
            self.logger.error(f"Error executing cleaning plan: {e}")
            execution_summary = {"status": "failed", "error": str(e)}
            return table_data, execution_summary

    def _generate_cleaning_summary(self, data_analysis: Dict[str, Any], cleaning_plan: Dict[str, Any], 
                                 execution_summary: Dict[str, Any], table_name: str) -> Dict[str, Any]:
        """Generate final cleaning summary using LLM."""
        try:
            prompt = format_cleaning_summary_prompt(
                table_name=table_name,
                data_analysis=data_analysis,
                cleaning_plan=cleaning_plan,
                execution_summary=execution_summary
            )
            
            # Use sfn_blueprint's centralized approach with supported provider
            # Get the model name from centralized configuration using config values
            model_config = sfn_blueprint.MODEL_CONFIG.get(self.config.ai_task_type, {}).get(self.config.ai_provider, {})
            model_name = model_config.get('model', 'gpt-4o-mini')
            
            response = self.llm_handler.route_to(
                self.config.ai_provider,  # Use provider from config
                configuration={
                    "messages": [{"role": "user", "content": prompt}]
                },
                model=model_name  # Use the centralized model name
            )
            
            # route_to returns (response, cost_summary) tuple
            if isinstance(response, tuple):
                llm_response = response[0]
            else:
                llm_response = response
            
            # Handle the new response format from sfn_blueprint
            if hasattr(llm_response, 'get'):
                # Try the new format first
                if 'choices' in llm_response:
                    content = llm_response.get('choices', [{}])[0].get('message', {}).get('content', '')
                else:
                    # Fallback to direct content access
                    content = llm_response.get('content', str(llm_response))
            else:
                # If it's not a dict-like object, convert to string
                content = str(llm_response)
            
            return {
                "summary": content,
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.warning(f"LLM summary generation failed: {e}")
            return {
                "summary": "Basic cleaning summary (LLM unavailable)",
                "generated_at": datetime.now().isoformat()
            }

    def clean_data(
        self, 
        data: Union[pd.DataFrame, Dict[str, Any], str], 
        goal: str, 
        cleaning_parameters: Optional[Dict[str, Any]] = None
    ) -> CleaningResponse:
        """
        Clean the provided data according to the specified goal.
        
        Args:
            data: Input data (DataFrame, dict, or file path)
            goal: Cleaning goal or objective
            cleaning_parameters: Optional cleaning parameters
            
        Returns:
            CleaningResponse with cleaned data and report
        """
        start_time = time.time()
        operation_id = str(uuid.uuid4())
        
        try:
            self.logger.info(f"Starting data cleaning operation {operation_id} with goal: {goal}")
            
            # Parse input data
            df = self._parse_input_data(data)
            print('df', df, type(df))
            if df is None:
                return CleaningResponse(
                    success=False,
                    message="Failed to parse input data",
                    errors=["Invalid input data format"]
                )
            
            # Create cleaning request
            request = CleaningRequest(
                data=data,
                goal=goal,
                cleaning_parameters=cleaning_parameters or {}
            )
            
            # Analyze data quality
            quality_metrics = self.quality_analyzer.analyze_data_quality(df)
            print('\n quality metrics', quality_metrics)
            self.logger.info(f"Data quality analysis completed. Score: {quality_metrics.quality_score:.2f}")
            
            # Detect data quality issues
            issues = self.quality_analyzer.detect_issues(df, quality_metrics)
            print('\n issues', issues)
            self.logger.info(f"Detected {len(issues)} data quality issues")
            
            # Generate cleaning strategies
            strategies = self._generate_cleaning_strategies(df, issues, goal, quality_metrics) 
            print()
            self.logger.info(f"Generated {len(strategies)} cleaning strategies")

            # Apply cleaning strategies
            cleaned_df, operations = self._apply_cleaning_strategies(df, strategies, cleaning_parameters)
            
            # Validate cleaned data
            validation_result = self.validator.validate_cleaned_data(cleaned_df, quality_metrics)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Generate cleaning report
            report = self._generate_cleaning_report(
                operation_id, df, cleaned_df, issues, operations, 
                quality_metrics, validation_result, execution_time
            )
            
            # Prepare response
            response = CleaningResponse(
                success=True,
                cleaned_data=cleaned_df,
                report=report,
                message=f"Data cleaning completed successfully. Quality improved from {quality_metrics.quality_score:.2f} to {validation_result.final_quality_score:.2f}",
                metadata={
                    "operation_id": operation_id,
                    "execution_time": execution_time,
                    "rows_processed": len(df),
                    "strategies_applied": len(strategies)
                }
            )
            
            self.logger.info(f"Data cleaning operation {operation_id} completed successfully in {execution_time:.2f}s")
            return response
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Data cleaning operation {operation_id} failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            return CleaningResponse(
                success=False,
                message=error_msg,
                errors=[str(e)],
                metadata={
                    "operation_id": operation_id,
                    "execution_time": execution_time
                }
            )
    
    def _parse_input_data(self, data: Union[pd.DataFrame, Dict[str, Any], str]) -> Optional[pd.DataFrame]:
        """Parse input data into a pandas DataFrame using sfn_blueprint data loader."""
        try:
            if isinstance(data, pd.DataFrame):
                return data.copy()
            elif isinstance(data, dict):
                return pd.DataFrame(data)
            elif isinstance(data, str):
                # Use sfn_blueprint data loader for file operations
                if self.data_loader is None:
                    self.logger.warning("SFNDataLoader not available, using fallback pandas loading")
                    # Fallback to pandas for file loading
                    if data.endswith('.csv'):
                        return pd.read_csv(data)
                    elif data.endswith('.xlsx') or data.endswith('.xls'):
                        return pd.read_excel(data)
                    elif data.endswith('.json'):
                        return pd.read_json(data)
                    else:
                        self.logger.warning(f"Unsupported file format for fallback: {data}")
                        return None
                else:
                    # Use sfn_blueprint data loader
                    if data.endswith('.csv'):
                        return self.data_loader.load_csv(data)
                    elif data.endswith('.xlsx') or data.endswith('.xls'):
                        return self.data_loader.load_excel(data)
                    elif data.endswith('.json'):
                        return self.data_loader.load_json(data)
                    elif data.endswith('.parquet'):
                        return self.data_loader.load_parquet(data)
                    else:
                        self.logger.warning(f"Unsupported file format: {data}")
                        return None
            else:
                self.logger.warning(f"Unsupported data type: {type(data)}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to parse input data: {e}")
            return None
        
    def _generate_cleaning_strategies(
        self, 
        df: pd.DataFrame, 
        issues: List[DataQualityIssue], 
        goal: str, 
        quality_metrics: DataQualityMetrics
    ) -> List[CleaningStrategy]:
        """Generate cleaning strategies based on detected issues and goal."""
        strategies = []
        
        # Handle missing values
        if any(issue.issue_type == "missing_values" for issue in issues):
            strategies.append(CleaningStrategy(
                strategy_name="handle_missing_values",
                description="Handle missing values using appropriate strategies",
                applicable_issues=["missing_values"],
                confidence_score=0.9,
                estimated_impact="high",
                implementation_complexity="medium"
            ))
        
        # Handle duplicates
        if quality_metrics.duplicate_percentage > 0:
            strategies.append(CleaningStrategy(
                strategy_name="remove_duplicates",
                description="Remove duplicate rows to improve data quality",
                applicable_issues=["duplicate_rows"],
                confidence_score=0.95,
                estimated_impact="high",
                implementation_complexity="low"
            ))
        
        # Standardize data types
        strategies.append(CleaningStrategy(
            strategy_name="standardize_data_types",
            description="Standardize data types for consistency",
            applicable_issues=["data_type_inconsistency"],
            confidence_score=0.8,
            estimated_impact="medium",
            implementation_complexity="low"
        ))
        
        # Handle outliers (if enabled)
        if self.config.handle_outliers:
            strategies.append(CleaningStrategy(
                strategy_name="handle_outliers",
                description="Detect and handle outliers in numerical columns",
                applicable_issues=["outliers"],
                confidence_score=0.7,
                estimated_impact="medium",
                implementation_complexity="high"
            ))
        
        return strategies
    
    def _apply_cleaning_strategies(
        self, 
        df: pd.DataFrame, 
        strategies: List[CleaningStrategy], 
        parameters: Optional[Dict[str, Any]]
    ) -> tuple[pd.DataFrame, List[CleaningOperation]]:
        """Apply cleaning strategies to the data."""
        cleaned_df = df.copy()
        operations = []
        
        for strategy in strategies:
            operation = CleaningOperation(
                operation_id=str(uuid.uuid4()),
                operation_type=strategy.strategy_name,
                description=strategy.description,
                parameters={"strategy": strategy.dict()},
                status="in_progress",
                start_time=datetime.utcnow()
            )
            
            try:
                if strategy.strategy_name == "handle_missing_values":
                    cleaned_df = self._handle_missing_values(cleaned_df, parameters)
                elif strategy.strategy_name == "remove_duplicates":
                    cleaned_df = self._remove_duplicates(cleaned_df, parameters)
                elif strategy.strategy_name == "standardize_data_types":
                    cleaned_df = self._standardize_data_types(cleaned_df, parameters)
                elif strategy.strategy_name == "handle_outliers":
                    cleaned_df = self._handle_outliers(cleaned_df, parameters)
                
                operation.status = "completed"
                operation.end_time = datetime.utcnow()
                operation.rows_affected = len(df) - len(cleaned_df)
                
            except Exception as e:
                operation.status = "failed"
                operation.end_time = datetime.utcnow()
                operation.error_message = str(e)
                self.logger.error(f"Strategy {strategy.strategy_name} failed: {e}")
            
            operations.append(operation)
        
        return cleaned_df, operations
    
    def _handle_missing_values(self, df: pd.DataFrame, parameters: Optional[Dict[str, Any]]) -> pd.DataFrame:
        """Handle missing values in the DataFrame."""
        cleaned_df = df.copy()
        
        for column in cleaned_df.columns:
            if cleaned_df[column].isnull().any():
                if cleaned_df[column].dtype in ['int64', 'float64']:
                    # For numerical columns, fill with median
                    cleaned_df[column] = cleaned_df[column].fillna(cleaned_df[column].median())
                elif cleaned_df[column].dtype == 'object':
                    # For categorical columns, fill with mode
                    mode_value = cleaned_df[column].mode().iloc[0] if not cleaned_df[column].mode().empty else "Unknown"
                    cleaned_df[column] = cleaned_df[column].fillna(mode_value)
        
        return cleaned_df
    
    def _remove_duplicates(self, df: pd.DataFrame, parameters: Optional[Dict[str, Any]]) -> pd.DataFrame:
        """Remove duplicate rows from the DataFrame."""
        return df.drop_duplicates()
    
    def _standardize_data_types(self, df: pd.DataFrame, parameters: Optional[Dict[str, Any]]) -> pd.DataFrame:
        """Standardize data types in the DataFrame."""
        cleaned_df = df.copy()
        
        for column in cleaned_df.columns:
            # Try to convert to appropriate numeric type
            try:
                if cleaned_df[column].dtype == 'object':
                    # Try to convert to numeric
                    pd.to_numeric(cleaned_df[column], errors='raise')
                    cleaned_df[column] = pd.to_numeric(cleaned_df[column], errors='coerce')
            except (ValueError, TypeError):
                # Keep as object if conversion fails
                pass
        
        return cleaned_df
    
    def _handle_outliers(self, df: pd.DataFrame, parameters: Optional[Dict[str, Any]]) -> pd.DataFrame:
        """Handle outliers in numerical columns."""
        cleaned_df = df.copy()
        
        for column in cleaned_df.columns:
            if cleaned_df[column].dtype in ['int64', 'float64']:
                Q1 = cleaned_df[column].quantile(0.25)
                Q3 = cleaned_df[column].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                # Cap outliers instead of removing them
                cleaned_df[column] = cleaned_df[column].clip(lower=lower_bound, upper=upper_bound)
        
        return cleaned_df
    
    def _generate_cleaning_report(
        self,
        operation_id: str,
        original_df: pd.DataFrame,
        cleaned_df: pd.DataFrame,
        issues: List[DataQualityIssue],
        operations: List[CleaningOperation],
        quality_metrics: DataQualityMetrics,
        validation_result: Any,
        execution_time: float
    ) -> CleaningReport:
        """Generate a comprehensive cleaning report."""
        return CleaningReport(
            report_id=operation_id,
            timestamp=datetime.utcnow(),
            data_summary={
                "original_shape": original_df.shape,
                "cleaned_shape": cleaned_df.shape,
                "rows_removed": len(original_df) - len(cleaned_df),
                "columns_processed": len(original_df.columns)
            },
            issues_detected=issues,
            cleaning_operations=operations,
            quality_metrics={
                "original_quality_score": quality_metrics.quality_score,
                "final_quality_score": getattr(validation_result, 'final_quality_score', quality_metrics.quality_score),
                "improvement": getattr(validation_result, 'final_quality_score', quality_metrics.quality_score) - quality_metrics.quality_score
            },
            recommendations=[
                "Consider implementing data validation at the source",
                "Set up automated data quality monitoring",
                "Review cleaning strategies periodically",
                "Document data cleaning procedures"
            ],
            execution_time=execution_time
        )
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and supported operations."""
        return {
            "agent_name": "cleaning_agent",
            "version": "0.1.0",
            "capabilities": [
                "missing_value_handling",
                "duplicate_removal",
                "data_type_standardization",
                "outlier_detection",
                "data_quality_analysis",
                "intelligent_strategy_generation"
            ],
            "supported_data_formats": ["csv", "xlsx", "json", "pandas_dataframe"],
            "supported_cleaning_strategies": [
                "handle_missing_values",
                "remove_duplicates", 
                "standardize_data_types",
                "handle_outliers"
            ],
            "configuration_options": self.config.dict()
        }
    
    def _fix_datetime_serialization(self, data: Any) -> Any:
        """Fix datetime serialization issues in response data"""
        if isinstance(data, dict):
            fixed_data = {}
            for key, value in data.items():
                if hasattr(value, 'isoformat'):  # Check if it's a datetime-like object
                    fixed_data[key] = value.isoformat()
                elif hasattr(value, '__dict__'):  # Handle custom objects
                    fixed_data[key] = self._fix_datetime_serialization(value.__dict__)
                elif isinstance(value, (dict, list)):
                    fixed_data[key] = self._fix_datetime_serialization(value)
                else:
                    fixed_data[key] = value
            return fixed_data
        elif isinstance(data, list):
            return [self._fix_datetime_serialization(item) for item in data]
        elif hasattr(data, '__dict__'):  # Handle custom objects
            return self._fix_datetime_serialization(data.__dict__)
        else:
            return data



# -----------------------------------------------------

    ## To clean data df with rule based cleaning - (involves - python, pandas) 
    def execute_cleaning_operation(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a cleaning task with the given task data.
        This method provides a standard interface for the orchestrator.
        
        Args:
            task_data: Dictionary containing task information
                - file: File path or data source
                - problem_context: Context about the cleaning task
                - goal: Optional cleaning goal (defaults to problem_context)
                - cleaning_parameters: Optional cleaning parameters
                
        Returns:
            Dictionary with execution results
        """
        try:
            # Extract parameters from task_data
            data = task_data.get('file', task_data.get('data'))
            problem_context = task_data.get('problem_context', 'Data cleaning task')
            goal = task_data.get('goal', problem_context)
            cleaning_parameters = task_data.get('cleaning_parameters', {})
            
            # Execute the cleaning operation
            response = self.clean_data(data, goal, cleaning_parameters)
            
            # Convert response to orchestrator format
            if response.success:
                # Convert report to dict and fix datetime serialization
                report_dict = response.report.__dict__ if hasattr(response.report, '__dict__') else str(response.report)
                if isinstance(report_dict, dict):
                    report_dict = self._fix_datetime_serialization(report_dict)
                
                # Convert all complex objects to serializable format
                cleaned_data = response.cleaned_data.to_dict() if hasattr(response.cleaned_data, 'to_dict') else str(response.cleaned_data)
                metadata = self._fix_datetime_serialization(response.metadata) if response.metadata else {}
                
                # Save results to workflow storage if available
                try:
                    # Check if we have workflow storage information
                    if 'workflow_storage_path' in task_data or 'workflow_id' in task_data:
                        from sfn_blueprint import WorkflowStorageManager
                        
                        # Determine workflow storage path
                        workflow_storage_path = task_data.get('workflow_storage_path', 'outputs/workflows')
                        workflow_id = task_data.get('workflow_id', 'unknown')
                        
                        # Initialize storage manager
                        storage_manager = WorkflowStorageManager(workflow_storage_path, workflow_id)
                        
                        # Save the cleaned data and results
                        storage_result = storage_manager.save_agent_result(
                            agent_name="cleaning_agent",
                            step_name="data_cleaning",
                            data=response.cleaned_data,  # Pass the actual DataFrame
                            metadata={
                                "cleaning_report": report_dict,
                                "cleaning_goal": goal,
                                "cleaning_parameters": cleaning_parameters,
                                "data_quality_score": metadata.get('data_quality_score', 0),
                                "rows_processed": len(response.cleaned_data),
                                "columns_processed": len(response.cleaned_data.columns),
                                "execution_time": datetime.now().isoformat()
                            }
                        )
                        
                        self.logger.info(f"Cleaning results saved to workflow storage: {storage_result['files']}")
                        
                except ImportError:
                    self.logger.warning("WorkflowStorageManager not available, skipping workflow storage")
                except Exception as e:
                    self.logger.warning(f"Failed to save to workflow storage: {e}")
                
                return {
                    "success": True,
                    "result": {
                        "cleaned_data": cleaned_data,
                        "report": report_dict,
                        "message": response.message,
                        "metadata": metadata,
                        "execution_time": datetime.now().isoformat()
                    },
                    "agent": "cleaning_agent"
                }
            else:
                return {
                    "success": False,
                    "error": response.message,
                    "errors": response.errors,
                    "agent": "cleaning_agent"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Task execution failed: {str(e)}",
                "agent": "cleaning_agent"
            }


# -----------------------------------------------------

    ## To clean data df with llm based cleaning - (involves - llm, python, pandas) 
    def execute_llm_driven_cleaning_cycle(
        self, df: pd.DataFrame, 
        goal: str
    ) :
        """
        Performs a two-step, self-correcting cleaning process using LLM-generated code.
        """
        model_config = sfn_blueprint.MODEL_CONFIG.get(self.config.ai_task_type, {}).get(self.config.ai_provider, {}) #ToDo - verify this
        model_name = model_config.get('model', 'gpt-4o-mini') #ToDo - verify this
        
        # Initialize the executor and validator for this cycle
        executor = CodeExecutor(globals_dict={"pd": pd, "np": np}, locals_dict={"df": df.copy()})
        code_validator = LLMCodeValidator(executor=executor, llm_client=self.llm_handler, llm_provider=self.config.ai_provider, model=model_name)
        self.logger.info("LLM Cycle - Stage 1: Generating analysis code.")
        df_head_str = df.head(5).to_string()
        user_prompt_data_analysis = format_data_analysis_agent_prompt(goal=goal, df_head_str=df_head_str)
        analysis_response, _ = self.llm_handler.route_to(
            self.config.ai_provider,
            configuration={"messages": [{"role": "user", "content": user_prompt_data_analysis}]},
            model=model_name
        )
        self.logger.info("Executing analysis code with self-correction.")
        initial_analysis_code = code_validator._extract_python_code(analysis_response)
        analysis_result = code_validator.run_with_validation(goal=goal, df_head_str=df_head_str, code=initial_analysis_code, user_prompt_template=format_data_analysis_agent_code_fixer_prompt)

        # Check if analysis stage succeeded
        if analysis_result["error"]:
            self.logger.error(f"Analysis code execution failed after retries: {analysis_result['error']}")
            return df # Return original df on failure
        
        analysis_report_df = analysis_result["locals"].get("analysis_report_df")
        if not isinstance(analysis_report_df, pd.DataFrame):
            error_msg = "Analysis code ran but did not produce a valid 'analysis_report_df' DataFrame."
            self.logger.error(error_msg)
            return df

        self.logger.info(f"Analysis successful. Report generated with shape: {analysis_report_df.shape}")

        # --- STAGE 2: Generate and Validate Cleaning Code ---
        self.logger.info("LLM Cycle - Stage 2: Generating cleaning DataFrame based on analysis.")
        cleaning_prompt = format_cleaning_agent_prompt(
            goal=goal, df_head_str=df_head_str, analysis_report_df=analysis_report_df
        )
        cleaning_response, _ = self.llm_handler.route_to(
            self.config.ai_provider,
            configuration={"messages": [{"role": "user", "content": cleaning_prompt}]},
            model=model_name
        )
        initial_cleaning_code = code_validator._extract_python_code(cleaning_response)
        self.logger.info("Executing cleaning code with self-correction.")
        cleaning_result = code_validator.run_with_validation(goal=goal, df_head_str=df_head_str, code=initial_cleaning_code, user_prompt_template=format_cleaning_agent_code_fixer_prompt)


        if cleaning_result["error"]:
            self.logger.error(f"Cleaning code execution failed after retries: {cleaning_result['error']}")
            return df

        cleaned_df = cleaning_result["locals"].get("clean_df")
        if not isinstance(cleaned_df, pd.DataFrame):
            error_msg = "Cleaning code ran but did not return a valid DataFrame in the 'df' variable."
            self.logger.error(error_msg)
            return df

        self.logger.info("LLM-driven cleaning cycle completed successfully.")

        return cleaned_df
         
    def execute_llm_driven_cleaning_operation(self, df: pd.DataFrame, goal: str) -> pd.DataFrame:
        """
        Execute an LLM-driven cleaning cycle on the given DataFrame.
        Args:
            df: Input DataFrame
            goal: Cleaning goal
        Returns:
            Cleaned DataFrame
        """
        try:
            # Execute the cleaning cycle
            cleaned_df = self.execute_llm_driven_cleaning_cycle(df, goal)
            # Return the cleaned DataFrame
            return cleaned_df
        except Exception as e:
            self.logger.error(f"LLM-driven cleaning cycle failed: {e}")
            raise

#  ---------------------------------------------------

    ## To suggest cleaning with sql - (involves - llm, python, pandas, sql) 
    def suggest_cleaning_with_sql(
        self,
        # df: pd.DataFrame,
        sample_data: int = 5,
        columns: list = [],
        data_types: dict = {},
        computed_stats: dict = {},
        identical_column_pairs: list = [],
        domain_metadata: dict = {},
        entity_name_and_description: dict = {},
        db_name: str = "test_db",
        schema: str = "public",
        table_name: str = "table_name",
        use_case: str = "",
        ml_approach: dict = {},
        cleaning_type: str = "golden_dataset"
    ) -> Dict[str, Any]:
        """
        Suggest feature transformations (SQL) and map them to UI operations using LLM.
        Args:
            df: Input DataFrame
            use_case: Business or ML use case string
            sample_rows: Number of rows to include as sample data in the prompt
        Returns:
            Dict with keys: 'feature_suggestions' (List[SqlCleaningSuggestion]), 'operation_mappings' (List[SqlCleaningOperationMapping])
        """
        from .constants import format_sql_cleaning_suggestion_system_prompt_for_golden_dataset, \
                        format_sql_cleaning_suggestion_system_prompt, format_sql_cleaning_suggestion_user_prompt, \
                        format_sql_cleaning_suggestion_user_prompt_for_golden_dataset, format_sql_to_operation_prompt
        from .models import SqlCleaningSuggestion, SqlCleaningOperationMapping
        from .utils import extract_sample_data_sql_cleaning, validate_llm_json_output_sql_cleaning

        try:

            # sample_data = extract_sample_data_sql_cleaning(df, sample_rows=sample_rows)

            # 1. LLM: Feature Suggestion
            if cleaning_type == "golden_dataset":
                system_prompt = format_sql_cleaning_suggestion_system_prompt_for_golden_dataset(
                    db_name=db_name,
                    schema=schema,
                    table_name=table_name,
                )
                user_prompt = format_sql_cleaning_suggestion_user_prompt_for_golden_dataset(
                    db_name=db_name,
                    schema=schema,
                    table_name=table_name,
                    columns=columns,
                    sample_data=sample_data,
                    data_types=data_types,
                    # feature_dtype_dict=feature_dtype_dict,
                    domain_metadata=domain_metadata,
                    entity_name_and_description=entity_name_and_description,
                    computed_stats=computed_stats,
                    identical_column_pairs=identical_column_pairs,
                    use_case=use_case
                )
            else:
                system_prompt = format_sql_cleaning_suggestion_system_prompt(
                    db_name=db_name,
                    schema=schema,
                    table_name=table_name,
                )
                user_prompt = format_sql_cleaning_suggestion_user_prompt(
                    db_name=db_name,
                    schema=schema,
                    table_name=table_name,
                    columns=columns,
                    sample_data=sample_data,
                    data_types=data_types,
                    # feature_dtype_dict=feature_dtype_dict,
                    domain_metadata=domain_metadata,
                    entity_name_and_description=entity_name_and_description,
                    computed_stats=computed_stats,
                    identical_column_pairs=identical_column_pairs,
                    use_case=use_case,
                    ml_approach=ml_approach
                )
            # print('\n\n formatted cleaning suggestion system prompt\n', system_prompt)
            # print('\n\n formatted cleaning suggestion user prompt\n', user_prompt)
            llm_result = self.llm_handler.route_to(
                self.config.ai_provider,
                configuration={"messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]},
                model=self.model_name
            )
            # print('\n\n sql  llm_result: ', llm_result)
            # self.response = llm_result
            if isinstance(llm_result, tuple):
                response, _ = llm_result
            else:
                response = llm_result
            try:
                suggestions_dict = validate_llm_json_output_sql_cleaning(response)
            except Exception as e:
                self.logger.error(f"Failed to parse LLM feature suggestion output: {e}")
                return {"success": False, "error": f"Feature_suggest_cleaning_and_sql_operationsure suggestion LLM output invalid: {e}"}
            # print('\n\n suggestions_dict: ', suggestions_dict)
            feature_suggestions = []
            for feat_name, feat in suggestions_dict.items():
                try:
                    feature_suggestions.append(SqlCleaningSuggestion(**feat))
                except Exception:
                    # fallback if keys are not nested
                    print("Warning: missing keys in feature suggestion: ", feat_name)
                    feature_suggestions.append(SqlCleaningSuggestion(
                        feature_name=feat.get("feature_name", feat_name),
                        sql_query=feat.get("sql_query", ""),
                        explanation=feat.get("explanation", "")
                    ))

            # 2. LLM: SQL-to-Operation Mapping
            # sql_queries = [fs.dict() for fs in feature_suggestions]
            # print('\n\n sql_queries: ', sql_queries)

            # op_user_prompt = format_sql_to_operation_prompt(
            #     sql_queries=sql_queries,
            #     column_names=columns,
            #     column_dtypes=data_types
            # )
            # print('sql_to_op_prompt: ', op_prompt)
            # op_llm_result = self.llm_handler.route_to(
            #     self.config.ai_provider,
            #     configuration={"messages": [{"role": "user", "content": op_user_prompt}]},
            #     model=self.model_name
            # )
            # self.op_llm_response = op_llm_result
            # # print('op_llm_result: ', op_llm_result)
            # if isinstance(op_llm_result, tuple):
            #     op_response, _ = op_llm_result
            # else:
            #     op_response = op_llm_result
            # try:
            #     op_list = validate_llm_json_output_sql_cleaning(op_response)
            # except Exception as e:
            #     self.logger.error(f"Failed to parse LLM operation mapping output: {e}")
            #     return {"success": False, "error": f"Operation mapping LLM output invalid: {e}"}
            # operation_mappings = []
            # for op in op_list:
            #     try:
            #         operation_mappings.append(SqlCleaningOperationMapping(**op))
            #     except Exception as e:
            #         self.logger.warning(f"Invalid operation mapping entry: {op} ({e})")
            return {
                "success": True,
                "feature_suggestions": [fs.dict() for fs in feature_suggestions],
                # "operation_mappings": [op.dict() for op in operation_mappings],
            }
        except Exception as e:
            self.logger.error(f"suggest_cleaning_and_sql_operations failed: {e}")
            print(traceback.format_exc()[:1000])
            return {"success": False, "error": str(e)}

    def clean_data_with_sql(
        self,
        # df: pd.DataFrame,
        sample_data:dict,
        columns_name:list,
        data_types:dict,
        computed_stats:dict,
        identical_column_pairs:list,
        db_name: str = "test_db",
        schema: str = "public",
        table: str = "sample_table",
        domain_metadata: Dict[str, Any] = None,
        entity_name_and_description: Dict[str, Any] = None,
        use_case: str = "",
        ml_approach: Dict[str, Any] = None,
        cleaning_type: str = "golden_dataset",
    ) -> Dict[str, Any]:
        """
        Clean data using LLM-driven SQL feature suggestions and operation mapping.
        Args:
            df: Input DataFrame
            db_name: Name of the database
            schema: Schema name
            table: Table name
            use_case: Business or ML use case string
            sample_rows: Number of rows for sample data
        Returns:
            Dict with keys: 'feature_suggestions', 'operation_mappings', and input/output metadata
        """

        # profile = extract_dataframe_profile(df)
        # print('profile:\n\n', profile)
        # print("-----------------**-----------------------")
        # Call the suggest_cleaning_and_sql_operations method   
        result = self.suggest_cleaning_with_sql(
            sample_data=sample_data,
            columns=columns_name,
            data_types=data_types,
            computed_stats=computed_stats,
            identical_column_pairs=identical_column_pairs,
            domain_metadata=domain_metadata,
            entity_name_and_description=entity_name_and_description,
            db_name=db_name,
            schema=schema,
            table_name=table,
            use_case=use_case,
            ml_approach=ml_approach,
            cleaning_type=cleaning_type if cleaning_type else "golden_dataset",
        )
        print('clean_data_with_sql result: ', result, type(result))
        # Structure output as dataclasses if successful
        if result.get("success"):
            return {
                "success": True,
                "db_name": db_name,
                "schema": schema,
                "table": table,
                "feature_suggestions": result.get("feature_suggestions", []),
                # "operation_mappings": result.get("operation_mappings", []),
                # "input_shape": df.shape,
                # "columns": list(df.columns),
                "use_case": use_case,
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown error"),
                "db_name": db_name,
                "schema": schema,
                "table": table,
                "use_case": use_case,
            }

    def execute_llm_driven_cleaning_operation_with_sql(
        self,
        # df: pd.DataFrame = None,
        sample_data,
        columns_name,
        data_types,
        computed_stats,
        identical_column_pairs,
        db_name: str = "test_db",
        schema: str = "public",
        table: str = "sample_table",
        domain_metadata: Dict[str, Any] = None,
        entity_name_and_description: Dict[str, Any] = None,
        use_case: str = "",
        ml_approach: Dict[str, Any] = None,
        cleaning_type: str = "golden_dataset",
    ) -> Dict[str, Any]:
        """
        Execute the full SQL cleaning operation pipeline.
        Args:
            df: Input DataFrame (required)
            db_name: Database name (optional)
            schema: Schema name (optional)
            table: Table name (optional)
            use_case: Use case string (optional)
            sample_rows: Sample rows for LLM context (optional)
        Returns:
            Structured result dict from clean_data_with_sql
        """
        # If no DataFrame is provided, create a sample one
        try:
            
            return self.clean_data_with_sql(
                # df=df,
                sample_data=sample_data,
                columns_name=columns_name,
                data_types=data_types,
                computed_stats=computed_stats,
                identical_column_pairs=identical_column_pairs,
                db_name=db_name,
                schema=schema,
                table=table,
                domain_metadata = domain_metadata,
                entity_name_and_description = entity_name_and_description,
                use_case=use_case,
                ml_approach=ml_approach,
                cleaning_type=cleaning_type if cleaning_type else "golden_dataset",
            )

        except Exception as e:
            print(f"Error in execute_sql_cleaning_operation: {str(e)}")
            print(traceback.format_exc()[:1000])
            return {
                "success": False,
                "error": str(e),
                "db_name": db_name,
                "schema": schema,
                "table": table,
                "use_case": use_case,
            }


