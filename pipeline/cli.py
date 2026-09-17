"""
AgriClutch Pipeline CLI.
Command-line runner for ingesting, validating, and normalizing agricultural market datasets.
"""

import argparse
import asyncio
import sys
from typing import Optional

from app.db.migrations import init_db
from app.db.session import async_session, engine
from app.services.pipeline_service import PipelineService


async def run_pipeline(
    input_file: str,
    source_name: str = "LOCAL_CSV",
    format_name: str = "canonical",
    dry_run: bool = False,
    output_report_path: Optional[str] = None,
) -> int:
    """Run data pipeline and print summary scorecard."""
    print("=" * 60)
    print("  AgriClutch Agricultural Data Pipeline Runner")
    print("=" * 60)
    print(f"Input file   : {input_file}")
    print(f"Source name  : {source_name}")
    print(f"Format profile: {format_name}")
    print(f"Execution mode: {'DRY RUN (Validation only)' if dry_run else 'PERSIST (Writing to database)'}")
    print("-" * 60)

    service = PipelineService()

    session = None
    if not dry_run and async_session is not None and engine is not None:
        try:
            # Ensure tables exist
            await init_db(engine)
            session = async_session()
        except Exception as exc:
            print(f"[WARN] Database connection unavailable ({exc}). Proceeding in dry-run mode.")
            session = None

    try:
        report, inserted = await service.process_file(
            file_path=input_file,
            source_name=source_name,
            format_name=format_name,
            dry_run=dry_run or (session is None),
            session=session,
        )

        print("\n--- Validation Quality Report ---")
        print(f"Total records processed : {report.total_records}")
        print(f"Valid records           : {report.valid_records}")
        print(f"Warning records         : {report.warning_records}")
        print(f"Invalid records         : {report.invalid_records}")
        print(f"Duplicate records       : {report.duplicate_records}")
        print(f"Overall Health Score    : {report.health_score:.1f}%")

        if report.errors:
            print(f"\n[ERRORS DETECTED ({len(report.errors)})]:")
            for err in report.errors[:10]:
                row_str = f" (Row {err.row_number})" if err.row_number else ""
                print(f"  - [{err.field}]{row_str}: {err.message} (Value: {err.raw_value})")
            if len(report.errors) > 10:
                print(f"  ... and {len(report.errors) - 10} more errors.")

        if report.warnings:
            print(f"\n[WARNINGS ({len(report.warnings)})]:")
            for warn in report.warnings[:5]:
                row_str = f" (Row {warn.row_number})" if warn.row_number else ""
                print(f"  - [{warn.field}]{row_str}: {warn.message}")
            if len(report.warnings) > 5:
                print(f"  ... and {len(report.warnings) - 5} more warnings.")

        if not dry_run and session is not None:
            print(f"\n[DATABASE]: Successfully inserted {inserted} price records.")
        elif dry_run:
            print("\n[INFO]: Dry run completed. Zero database modifications made.")

        if output_report_path:
            with open(output_report_path, "w", encoding="utf-8") as rf:
                rf.write(report.model_dump_json(indent=2))
            print(f"[INFO]: Full validation report exported to {output_report_path}")

        print("=" * 60)
        return 0 if report.is_acceptable else 1
    finally:
        if session is not None:
            await session.close()


def main() -> None:
    """CLI entrypoint parser."""
    parser = argparse.ArgumentParser(
        description="AgriClutch Agricultural Data Pipeline Ingestion CLI"
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to the input CSV file",
    )
    parser.add_argument(
        "--source",
        "-s",
        default="LOCAL_CSV",
        help="Origin data source identifier (default: LOCAL_CSV)",
    )
    parser.add_argument(
        "--format",
        "-f",
        default="canonical",
        choices=["canonical", "agmarknet", "auto"],
        help="Source format mapping profile (default: canonical)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute parsing and validation only without database persistence",
    )
    parser.add_argument(
        "--output-report",
        "-o",
        default=None,
        help="Optional path to export validation report JSON",
    )

    args = parser.parse_args()

    exit_code = asyncio.run(
        run_pipeline(
            input_file=args.input,
            source_name=args.source,
            format_name=args.format,
            dry_run=args.dry_run,
            output_report_path=args.output_report,
        )
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
