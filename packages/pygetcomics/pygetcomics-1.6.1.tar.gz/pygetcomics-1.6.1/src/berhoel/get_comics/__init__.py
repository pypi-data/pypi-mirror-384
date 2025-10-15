"""Download various daily comics."""

from __future__ import annotations

from importlib import metadata
import sys

import click
from playwright.sync_api import sync_playwright

from . import garfield, peanuts


@click.command()
@click.version_option(version=f"{metadata.version('pyGetComics')}")
def get_comics() -> None:
    """Download various periodic comics."""
    with sync_playwright() as playwright:
        sys.stdout.write("Get Peanuts.\n")
        peanuts.Peanuts(playwright)()
        sys.stdout.write("Get Garfield.\n")
        garfield.Garfield(playwright)()


if __name__ == "__main__":
    get_comics()
