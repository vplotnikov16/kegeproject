import click
from flask.cli import with_appcontext

from app.models.roles import ensure_default_roles
from app.models.users import ensure_default_admin_account


@click.command("seed")
@with_appcontext
def seed():
    ensure_default_roles()
    ensure_default_admin_account()
