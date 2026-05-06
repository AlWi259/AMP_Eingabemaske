from __future__ import annotations

import json
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
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


@dataclass
class DuplicateReportError(Exception):
    message: str


class ReportStore:
    def __init__(self, db_path: Path, json_path: Path) -> None:
        self.db_path = db_path
        self.json_path = json_path
        self.data_dir = db_path.parent
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._bootstrap_from_json()
        self._sync_json_file()

    def list_reports(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, signature, name, fachabteilung, timestamp, export_markdown, summary_json
                FROM reports
                ORDER BY created_at DESC
                """
            ).fetchall()

        return [self._row_to_report(row) for row in rows]

    def create_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        signature = str(payload.get("signature", "")).strip()
        export_markdown = str(payload.get("exportMarkdown", "")).strip()
        name = str(payload.get("name", "")).strip() or "Unbenannter Bericht"
        fachabteilung = str(payload.get("fachabteilung", "")).strip() or "-"
        timestamp = str(payload.get("timestamp", "")).strip() or self._display_timestamp()
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}

        if not signature or not export_markdown:
            raise ValueError("signature and exportMarkdown are required")

        report_id = str(payload.get("id", "")).strip() or str(uuid4())
        now = self._utc_timestamp()

        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO reports (
                        id, signature, name, fachabteilung, timestamp,
                        export_markdown, summary_json, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        report_id,
                        signature,
                        name,
                        fachabteilung,
                        timestamp,
                        export_markdown,
                        json.dumps(summary, ensure_ascii=False),
                        now,
                        now,
                    ),
                )
                connection.commit()
        except sqlite3.IntegrityError as error:
            raise DuplicateReportError("Dieser Bericht ist bereits gespeichert.") from error

        self._sync_json_file()
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
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM reports WHERE id = ?", (report_id,))
            connection.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            self._sync_json_file()
        return deleted

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
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
                """
            )
            connection.commit()

    def _bootstrap_from_json(self) -> None:
        if not self.json_path.exists():
            return

        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM reports").fetchone()
            if row["count"] > 0:
                return

        try:
            entries = json.loads(self.json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return

        if not isinstance(entries, list):
            return

        now = self._utc_timestamp()
        with self._connect() as connection:
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                signature = str(entry.get("signature", "")).strip()
                export_markdown = str(entry.get("exportMarkdown", "")).strip()
                if not signature or not export_markdown:
                    continue

                connection.execute(
                    """
                    INSERT OR IGNORE INTO reports (
                        id, signature, name, fachabteilung, timestamp,
                        export_markdown, summary_json, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(entry.get("id", "")).strip() or str(uuid4()),
                        signature,
                        str(entry.get("name", "")).strip() or "Unbenannter Bericht",
                        str(entry.get("fachabteilung", "")).strip() or "-",
                        str(entry.get("timestamp", "")).strip() or self._display_timestamp(),
                        export_markdown,
                        json.dumps(entry.get("summary", {}), ensure_ascii=False),
                        now,
                        now,
                    ),
                )
            connection.commit()

    def _sync_json_file(self) -> None:
        self.json_path.write_text(
            json.dumps(self.list_reports(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _row_to_report(self, row: sqlite3.Row) -> dict[str, Any]:
        try:
            summary = json.loads(row["summary_json"])
        except json.JSONDecodeError:
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

    def _utc_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _display_timestamp(self) -> str:
        return datetime.now().strftime("%d.%m.%Y, %H:%M:%S")


STORE = ReportStore(DB_PATH, JSON_PATH)


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, directory: str | None = None, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self._write_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._send_json({"ok": True})
            return

        if parsed.path == "/api/reports":
            self._send_json({"entries": STORE.list_reports()})
            return

        super().do_GET()

    def do_POST(self) -> None:
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
