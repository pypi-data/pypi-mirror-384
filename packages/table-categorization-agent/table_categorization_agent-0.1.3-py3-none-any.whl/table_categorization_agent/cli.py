"""
Command Line Interface for Table Categorization Agent

Provides command-line access to table categorization functionality.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict

import pandas as pd
from sfn_blueprint import SFNDataLoader

from .agent import TableCategorizationAgent
from .config import get_logging_config


def setup_logging():
    """Setup logging configuration"""
    config = get_logging_config()

    logging.basicConfig(
        level=getattr(logging, config.get("level", "INFO")),
        format=config.get(
            "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ),
    )


def load_data_files(file_paths: list) -> Dict[str, pd.DataFrame]:
    """
    Load multiple data files into DataFrames

    Args:
        file_paths: List of file paths to load

    Returns:
        Dictionary mapping file names to DataFrames
    """
    data_loader = SFNDataLoader()
    tables = {}

    for file_path in file_paths:
        try:
            path = Path(file_path)
            table_name = path.stem  # Use filename without extension

            # Load data based on file type
            if path.suffix.lower() in [".csv"]:
                df = data_loader.read_csv(file_path)
            elif path.suffix.lower() in [".xlsx", ".xls"]:
                df = data_loader.read_xlsx(file_path)
            elif path.suffix.lower() in [".json"]:
                df = data_loader.read_json(file_path)
            elif path.suffix.lower() in [".parquet"]:
                df = data_loader.read_parquet(file_path)
            else:
                print(f"Unsupported file type: {path.suffix}")
                continue

            tables[table_name] = df
            print(f"Loaded {table_name}: {len(df)} rows, {len(df.columns)} columns")

        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            continue

    return tables


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Table Categorization Agent - LLM-driven table analysis and categorization"
    )

    parser.add_argument(
        "files", nargs="+", help="Data files to categorize (CSV, Excel, JSON, Parquet)"
    )

    parser.add_argument("--schema", help="Path to domain schema JSON file")

    parser.add_argument("--output", help="Output file path for results (JSON format)")

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.7,
        help="Minimum confidence threshold for categorization (default: 0.7)",
    )

    parser.add_argument(
        "--quality-threshold",
        type=float,
        default=0.7,
        help="Minimum data quality threshold (default: 0.7)",
    )

    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        setup_logging()

    logger = logging.getLogger(__name__)

    try:
        # Load data files
        print("Loading data files...")
        tables = load_data_files(args.files)

        if not tables:
            print("No data files could be loaded. Exiting.")
            sys.exit(1)

        # Initialize agent
        print("Initializing Table Categorization Agent...")
        agent = TableCategorizationAgent(domain_schema_path=args.schema)

        # Categorize tables
        print(f"Categorizing {len(tables)} tables...")
        result = agent.categorize_multiple_tables(tables)

        # Display results
        print("\n" + "=" * 60)
        print("TABLE CATEGORIZATION RESULTS")
        print("=" * 60)

        print(f"Total Tables: {result.total_tables}")
        print(f"Domain Coverage: {result.domain_coverage:.1%}")
        print(f"High Confidence: {result.high_confidence_count}/{result.total_tables}")
        print(f"High Quality: {result.high_quality_count}/{result.total_tables}")

        print("\nTABLE BREAKDOWN:")
        print("-" * 40)

        for category in result.table_categories:
            print(f"\n{category.table_name}:")
            print(f"  Primary Entity: {category.primary_entity}")
            print(f"  Confidence: {category.confidence_score:.1%}")
            print(f"  Data Quality: {category.data_quality_score:.1%}")
            print(f"  Mapped Attributes: {len(category.mapped_attributes)}")
            print(f"  Relationships: {len(category.suggested_relationships)}")

            if category.mapped_attributes:
                print("  Attribute Mappings:")
                for col, attr in category.mapped_attributes.items():
                    print(f"    {col} -> {attr}")

            if category.recommendations:
                print("  Recommendations:")
                for rec in category.recommendations:
                    print(f"    - {rec}")

        print("\nDATA INSIGHTS:")
        print("-" * 40)
        for insight in result.data_insights:
            print(f"  - {insight}")

        print("\nRECOMMENDED NEXT STEPS:")
        print("-" * 40)
        for step in result.next_steps:
            print(f"  - {step}")

        # Export results if requested
        if args.output:
            try:
                result.export_json(args.output)
                print(f"\nResults exported to: {args.output}")
            except Exception as e:
                logger.error(f"Failed to export results: {e}")
                print(f"Warning: Could not export results to {args.output}")

        # Exit with appropriate code
        low_confidence = result.total_tables - result.high_confidence_count
        if low_confidence > 0:
            print(
                f"\nWarning: {low_confidence} tables have low confidence categorization"
            )
            sys.exit(1)
        else:
            print("\nAll tables categorized successfully!")
            sys.exit(0)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
