#!/usr/bin/env python3
# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

"""
Runnable Python script for VRS Health Check using the simple Runner API.

This script provides a command-line interface to run VRS health checks
using the simplified Runner::runVrsHealthCheck API.
"""

import argparse
import os
import sys

# Add the projectaria_tools to the path if needed
try:
    from projectaria_vrs_health_check import vrs_health_check
except ImportError:
    print("Error: Could not import projectaria_vrs_health_check.vrs_health_check")
    print("Make sure projectaria_vrs_health_check is installed or built properly.")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Run VRS Health Check using the simple Runner API",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--path", help="Path to the VRS file to check")

    parser.add_argument(
        "--output-json",
        "-j",
        default="",
        help="Path to output JSON file with health check results",
    )

    parser.add_argument(
        "--output-json-compact",
        default="",
        help="Path to output compact JSON file (only failed/warning checks)",
    )

    parser.add_argument(
        "--output-dropped-frame-csv",
        default="",
        help="Path to output csv file for dropped frames information",
    )

    parser.add_argument(
        "--print-stats", "-s", action="store_true", help="Print statistics to console"
    )

    parser.add_argument(
        "--disable-logging", "-q", action="store_true", help="Disable logging output"
    )

    parser.add_argument(
        "--override-check-file",
        help="Path to JSON file containing override checks",
    )

    parser.add_argument(
        "--override-checks",
        help="Comma-separated key=value threshold overrides (e.g., 'Camera Data (SLAM).ratio_dropped_over_expected.fail_threshold=0.02')",
    )

    parser.add_argument(
        "--configuration-to-override",
        help="Base configuration to override (required when using --override-checks)",
    )

    parser.add_argument(
        "--list-configurations",
        action="store_true",
        help="List available configurations and exit",
    )

    parser.add_argument(
        "--show-configuration-json",
        help="Show details of a specific configuration and exit",
    )

    parser.add_argument(
        "--choose-configuration",
        help="Only print results from a specific configuration",
    )

    args = parser.parse_args()

    # Handle configuration commands first (these exit immediately)
    if args.list_configurations:
        try:
            vrs_health_check.list_configurations()
            sys.exit(0)
        except Exception as e:
            print(f"Error listing configurations: {e}")
            sys.exit(1)

    if args.show_configuration_json:
        try:
            vrs_health_check.show_configuration(args.show_configuration_json)
            sys.exit(0)
        except Exception as e:
            print(f"Error showing configuration '{args.show_configuration_json}': {e}")
            sys.exit(1)

    # For normal health check, path is required
    if not args.path:
        print("Error: --path is required when not using configuration commands.")
        parser.print_help()
        sys.exit(1)

    # Validate override check options (match C++ logic)
    if args.override_check_file and args.override_checks:
        print(
            "Error: Cannot use both --override-check-file and --override-checks simultaneously"
        )
        sys.exit(1)

    if args.override_checks and not args.configuration_to_override:
        print(
            "Error: Configuration to override must be specified when using override checks"
        )
        sys.exit(1)

    # Parse comma-separated override checks (match C++ format)
    override_check_list = None
    if args.override_checks:
        override_check_list = [
            check.strip() for check in args.override_checks.split(",") if check.strip()
        ]

    # Validate input file exists for non-GAIA paths
    if (
        not args.path.startswith("gaia:")
        and not args.path.startswith("manifold:")
        and not os.path.exists(args.path)
    ):
        print(f"Error: VRS file '{args.path}' does not exist.")
        sys.exit(1)

    # Validate output directories exist if specified
    if args.output_json:
        json_dir = os.path.dirname(args.output_json)
        if json_dir and not os.path.exists(json_dir):
            print(f"Error: Output directory for JSON file '{json_dir}' does not exist.")
            sys.exit(1)

    if args.output_json_compact:
        json_compact_dir = os.path.dirname(args.output_json_compact)
        if json_compact_dir and not os.path.exists(json_compact_dir):
            print(
                f"Error: Output directory for compact JSON file '{json_compact_dir}' does not exist."
            )
            sys.exit(1)

    if args.output_dropped_frame_csv:
        dropped_dir = os.path.dirname(args.output_dropped_frame_csv)
        if dropped_dir and not os.path.exists(dropped_dir):
            print(
                f"Error: Output directory for dropped frames file '{dropped_dir}' does not exist."
            )
            sys.exit(1)

    print(f"Running VRS health check on: {args.path}")

    try:
        # Call the simple Runner API through Python binding
        result = vrs_health_check.run_vrs_health_check(
            path=args.path,
            json_out_filename=args.output_json,
            json_compact_out_filename=args.output_json_compact,
            dropped_out_filename=args.output_dropped_frame_csv,
            print_stats=args.print_stats,
            disable_logging=args.disable_logging,
            maybeOverrideCheckFile=args.override_check_file,
            maybeOverrideCheckStrings=override_check_list,
            maybeConfigurationToOverride=args.configuration_to_override
            if override_check_list
            else None,
            maybeChooseConfiguration=args.choose_configuration
            if args.choose_configuration
            else None,
        )

        if result == 0:
            print("VRS health check completed successfully.")
        else:
            print(f"VRS health check completed with return code: {result}")

        if args.output_json and os.path.exists(args.output_json):
            print(f"Results saved to: {args.output_json}")

        if args.output_json_compact and os.path.exists(args.output_json_compact):
            print(f"Compact results saved to: {args.output_json_compact}")

        if args.output_dropped_frame_csv and os.path.exists(
            args.output_dropped_frame_csv
        ):
            print(f"Dropped frames info saved to: {args.output_dropped_frame_csv}")

        sys.exit(result)

    except Exception as e:
        print(f"Error running VRS health check: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
