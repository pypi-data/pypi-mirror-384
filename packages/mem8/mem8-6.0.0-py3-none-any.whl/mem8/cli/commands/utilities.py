#!/usr/bin/env python3
"""
Utility commands: gh, tools, ports.
"""

import typer
from typing import Annotated, Optional
from pathlib import Path

from ..state import set_app_state
from ..utils import get_console

# Get console instance
console = get_console()

# ============================================================================
# GitHub CLI Integration
# ============================================================================

gh_app = typer.Typer(name="gh", help="GitHub CLI integration helpers")


@gh_app.command("whoami")
def gh_whoami(
    host: Annotated[str, typer.Option("--host", help="GitHub host")] = "github.com",
):
    """Show active GitHub CLI login and current repository context."""
    set_app_state()
    from ...integrations.github import get_consistent_github_context

    gh_context = get_consistent_github_context()

    if gh_context["username"]:
        console.print(f"Logged in to {host} as [bold]{gh_context['username']}[/bold]")

        if gh_context["org"] and gh_context["repo"]:
            console.print(f"Current repository: [bold]{gh_context['org']}/{gh_context['repo']}[/bold]")

            if gh_context["auth_user"] != gh_context["repo_owner"]:
                console.print(f"[dim]Note: You're authenticated as {gh_context['auth_user']} but this repo is owned by {gh_context['repo_owner']}[/dim]")
        else:
            console.print("[dim]No repository detected in current directory[/dim]")
    else:
        console.print("[yellow]gh not detected or no active login for this host[/yellow]")


# ============================================================================
# Tools Command
# ============================================================================

def register_tools_command(app: typer.Typer):
    """Register the tools command."""

    @app.command()
    def tools(
        save: Annotated[bool, typer.Option("--save", help="Save toolbelt to .mem8/tools.md")] = False,
        verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output")] = False
    ):
        """List toolbelt CLI tools and OS details for AI system prompts."""
        from ...core.toolbelt import check_toolbelt, save_toolbelt as save_tools_to_file
        from rich.table import Table

        set_app_state(verbose=verbose)

        # Check tools
        output_data = check_toolbelt()
        os_info = output_data['os']
        verified = output_data['tools']

        # Display to user
        console.print("[bold blue]System Environment[/bold blue]")
        console.print(f"OS: {os_info['system']} {os_info['release']} ({os_info['machine']})")
        console.print(f"Python: {os_info['python_version']}")

        console.print("\n[bold blue]Verified Tools[/bold blue]")
        if verified:
            table = Table()
            table.add_column("Tool", style="cyan")
            table.add_column("Version", style="green")

            for tool, version in sorted(verified.items()):
                table.add_row(tool, version)
            console.print(table)
        else:
            console.print("[yellow]No tools verified[/yellow]")

        # Save if requested
        if save:
            output_file = save_tools_to_file()
            console.print(f"\n✅ [green]Saved to {output_file}[/green]")
        else:
            console.print("\n💡 [dim]Use --save to write to .mem8/tools.md[/dim]")


# ============================================================================
# Ports Command
# ============================================================================

def register_ports_command(app: typer.Typer):
    """Register the ports command."""

    @app.command()
    def ports(
        lease: Annotated[bool, typer.Option("--lease", help="Lease new ports for this project")] = False,
        start: Annotated[Optional[int], typer.Option("--start", help="Starting port number (auto-assign if not specified)")] = None,
        count: Annotated[int, typer.Option("--count", help="Number of ports to lease")] = 5,
        release: Annotated[bool, typer.Option("--release", help="Release this project's port lease")] = False,
        list_all: Annotated[bool, typer.Option("--list-all", help="List all port leases across all projects")] = False,
        check_conflicts: Annotated[bool, typer.Option("--check-conflicts", help="Check for port conflicts")] = False,
        kill: Annotated[Optional[int], typer.Option("--kill", help="Kill process using specified port")] = None,
        force: Annotated[bool, typer.Option("--force", help="Force kill port outside project range")] = False,
        show: Annotated[bool, typer.Option("--show", help="Show current project's port assignments")] = True,
        verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output")] = False
    ):
        """Manage project port assignments to prevent conflicts across projects."""
        from ...core.ports import PortManager, save_ports_file

        set_app_state(verbose=verbose)

        manager = PortManager()

        # Kill port process
        if kill:
            console.print(f"[yellow]Attempting to kill process on port {kill}...[/yellow]")
            success, message = manager.kill_port(kill, force=force)
            if success:
                console.print(f"[green]✓ {message}[/green]")
            else:
                console.print(f"[red]✗ {message}[/red]")
                if not force and "outside project's range" in message:
                    console.print("[dim]Use --force to kill ports outside your range[/dim]")
            return

        # Release lease
        if release:
            if manager.release_lease():
                console.print("[green]✓ Port lease released[/green]")
                # Remove ports.md
                ports_file = Path.cwd() / ".mem8" / "ports.md"
                if ports_file.exists():
                    ports_file.unlink()
                    console.print(f"[dim]Removed {ports_file}[/dim]")
            else:
                console.print("[yellow]No active lease for this project[/yellow]")
            return

        # Check conflicts
        if check_conflicts:
            conflicts = manager.check_conflicts()
            if conflicts:
                console.print(f"[red]Found {len(conflicts)} port conflicts:[/red]")
                for conflict in conflicts:
                    console.print(f"  Port {conflict['port']}: {conflict['project1']} ⚠️  {conflict['project2']}")
            else:
                console.print("[green]✓ No port conflicts detected[/green]")
            return

        # List all leases
        if list_all:
            leases = manager.list_all_leases()
            if not leases:
                console.print("[yellow]No port leases found[/yellow]")
                return

            console.print(f"\n[bold]Global Port Leases[/bold] ({len(leases)} projects)\n")

            for project_path, lease in leases.items():
                console.print(f"[cyan]{lease['project_name']}[/cyan]")
                console.print(f"  Path: {project_path}")
                console.print(f"  Ports: {lease['port_range']}")
                console.print(f"  Leased: {lease['leased_at']}\n")

            console.print(f"[dim]Registry: {manager.registry_file}[/dim]")
            return

        # Lease new ports
        if lease:
            try:
                lease_info = manager.lease_ports(start=start, count=count)
                console.print(f"[green]✓ Leased ports {lease_info['port_range']}[/green]")
                console.print(f"[dim]{lease_info['port_count']} ports available for your services[/dim]")

                # Save ports.md
                output_file = save_ports_file(lease_info)
                console.print(f"[dim]Created {output_file}[/dim]")

            except ValueError as e:
                console.print(f"[red]Error: {e}[/red]")
                return

        # Show current lease (default)
        elif show:
            lease_info = manager.get_lease()
            if not lease_info:
                console.print("[yellow]No port lease for this project[/yellow]")
                console.print("\n[dim]Lease ports with:[/dim] mem8 ports --lease")
                console.print("[dim]Or specify a range:[/dim] mem8 ports --lease --start 20000 --count 5")
                return

            console.print(f"\n[bold]{lease_info['project_name']}[/bold]")
            console.print(f"Port Range: [cyan]{lease_info['port_range']}[/cyan]")
            console.print(f"Port Count: {lease_info['port_count']}")
            console.print(f"Leased: {lease_info['leased_at']}\n")

            console.print("[dim]Config file:[/dim] .mem8/ports.md")
            console.print("[dim]Global registry:[/dim] ~/.mem8/port_leases.yaml")
            console.print(f"\n[dim]Use any port in range {lease_info['port_range']} for your services[/dim]")
