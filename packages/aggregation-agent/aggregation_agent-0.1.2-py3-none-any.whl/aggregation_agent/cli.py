"""
Command Line Interface for the Aggregation Agent

This module provides a command-line interface for using the Aggregation Agent
independently or as part of automated workflows.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

from .agent import AggregationAgent
from .config import DEFAULT_AI_PROVIDER, DEFAULT_AI_TASK_TYPE


def load_data(file_path: str) -> Dict[str, Any]:
    """Load data from JSON or CSV file"""
    path = Path(file_path)
    
    if path.suffix.lower() == '.json':
        with open(path, 'r') as f:
            return json.load(f)
    elif path.suffix.lower() == '.csv':
        import pandas as pd
        df = pd.read_csv(path)
        return df.to_dict('records')
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")


def save_results(results: Dict[str, Any], output_path: str):
    """Save results to JSON file"""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Aggregation Agent - Suggest optimal aggregation methods",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic aggregation suggestions
  python -m aggregation_agent.cli --schema schema.json --mappings mappings.json --problem-type regression --group-by customer_id --output suggestions.json
  
  # With custom AI provider
  python -m aggregation_agent.cli --schema schema.json --mappings mappings.json --problem-type classification --ai-provider openai --output suggestions.json
        """
    )
    
    parser.add_argument(
        "--schema", "-s",
        required=True,
        help="Table schema file (JSON)"
    )
    
    parser.add_argument(
        "--mappings", "-m",
        required=True,
        help="Field mappings file (JSON)"
    )
    
    parser.add_argument(
        "--problem-type", "-p",
        required=True,
        choices=["regression", "classification", "clustering", "forecasting"],
        help="Type of problem to solve"
    )
    
    parser.add_argument(
        "--group-by", "-g",
        required=True,
        nargs="+",
        help="Fields to group by"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="aggregation_suggestions.json",
        help="Output file for results (default: aggregation_suggestions.json)"
    )
    
    parser.add_argument(
        "--ai-provider",
        default=DEFAULT_AI_PROVIDER,
        choices=["openai", "anthropic", "local"],
        help=f"AI provider to use (default: {DEFAULT_AI_PROVIDER})"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        # Load table schema
        if args.verbose:
            print(f"Loading table schema from: {args.schema}")
        table_schema = load_data(args.schema)
        
        # Load field mappings
        if args.verbose:
            print(f"Loading field mappings from: {args.mappings}")
        field_mappings = load_data(args.mappings)
        
        # Initialize agent
        if args.verbose:
            print(f"Initializing Aggregation Agent with {args.ai_provider}")
        
        agent = AggregationAgent(llm_provider=args.ai_provider)
        
        # Perform aggregation suggestions
        if args.verbose:
            print(f"Starting aggregation suggestions for problem type: {args.problem_type}")
            print(f"Grouping by fields: {', '.join(args.group_by)}")
        
        # Generate suggestions
        suggestions = agent.suggest_aggregation_methods(
            table_schema=table_schema,
            field_mappings=field_mappings,
            problem_type=args.problem_type,
            group_by_fields=args.group_by
        )
        
        if args.verbose:
            print(f"Aggregation suggestions completed. Saving results to: {args.output}")
        
        # Save results
        save_results(suggestions, args.output)
        
        print(f"✅ Aggregation suggestions completed successfully!")
        print(f"📁 Results saved to: {args.output}")
        
        # Print summary
        if isinstance(suggestions, dict) and 'suggestions' in suggestions:
            total_suggestions = len(suggestions.get('suggestions', []))
            print(f"📊 Generated {total_suggestions} aggregation suggestions")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
