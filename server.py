from __future__ import annotations

import base64
import hmac
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "reports.sqlite3"
JSON_PATH = DATA_DIR / "reports.json"
DEFAULT_HOST = os.environ.get("HOST", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("PORT", "8000"))
DATABASE_URL = os.environ.get("DATABASE_URL")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")


@dataclass
class DuplicateReportError(Exception):
    message: str


class ReportStore:
    def __init__(self) -> None:
        self._use_postgres = bool(DATABASE_URL)
        if self._use_postgres:
            self._init_postgres()
        else:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            self._init_sqlite()
            self._bootstrap_from_json()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_reports(self) -> list[dict[str, Any]]:
        if self._use_postgres:
            return self._pg_list()
        return self._sqlite_list()

    def create_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        signature = str(payload.get("signature", "")).strip()
        export_markdown = str(payload.get("exportMarkdown", "")).strip()
        name = str(payload.get("name", "")).strip() or "Unbenannter Bericht"
        fachabteilung = str(payload.get("fachabteilung", "")).strip() or "-"
        timestamp = str(payload.get("timestamp", "")).strip() or _display_timestamp()
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}

        if not signature or not export_markdown:
            raise ValueError("signature and exportMarkdown are required")

        report_id = str(payload.get("id", "")).strip() or str(uuid4())
        now = _utc_timestamp()

        if self._use_postgres:
            self._pg_insert(report_id, signature, name, fachabteilung, timestamp,
                            export_markdown, summary, now)
        else:
            self._sqlite_insert(report_id, signature, name, fachabteilung, timestamp,
                                export_markdown, summary, now)

        return {
            "id": report_id,
            "signature": signature,
            "name": name,
            "fachabteilung": fachabteilung,
            "timestamp": timestamp,
            "exportMarkdown": export_markdown,
            "summary": summary,
        }

    def delete_report(self, report_id: str) -> bool:
        if self._use_postgres:
            return self._pg_delete(report_id)
        deleted = self._sqlite_delete(report_id)
        if deleted:
            self._sync_json_file()
        return deleted

    # ------------------------------------------------------------------
    # PostgreSQL backend
    # ------------------------------------------------------------------

    def _init_postgres(self) -> None:
        import psycopg2
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS reports (
                        id TEXT PRIMARY KEY,
                        signature TEXT NOT NULL UNIQUE,
                        name TEXT NOT NULL,
                        fachabteilung TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        export_markdown TEXT NOT NULL,
                        summary_json TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
            conn.commit()

    def _pg_list(self) -> list[dict[str, Any]]:
        import psycopg2.extras
        with psycopg2.connect(DATABASE_URL) as conn:  # type: ignore[name-defined]
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, signature, name, fachabteilung, timestamp,
                           export_markdown, summary_json
                    FROM reports
                    ORDER BY created_at DESC
                """)
                rows = cur.fetchall()
        return [_row_to_report(dict(row)) for row in rows]

    def _pg_insert(self, report_id: str, signature: str, name: str,
                   fachabteilung: str, timestamp: str, export_markdown: str,
                   summary: dict[str, Any], now: str) -> None:
        import psycopg2
        try:
            with psycopg2.connect(DATABASE_URL) as conn:  # type: ignore[name-defined]
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO reports (
                            id, signature, name, fachabteilung, timestamp,
                            export_markdown, summary_json, created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        report_id, signature, name, fachabteilung, timestamp,
                        export_markdown, json.dumps(summary, ensure_ascii=False),
                        now, now,
                    ))
                conn.commit()
        except psycopg2.errors.UniqueViolation:  # type: ignore[attr-defined]
            raise DuplicateReportError("Dieser Bericht ist bereits gespeichert.")

    def _pg_delete(self, report_id: str) -> bool:
        import psycopg2
        with psycopg2.connect(DATABASE_URL) as conn:  # type: ignore[name-defined]
            with conn.cursor() as cur:
                cur.execute("DELETE FROM reports WHERE id = %s", (report_id,))
                deleted = cur.rowcount > 0
            conn.commit()
        return deleted

    # ------------------------------------------------------------------
    # SQLite backend
    # ------------------------------------------------------------------

    def _sqlite_connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_sqlite(self) -> None:
        with self._sqlite_connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id TEXT PRIMARY KEY,
                    signature TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    fachabteilung TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    export_markdown TEXT NOT NULL,
                    summary_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def _sqlite_list(self) -> list[dict[str, Any]]:
        with self._sqlite_connect() as conn:
            rows = conn.execute("""
                SELECT id, signature, name, fachabteilung, timestamp,
                       export_markdown, summary_json
                FROM reports
                ORDER BY created_at DESC
            """).fetchall()
        return [_row_to_report(dict(row)) for row in rows]

    def _sqlite_insert(self, report_id: str, signature: str, name: str,
                       fachabteilung: str, timestamp: str, export_markdown: str,
                       summary: dict[str, Any], now: str) -> None:
        try:
            with self._sqlite_connect() as conn:
                conn.execute("""
                    INSERT INTO reports (
                        id, signature, name, fachabteilung, timestamp,
                        export_markdown, summary_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    report_id, signature, name, fachabteilung, timestamp,
                    export_markdown, json.dumps(summary, ensure_ascii=False),
                    now, now,
                ))
                conn.commit()
        except sqlite3.IntegrityError as error:
            raise DuplicateReportError("Dieser Bericht ist bereits gespeichert.") from error

    def _sqlite_delete(self, report_id: str) -> bool:
        with self._sqlite_connect() as conn:
            cursor = conn.execute("DELETE FROM reports WHERE id = ?", (report_id,))
            conn.commit()
        return cursor.rowcount > 0

    def _bootstrap_from_json(self) -> None:
        if not JSON_PATH.exists():
            return
        with self._sqlite_connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS count FROM reports").fetchone()
            if row["count"] > 0:
                return
        try:
            entries = json.loads(JSON_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(entries, list):
            return
        now = _utc_timestamp()
        with self._sqlite_connect() as conn:
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                sig = str(entry.get("signature", "")).strip()
                md = str(entry.get("exportMarkdown", "")).strip()
                if not sig or not md:
                    continue
                conn.execute("""
                    INSERT OR IGNORE INTO reports (
                        id, signature, name, fachabteilung, timestamp,
                        export_markdown, summary_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(entry.get("id", "")).strip() or str(uuid4()),
                    sig,
                    str(entry.get("name", "")).strip() or "Unbenannter Bericht",
                    str(entry.get("fachabteilung", "")).strip() or "-",
                    str(entry.get("timestamp", "")).strip() or _display_timestamp(),
                    md,
                    json.dumps(entry.get("summary", {}), ensure_ascii=False),
                    now, now,
                ))
            conn.commit()

    def _sync_json_file(self) -> None:
        JSON_PATH.write_text(
            json.dumps(self.list_reports(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


# ------------------------------------------------------------------
# Shared helpers
# ------------------------------------------------------------------

def _row_to_report(row: dict[str, Any]) -> dict[str, Any]:
    try:
        summary = json.loads(row["summary_json"])
    except (json.JSONDecodeError, KeyError):
        summary = {}
    return {
        "id": row["id"],
        "signature": row["signature"],
        "name": row["name"],
        "fachabteilung": row["fachabteilung"],
        "timestamp": row["timestamp"],
        "exportMarkdown": row["export_markdown"],
        "summary": summary if isinstance(summary, dict) else {},
    }


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _display_timestamp() -> str:
    return datetime.now().strftime("%d.%m.%Y, %H:%M:%S")


STORE = ReportStore()


# ------------------------------------------------------------------
# HTTP handler
# ------------------------------------------------------------------

class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, directory: str | None = None, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def _is_authorized(self) -> bool:
        if not APP_PASSWORD:
            return True
        header = self.headers.get("Authorization", "")
        if not header.startswith("Basic "):
            return False
        try:
            decoded = base64.b64decode(header[6:]).decode("utf-8")
            _, password = decoded.split(":", 1)
            return hmac.compare_digest(password, APP_PASSWORD)
        except Exception:
            return False

    def _require_auth(self) -> bool:
        if self._is_authorized():
            return False
        self.send_response(HTTPStatus.UNAUTHORIZED)
        self.send_header("WWW-Authenticate", 'Basic realm="Berichtskatalog"')
        self.send_header("Content-Length", "0")
        self.end_headers()
        return True

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self._write_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        if self._require_auth():
            return
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._send_json({"ok": True})
            return
        if parsed.path == "/api/reports":
            self._send_json({"entries": STORE.list_reports()})
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self._require_auth():
            return
        parsed = urlparse(self.path)
        if parsed.path != "/api/reports":
            self._send_json({"error": "Not found."}, status=HTTPStatus.NOT_FOUND)
            return
        try:
            payload = self._read_json_body()
            entry = STORE.create_report(payload)
        except DuplicateReportError as error:
            self._send_json({"error": error.message}, status=HTTPStatus.CONFLICT)
            return
        except ValueError as error:
            self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            return
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON body."}, status=HTTPStatus.BAD_REQUEST)
            return
        self._send_json({"entry": entry}, status=HTTPStatus.CREATED)

    def do_DELETE(self) -> None:
        if self._require_auth():
            return
        parsed = urlparse(self.path)
        prefix = "/api/reports/"
        if not parsed.path.startswith(prefix):
            self._send_json({"error": "Not found."}, status=HTTPStatus.NOT_FOUND)
            return
        report_id = parsed.path.removeprefix(prefix).strip()
        if not report_id:
            self._send_json({"error": "Missing report id."}, status=HTTPStatus.BAD_REQUEST)
            return
        deleted = STORE.delete_report(report_id)
        if not deleted:
            self._send_json({"error": "Report not found."}, status=HTTPStatus.NOT_FOUND)
            return
        self._send_json({"deleted": True, "id": report_id})

    def end_headers(self) -> None:
        self._write_cors_headers()
        super().end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        pass

    def _read_json_body(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        payload = json.loads(raw_body.decode("utf-8") or "{}")
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object.")
        return payload

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _write_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    server = ThreadingHTTPServer((host, port), partial(AppHandler, directory=str(BASE_DIR)))
    print(f"Server running on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
