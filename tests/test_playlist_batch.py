"""Check batch playlist operations against durable state and independent list models."""

import shutil
import sqlite3
from contextlib import closing
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st
from sqlalchemy import event, text
from sqlalchemy.exc import IntegrityError

from pyrekordbox import MasterDatabase
from pyrekordbox.masterdb import models
from pyrekordbox.masterdb.smartlist import SmartList

TEST_ROOT = Path(__file__).resolve().parents[1] / ".testdata" / "rekordbox 6"
CONTENT_IDS = [178162577, 66382436, 178162577, 181094952, 24401986, 66382436]


@pytest.fixture
def batch_db(tmp_path, monkeypatch):
    """Use only copies of the repository's public database and XML fixtures."""
    monkeypatch.setattr("pyrekordbox.masterdb.database.get_config", lambda *args: {})
    monkeypatch.setattr("pyrekordbox.masterdb.database.get_rekordbox_pid", lambda: 0)
    path = tmp_path / "master.db"
    shutil.copyfile(TEST_ROOT / "master_unlocked.db", path)
    shutil.copyfile(TEST_ROOT / "masterPlaylists6_template.xml", tmp_path / "masterPlaylists6.xml")
    db = MasterDatabase(path=path, db_dir=tmp_path, unlock=False)
    db.registry.enable_tracking()
    playlist = db.create_playlist("Batch operations")
    songs = [db.add_to_playlist(playlist, content_id) for content_id in CONTENT_IDS]
    other = db.create_playlist("Other playlist")
    foreign = db.add_to_playlist(other, CONTENT_IDS[0])
    folder = db.create_playlist_folder("Folder")
    smart = db.create_smart_playlist("Smart playlist", SmartList())
    db.commit()
    ids = [song.ID for song in songs]
    try:
        yield db, path, playlist.ID, ids, foreign.ID, folder.ID, smart.ID
    finally:
        db.registry.enable_tracking()
        if db.session is not None:
            db.rollback()
            db.close()
        db.engine.dispose()


def snapshot(path):
    """Read every playlist member, USN, and content row without touching the ORM."""
    with closing(sqlite3.connect(path)) as connection:
        rows = connection.execute(
            "SELECT ID, PlaylistID, ContentID, TrackNo, rb_local_usn, updated_at "
            "FROM djmdSongPlaylist ORDER BY PlaylistID, TrackNo, ID"
        ).fetchall()
        usn = connection.execute(
            "SELECT int_1 FROM agentRegistry WHERE registry_id='localUpdateCount'"
        ).fetchone()[0]
        contents = connection.execute("SELECT * FROM djmdContent ORDER BY ID").fetchall()
    return rows, usn, contents, path.with_name("masterPlaylists6.xml").read_bytes()


def members(db, playlist_id):
    """Read the caller's current order, including its pending changes."""
    return (
        db.get_playlist_songs(PlaylistID=playlist_id)
        .order_by(models.DjmdSongPlaylist.TrackNo)
        .all()
    )


def operate(db, operation, playlist, songs, position=1):
    """Call either public batch API with the same selection."""
    if operation == "remove":
        db.remove_songs_from_playlist(playlist, songs)
    else:
        db.move_songs_in_playlist(playlist, songs, position)


@pytest.mark.parametrize("operation", ["remove", "move"])
@pytest.mark.parametrize("as_objects", [False, True])
def test_batches_stage_then_commit_once(batch_db, operation, as_objects):
    db, path, pid, ids, *_ = batch_db
    before = snapshot(path)
    commits = []
    event.listen(db.session, "after_commit", lambda session: commits.append(True))
    songs = members(db, pid)
    playlist = db.get_playlist(ID=pid) if as_objects else pid
    selected = [songs[1], songs[3]] if as_objects else [ids[1], ids[3]]
    operate(db, operation, playlist, selected, 1)
    expected = [ids[i] for i in ((0, 2, 4, 5) if operation == "remove" else (1, 3, 0, 2, 4, 5))]
    assert [song.ID for song in members(db, pid)] == expected
    assert snapshot(path) == before
    assert commits == []
    db.commit()
    rows, usn, contents, xml = snapshot(path)
    own = [row for row in rows if row[1] == pid]
    assert [row[0] for row in own] == expected
    assert [row[3] for row in own] == list(range(1, len(expected) + 1))
    old = {row[0]: row for row in before[0]}
    changed = [row for row in own if old[row[0]][3] != row[3]]
    assert {row[4] for row in changed} == {usn}
    assert all(row[5] != old[row[0]][5] for row in changed)
    assert all(row == old[row[0]] for row in own if row not in changed)
    assert [row for row in rows if row[1] != pid] == [row for row in before[0] if row[1] != pid]
    assert usn == before[1] + (3 if operation == "remove" else 1)
    assert (contents, xml) == before[2:]
    # Removing one occurrence of a content ID preserves its other occurrence.
    assert sum(row[2] == str(CONTENT_IDS[0]) for row in own) == 2
    assert commits == [True]


@pytest.mark.parametrize("operation", ["remove", "move"])
def test_rollback_also_restores_pending_metadata(batch_db, operation):
    db, path, pid, ids, *_ = batch_db
    before = snapshot(path)
    db.get_content(ID=CONTENT_IDS[0]).Title = "Pending metadata"
    operate(db, operation, pid, [ids[0], ids[4]], 3)
    db.flush()
    assert snapshot(path) == before
    db.rollback()
    assert snapshot(path) == before
    assert [song.ID for song in members(db, pid)] == ids


@pytest.mark.parametrize("operation", ["remove", "move"])
def test_repeated_member_references_are_processed_once(batch_db, operation):
    db, path, pid, ids, *_ = batch_db
    before = snapshot(path)
    song = members(db, pid)[1]
    operate(db, operation, pid, [ids[1], song, ids[3], ids[1]], 1)
    db.commit()
    rows, usn, *_ = snapshot(path)
    expected = [ids[i] for i in ((0, 2, 4, 5) if operation == "remove" else (1, 3, 0, 2, 4, 5))]
    assert [row[0] for row in rows if row[1] == pid] == expected
    assert usn == before[1] + (3 if operation == "remove" else 1)


@pytest.mark.parametrize("operation", ["remove", "move"])
@pytest.mark.parametrize("invalid", ["missing", "foreign", "content", "type", "scalar"])
def test_invalid_selection_has_no_partial_changes(batch_db, operation, invalid):
    db, path, pid, ids, foreign, *_ = batch_db
    before = snapshot(path)
    bad = {"missing": "missing", "foreign": foreign, "content": CONTENT_IDS[0], "type": None}
    selection = ids[0] if invalid == "scalar" else [ids[0], bad[invalid]]
    error = TypeError if invalid in ("type", "scalar") else ValueError
    with pytest.raises(error):
        operate(db, operation, pid, selection)
    assert not db.session.dirty
    assert not db.session.deleted
    db.commit()
    assert snapshot(path) == before


@pytest.mark.parametrize("operation", ["remove", "move"])
@pytest.mark.parametrize("invalid", ["missing", "folder", "smart"])
def test_rejects_missing_or_non_normal_playlists(batch_db, operation, invalid):
    db, path, _, ids, _, folder, smart = batch_db
    before = snapshot(path)
    pid = {"missing": "missing", "folder": folder, "smart": smart}[invalid]
    with pytest.raises(ValueError):
        operate(db, operation, pid, ids[:1])
    db.commit()
    assert snapshot(path) == before


@pytest.mark.parametrize("position", [0, -1, 6, 7, 1.5, "1", True, None])
def test_invalid_move_position_has_no_changes(batch_db, position):
    db, path, pid, ids, *_ = batch_db
    before = snapshot(path)
    error = ValueError if type(position) is int else TypeError
    with pytest.raises(error):
        db.move_songs_in_playlist(pid, ids[:2], position)
    db.commit()
    assert snapshot(path) == before


@pytest.mark.parametrize("operation", ["remove", "move"])
def test_empty_selection_does_not_write(batch_db, operation):
    db, path, pid, _, *_ = batch_db
    before = snapshot(path)
    operate(db, operation, pid, [])
    assert not db.session.dirty
    assert not db.session.deleted
    db.commit()
    assert snapshot(path) == before


@pytest.mark.parametrize("selection,position", [([1, 2], 2), ([5], 6), (list(range(6)), 1)])
def test_unchanged_order_does_not_write(batch_db, selection, position):
    db, path, pid, ids, *_ = batch_db
    before = snapshot(path)
    db.move_songs_in_playlist(pid, [ids[i] for i in selection], position)
    assert not db.session.dirty
    db.commit()
    assert snapshot(path) == before


def test_removing_tail_does_not_register_a_move(batch_db):
    db, path, pid, ids, *_ = batch_db
    before = snapshot(path)
    db.remove_songs_from_playlist(pid, ids[-2:])
    db.commit()
    rows, usn, *_ = snapshot(path)
    assert [row for row in rows if row[1] == pid] == [row for row in before[0] if row[1] == pid][:4]
    assert usn == before[1] + 2


def test_remove_all_members(batch_db):
    db, path, pid, ids, *_ = batch_db
    before = snapshot(path)
    db.remove_songs_from_playlist(pid, ids)
    db.commit()
    rows, usn, contents, xml = snapshot(path)
    assert not [row for row in rows if row[1] == pid]
    assert usn == before[1] + len(ids)
    assert (contents, xml) == before[2:]


def test_batches_compose_with_pending_additions_and_removals(batch_db):
    db, path, pid, ids, *_ = batch_db
    commits = []
    event.listen(db.session, "after_commit", lambda session: commits.append(True))
    added = db.add_to_playlist(pid, CONTENT_IDS[0])
    db.remove_songs_from_playlist(pid, [ids[1], ids[4]])
    db.move_songs_in_playlist(pid, [added, ids[3]], 2)
    db.remove_songs_from_playlist(pid, [ids[0]])
    db.commit()
    rows = [row for row in snapshot(path)[0] if row[1] == pid]
    assert [row[0] for row in rows] == [added.ID, ids[3], ids[2], ids[5]]
    assert [row[3] for row in rows] == [1, 2, 3, 4]
    assert commits == [True]


@pytest.mark.parametrize("operation", ["remove", "move"])
def test_batches_compose_without_autoflush(batch_db, operation):
    db, path, pid, ids, *_ = batch_db
    before = snapshot(path)
    with db.no_autoflush:
        if operation == "remove":
            db.remove_songs_from_playlist(pid, ids[:1])
            db.remove_songs_from_playlist(pid, ids[1:2])
            expected = ids[2:]
        else:
            db.move_songs_in_playlist(pid, ids[-1:], 1)
            db.move_songs_in_playlist(pid, ids[1:2], 1)
            expected = [ids[i] for i in (1, 5, 0, 2, 3, 4)]
        assert snapshot(path) == before
    db.commit()
    rows, usn, *_ = snapshot(path)
    own = [row for row in rows if row[1] == pid]
    assert [row[0] for row in own] == expected
    assert [row[3] for row in own] == list(range(1, len(expected) + 1))
    assert usn == before[1] + (4 if operation == "remove" else 2)


@pytest.mark.parametrize("operation", ["remove", "move"])
def test_batch_sees_pending_addition_without_autoflush(batch_db, operation):
    db, path, pid, ids, *_ = batch_db
    before = snapshot(path)
    with db.no_autoflush:
        song = db.add_to_playlist(pid, CONTENT_IDS[0])
        operate(db, operation, pid, [song], 1)
        assert snapshot(path) == before
    db.commit()
    own = [row for row in snapshot(path)[0] if row[1] == pid]
    expected = ids if operation == "remove" else [song.ID] + ids
    assert [row[0] for row in own] == expected
    assert [row[3] for row in own] == list(range(1, len(expected) + 1))


@pytest.mark.parametrize("operation", ["remove", "move"])
def test_batch_rejects_pending_deletion_without_autoflush(batch_db, operation):
    db, path, pid, ids, *_ = batch_db
    before = snapshot(path)
    with db.no_autoflush:
        db.remove_songs_from_playlist(pid, ids[:1])
        with pytest.raises(ValueError, match="is not in playlist"):
            operate(db, operation, pid, [ids[0]])
        assert snapshot(path) == before
    db.rollback()
    assert snapshot(path) == before


@pytest.mark.parametrize("operation", ["remove", "move"])
def test_empty_batch_flushes_pending_edits_without_committing(batch_db, operation):
    db, path, pid, _, *_ = batch_db
    before = snapshot(path)
    content = db.get_content(ID=CONTENT_IDS[0])
    with db.no_autoflush:
        content.Title = "Pending metadata"
        operate(db, operation, pid, [])
        title = db.session.execute(
            text("SELECT Title FROM djmdContent WHERE ID=:id"), {"id": content.ID}
        ).scalar_one()
        assert title == "Pending metadata"
        assert snapshot(path) == before
    db.rollback()
    assert snapshot(path) == before


def test_invalid_later_batch_preserves_earlier_staged_edits(batch_db):
    db, path, pid, ids, foreign, *_ = batch_db
    before = snapshot(path)
    db.remove_songs_from_playlist(pid, ids[:1])
    with pytest.raises(ValueError):
        db.move_songs_in_playlist(pid, [ids[1], foreign], 1)
    assert snapshot(path) == before
    db.commit()
    assert [row[0] for row in snapshot(path)[0] if row[1] == pid] == ids[1:]


@pytest.mark.parametrize("operation", ["remove", "move"])
def test_selection_loads_members_once(batch_db, operation):
    db, _, pid, ids, *_ = batch_db
    statements = []

    def record(conn, cursor, statement, parameters, context, executemany):
        normalized = statement.replace('"', "").lstrip().upper()
        if normalized.startswith("SELECT") and "FROM DJMDSONGPLAYLIST" in normalized:
            statements.append(statement)

    event.listen(db.engine, "before_cursor_execute", record)
    operate(db, operation, pid, ids[:3], 4)
    event.remove(db.engine, "before_cursor_execute", record)
    assert len(statements) == 1


def test_single_member_move_matches_existing_method(batch_db):
    db, _, pid, ids, *_ = batch_db
    for song_id in ids:
        for position in range(1, len(ids) + 1):
            db.move_song_in_playlist(pid, song_id, position)
            expected = [(song.ID, song.TrackNo) for song in members(db, pid)]
            db.rollback()
            db.move_songs_in_playlist(pid, [song_id], position)
            assert [(song.ID, song.TrackNo) for song in members(db, pid)] == expected
            db.rollback()


@pytest.mark.parametrize("operation", ["remove", "move"])
def test_sql_failure_rolls_back_whole_batch(batch_db, operation):
    db, path, pid, ids, *_ = batch_db
    db.session.execute(
        text(
            "CREATE TRIGGER reject_batch BEFORE UPDATE OF TrackNo ON djmdSongPlaylist "
            "WHEN OLD.TrackNo = 4 BEGIN SELECT RAISE(ABORT, 'numbering failed'); END"
        )
    )
    db.commit()
    before = snapshot(path)
    operate(db, operation, pid, ids[:2], 5)
    with pytest.raises(IntegrityError, match="numbering failed"):
        db.flush()
    db.rollback()
    assert snapshot(path) == before
    assert [song.ID for song in members(db, pid)] == ids


@pytest.mark.parametrize("operation", ["remove", "move"])
def test_failure_after_flush_is_not_durable(batch_db, operation):
    db, path, pid, ids, *_ = batch_db
    before = snapshot(path)

    def fail(session, context):
        raise RuntimeError("flush failed")

    operate(db, operation, pid, ids[:2], 5)
    event.listen(db.session, "after_flush", fail)
    with pytest.raises(RuntimeError, match="flush failed"):
        db.flush()
    event.remove(db.session, "after_flush", fail)
    db.rollback()
    assert snapshot(path) == before


@pytest.mark.parametrize("operation", ["remove", "move"])
def test_failure_before_commit_restores_assigned_usns(batch_db, operation):
    db, path, pid, ids, *_ = batch_db
    before = snapshot(path)

    def fail(session):
        assert db.get_local_usn() > before[1]
        raise RuntimeError("commit failed")

    operate(db, operation, pid, ids[:2], 5)
    event.listen(db.session, "before_commit", fail)
    with pytest.raises(RuntimeError, match="commit failed"):
        db.commit()
    event.remove(db.session, "before_commit", fail)
    db.rollback()
    assert snapshot(path) == before
    # A fresh operation after rollback must still be tracked correctly.
    operate(db, operation, pid, ids[:2], 5)
    db.commit()
    assert snapshot(path)[1] > before[1]


@pytest.mark.parametrize("operation", ["remove", "move"])
def test_auxiliary_xml_failure_happens_after_database_commit(batch_db, operation):
    db, path, pid, ids, *_ = batch_db
    before = snapshot(path)
    # Queue a real auxiliary XML edit so commit must save it after committing SQL.
    db.playlist_xml.update(
        pid, updated_at=db.get_playlist(ID=pid).updated_at - timedelta(seconds=10)
    )
    operate(db, operation, pid, ids[:2], 5)
    with patch.object(db.playlist_xml, "save", side_effect=OSError("XML save failed")):
        with pytest.raises(OSError, match="XML save failed"):
            db.commit()
    db.rollback()
    rows, usn, contents, xml = snapshot(path)
    expected = ids[2:] if operation == "remove" else ids[2:] + ids[:2]
    assert [row[0] for row in rows if row[1] == pid] == expected
    assert usn > before[1]
    assert (contents, xml) == before[2:]


def test_exception_during_second_delete_can_be_rolled_back(batch_db):
    db, path, pid, ids, *_ = batch_db
    before = snapshot(path)
    delete = db.delete
    calls = []

    def fail(song):
        calls.append(song.ID)
        if len(calls) == 2:
            raise RuntimeError("second deletion failed")
        delete(song)

    with patch.object(db, "delete", side_effect=fail):
        with pytest.raises(RuntimeError, match="second deletion failed"):
            db.remove_songs_from_playlist(pid, ids[:2])
    db.rollback()
    assert snapshot(path) == before


@pytest.mark.parametrize("operation", ["remove", "move"])
def test_exception_during_numbering_restores_registry_tracking(batch_db, operation):
    db, path, pid, ids, *_ = batch_db
    before = snapshot(path)

    def fail(target, value, old_value, initiator):
        if target.ID == ids[3]:
            raise RuntimeError("numbering failed")

    event.listen(models.DjmdSongPlaylist.TrackNo, "set", fail)
    try:
        with pytest.raises(RuntimeError, match="numbering failed"):
            operate(db, operation, pid, ids[:2], 5)
    finally:
        event.remove(models.DjmdSongPlaylist.TrackNo, "set", fail)
    assert db.registry.__enabled__
    db.rollback()
    assert snapshot(path) == before


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(order=st.permutations(range(6)), count=st.integers(0, 6), offset=st.integers(0, 6))
def test_move_matches_independent_position_model(batch_db, order, count, offset):
    db, path, pid, ids, *_ = batch_db
    before = snapshot(path)
    selection = [ids[i] for i in order[:count]]
    position = offset % (len(ids) - count + 1) + 1
    expected = [None] * len(ids)
    for index, song_id in enumerate(selection, start=position - 1):
        expected[index] = song_id
    remaining = iter(song_id for song_id in ids if song_id not in selection)
    expected = [next(remaining) if song_id is None else song_id for song_id in expected]
    try:
        db.move_songs_in_playlist(pid, selection, position)
        actual = members(db, pid)
        assert [song.ID for song in actual] == expected
        assert [song.TrackNo for song in actual] == list(range(1, 7))
        assert snapshot(path) == before
    finally:
        db.rollback()


@settings(
    max_examples=64,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(mask=st.integers(0, 63))
def test_remove_matches_membership_model(batch_db, mask):
    db, path, pid, ids, *_ = batch_db
    before = snapshot(path)
    selection = [song_id for index, song_id in enumerate(ids) if mask & (1 << index)]
    expected = [song_id for song_id in ids if song_id not in selection]
    try:
        db.remove_songs_from_playlist(pid, selection)
        actual = members(db, pid)
        assert [song.ID for song in actual] == expected
        assert [song.TrackNo for song in actual] == list(range(1, len(expected) + 1))
        assert snapshot(path) == before
    finally:
        db.rollback()
