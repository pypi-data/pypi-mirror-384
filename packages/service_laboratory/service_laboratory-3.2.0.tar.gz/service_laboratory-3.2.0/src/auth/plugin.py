import asyncio
from sqlalchemy import delete
from faker import Faker
from functools import wraps
from click import Group
import click

from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from polyfactory.fields import Use
from litestar.plugins import CLIPlugin

from .models import UserModel


faker = Faker()


class UserFactory(SQLAlchemyFactory[UserModel]):
    email = Use(faker.email)


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


class AuthPlugin(CLIPlugin):
    def __init__(self, session_maker):
        self.session_maker = session_maker

    def on_cli_init(self, cli: Group) -> None:
        @cli.group(help="Manage auth, load data with ``load`` command")
        @click.version_option(prog_name="auth")
        def auth(): ...

        @auth.command(help="load auth data")
        @coro
        async def load():
            async with self.session_maker() as session:
                click.echo("Loading auth data...")

                for _ in range(10):
                    session.add(UserFactory.build())
                await session.commit()

        @auth.command(help="load auth data")
        @coro
        async def reset():
            async with self.session_maker() as session:
                await session.execute(delete(UserModel))

                for _ in range(10):
                    session.add(UserFactory.build())
                await session.commit()
