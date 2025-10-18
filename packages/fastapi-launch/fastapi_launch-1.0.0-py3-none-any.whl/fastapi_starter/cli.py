"""CLI entry point for FastAPI Starter."""

import shutil
from pathlib import Path

import click


@click.group()
def cli() -> None:
    """FastAPI Starter CLI - Quickly scaffold FastAPI projects."""


@cli.command()
@click.option("--name", default="fastapi_app", help="Project folder name")
@click.option("--path", "-p", default=".", help="Path where to create the project")
def init(name: str, path: str) -> None:
    """Initialize a new FastAPI project."""
    dest = Path(path) / name
    src = Path(__file__).parent / "template"

    if dest.exists():
        click.echo(f"❌ Folder '{name}' already exists.")
        return

    try:
        _ = shutil.copytree(src, dest)
        click.echo(f"✅ FastAPI project created at {dest}")
        click.echo(f"📁 Project location: {dest.absolute()}")
        click.echo("\n🚀 Next steps:")
        click.echo("1. cd into your project directory")
        click.echo("2. Follow the setup instructions in README.md")
        click.echo("   - Install dependencies: uv sync")
        click.echo("   - Set up environment variables")
        click.echo("   - Create your database")
        click.echo("   - Run migrations: uv run alembic upgrade head")
        click.echo("   - Start the server: uv run python run.py")
    except Exception as e:
        click.echo(f"❌ Error creating project: {e}")


if __name__ == "__main__":
    cli()
