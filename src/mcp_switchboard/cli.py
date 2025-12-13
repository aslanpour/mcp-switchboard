"""CLI entry point for mcp-switchboard."""
import sys
import argparse
from pathlib import Path
from mcp_switchboard.analyzer.analyzer import TaskAnalyzer
from mcp_switchboard.selector.selector import ServerSelector
from mcp_switchboard.config.registry import ServerRegistry


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="mcp-switchboard: Intelligent MCP server orchestration"
    )
    parser.add_argument(
        "task",
        nargs="?",
        help="Task description to analyze"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="mcp-switchboard 0.1.0"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze task and show recommended servers"
    )
    
    args = parser.parse_args()
    
    if not args.task:
        parser.print_help()
        return 0
    
    if args.analyze:
        analyzer = TaskAnalyzer()
        analysis = analyzer.analyze(args.task)
        
        print(f"\nTask Analysis:")
        print(f"  AWS Account: {analysis.aws_account or 'N/A'}")
        print(f"  AWS Region: {analysis.aws_region or 'N/A'}")
        print(f"  Jira Ticket: {analysis.jira_ticket or 'N/A'}")
        print(f"  Required Services: {', '.join(analysis.required_services)}")
        print(f"  Confidence: {analysis.confidence:.2f}")
        
        registry = ServerRegistry()
        selector = ServerSelector(registry)
        selection = selector.select(analysis)
        
        print(f"\nRecommended Servers:")
        for server in selection.selected_servers:
            print(f"  • {server.server_name} ({server.confidence:.2f})")
            print(f"    {server.reasoning}")
        
        return 0
    
    print("Use --analyze to analyze a task")
    return 0


if __name__ == "__main__":
    sys.exit(main())
