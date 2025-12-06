import click
from flask.cli import with_appcontext

from app.models.roles import ensure_default_roles


@click.command("seed")
@with_appcontext
def seed():
    ensure_default_roles()
