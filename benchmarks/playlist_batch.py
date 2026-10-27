"""Compare single-member loops and batch APIs using temporary SQLCipher fixtures.

Run from the repository root with ``python -m benchmarks.playlist_batch``.
The removal baseline requires the optional ``commit=False`` argument introduced
by PR #226. Both strategies commit once. No installed rekordbox library is read
or written, and all generated databases are deleted when the script exits.

Timings include the lazy first connection and SQLCipher KDF, but exclude fixture
creation, copying, database closure, and durable-result checks. This is a small,
single-host benchmark with warm filesystem caches and uncontrolled background
load. It does not measure UI latency or native rekordbox compatibility. Cursor
counts treat executemany as one call, not one affected SQL row.
"""

import argparse
import hashlib
import json
import platform
import shutil
import statistics
import sys
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator
from unittest.mock import patch

from sqlalchemy import MetaData, create_engine, event
from sqlalchemy.engine import Connection
from sqlcipher3 import dbapi2

import pyrekordbox
from pyrekordbox import MasterDatabase
from pyrekordbox.masterdb import models
from pyrekordbox.masterdb.database import BLOB
from pyrekordbox.utils import deobfuscate

INITIAL_USN = 10000
FIXED_TIME = datetime(2026, 1, 1, 12)


@dataclass
class Counts:
    commits: int = 0
    cursor_calls: int = 0
    selects: int = 0
    updates: int = 0
    deletes: int = 0


@dataclass
class Measurement:
    operation: str
    strategy: str
    repeat: int
    milliseconds: float
    counts: Counts


def column_values(model: type[models.Base], **overrides: object) -> dict[str, object]:
    """Populate required columns for these synthetic, non-audio fixtures."""
    result: dict[str, object] = {}
    for column in model.__table__.columns:
        if column.nullable or column.default is not None:
            continue
        if column.key.startswith("date_"):
            result[column.key] = FIXED_TIME
        elif column.type.python_type in (int, float):
            result[column.key] = 0
        else:
            result[column.key] = ""
    result.update(created_at=FIXED_TIME, updated_at=FIXED_TIME)
    result.update(overrides)
    return result


def seed_fixture(folder: Path, size: int) -> Path:
    """Create a synthetic encrypted database in a new temporary subdirectory."""
    folder.mkdir()
    path = folder / "master.db"
    engine = create_engine(f"sqlite+pysqlcipher://:{deobfuscate(BLOB)}@/{path}?", module=dbapi2)
    schema = MetaData()
    for table in models.Base.metadata.sorted_tables:
        copied = table.to_metadata(schema)
        if table.name == "djmdSongPlaylist":
            # Match the nullable USN columns in the repository's native fixture.
            for name in ("usn", "rb_local_usn"):
                copied.c[name].nullable = True
    try:
        schema.create_all(engine)
        with engine.begin() as connection:
            connection.execute(
                models.AgentRegistry.__table__.insert(),
                [
                    column_values(
                        models.AgentRegistry, registry_id="localUpdateCount", int_1=INITIAL_USN
                    )
                ],
            )
            connection.execute(
                models.DjmdPlaylist.__table__.insert(),
                [
                    column_values(
                        models.DjmdPlaylist, ID="10", Name="Fixture", ParentID="root", Seq=1
                    )
                ],
            )
            connection.execute(
                models.DjmdContent.__table__.insert(),
                [
                    column_values(
                        models.DjmdContent,
                        ID=str(i),
                        Title=f"Track {i}",
                        FolderPath=f"/synthetic-fixture/{i}.mp3",
                    )
                    for i in range(1, size + 1)
                ],
            )
            connection.execute(
                models.DjmdSongPlaylist.__table__.insert(),
                [
                    column_values(
                        models.DjmdSongPlaylist,
                        ID=str(100000 + i),
                        PlaylistID="10",
                        ContentID=str(i),
                        TrackNo=i,
                        rb_local_usn=100,
                    )
                    for i in range(1, size + 1)
                ],
            )
    finally:
        engine.dispose()
    timestamp = int(FIXED_TIME.timestamp() * 1000)
    path.with_name("masterPlaylists6.xml").write_text(
        '<MASTERPLAYLIST Version="1" AutomaticSync="0"><PRODUCT Version="7.2.16"/>'
        '<PLAYLISTS><NODE Id="A" ParentId="0" Attribute="0" '
        f'Timestamp="{timestamp}" Lib_Type="0" CheckType="0"/></PLAYLISTS></MASTERPLAYLIST>',
        encoding="utf-8",
    )
    return path


@contextmanager
def open_fixture(path: Path, temporary_root: Path) -> Iterator[MasterDatabase]:
    """Suppress process/config lookup only for a verified temporary fixture."""
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(temporary_root.resolve(strict=True)):
        raise ValueError("Benchmark database must be inside its new temporary directory")
    with (
        patch("pyrekordbox.masterdb.database.get_config", return_value={}),
        patch("pyrekordbox.masterdb.database.get_rekordbox_pid", return_value=0),
    ):
        db = MasterDatabase(path=resolved, db_dir=resolved.parent)
        try:
            yield db
        finally:
            db.close()
            db.engine.dispose()


def instrument(db: MasterDatabase) -> Counts:
    """Count SQL cursor calls and commits on the writer only."""
    counts = Counts()

    def record_sql(
        connection: Connection,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        counts.cursor_calls += 1
        command = statement.lstrip().split()[0].upper()
        if command == "SELECT":
            counts.selects += 1
        elif command == "UPDATE":
            counts.updates += 1
        elif command == "DELETE":
            counts.deletes += 1

    def record_commit(session: object) -> None:
        counts.commits += 1

    event.listen(db.engine, "before_cursor_execute", record_sql)
    event.listen(db.session, "after_commit", record_commit)
    return counts


def check_result(path: Path, expected: list[int], size: int, xml_before: bytes) -> None:
    """Verify durable order, numbering, content identity and USNs after closure."""
    connection = dbapi2.connect(str(path))
    try:
        connection.execute("PRAGMA key = '" + deobfuscate(BLOB) + "'")
        rows = connection.execute(
            "SELECT ID, ContentID, TrackNo, rb_local_usn FROM djmdSongPlaylist "
            "WHERE PlaylistID='10' ORDER BY TrackNo, ID"
        ).fetchall()
        usn = connection.execute(
            "SELECT int_1 FROM agentRegistry WHERE registry_id='localUpdateCount'"
        ).fetchone()[0]
        contents = connection.execute("SELECT ID, Title FROM djmdContent ORDER BY ID").fetchall()
    finally:
        connection.close()
    assert [(row[0], row[1], row[2]) for row in rows] == [
        (str(100000 + i), str(i), position) for position, i in enumerate(expected, start=1)
    ]
    assert usn > INITIAL_USN
    # Every survivor changes position in these two benchmark scenarios.
    assert all(INITIAL_USN < row[3] <= usn for row in rows)
    assert contents == sorted((str(i), f"Track {i}") for i in range(1, size + 1))
    assert path.with_name("masterPlaylists6.xml").read_bytes() == xml_before


def measure(root: Path, size: int, count: int, repeats: int) -> list[Measurement]:
    """Alternate strategies against identical fresh copies of one seed database."""
    base = seed_fixture(root / "base", size)
    xml_before = base.with_name("masterPlaylists6.xml").read_bytes()
    results = []
    for operation in ("remove", "move"):
        selected = (
            list(range(1, count + 1))
            if operation == "remove"
            else list(range(size - count + 1, size + 1))
        )
        expected = (
            list(range(count + 1, size + 1))
            if operation == "remove"
            else selected + list(range(1, size - count + 1))
        )
        for repeat in range(repeats):
            strategies = ("loop", "batch") if repeat % 2 == 0 else ("batch", "loop")
            for strategy in strategies:
                folder = root / f"{operation}-{strategy}-{repeat}"
                folder.mkdir()
                path = folder / "master.db"
                shutil.copyfile(base, path)
                path.with_name("masterPlaylists6.xml").write_bytes(xml_before)
                with open_fixture(path, root) as db:
                    counts = instrument(db)
                    start = time.perf_counter()
                    ids = [100000 + i for i in selected]
                    if strategy == "batch":
                        if operation == "remove":
                            db.remove_songs_from_playlist(10, ids)
                        else:
                            db.move_songs_in_playlist(10, ids, new_track_no=1)
                    elif operation == "remove":
                        for song_id in ids:
                            db.remove_from_playlist(10, song_id, commit=False)
                    else:
                        for position, song_id in enumerate(ids, start=1):
                            db.move_song_in_playlist(10, song_id, position)
                    db.commit()
                    elapsed = (time.perf_counter() - start) * 1000
                    recorded = Counts(**asdict(counts))
                check_result(path, expected, size, xml_before)
                assert recorded.commits == 1
                measurement = Measurement(operation, strategy, repeat, round(elapsed, 3), recorded)
                results.append(measurement)
                print(json.dumps(asdict(measurement)), file=sys.stderr, flush=True)
    return results


def main() -> None:
    """Run the benchmark, optionally saving the JSON report outside temporary storage."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=1000)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path, help="Write JSON to this file; otherwise use stdout")
    args = parser.parse_args()
    if not 0 < args.count < args.size or args.repeats < 1:
        parser.error("Require 0 < count < size and repeats >= 1")
    source = Path(pyrekordbox.__file__).parent / "masterdb" / "database.py"
    expected_source = Path(__file__).resolve().parents[1] / "pyrekordbox/masterdb/database.py"
    if source.resolve() != expected_source:
        parser.error("Run python -m benchmarks.playlist_batch from this checkout's root")
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    with TemporaryDirectory(prefix="pyrekordbox-playlist-batch-") as temporary:
        measurements = measure(Path(temporary), args.size, args.count, args.repeats)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
    summary = {}
    for operation in ("remove", "move"):
        summary[operation] = {}
        for strategy in ("loop", "batch"):
            samples = [
                item
                for item in measurements
                if item.operation == operation and item.strategy == strategy
            ]
            summary[operation][strategy] = {
                "medianMs": statistics.median(item.milliseconds for item in samples),
                "samplesMs": [item.milliseconds for item in samples],
                "cursorCalls": [item.counts.cursor_calls for item in samples],
                "commits": [item.counts.commits for item in samples],
            }
    report = {
        "sourceSha256": source_hash,
        "scriptSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": sys.version,
        "platform": platform.platform(),
        "playlistSize": args.size,
        "selectionSize": args.count,
        "repeats": args.repeats,
        "scope": __doc__,
        "samples": [asdict(item) for item in measurements],
        "summary": summary,
    }
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
