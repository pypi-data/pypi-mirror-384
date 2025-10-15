#!/usr/bin/env python3
"""
Command-line interface for the Cleaning Agent.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

import pandas as pd

from .agent import CleaningAgent
from .config import get_config


def setup_logging(level: str = "INFO"):
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def load_data(file_path: str) -> pd.DataFrame:
    """Load data from various file formats."""
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if file_path.suffix.lower() == '.csv':
        return pd.read_csv(file_path)
    elif file_path.suffix.lower() in ['.xlsx', '.xls']:
        return pd.read_excel(file_path)
    elif file_path.suffix.lower() == '.json':
        return pd.read_json(file_path)
    elif file_path.suffix.lower() == '.parquet':
        return pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")


def save_data(df: pd.DataFrame, output_path: str, format: str = "csv"):
    """Save data to various file formats."""
    output_path = Path(output_path)
    
    if format.lower() == 'csv':
        df.to_csv(output_path, index=False)
    elif format.lower() == 'xlsx':
        df.to_excel(output_path, index=False)
    elif format.lower() == 'json':
        df.to_json(output_path, orient='records', indent=2)
    elif format.lower() == 'parquet':
        df.to_parquet(output_path, index=False)
    else:
        raise ValueError(f"Unsupported output format: {format}")


def clean_data_command(args):
    """Execute data cleaning command."""
    try:
        # Load data
        print(f"Loading data from: {args.input}")
        data = load_data(args.input)
        print(f"Loaded data shape: {data.shape}")
        
        # Initialize cleaning agent
        config = get_config()
        if args.model:
            config.model_name = args.model
        
        agent = CleaningAgent(model_name=config.model_name, config=config)
        print(f"Initialized Cleaning Agent with model: {config.model_name}")
        
        # Execute cleaning
        print(f"Starting data cleaning with goal: {args.goal}")
        response = agent.clean_data(data, args.goal, args.parameters)
        
        if response.success:
            print("✅ Data cleaning completed successfully!")
            print(f"Message: {response.message}")
            
            # Save cleaned data
            if args.output:
                output_format = args.output.split('.')[-1] if '.' in args.output else 'csv'
                save_data(response.cleaned_data, args.output, output_format)
                print(f"✅ Cleaned data saved to: {args.output}")
            
            # Display report summary
            if response.report:
                report = response.report
                print("\n📊 Cleaning Report Summary:")
                print(f"  - Original shape: {report.data_summary['original_shape']}")
                print(f"  - Cleaned shape: {report.data_summary['cleaned_shape']}")
                print(f"  - Rows removed: {report.data_summary['rows_removed']}")
                print(f"  - Operations performed: {len(report.cleaning_operations)}")
                print(f"  - Execution time: {report.execution_time:.2f}s")
                
                if report.issues_detected:
                    print(f"\n🔍 Issues Detected: {len(report.issues_detected)}")
                    for issue in report.issues_detected[:3]:  # Show first 3 issues
                        print(f"  - {issue.issue_type}: {issue.description}")
                
                if report.recommendations:
                    print(f"\n💡 Recommendations:")
                    for rec in report.recommendations[:3]:  # Show first 3 recommendations
                        print(f"  - {rec}")
            
            # Save detailed report if requested
            if args.report:
                report_data = response.report.dict() if response.report else {}
                with open(args.report, 'w') as f:
                    json.dump(report_data, f, indent=2, default=str)
                print(f"✅ Detailed report saved to: {args.report}")
                
        else:
            print("❌ Data cleaning failed!")
            print(f"Error: {response.message}")
            if response.errors:
                for error in response.errors:
                    print(f"  - {error}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def analyze_data_command(args):
    """Execute data analysis command."""
    try:
        # Load data
        print(f"Loading data from: {args.input}")
        data = load_data(args.input)
        print(f"Loaded data shape: {data.shape}")
        
        # Initialize cleaning agent
        agent = CleaningAgent(model_name=args.model or "gpt-4")
        
        # Get capabilities
        capabilities = agent.get_capabilities()
        print("\n🔧 Agent Capabilities:")
        for capability in capabilities['capabilities']:
            print(f"  - {capability}")
        
        # Analyze data quality
        from .utils import DataQualityAnalyzer
        analyzer = DataQualityAnalyzer()
        metrics = analyzer.analyze_data_quality(data)
        
        print(f"\n📊 Data Quality Analysis:")
        print(f"  - Total rows: {metrics.total_rows:,}")
        print(f"  - Total columns: {metrics.total_columns}")
        print(f"  - Overall quality score: {metrics.quality_score:.2%}")
        print(f"  - Missing values: {sum(metrics.missing_values.values()):,}")
        print(f"  - Duplicate rows: {metrics.duplicate_rows:,} ({metrics.duplicate_percentage:.1f}%)")
        
        # Detect issues
        issues = analyzer.detect_issues(data, metrics)
        if issues:
            print(f"\n🔍 Data Quality Issues Detected: {len(issues)}")
            for i, issue in enumerate(issues[:5], 1):  # Show first 5 issues
                print(f"  {i}. {issue.issue_type} ({issue.severity}): {issue.description}")
                if issue.suggested_fixes:
                    print(f"     Suggested fixes: {', '.join(issue.suggested_fixes[:2])}")
        else:
            print("\n✅ No significant data quality issues detected!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Cleaning Agent - Intelligent data cleaning for automated data quality improvement",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Clean a CSV file
  cleaning-agent clean data.csv --goal "improve data quality" --output cleaned_data.csv
  
  # Analyze data quality
  cleaning-agent analyze data.csv
  
  # Clean with custom parameters
  cleaning-agent clean data.csv --goal "remove duplicates" --parameters '{"remove_duplicates": true}'
        """
    )
    
    # Global arguments
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    # Create subparsers
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Clean command
    clean_parser = subparsers.add_parser('clean', help='Clean data')
    clean_parser.add_argument('input', help='Input data file path')
    clean_parser.add_argument('--goal', required=True, help='Cleaning goal or objective')
    clean_parser.add_argument('--output', help='Output file path for cleaned data')
    clean_parser.add_argument('--model', help='LLM model to use (default: gpt-4)')
    clean_parser.add_argument('--parameters', type=json.loads, default={}, help='Cleaning parameters (JSON string)')
    clean_parser.add_argument('--report', help='Save detailed cleaning report to file')
    clean_parser.set_defaults(func=clean_data_command)
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze data quality')
    analyze_parser.add_argument('input', help='Input data file path')
    analyze_parser.add_argument('--model', help='LLM model to use (default: gpt-4)')
    analyze_parser.set_defaults(func=analyze_data_command)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log_level)
    
    # Execute command
    if args.command:
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
