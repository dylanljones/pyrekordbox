# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2025-03-01

import functools
import json as json_
from typing import Tuple

import click

from pyrekordbox import Rekordbox6Database
from pyrekordbox.db6 import tables

from .cli import cli

SPACE = " "
HORIZONTAL = "│"
VERTICAL = "─"
TEE = "├"
LAST = "└"

PLAYLIST_LOGOS = {0: "📃", 1: "📁", 4: "⚙️", -128: "☁️"}


def _playlist_info(playlist: tables.DjmdPlaylist):
    logo = PLAYLIST_LOGOS.get(playlist.Attribute, "�?")
    name = playlist.Name
    return f"{logo} {name}"


def _song_info(song: tables.DjmdSongPlaylist):
    content = song.Content
    usn = song.rb_local_usn
    mtime = song.updated_at
    info = f" (USN={usn} Updated={mtime})"
    if content.ArtistName:
        return f"🎵 {content.Title} - {content.ArtistName}" + info
    return f"🎵 {content.Title}" + info


def _playlist_tree(
    playlist: tables.DjmdPlaylist,
    space: str,
    branch: str,
    tee: str,
    last: str,
    prefix: str = "",
    print_songs=True,
):
    """A recursive generator for the playlist tree."""
    if playlist.Attribute == 0 and print_songs:
        # Normal playlist: print all songs
        songs = list(playlist.Songs)  # noqa
        songs.sort(key=lambda x: x.TrackNo)
        # contents each get pointers that are ├── with a final └── :
        pointers = [tee] * (len(songs) - 1) + [last]
        for pointer, song in zip(pointers, songs):
            yield prefix + pointer + _song_info(song)

    elif playlist.Attribute == 1:
        # Playlist folder: print all children
        children = list(playlist.Children)  # noqa
        children.sort(key=lambda x: x.Seq)
        # contents each get pointers that are ├── with a final └── :
        child_pointers = [tee] * (len(children) - 1) + [last]
        for pointer, child in zip(child_pointers, children):
            yield prefix + pointer + _playlist_info(child)
            # extend the prefix and recurse:
            extension = branch if pointer == tee else space
            # i.e. space because last, └── , above so no more |
            yield from _playlist_tree(
                child, space, branch, tee, last, prefix + extension, print_songs
            )


def _iter_plalist_tree(db: Rekordbox6Database, songs: bool = True, indent: int = None):
    if indent is None:
        indent = 4  # default value

    if indent < 2:
        raise ValueError("Indentation must be at least 2")

    # prepare prefix components
    space = SPACE * indent
    branch = HORIZONTAL + (indent - 1) * SPACE
    tee = TEE + (indent - 2) * VERTICAL + SPACE
    last = LAST + (indent - 2) * VERTICAL + SPACE

    playlists = db.get_playlist(ParentID="root").all()
    playlists.sort(key=lambda x: x.Seq)
    for playlist in playlists:
        yield _playlist_info(playlist)
        yield from _playlist_tree(playlist, space, branch, tee, last, print_songs=songs)


def _song_to_dict(song: tables.DjmdSongPlaylist):
    content: tables.DjmdContent = song.Content
    return {
        "ID": content.ID,
        "Path": content.FolderPath,
        "Title": content.Title,
        "Artist": content.ArtistName,
        "Album": content.AlbumName,
    }


def _playlist_to_dict(pl: tables.DjmdPlaylist, contents: bool = False) -> dict:
    item = {
        "ID": pl.ID,
        "Name": pl.Name,
        "Attribute": pl.Attribute,
        "Seq": pl.Seq,
        "ParentID": pl.ParentID,
    }
    if pl.Attribute == 0:
        # Normal playlist: add songs
        if contents:
            songs = list(pl.Songs)  # noqa
            songs.sort(key=lambda x: x.TrackNo)

            item["Songs"] = list()
            for song in pl.Songs:
                item["Songs"].append(_song_to_dict(song))
    else:
        # Folder playlist: add children
        item["Children"] = list()
    return item


def _playlist_tree_json(db: Rekordbox6Database, contents: bool = False, indent: int = None) -> str:
    playlists = db.get_playlist(ParentID="root").all()
    playlists.sort(key=lambda x: x.Seq)

    items = [_playlist_to_dict(pl, contents) for pl in playlists]
    parents = list(zip(playlists, items))
    while parents:
        pl, pl_dict = parents.pop(0)
        for child in pl.Children:
            item = _playlist_to_dict(child, contents)
            pl_dict["Children"].append(item)
            parents.append((child, item))

    return json_.dumps(items, indent=indent)


@cli.group(name="playlist", help="Manage playlists.")
def playlist_cli():
    pass


def format_opt(func):
    """Click option decorator for human-readable output."""

    @click.option("--format", "-f", is_flag=True, help="Format output as human readable string.")
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def indent_opt(func):
    """Click option decorator for commands usiong indentaion."""

    @click.option("--indent", "-i", type=int, default=None, help="Indentation level.")
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


# noinspection PyShadowingBuiltins
@playlist_cli.command(name="tree")
@click.option("--songs", "-s", is_flag=True, help="Show songs contained in the playlists.")
@format_opt
@indent_opt
def playlist_tree(songs: bool, format: bool, indent: int = None):
    """Get the tree of playlists in the Rekordbox database."""
    db = Rekordbox6Database()
    if format:
        for line in _iter_plalist_tree(db, songs, indent):
            click.echo(line)
    else:
        s = _playlist_tree_json(db, songs, indent)
        click.echo(s)


# noinspection PyShadowingBuiltins
@playlist_cli.command(name="content")
@click.argument("playlist_id", type=str)
@format_opt
@indent_opt
def playlist_content(playlist_id: str, format: bool, indent: int = None):
    """Get the contents of a playlist."""
    db = Rekordbox6Database()
    playlist = db.get_playlist(ID=playlist_id)
    if playlist is None:
        click.echo(f"Playlist with ID '{playlist_id}' not found.")
        return
    if playlist.Attribute == 1:
        click.echo(f"Playlist '{playlist.Name}' is a folder and has no contents.")
        return

    songs = list(playlist.Songs)
    if format:
        for song in songs:
            click.echo(_song_info(song))
    else:
        s = json_.dumps([_song_to_dict(song) for song in songs], indent=indent)
        click.echo(s)


@playlist_cli.command(name="add")
@click.argument("playlist_id", type=str)
@click.argument("items", type=str, nargs=-1)
def add_content(playlist_id: str, items: Tuple[str]):
    r"""Add contents to a playlist.

    The items are a list of JSON strings representing the content to add.
    Each item should have a 'path' key with the path of the content.
    Optionally, a 'seq' key can be used to specify the sequence of the content.

    **Important**: On Windows, double quotes must be escaped with a backslash.

    Example:
    pyrekordbox playlist add 1234 [{\"path\": \"path/to/content\", \"seq\": 1}]
    """
    s = " ".join(items)
    data = json_.loads(s)

    db = Rekordbox6Database()
    playlist = db.get_playlist(ID=playlist_id)

    for item in data:
        path = item["path"]
        seq = item.get("seq", None)
        content = db.get_content(FolderPath=path).first()
        db.add_to_playlist(playlist, content, seq)

    db.commit()
