"""
CERT Framework CLI

Command-line interface for CERT framework operations.
"""

import argparse
import sys


def compare_texts():
    """CLI for comparing two texts."""
    if len(sys.argv) < 3:
        print("Usage: cert-compare <text1> <text2> [--threshold THRESHOLD]")
        print()
        print("Example:")
        print('  cert-compare "revenue up" "sales increased"')
        print('  cert-compare "profit down" "earnings declined" --threshold 0.85')
        sys.exit(1)

    # Parse arguments
    parser = argparse.ArgumentParser(description="Compare two texts semantically")
    parser.add_argument("text1", help="First text to compare")
    parser.add_argument("text2", help="Second text to compare")
    parser.add_argument(
        "--threshold",
        "-t",
        type=float,
        default=None,
        help="Similarity threshold (0.0-1.0)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed results"
    )

    args = parser.parse_args()

    # Import and run comparison
    from cert import compare

    try:
        result = compare(args.text1, args.text2, threshold=args.threshold)

        if args.verbose:
            print(f"Text 1: {args.text1}")
            print(f"Text 2: {args.text2}")
            print(f"Matched: {result.matched}")
            print(f"Confidence: {result.confidence:.1%}")
            print(f"Rule: {result.rule}")
        else:
            print(result)

        # Exit code: 0 for match, 1 for no match
        sys.exit(0 if result.matched else 1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="CERT Framework - LLM Reliability Testing"
    )
    parser.add_argument(
        "command",
        choices=["test", "inspect", "version", "validate"],
        help="Command to run",
    )
    parser.add_argument(
        "--port", type=int, default=5000, help="Port for inspector UI (default: 5000)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick validation (for validate command)",
    )

    args = parser.parse_args()

    if args.command == "version":
        from cert import __version__

        print(f"CERT Framework v{__version__}")
        return 0

    elif args.command == "inspect":
        try:
            from cert.inspector import run_inspector

            print(f"🚀 Starting CERT Inspector on http://localhost:{args.port}")
            print("📝 Press Ctrl+C to stop")
            run_inspector(port=args.port)
        except ImportError:
            print(
                "❌ Inspector requires Flask. Install with: pip install cert-framework[inspector]"
            )
            return 1

    elif args.command == "validate":
        from cert.validation import quick_validation, run_sts_benchmark

        if args.quick:
            quick_validation()
        else:
            run_sts_benchmark()
        return 0

    elif args.command == "test":
        print("Running tests...")
        # Add test discovery logic here
        print("⚠️  Test discovery coming soon. Use Python API for now.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
