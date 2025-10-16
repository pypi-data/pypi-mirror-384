import asyncio
from sqlalchemy import delete
from faker import Faker
from functools import wraps
from click import Group
import click

from litestar.plugins import CLIPlugin
from app.core.database import session_maker

from .models import UserModel
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from polyfactory.fields import Use


faker = Faker()


class UserFactory(SQLAlchemyFactory[UserModel]):
    email = Use(faker.email)


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


class AuthPlugin(CLIPlugin):
    def on_cli_init(self, cli: Group) -> None:
        @cli.group(help="Manage auth, load data with ``load`` command")
        @click.version_option(prog_name="auth")
        def auth(): ...

        @auth.command(help="load auth data")
        @coro
        async def load():
            async with session_maker() as session:
                click.echo("Loading auth data...")

                for _ in range(10):
                    session.add(UserFactory.build())
                await session.commit()

        @auth.command(help="load auth data")
        @coro
        async def reset():
            async with session_maker() as session:
                await session.execute(delete(UserModel))

                for _ in range(10):
                    session.add(UserFactory.build())
                await session.commit()
