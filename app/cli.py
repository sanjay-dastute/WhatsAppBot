# Author: SANJAY KR
import click
from flask.cli import with_appcontext
from . import db
from .models.family import Samaj, Member

@click.command('check-db')
@with_appcontext
def check_db():
    """Check database records."""
    try:
        samaj_count = db.session.query(Samaj).count()
        member_count = db.session.query(Member).count()
        click.echo(f'Total Samaj records: {samaj_count}')
        click.echo(f'Total Member records: {member_count}')
    except Exception as e:
        click.echo(f'Error checking database: {str(e)}')

def init_app(app):
    app.cli.add_command(check_db)
