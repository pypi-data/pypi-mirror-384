"""
Command-line interface for the Debug Helper SDK.
"""

import sys
import argparse
import json
from pathlib import Path
from debug_helper import DebugLogger


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Debug Helper SDK Command Line Interface"
    )
    parser.add_argument(
        "--api-key",
        required=True,
        help="Project API key from Debug Helper dashboard"
    )
    parser.add_argument(
        "--api-url",
        default="http://127.0.0.1:8000",
        help="Debug Helper API URL (default: http://127.0.0.1:8000)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Test connection command
    test_parser = subparsers.add_parser("test", help="Test connection to Debug Helper API")
    
    # Report issue command
    issue_parser = subparsers.add_parser("issue", help="Report a new issue")
    issue_parser.add_argument("--title", required=True, help="Issue title")
    issue_parser.add_argument("--description", default="", help="Issue description")
    issue_parser.add_argument("--file-name", help="File name where issue occurred")
    issue_parser.add_argument("--line-number", type=int, help="Line number where issue occurred")
    issue_parser.add_argument("--severity", choices=["low", "medium", "high", "critical"], 
                             default="medium", help="Issue severity")
    issue_parser.add_argument("--log-path", help="Path to log file")
    
    # Project info command
    info_parser = subparsers.add_parser("info", help="Get project information")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        logger = DebugLogger(api_key=args.api_key, api_url=args.api_url)
        
        if args.command == "test":
            if logger.test_connection():
                print("✅ Connection to Debug Helper API successful!")
                return 0
            else:
                print("❌ Failed to connect to Debug Helper API")
                return 1
        
        elif args.command == "issue":
            issue_data = {
                "title": args.title,
                "description": args.description,
                "severity": args.severity
            }
            
            if args.file_name:
                issue_data["file_name"] = args.file_name
            if args.line_number:
                issue_data["line_number"] = args.line_number
            if args.log_path:
                issue_data["log_path"] = args.log_path
            
            issue = logger.issue(**issue_data)
            print(f"✅ Issue created successfully!")
            print(f"Issue ID: {issue['id']}")
            print(f"Title: {issue['title']}")
            print(f"Status: {issue['status']}")
            return 0
        
        elif args.command == "info":
            info = logger.get_project_info()
            print("📊 Project Information:")
            print(json.dumps(info, indent=2))
            return 0
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())