import logging

import click

logger = logging.getLogger(__name__)


@click.command(help="Log in to AI Platform.")
@click.pass_obj
def login(client):
    print("Welcome to Renesas AI Platform")


@click.command(help="Log out to remove access to AI Platform.")
@click.pass_obj
def logout(client):
    print("Bye!")


@click.command(help="Show the current authenticated user info.")
@click.pass_obj
def whoami(client):
    print("test user 123")
