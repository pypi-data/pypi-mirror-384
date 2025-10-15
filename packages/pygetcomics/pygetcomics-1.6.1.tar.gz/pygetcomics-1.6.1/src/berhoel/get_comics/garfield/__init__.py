"""Download Garfield comic strips."""

from __future__ import annotations

from importlib import metadata
from pathlib import Path

import click
from playwright.sync_api import sync_playwright

from berhoel.get_comics.gocomics import GoComics


class Garfield(GoComics):
    """Download daily Garfield comcs fromGoComics."""

    # June 19, 1978
    start_year = 1978
    start_month = 6
    start_day = 19

    garfield_path = Path.home() / "Bilder" / "Garfield"

    gif_path_fmt = f"{garfield_path / '%Y' / '%m' / '%d.gif'}"
    png_path_fmt = f"{garfield_path / '%Y' / '%m' / '%d.png'}"
    url_fmt = "http://www.gocomics.com/garfield/%Y/%m/%d"

    statefile_name = garfield_path / "garfield.statfile"


@click.command()
@click.version_option(version=f"{metadata.version('pyGetComics')}")
def get_garfield() -> None:
    """Download daily Garfield comics."""
    with sync_playwright() as playwright:
        Garfield(playwright)()


if __name__ == "__main__":
    get_garfield()
