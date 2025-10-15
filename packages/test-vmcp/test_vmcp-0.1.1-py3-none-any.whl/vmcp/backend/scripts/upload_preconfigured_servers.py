#!/usr/bin/env python3
"""
Script to upload pre-configured MCP servers to the global_mcp_server_registry table.
This script reads the preconfigured-servers.json file and uploads each server
to the database with proper MCP configurations.

Usage:
    python -m vmcp.backend.scripts.upload_preconfigured_servers
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Get the package root directory
PACKAGE_ROOT = Path(__file__).parent.parent
DATA_DIR = PACKAGE_ROOT / "data"
JSON_FILE = DATA_DIR / "preconfigured-servers.json"


def load_preconfigured_servers(json_file_path: Path) -> List[Dict[str, Any]]:
    """Load pre-configured servers from JSON file"""
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    return data.get('servers', [])


def create_mcp_registry_entry(server_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create MCP registry entry from server data"""

    # Map transport types to standardized format
    transport_type = server_data.get('transport', 'http')

    return {
        'server_id': server_data.get('id'),
        'name': server_data['name'],
        'description': server_data.get('description', ''),
        'transport_type': transport_type,
        'url': server_data.get('url'),
        'headers': server_data.get('headers', {}),
        'favicon_url': server_data.get('favicon_url', ''),
        'category': server_data.get('category', ''),
        'icon': server_data.get('icon', ''),
        'requires_auth': server_data.get('requiresAuth', False),
        'env_vars': server_data.get('env_vars', ''),
        'note': server_data.get('note', ''),
        'enabled': True,
        'status': 'unknown',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }


def upload_servers_to_database(servers: List[Dict[str, Any]]):
    """Upload servers to the database using SQLAlchemy ORM"""
    from vmcp.backend.storage.database import SessionLocal, init_db
    from vmcp.backend.storage.models import GlobalMCPServerRegistry
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

    # Ensure tables exist
    init_db()

    session = SessionLocal()
    try:
        # Clear existing data
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Clearing existing registry data...", total=None)
            session.query(GlobalMCPServerRegistry).delete()
            session.commit()

        # Upload each server with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
        ) as progress:
            upload_task = progress.add_task(
                "[cyan]Loading MCP servers into registry...",
                total=len(servers)
            )

            failed_count = 0
            for i, server_data in enumerate(servers):
                try:
                    # Create registry entry
                    registry_data = create_mcp_registry_entry(server_data)

                    # Create database record
                    registry_entry = GlobalMCPServerRegistry(
                        server_id=registry_data['server_id'],
                        name=registry_data['name'],
                        description=registry_data['description'],
                        transport_type=registry_data['transport_type'],
                        url=registry_data['url'],
                        headers=registry_data['headers'],
                        favicon_url=registry_data['favicon_url'],
                        category=registry_data['category'],
                        icon=registry_data['icon'],
                        requires_auth=registry_data['requires_auth'],
                        env_vars=registry_data['env_vars'],
                        note=registry_data['note'],
                        enabled=registry_data['enabled'],
                        status=registry_data['status']
                    )

                    session.add(registry_entry)
                    progress.update(upload_task, advance=1)

                except Exception as e:
                    failed_count += 1
                    progress.console.print(f"[yellow]⚠[/yellow] Error processing {server_data.get('name', 'unknown')}: {e}")
                    progress.update(upload_task, advance=1)
                    continue

        # Commit all changes
        session.commit()

        # Use Rich console for colored output
        from rich.console import Console
        console = Console()

        success_count = len(servers) - failed_count
        console.print(f"[green]✓[/green] Successfully loaded {success_count}/{len(servers)} servers into registry")
        if failed_count > 0:
            console.print(f"[yellow]⚠[/yellow] {failed_count} server(s) failed to load")

    except Exception as e:
        from rich.console import Console
        console = Console()
        console.print(f"[red]✗[/red] Database error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def main():
    """Main function"""
    from rich.console import Console

    console = Console()

    # Check if JSON file exists
    if not JSON_FILE.exists():
        console.print(f"[red]✗[/red] Error: JSON file not found at {JSON_FILE}")
        sys.exit(1)

    # Load servers
    servers = load_preconfigured_servers(JSON_FILE)
    console.print(f"[cyan]Found {len(servers)} preconfigured MCP servers[/cyan]")

    # Upload to database
    upload_servers_to_database(servers)


if __name__ == "__main__":
    main()
