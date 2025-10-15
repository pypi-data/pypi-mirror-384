from typing import Optional
import typer
from kink import inject
from rich.table import Table
from rich import print

from deployman.services.targets_service import TargetsService


def _print_targets_table(service: TargetsService) -> None:
    rows = service.list()
    table = Table(show_header=True, header_style="bold")
    table.add_column("Name", style="bold")
    table.add_column("Connector")
    table.add_column("Host")
    table.add_column("Port")
    table.add_column("User")
    table.add_column("Tags")
    for t in sorted(rows, key=lambda x: x.name):
        host = t.ssh.host if t.ssh else "-"
        port = str(t.ssh.port) if t.ssh else "-"
        user = t.ssh.username or "-" if t.ssh else "-"
        table.add_row(t.name, t.connector, host, port, user, ",".join(sorted(t.tags)))
    print(table)


class CommandTargets:
    @inject
    def __init__(self, targets_service: TargetsService) -> None:
        self.targets_service = targets_service

    def cmd_targets_list(self) -> None:
        """List all configured targets."""
        _print_targets_table(self.targets_service)

    def cmd_targets_add(
        self,
        name: str = typer.Option(..., help="Unique name of the target"),
        host: str = typer.Option(..., help="Hostname or IP"),
        user: Optional[str] = typer.Option(None, "--user", help="SSH username"),
        port: int = typer.Option(22, "--port", help="SSH port"),
        key_path: Optional[str] = typer.Option(None, "--key-path", help="Path to private key (optional)"),
        tags: str = typer.Option("", help="Comma-separated tags, e.g. prod,edge")
    ):
        """Add a new target (SSH)."""
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        t = self.targets_service.add(name=name, tags=tag_list, host=host, port=port, username=user, key_path=key_path)
        print(f"[green]Added target[/green]: {t.name} -> {t.ssh.host}:{t.ssh.port}")

    def cmd_targets_remove(
        self,
        name: str = typer.Option(..., help="Name of target to remove")
    ) -> None:
        """Remove a target by name."""
        if self.targets_service.remove(name):
            print(f"[yellow]Removed[/yellow] target: {name}")
        else:
            print(f"[red]No such target[/red]: {name}")

    def cmd_targets_check(
        self,
        name: Optional[str] = typer.Option(None, "--name", help="Name of a single target to check")
    ) -> None:
        """Check reachability of one target or all targets."""
        results = self.targets_service.check([name] if name else None)
        if not results:
            print("[yellow]No targets configured.[/yellow]")
            return
        table = Table(show_header=True, header_style="bold")
        table.add_column("Name", style="bold")
        table.add_column("Status")
        table.add_column("Message")
        for n, ok, msg in results:
            status = "OK" if ok else "FAIL"
            status_markup = f"[green]{status}[/green]" if ok else f"[red]{status}[/red]"
            table.add_row(n, status_markup, msg)
        print(table)


def get_app() -> typer.Typer:
    return typer.Typer(help="Manage targets")
