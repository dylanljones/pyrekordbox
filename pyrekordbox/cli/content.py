# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2025-04-07

import functools
import json as json_
from typing import Tuple

import click

from pyrekordbox import Rekordbox6Database

from .cli import cli


def format_opt(func):
    """Click option decorator for human-readable output."""

    @click.option("--format", "-f", is_flag=True, help="Format output as human readable string.")
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def indent_opt(func):
    """Click option decorator for commands using indentaion."""

    @click.option("--indent", "-i", type=int, default=None, help="Indentation level.")
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def content_id_arg(func):
    """Click argument decorator for commands using a content ID."""

    @click.argument("content_id", type=str, nargs=1)
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def content_items_args(func):
    """Click argument decorator for commands using content items."""

    @click.argument("items", type=str, nargs=-1)
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@cli.group(name="content", help="Manage content.")
def content_cli():
    pass


# noinspection PyShadowingBuiltins
@content_cli.command(name="list", help="List all content.")
@format_opt
@indent_opt
def list_content(format: bool, indent: int = None):
    """List all content in the database."""
    db = Rekordbox6Database()
    content = db.get_content()
    if format:
        for item in content:
            click.echo(f"ID: {item.ID}, Title: {item.Title}, Artist: {item.ArtistName}")
    else:
        data = [
            {
                "ID": item.ID,
                "Title": item.Title,
                "Artist": item.ArtistName,
                "Album": item.AlbumName,
            }
            for item in content
        ]
        string = json_.dumps(data, indent=indent)
        click.echo(string)


@content_cli.command(name="update-path", help="Update the path of a content item.")
@content_id_arg
@click.argument("path", type=str, nargs=1)
def update_content_path(content_id: str, path: str):
    """Update the path of a content item.

    Example:
    pyrekordbox content update-path 1234 'path/to/content'
    """
    db = Rekordbox6Database()
    content = db.get_content(ID=content_id).one()
    db.update_content_path(content, path, save=True, commit=True)


@content_cli.command(name="update-paths", help="Update the paths of multiple content paths.")
@click.argument("items", type=str, nargs=-1)
def update_content_paths(items: Tuple[str]):
    r"""Update the paths of multiple content paths.

    The items are a list of JSON strings representing the content to update.
    Each item should have a 'ID' key with the ID of the content and a 'Path' key with the new path.

    **Important**: On Windows, double quotes must be escaped with a backslash.

    Example:
    pyrekordbox content update-paths [{\"id\": 1234, \"path\": \"path/to/content\"}]
    """
    s = " ".join(items)
    data = json_.loads(s)

    db = Rekordbox6Database()
    for item in data:
        content_id = item["id"]
        path = item["path"]
        content = db.get_content(ID=content_id).one()
        db.update_content_path(content, path, save=True, commit=True)
