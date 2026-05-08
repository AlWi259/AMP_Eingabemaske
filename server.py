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

# Load .env for local development (won't overwrite vars already set by the host)
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    for _env_line in _env_file.read_text(encoding="utf-8").splitlines():
        _env_line = _env_line.strip()
        if not _env_line or _env_line.startswith("#") or "=" not in _env_line:
            continue
        _env_key, _, _env_val = _env_line.partition("=")
        _env_key = _env_key.strip()
        _env_val = _env_val.strip().strip('"').strip("'")
        if _env_key and _env_key not in os.environ:
            os.environ[_env_key] = _env_val

DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "reports.sqlite3"
JSON_PATH = DATA_DIR / "reports.json"
DEFAULT_HOST = os.environ.get("HOST", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("PORT", "8000"))
DATABASE_URL = os.environ.get("DATABASE_URL")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


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
{audit_section}
Bereits erfasste Felder:
{collected_json}

Noch offene Pflichtfelder: {missing}
"""

_REALTIME_TOOLS = [
    {
        "type": "function",
        "name": "update_fields",
        "description": "Speichert extrahierte Feldwerte aus dem Gespräch. Sofort aufrufen wenn ein Wert klar ist.",
        "parameters": {
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
        "type": "function",
        "name": "complete_interview",
        "description": "Aufrufen wenn alle Pflichtfelder erfasst sind. Schließt die Erfassung ab.",
        "parameters": {
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


def _build_chat_system(collected: dict, audit_note: str = "") -> str:
    filled = {k for k, v in collected.items() if v and v not in ("-", "")}
    missing = [k for k in _REQUIRED_KEYS if k not in filled]
    audit_section = ""
    if audit_note:
        audit_section = (
            f"\nSTEUERUNGS-HINWEIS (vom letzten Turn): {audit_note}\n"
            "Richte deine nächste Frage auf das oben genannte Feld aus – "
            "es sei denn, der Gesprächspartner bringt gerade etwas anderes Wichtiges auf.\n"
        )
    return _SYSTEM_TEMPLATE.format(
        collected_json=json.dumps(collected, ensure_ascii=False, indent=2),
        missing=", ".join(missing) if missing else "Alle Pflichtfelder erfasst!",
        audit_section=audit_section,
    )


def _run_field_audit(
    last_user_msg: str,
    last_assistant_msg: str,
    collected: dict,
    client: Any,
) -> str:
    """Lightweight second Haiku call: detects evasion and returns a one-line steering note."""
    filled = {k for k, v in collected.items() if v and v not in ("-", "")}
    missing_fields = [
        f"{f['key']} ({f['label']})"
        for f in _FIELD_META
        if f["required"] and f["key"] not in filled
    ]
    if not missing_fields:
        return ""

    missing_str = "\n".join(f"- {m}" for m in missing_fields)
    prompt = (
        "Du prüfst ein laufendes Interview zur Berichtskatalog-Erfassung.\n\n"
        f"Noch fehlende Pflichtfelder:\n{missing_str}\n\n"
        "Letzter Gesprächsturn:\n"
        f"Interviewer: {last_assistant_msg}\n"
        f"Nutzer: {last_user_msg}\n\n"
        "AUFGABE: Entscheide in EINEM Satz, welches Pflichtfeld beim nächsten Turn prioritär "
        "angesprochen werden soll. Hat der Interviewer nach einem Feld gefragt und der Nutzer "
        "ausgewichen oder vage geantwortet? Dann das gleiche Feld wiederholen.\n\n"
        'Format: "PRIORITÄT: [feldkey] ([Label]) — [Begründung max. 8 Wörter]"'
    )

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=80,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception:
        return ""


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
    audit_note: str = str(payload.get("auditNote", "")).strip()

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
            system=_build_chat_system(collected, audit_note),
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
                missing = [k for k in _REQUIRED_KEYS if not collected.get(k) or collected[k] in ("-", "")]
                if missing:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tc.id,
                        "content": f"ABGELEHNT: Noch nicht alle Pflichtfelder erfasst. Fehlende Felder: {', '.join(missing)}. Bitte diese noch erfragen."
                    })
                else:
                    complete = True
                    closing = tc.input.get("closing_message", "Erfassung abgeschlossen.")
                    final_text = " ".join(text_parts).strip() or closing
                    tool_results.append({"type": "tool_result", "tool_use_id": tc.id, "content": "OK"})

        claude_messages.append({"role": "assistant", "content": [_block_to_dict(b) for b in response.content]})
        claude_messages.append({"role": "user", "content": tool_results})

        if complete:
            break

    # Run field auditor to steer the next turn
    last_user = next(
        (m["content"] for m in reversed(raw_messages) if m.get("role") == "user"),
        "",
    )
    new_audit_note = "" if complete else _run_field_audit(
        last_user_msg=last_user,
        last_assistant_msg=final_text,
        collected=collected,
        client=client,
    )

    result: dict[str, Any] = {
        "reply": final_text or "Ich habe Ihre Antwort verarbeitet.",
        "collectedFields": collected,
        "complete": complete,
        "auditNote": new_audit_note,
    }

    if complete:
        result["exportMarkdown"] = _build_export_markdown(collected)

    return result


def run_chat_stream(payload: dict):
    try:
        import anthropic as _anthropic
    except ImportError:
        yield {"type": "error", "message": "Das 'anthropic'-Paket ist nicht installiert."}
        return

    if not ANTHROPIC_API_KEY:
        yield {"type": "error", "message": "ANTHROPIC_API_KEY nicht gesetzt."}
        return

    raw_messages = payload.get("messages", [])
    collected: dict[str, Any] = dict(payload.get("collectedFields", {}))
    audit_note: str = str(payload.get("auditNote", "")).strip()

    if not isinstance(raw_messages, list):
        yield {"type": "error", "message": "messages muss eine Liste sein."}
        return

    claude_messages: list[dict[str, Any]] = [
        {"role": m["role"], "content": str(m["content"])}
        for m in raw_messages
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]

    if not claude_messages or claude_messages[0]["role"] != "user":
        yield {"type": "error", "message": "Die erste Nachricht muss vom Nutzer sein."}
        return

    client = _anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    complete = False
    accumulated_text = ""

    for _ in range(8):
        iteration_text = ""

        with client.messages.stream(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            temperature=0.75,
            system=_build_chat_system(collected, audit_note),
            messages=claude_messages,
            tools=_CHAT_TOOLS,
        ) as stream:
            for text_chunk in stream.text_stream:
                iteration_text += text_chunk
                accumulated_text += text_chunk
                yield {"type": "delta", "text": text_chunk}
            final_message = stream.get_final_message()

        tool_calls_blocks = [b for b in final_message.content if b.type == "tool_use"]

        if final_message.stop_reason != "tool_use" or not tool_calls_blocks:
            break

        tool_results: list[dict[str, Any]] = []
        for tc in tool_calls_blocks:
            if tc.name == "update_fields":
                fields = tc.input.get("fields", {})
                if isinstance(fields, dict):
                    collected.update(fields)
                tool_results.append({"type": "tool_result", "tool_use_id": tc.id, "content": "OK"})
            elif tc.name == "complete_interview":
                missing = [k for k in _REQUIRED_KEYS if not collected.get(k) or collected[k] in ("-", "")]
                if missing:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tc.id,
                        "content": f"ABGELEHNT: Noch nicht alle Pflichtfelder erfasst. Fehlende Felder: {', '.join(missing)}. Bitte diese noch erfragen."
                    })
                else:
                    complete = True
                    if not accumulated_text.strip():
                        closing = tc.input.get("closing_message", "Erfassung abgeschlossen.")
                        accumulated_text = closing
                        yield {"type": "delta", "text": closing}
                    tool_results.append({"type": "tool_result", "tool_use_id": tc.id, "content": "OK"})

        claude_messages.append({"role": "assistant", "content": [_block_to_dict(b) for b in final_message.content]})
        claude_messages.append({"role": "user", "content": tool_results})

        if complete:
            break

        # Ensure a space between streamed text from different iterations
        if accumulated_text and not accumulated_text[-1].isspace():
            yield {"type": "delta", "text": " "}
            accumulated_text += " "

    # Run field auditor to steer the next turn
    last_user = next(
        (m["content"] for m in reversed(raw_messages) if m.get("role") == "user"),
        "",
    )
    new_audit_note = "" if complete else _run_field_audit(
        last_user_msg=last_user,
        last_assistant_msg=accumulated_text,
        collected=collected,
        client=client,
    )

    result: dict[str, Any] = {
        "type": "done",
        "collectedFields": collected,
        "complete": complete,
        "auditNote": new_audit_note,
    }
    if complete:
        result["exportMarkdown"] = _build_export_markdown(collected)

    yield result


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
        parsed = urlparse(self.path)
        if parsed.path == "/api/realtime-session":
            self._handle_realtime_session()
            return
        if self._require_auth():
            return
        if parsed.path == "/api/chat":
            self._handle_chat()
            return
        if parsed.path == "/api/chat/stream":
            self._handle_chat_stream()
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

    def _handle_realtime_session(self) -> None:
        if not OPENAI_API_KEY:
            self._send_json(
                {"error": "OPENAI_API_KEY nicht gesetzt."},
                status=HTTPStatus.SERVICE_UNAVAILABLE,
            )
            return
        try:
            payload = self._read_json_body()
        except Exception:
            payload = {}
        collected = dict(payload.get("collectedFields", {}))
        session_body = json.dumps({
            "model": "gpt-4o-realtime-preview",
            "voice": "shimmer",
            "instructions": _build_chat_system(collected),
            "tools": _REALTIME_TOOLS,
            "tool_choice": "auto",
            "input_audio_transcription": {"model": "whisper-1"},
            "turn_detection": {"type": "server_vad"},
            "modalities": ["text", "audio"],
        }, ensure_ascii=False).encode("utf-8")
        from urllib.request import Request, urlopen
        from urllib.error import URLError
        req = Request(
            "https://api.openai.com/v1/realtime/sessions",
            data=session_body,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
            self._send_json({"token": data["client_secret"]["value"]})
        except URLError as error:
            self._send_json(
                {"error": f"OpenAI-Verbindung fehlgeschlagen: {error}"},
                status=HTTPStatus.BAD_GATEWAY,
            )

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

    def _handle_chat_stream(self) -> None:
        try:
            payload = self._read_json_body()
        except Exception as error:
            self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        def _send_event(event: dict) -> None:
            data = json.dumps(event, ensure_ascii=False)
            self.wfile.write(f"data: {data}\n\n".encode("utf-8"))
            self.wfile.flush()

        try:
            for event in run_chat_stream(payload):
                _send_event(event)
        except BrokenPipeError:
            pass
        except Exception as error:
            try:
                _send_event({"type": "error", "message": str(error)})
            except Exception:
                pass

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
