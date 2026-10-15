"""Exercise removal durability through independent SQLite readers."""

import shutil
import sqlite3
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import event, text
from sqlalchemy.exc import IntegrityError

from pyrekordbox import MasterDatabase
from pyrekordbox.masterdb import models

TEST_ROOT = Path(__file__).resolve().parents[1] / ".testdata" / "rekordbox 6"
CONTENT_IDS = [178162577, 66382436, 178162577, 181094952, 24401986, 66382436]


@pytest.fixture
def removal_db(tmp_path, monkeypatch):
    monkeypatch.setattr("pyrekordbox.masterdb.database.get_config", lambda *args: {})
    monkeypatch.setattr("pyrekordbox.masterdb.database.get_rekordbox_pid", lambda: 0)
    path = tmp_path / "master.db"
    shutil.copyfile(TEST_ROOT / "master_unlocked.db", path)
    shutil.copyfile(TEST_ROOT / "masterPlaylists6_template.xml", tmp_path / "masterPlaylists6.xml")
    db = MasterDatabase(path=path, db_dir=tmp_path, unlock=False)
    playlist = db.create_playlist("Removal transactions")
    songs = [db.add_to_playlist(playlist, content_id) for content_id in CONTENT_IDS]
    db.commit()
    playlist_id = playlist.ID
    song_ids = [song.ID for song in songs]
    try:
        yield db, path, playlist_id, song_ids
    finally:
        if db.session is not None:
            db.close()
        db.engine.dispose()


def snapshot(path, playlist_id):
    # A second MasterDatabase would clear the class-level registry buffer.
    # A raw reader observes durability without touching the writer's ORM state.
    with closing(sqlite3.connect(path)) as connection:
        songs = connection.execute(
            "SELECT ID, ContentID, TrackNo, rb_local_usn, updated_at "
            "FROM djmdSongPlaylist WHERE PlaylistID=? ORDER BY TrackNo, ID",
            (playlist_id,),
        ).fetchall()
        usn = connection.execute(
            "SELECT int_1 FROM agentRegistry WHERE registry_id='localUpdateCount'"
        ).fetchone()[0]
        titles = connection.execute("SELECT ID, Title FROM djmdContent ORDER BY ID").fetchall()
    return songs, usn, titles, path.with_name("masterPlaylists6.xml").read_bytes()


def count_commits(db):
    commits = []
    event.listen(db.session, "after_commit", lambda session: commits.append(True))
    return commits


@pytest.mark.parametrize("explicit", [False, True])
def test_default_commits_deletion_and_numbering_together(removal_db, explicit):
    db, path, playlist_id, song_ids = removal_db
    before = snapshot(path, playlist_id)
    commits = count_commits(db)
    kwargs = {"commit": True} if explicit else {}
    db.remove_from_playlist(playlist_id, song_ids[1], **kwargs)
    rows, usn, titles, xml = snapshot(path, playlist_id)
    assert [row[0] for row in rows] == song_ids[:1] + song_ids[2:]
    assert [row[2] for row in rows] == [1, 2, 3, 4, 5]
    assert rows[0][3] == before[0][0][3]
    assert all(row[3] == before[1] + 2 for row in rows[1:])
    assert usn == before[1] + 2
    assert (titles, xml) == before[2:]
    assert len(commits) == 1


@pytest.mark.parametrize("by_id", [False, True])
def test_deferred_removal_is_invisible_and_fully_rolls_back(removal_db, by_id):
    db, path, playlist_id, song_ids = removal_db
    before = snapshot(path, playlist_id)
    commits = count_commits(db)
    song = song_ids[1] if by_id else db.session.get(models.DjmdSongPlaylist, song_ids[1])
    db.get_content(ID=CONTENT_IDS[0]).Title = "Uncommitted metadata"
    db.remove_from_playlist(playlist_id, song, commit=False)
    rows = (
        db.get_playlist_songs(PlaylistID=playlist_id)
        .order_by(models.DjmdSongPlaylist.TrackNo)
        .all()
    )
    assert [row.TrackNo for row in rows] == [1, 2, 3, 4, 5]
    assert snapshot(path, playlist_id) == before
    db.rollback()
    assert snapshot(path, playlist_id) == before
    assert commits == []


def test_deferred_removals_share_one_commit_and_keep_duplicate_members(removal_db):
    db, path, playlist_id, song_ids = removal_db
    before = snapshot(path, playlist_id)
    commits = count_commits(db)
    for song_id in (song_ids[0], song_ids[3]):
        db.remove_from_playlist(playlist_id, song_id, commit=False)
    assert snapshot(path, playlist_id) == before
    db.commit()
    rows, usn, titles, xml = snapshot(path, playlist_id)
    assert [row[0] for row in rows] == [song_ids[i] for i in (1, 2, 4, 5)]
    assert [row[2] for row in rows] == [1, 2, 3, 4]
    # The other member of the same content survives the first deletion.
    assert rows[1][1] == str(CONTENT_IDS[0])
    assert all(before[1] < row[3] <= usn for row in rows)
    assert usn == before[1] + 4
    assert (titles, xml) == before[2:]
    assert len(commits) == 1


@pytest.mark.parametrize("deferred", [False, True])
def test_sql_numbering_failure_rolls_back_deletion_and_usn(removal_db, deferred):
    db, path, playlist_id, song_ids = removal_db
    db.session.execute(
        text(
            "CREATE TRIGGER reject_numbering BEFORE UPDATE OF TrackNo ON djmdSongPlaylist "
            "WHEN OLD.TrackNo = 4 BEGIN SELECT RAISE(ABORT, 'numbering failed'); END"
        )
    )
    db.commit()
    before = snapshot(path, playlist_id)
    commits = count_commits(db)
    kwargs = {"commit": False} if deferred else {}
    with pytest.raises(IntegrityError, match="numbering failed"):
        db.remove_from_playlist(playlist_id, song_ids[1], **kwargs)
        db.flush()
    db.rollback()
    assert snapshot(path, playlist_id) == before
    assert commits == []


def test_failure_before_commit_restores_assigned_usns(removal_db):
    db, path, playlist_id, song_ids = removal_db
    before = snapshot(path, playlist_id)
    commits = count_commits(db)

    def fail(session):
        assert db.get_local_usn() > before[1]
        raise RuntimeError("commit failed")

    event.listen(db.session, "before_commit", fail)
    with pytest.raises(RuntimeError, match="commit failed"):
        db.remove_from_playlist(playlist_id, song_ids[1])
    db.rollback()
    assert snapshot(path, playlist_id) == before
    assert commits == []


def test_failure_during_second_deletion_rolls_back_first(removal_db):
    db, path, playlist_id, song_ids = removal_db
    before = snapshot(path, playlist_id)
    commits = count_commits(db)
    db.remove_from_playlist(playlist_id, song_ids[0], commit=False)
    with patch.object(db, "delete", side_effect=RuntimeError("second deletion failed")):
        with pytest.raises(RuntimeError, match="second deletion failed"):
            db.remove_from_playlist(playlist_id, song_ids[1], commit=False)
    db.rollback()
    assert snapshot(path, playlist_id) == before
    assert commits == []


@pytest.mark.parametrize("fail", [False, True])
def test_deferred_removal_in_autocommit_context(removal_db, fail):
    db, path, playlist_id, song_ids = removal_db
    before = snapshot(path, playlist_id)
    commits = count_commits(db)
    db.autocommit = True

    def remove():
        with db:
            db.remove_from_playlist(playlist_id, song_ids[1], commit=False)
            if fail:
                raise RuntimeError("later operation failed")

    if fail:
        with pytest.raises(RuntimeError, match="later operation failed"):
            remove()
        assert snapshot(path, playlist_id) == before
        assert commits == []
    else:
        remove()
        rows = snapshot(path, playlist_id)[0]
        assert [row[0] for row in rows] == song_ids[:1] + song_ids[2:]
        assert [row[2] for row in rows] == [1, 2, 3, 4, 5]
        assert len(commits) == 1
