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
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


# ---------------------------------------------------------------------------
# Chat / LLM helpers
# ---------------------------------------------------------------------------

_FIELD_META = [
    {"key": "berichtId",              "label": "Bericht-ID",               "required": False, "default": "-"},
    {"key": "berichtsname",           "label": "Berichtsname",              "required": True,  "default": ""},
    {"key": "beschreibung",           "label": "Beschreibung",              "required": True,  "default": ""},
    {"key": "workspace",              "label": "Workspace / Ablageort",     "required": False, "default": "-"},
    {"key": "berichtstyp",            "label": "Berichtstyp",               "required": True,  "default": ""},
    {"key": "besitzer",               "label": "Besitzer",                  "required": True,  "default": ""},
    {"key": "fachabteilung",          "label": "Fachabteilung",             "required": True,  "default": ""},
    {"key": "itAnsprechpartner",      "label": "IT-Ansprechpartner",        "required": False, "default": "-"},
    {"key": "primaereDatenquelle",    "label": "Primäre Datenquelle",       "required": True,  "default": ""},
    {"key": "weitereDatenquellen",    "label": "Weitere Datenquellen",      "required": False, "default": "-"},
    {"key": "aktuellesTool",          "label": "Aktuelles Tool",            "required": True,  "default": ""},
    {"key": "ausgabeformat",          "label": "Ausgabeformat",             "required": True,  "default": ""},
    {"key": "zielgruppe",             "label": "Zielgruppe",                "required": True,  "default": ""},
    {"key": "parameterFilter",        "label": "Parameter / Filter",        "required": False, "default": "Keine"},
    {"key": "gatewayVerbindungen",    "label": "Gateway-Verbindungen",      "required": True,  "default": ""},
    {"key": "automatisierungsgrad",   "label": "Automatisierungsgrad",      "required": True,  "default": ""},
    {"key": "manuellerAufwand",       "label": "Manueller Aufwand",         "required": True,  "default": ""},
    {"key": "aufwandKonkret",         "label": "Aufwand konkret",           "required": False, "default": "-"},
    {"key": "aktualisierungsfrequenz","label": "Aktualisierungsfrequenz",   "required": True,  "default": ""},
    {"key": "datenaktualitaet",       "label": "Datenaktualität",           "required": True,  "default": ""},
    {"key": "approvalNachAenderung",  "label": "Approval nach Änderung",    "required": True,  "default": ""},
    {"key": "letztesReview",          "label": "Letztes Review",            "required": False, "default": "Unbekannt"},
    {"key": "komplexitaet",           "label": "Komplexität",               "required": True,  "default": ""},
    {"key": "migrationsstatus",       "label": "Migrationsstatus",          "required": True,  "default": ""},
    {"key": "prioritaet",             "label": "Priorität",                 "required": True,  "default": ""},
    {"key": "aufwandPt",              "label": "Aufwand (PT)",              "required": False, "default": "-"},
    {"key": "bemerkungen",            "label": "Bemerkungen",               "required": False, "default": "-"},
]

_REQUIRED_KEYS = [f["key"] for f in _FIELD_META if f["required"]]

_SYSTEM_TEMPLATE = """\
Du bist ein erfahrener BI Senior Consultant, der im Rahmen eines Reporting-Migrationsprojekts strukturierte Interviews mit internen Stakeholdern führt, um einen vollständigen Berichtskatalog aufzubauen.

SPRACHE: Immer Deutsch. Immer "Sie"-Form. Nie "du".

DEINE ROLLE:
Du kennst BI-Architekturen, Reporting-Prozesse und Unternehmensstrukturen aus dem Effeff. Du weißt, welche Informationen für eine saubere Migration wirklich zählen – und du hörst auch zwischen den Zeilen. Du berätst, ohne zu bewerten. Du bringst Menschen dazu, Dinge zu artikulieren, die sie vielleicht selbst noch nicht klar formuliert hatten.

GESPRÄCHSFÜHRUNG (wichtig – halte dich konsequent daran):
- Stelle immer nur EINE Frage auf einmal. Nie zwei.
- Beginne mit offenen W-Fragen ("Was...", "Wie...", "Woran..."), nicht mit Ja/Nein-Fragen.
- Wenn eine Antwort vage ist, bohre nach: "Was genau meinen Sie mit ...?" / "Inwiefern ...?"
- Wenn jemand einen Schmerzpunkt erwähnt (hoher manueller Aufwand, Qualitätsprobleme, Abhängigkeiten), erkunde das kurz – das ist wertvolle Information. Zeige, dass du das einordnen kannst.
- Verwende die Worte des Gesprächspartners: Wenn jemand sagt "das Ding läuft irgendwie halb automatisch", dann greif genau das auf.
- Biete Optionslisten NUR an, wenn der Gesprächspartner offensichtlich nicht weiterkommt oder selbst fragt.
- Kurze Bestätigungen sind in Ordnung: "Verstanden.", "Das kenne ich.", "Macht Sinn." – aber kein "Super!", "Toll!", "Fantastisch!".
- Wenn du genug weißt, fass kurz zusammen und leite natürlich zum nächsten Thema über.
- Halte das Gespräch flüssig – es soll sich wie ein echtes Beratungsgespräch anfühlen, nicht wie ein Formular.

FELDER ZU ERFASSEN (Pflichtfelder mit *):

Identifikation:
  * berichtsname – Wie heißt der Bericht?
  * beschreibung – Was leistet der Bericht? Wer nutzt ihn wofür?
  * berichtstyp – Exakt eine Option: Operativer Bericht | Managementbericht | Finanzbericht | Dashboard | Ad-hoc-Analyse | KPI-Übersicht | Regulatorischer Bericht | Forecast / Prognose | Sonstiges
    berichtId – optional (z. B. REP-2048)
    workspace – optional (Ablageort / Workspace)

Verantwortung:
  * besitzer – Wer ist fachlich verantwortlich?
  * fachabteilung – Exakt eine Option: Controlling | Finanzen | Vertrieb | Marketing | Einkauf | Logistik | Produktion | Personal / HR | IT | Geschäftsführung | Qualitätssicherung | Rechtswesen | Sonstiges
    itAnsprechpartner – optional

Technologie & Daten:
  * primaereDatenquelle – Exakt eine Option: SQL Server | Power BI Dataflow | Oracle | SAP HANA | MySQL | PostgreSQL | Azure SQL | Snowflake | BigQuery | Excel / CSV | SharePoint-Liste | REST API | OData | SAP BW | Sonstiges
  * aktuellesTool – Exakt eine Option: Excel | Power BI | SSRS | Tableau | Qlik | IBM Cognos | Sonstiges
  * ausgabeformat – Exakt eine Option: Excel (.xlsx) | Power BI Report | Power BI App | PDF | PowerPoint | Web-Browser / URL | E-Mail | SharePoint-Seite | Confluence | Microsoft Teams | CSV / Text | Sonstiges
  * zielgruppe – Exakt eine Option: Management | Fachabteilung | Analysten | Externe Stakeholder
  * gatewayVerbindungen – Exakt eine Option: Ja | Nein | Unbekannt
    weitereDatenquellen – optional
    parameterFilter – optional

Qualität & Betrieb:
  * automatisierungsgrad – Exakt eine Option: Vollautomatisiert | Teilautomatisiert | Manuell
  * manuellerAufwand – Exakt eine Option: Kein Aufwand | Stunden | Tage | Wochen
  * aktualisierungsfrequenz – Exakt eine Option: Echtzeit | Stündlich | Täglich | Wöchentlich | 14-tägig | Monatlich | Quartalsweise | Halbjährlich | Jährlich | On-Demand
  * datenaktualitaet – Exakt eine Option: Aktuell | Veraltet
  * approvalNachAenderung – Exakt eine Option: Kein Approval | Fachbereich | Management | Regulatorisch
    aufwandKonkret – optional, nur wenn manuellerAufwand nicht "Kein Aufwand"
    letztesReview – optional, Format MM.JJJJ

Power BI Migration:
  * komplexitaet – Exakt eine Option: Niedrig | Mittel | Hoch | Sehr hoch
  * migrationsstatus – Exakt eine Option: Offen | In Analyse | In Entwicklung | In Review / Test | Abgeschlossen | Zurückgestellt | Nicht migrieren

Priorisierung:
  * prioritaet – Exakt eine Option: Kritisch | Hoch | Mittel | Niedrig
    aufwandPt – optional (Personentage als Zahl)

Notizen:
    bemerkungen – optional

TECHNISCHE REGELN:
- Ruf `update_fields` sofort auf, sobald du aus dem Gespräch einen Feldwert ableiten kannst. Nutze exakt die Optionswerte.
- Wenn manuellerAufwand = "Kein Aufwand": setze aufwandKonkret = "-".
- Wenn alle Pflichtfelder erfasst sind: ruf `complete_interview` auf mit einer natürlichen Abschlussformulierung.
- Optionale Felder nur erfassen, wenn sie sich im Gespräch ergeben.

Bereits erfasste Felder:
{collected_json}

Noch offene Pflichtfelder: {missing}
"""

_CHAT_TOOLS = [
    {
        "name": "update_fields",
        "description": "Speichert extrahierte Feldwerte aus dem Gespräch. Sofort aufrufen wenn ein Wert klar ist.",
        "input_schema": {
            "type": "object",
            "properties": {
                "fields": {
                    "type": "object",
                    "description": "Key-Value-Paare: Feldschlüssel → Wert (bei Select-Feldern exakt die vorgegebenen Optionswerte)",
                }
            },
            "required": ["fields"],
        },
    },
    {
        "name": "complete_interview",
        "description": "Aufrufen wenn alle Pflichtfelder erfasst sind. Schließt die Erfassung ab.",
        "input_schema": {
            "type": "object",
            "properties": {
                "closing_message": {
                    "type": "string",
                    "description": "Kurze Abschlussbestätigung für den Nutzer",
                }
            },
            "required": ["closing_message"],
        },
    },
]


def _build_chat_system(collected: dict) -> str:
    filled = {k for k, v in collected.items() if v and v not in ("-", "")}
    missing = [k for k in _REQUIRED_KEYS if k not in filled]
    return _SYSTEM_TEMPLATE.format(
        collected_json=json.dumps(collected, ensure_ascii=False, indent=2),
        missing=", ".join(missing) if missing else "Alle Pflichtfelder erfasst!",
    )


def _block_to_dict(block: Any) -> dict[str, Any]:
    if block.type == "text":
        return {"type": "text", "text": block.text}
    if block.type == "tool_use":
        return {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
    return {}


def _build_export_markdown(collected: dict) -> str:
    lines = ["# Berichtskatalog-Eintrag", ""]
    for field in _FIELD_META:
        value = collected.get(field["key"]) or field["default"] or "-"
        lines.append(f"- **{field['label']}:** {value}")
    return "\n".join(lines)


def run_chat(payload: dict) -> dict[str, Any]:
    try:
        import anthropic as _anthropic
    except ImportError:
        raise RuntimeError(
            "Das 'anthropic'-Paket ist nicht installiert. Bitte: pip install anthropic"
        )

    if not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEY nicht gesetzt. Bitte in der .env-Datei eintragen und Server neu starten."
        )

    raw_messages = payload.get("messages", [])
    collected: dict[str, Any] = dict(payload.get("collectedFields", {}))

    if not isinstance(raw_messages, list):
        raise ValueError("messages muss eine Liste sein.")

    claude_messages: list[dict[str, Any]] = [
        {"role": m["role"], "content": str(m["content"])}
        for m in raw_messages
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]

    if not claude_messages or claude_messages[0]["role"] != "user":
        raise ValueError("Die erste Nachricht muss vom Nutzer sein.")

    client = _anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    complete = False
    final_text = ""

    for _ in range(8):
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            temperature=0.75,
            system=_build_chat_system(collected),
            messages=claude_messages,
            tools=_CHAT_TOOLS,
        )

        text_parts: list[str] = []
        tool_calls: list[Any] = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(block)

        if response.stop_reason != "tool_use" or not tool_calls:
            final_text = " ".join(text_parts).strip()
            break

        tool_results: list[dict[str, Any]] = []
        for tc in tool_calls:
            if tc.name == "update_fields":
                fields = tc.input.get("fields", {})
                if isinstance(fields, dict):
                    collected.update(fields)
                tool_results.append({"type": "tool_result", "tool_use_id": tc.id, "content": "OK"})
            elif tc.name == "complete_interview":
                complete = True
                closing = tc.input.get("closing_message", "Erfassung abgeschlossen.")
                final_text = " ".join(text_parts).strip() or closing
                tool_results.append({"type": "tool_result", "tool_use_id": tc.id, "content": "OK"})

        claude_messages.append({"role": "assistant", "content": [_block_to_dict(b) for b in response.content]})
        claude_messages.append({"role": "user", "content": tool_results})

        if complete:
            break

    result: dict[str, Any] = {
        "reply": final_text or "Ich habe Ihre Antwort verarbeitet.",
        "collectedFields": collected,
        "complete": complete,
    }

    if complete:
        result["exportMarkdown"] = _build_export_markdown(collected)

    return result


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
        if parsed.path == "/api/chat":
            self._handle_chat()
            return
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

    def _handle_chat(self) -> None:
        try:
            payload = self._read_json_body()
            result = run_chat(payload)
            self._send_json(result)
        except RuntimeError as error:
            self._send_json({"error": str(error)}, status=HTTPStatus.SERVICE_UNAVAILABLE)
        except ValueError as error:
            self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:
            self._send_json(
                {"error": f"Chat-Anfrage fehlgeschlagen: {error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

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
