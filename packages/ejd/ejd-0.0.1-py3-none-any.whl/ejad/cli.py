#!/usr/bin/env python3
import argparse
from ejad.static_issue import fix_static_issue

def main():
    parser = argparse.ArgumentParser(
        prog="ejd",
        description="EJAD CLI Tool"
    )

    parser.add_argument("-si", "--static-issue", action="store_true",
                        help="Enable static issue fixing mode.")

    subparsers = parser.add_subparsers(dest="command")

    # fix command
    fix_parser = subparsers.add_parser("fix", help="Fix static issue in a file")
    fix_parser.add_argument("path", type=str, help="Path to the file to fix")

    args = parser.parse_args()

    if args.static_issue and args.command == "fix":
        fix_static_issue(args.path)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
