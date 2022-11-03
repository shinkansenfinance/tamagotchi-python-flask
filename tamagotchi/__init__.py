import click
from .app import app, db
from .views import *


@app.cli.add_command
@click.command("init-db")
def init_db():
    db.create_all()
    click.echo(f'Initialized the database: {app.config["SQLALCHEMY_DATABASE_URI"]}')
