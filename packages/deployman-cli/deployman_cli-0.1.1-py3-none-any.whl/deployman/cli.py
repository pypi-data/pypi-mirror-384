import typer

from deployman.bootstrap import bootstrap

from deployman.commands.service import get_app as get_service_app
from deployman.commands.targets import get_app as get_targets_app


bootstrap()


app = typer.Typer(help="deployman — manage deployment targets and deployments")
app.add_typer(get_service_app(), name="service")
app.add_typer(get_targets_app(), name="targets")
