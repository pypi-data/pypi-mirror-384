#!/usr/bin/env python3
"""
sparq CLI - Command-line interface for the sparq API
"""

import sys
import argparse
from auth import register
from recover import recover_key
from usage import show_usage


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="sparq - Automated degree planning for SJSU students",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  auth      Register and get your API key
  recover   Recover your existing API key
  usage     View your API usage statistics

Examples:
  sparq auth       # Register and get API key
  sparq recover    # Recover existing API key
  sparq usage      # View usage statistics
        """
    )
    
    parser.add_argument(
        'command',
        nargs='?',
        choices=['auth', 'recover', 'usage'],
        help='Command to execute'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'auth':
            register()
        elif args.command == 'recover':
            recover_key()
        elif args.command == 'usage':
            show_usage()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
