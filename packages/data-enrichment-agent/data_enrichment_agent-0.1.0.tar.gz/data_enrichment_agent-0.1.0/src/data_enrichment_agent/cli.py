#!/usr/bin/env python3
"""
Command-line interface for the Enrichment Agent.
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any
import pandas as pd
from .agent import EnrichmentAgent
from .config import get_config

def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def load_data(file_path: str) -> pd.DataFrame:
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

def enrich_data_command(args):
    try:
        print(f"Loading data from: {args.input}")
        data = load_data(args.input)
        print(f"Loaded data shape: {data.shape}")
        config = get_config()
        if args.model:
            config.model_name = args.model
        agent = EnrichmentAgent(model_name=config.model_name, config=config)
        print(f"Initialized Enrichment Agent with model: {config.model_name}")
        print(f"Starting data enrichment with goal: {args.goal}")
        response = agent.enrich_data(data, args.goal, args.parameters)
        if response.success:
            print("\u2705 Data enrichment completed successfully!")
            print(f"Message: {response.message}")
            if args.output:
                output_format = args.output.split('.')[-1] if '.' in args.output else 'csv'
                save_data(response.enriched_data, args.output, output_format)
                print(f"\u2705 Enriched data saved to: {args.output}")
            if response.report:
                report = response.report
                print("\n\U0001F4CA Enrichment Report Summary:")
                print(f"  - Original shape: {report.original_shape}")
                print(f"  - Enriched shape: {report.enriched_shape}")
                print(f"  - Features added: {report.features_added}")
                print(f"  - Operations performed: {len(report.operations)}")
                print(f"  - Execution time: {report.execution_time}")
        else:
            print(f"\u274C Enrichment failed: {response.errors}")
            sys.exit(1)
    except Exception as e:
        print(f"\u274C Error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Enrichment Agent - Automated feature engineering for ML modeling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Enrich a CSV file
  enrichment-agent enrich data.csv --goal "add time features" --output enriched_data.csv
  
  # Enrich with custom parameters
  enrichment-agent enrich data.csv --goal "create polynomials" --parameters '{"create_polynomials": true}'
        """
    )
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO', help='Logging level (default: INFO)')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    enrich_parser = subparsers.add_parser('enrich', help='Enrich data with new features')
    enrich_parser.add_argument('input', help='Input data file path')
    enrich_parser.add_argument('--goal', required=True, help='Enrichment goal or objective')
    enrich_parser.add_argument('--output', help='Output file path for enriched data')
    enrich_parser.add_argument('--model', help='LLM model to use (default: gpt-4)')
    enrich_parser.add_argument('--parameters', type=json.loads, default={}, help='Enrichment parameters (JSON string)')
    enrich_parser.set_defaults(func=enrich_data_command)
    args = parser.parse_args()
    setup_logging(args.log_level)
    if args.command:
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
