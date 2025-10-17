import click
import sienna
from arxivfeedagent import user_dir


@click.group()
def cli():
    pass


@cli.command(name="set")
@click.argument("url")
@click.argument("key")
def set_endpoint(url: str, key: str):
    path = user_dir() / "endpoint.json"
    sienna.save({"url": url, "key": key}, path)
