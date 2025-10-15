"""
Command-line interface for Digilog.
"""

import argparse
import getpass
import os
import sys
from typing import Optional
from .exceptions import DigilogError


def login(api_key: Optional[str] = None) -> None:
    """Interactive login to get authentication token.
    
    Args:
        api_key: Optional API key for headless/non-interactive mode
    """
    print("Digilog Login")
    print("=" * 50)
    
    # Get token from argument or prompt user
    if api_key:
        token = api_key
    else:
        token = getpass.getpass("Enter your Digilog token: ")
    
    if not token.strip():
        print("Error: Token cannot be empty")
        sys.exit(1)
    
    # Save token to environment
    os.environ['DIGILOG_API_KEY'] = token
    print("✓ Token saved to environment variable DIGILOG_API_KEY")
    print("  You can also set this in your shell profile for persistence.")


def status() -> None:
    """Show current Digilog status."""
    print("Digilog Status")
    print("=" * 50)
    
    # Check token
    token = os.environ.get('DIGILOG_API_KEY')
    if token:
        print(f"✓ Authentication token: {'*' * (len(token) - 4) + token[-4:]}")
    else:
        print("✗ No authentication token found")
        print("  Set DIGILOG_API_KEY environment variable or run 'digilog login'")
    
    # Check API base URL
    from . import get_api_base_url
    api_url = get_api_base_url()
    print(f"API Base URL: {api_url}")
    
    # Test connection if token is available
    if token:
        try:
            from .api import APIClient
            client = APIClient(api_url, token)
            projects = client.get_projects()
            print(f"✓ Connected successfully - {len(projects)} projects found")
        except Exception as e:
            print(f"✗ Connection failed: {e}")


def init_project(project: str, description: Optional[str] = None) -> None:
    """Initialize a new project."""
    
    try:
        from .api import APIClient
        from . import get_api_base_url
        
        token = os.environ.get('DIGILOG_API_KEY')
        if not token:
            print("Error: No authentication token found")
            print("Set DIGILOG_API_KEY environment variable or run 'digilog login'")
            sys.exit(1)
        
        client = APIClient(get_api_base_url(), token)
        created_project = client.create_project(project, description)
        
        print(f"✓ Project '{created_project['name']}' created successfully")
        print(f"  ID: {created_project['id']}")
        if created_project.get('description'):
            print(f"  Description: {created_project['description']}")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def list_projects() -> None:
    """List all projects."""
    try:
        from .api import APIClient
        from . import get_api_base_url
        
        token = os.environ.get('DIGILOG_API_KEY')
        if not token:
            print("Error: No authentication token found")
            print("Set DIGILOG_API_KEY environment variable or run 'digilog login'")
            sys.exit(1)
        
        client = APIClient(get_api_base_url(), token)
        projects = client.get_projects()
        
        if not projects:
            print("No projects found")
            return
        
        print("Your Projects")
        print("=" * 50)
        for project in projects:
            print(f"• Name: {project['name']}")
            print(f"  ID: {project['id']}")
            if project.get('description'):
                print(f"  Description: {project['description']}\n")
            print(f"  Runs: {project['_count']['runs']}")
            print(f"  Created: {project['createdAt']}")
            print()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def list_runs(project_id: str, limit: int = 50, offset: int = 0) -> None:
    """List runs for a project."""
    
    try:
        from .api import APIClient
        from . import get_api_base_url
        
        token = os.environ.get('DIGILOG_API_KEY')
        if not token:
            print("Error: No authentication token found")
            print("Set DIGILOG_API_KEY environment variable or run 'digilog login'")
            sys.exit(1)
        
        client = APIClient(get_api_base_url(), token)
        runs = client.get_runs(project_id, limit, offset)
        
        if not runs:
            print(f"No runs found for project {project_id}")
            return
        
        print(f"Runs for Project {project_id}")
        print("=" * 50)
        for run in runs:
            print(f"• Name: {run.get('name', 'Unnamed')}")
            print(f"  ID: {run['id']}")
            if run.get('description'):
                print(f"  Description: {run['description']}")
            print(f"  Status: {run.get('status', 'UNKNOWN')}")
            print(f"  Created: {run.get('createdAt', 'Unknown')}")
            if run.get('finishedAt'):
                print(f"  Finished: {run['finishedAt']}")
            print()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Digilog - Experiment tracking with wandb-like interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  digilog login                    # Interactive login to get authentication token
  digilog login --key <api-key>    # Non-interactive login (headless mode)
  digilog status                   # Show current status
  digilog init my-project          # Initialize a new project
  digilog projects                 # List all projects
  digilog runs <project-id>        # List runs for a project
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Login command
    login_parser = subparsers.add_parser('login', help='Login to get authentication token')
    login_parser.add_argument('--key', '-k', help='API key for headless/non-interactive mode')
    
    # Status command
    subparsers.add_parser('status', help='Show current status')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize a new project')
    init_parser.add_argument('project', help='Project name')
    init_parser.add_argument('--description', '-d', help='Project description')
    
    # Projects command
    subparsers.add_parser('projects', help='List all projects')
    
    # Runs command
    runs_parser = subparsers.add_parser('runs', help='List runs for a project')
    runs_parser.add_argument('project_id', help='Project ID')
    runs_parser.add_argument('--limit', '-l', type=int, default=50, help='Maximum number of runs to return (default: 50)')
    runs_parser.add_argument('--offset', '-o', type=int, default=0, help='Number of runs to skip (default: 0)')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'login':
            login(api_key=args.key)
        elif args.command == 'status':
            status()
        elif args.command == 'init':
            init_project(args.project, args.description)
        elif args.command == 'projects':
            list_projects()
        elif args.command == 'runs':
            list_runs(args.project_id, args.limit, args.offset)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except DigilogError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 