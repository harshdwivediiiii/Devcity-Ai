import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator


LOGGER = logging.getLogger(__name__)
DB_PATH = Path(__file__).resolve().parent / "codecity.db"


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def db_init() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS snapshots (
                id TEXT PRIMARY KEY,
                repo_url TEXT NOT NULL,
                label TEXT,
                branch TEXT DEFAULT 'main',
                created_at TEXT NOT NULL,
                file_count INTEGER DEFAULT 0,
                model_version TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS file_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id TEXT NOT NULL REFERENCES snapshots(id) ON DELETE CASCADE,
                name TEXT,
                path TEXT,
                extension TEXT,
                size INTEGER,
                byte_size INTEGER,
                complexity REAL,
                function_count INTEGER,
                avg_params REAL,
                depth INTEGER,
                churn INTEGER,
                bug_churn INTEGER,
                fan_out INTEGER,
                risk_score REAL,
                anomaly_score REAL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_fm_snapshot ON file_metrics(snapshot_id)"
        )


def insert_snapshot(meta: dict[str, Any]) -> None:
    created_at = str(meta.get("created_at") or (datetime.utcnow().isoformat() + "Z"))
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO snapshots (
                id, repo_url, label, branch, created_at, file_count, model_version
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                repo_url = excluded.repo_url,
                label = excluded.label,
                branch = excluded.branch,
                created_at = excluded.created_at,
                file_count = excluded.file_count,
                model_version = excluded.model_version
            """,
            (
                str(meta["id"]),
                str(meta["repo_url"]),
                meta.get("label"),
                str(meta.get("branch") or "main"),
                created_at,
                int(meta.get("file_count") or 0),
                meta.get("model_version"),
            ),
        )


def bulk_insert_file_metrics(snapshot_id: str, rows: list[dict]) -> None:
    values = [
        (
            snapshot_id,
            row.get("name"),
            row.get("path"),
            row.get("extension"),
            int(row.get("size") or 0),
            int(row.get("byte_size") or 0),
            float(row.get("complexity") or 0.0),
            int(row.get("function_count") or 0),
            float(row.get("avg_params") or 0.0),
            int(row.get("depth") or 0),
            int(row.get("churn") or 0),
            int(row.get("bug_churn") or 0),
            int(row.get("fan_out") or 0),
            None if row.get("risk_score") is None else float(row.get("risk_score")),
            None
            if row.get("anomaly_score") is None
            else float(row.get("anomaly_score")),
        )
        for row in rows
    ]

    with get_db() as conn:
        conn.execute("DELETE FROM file_metrics WHERE snapshot_id = ?", (snapshot_id,))
        if values:
            conn.executemany(
                """
                INSERT INTO file_metrics (
                    snapshot_id,
                    name,
                    path,
                    extension,
                    size,
                    byte_size,
                    complexity,
                    function_count,
                    avg_params,
                    depth,
                    churn,
                    bug_churn,
                    fan_out,
                    risk_score,
                    anomaly_score
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )


def get_snapshot_files(snapshot_id: str) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT
                name,
                path,
                extension,
                size,
                byte_size,
                complexity,
                function_count,
                avg_params,
                depth,
                churn,
                bug_churn,
                fan_out,
                risk_score,
                anomaly_score
            FROM file_metrics
            WHERE snapshot_id = ?
            ORDER BY path, name
            """,
            (snapshot_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_all_snapshots() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, repo_url, label, branch, created_at, file_count, model_version
            FROM snapshots
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def update_snapshot_file_count(snapshot_id: str, n: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE snapshots SET file_count = ? WHERE id = ?",
            (int(n), snapshot_id),
        )
