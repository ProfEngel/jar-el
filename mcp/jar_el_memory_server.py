# /jar-el/mcp/jar_el_memory_server.py

import json
import os
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv
from openai import OpenAI
from mcp.server.fastmcp import FastMCP

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "GPT-OSS20B")
MEMORY_API_URL = os.getenv("MEMORY_API_URL", "http://localhost:8000")

if not OPENAI_API_KEY or not OPENAI_BASE_URL:
    raise RuntimeError("OPENAI_API_KEY oder OPENAI_BASE_URL fehlt")

client_oa = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

# FastMCP-Server initialisieren
mcp = FastMCP("jar-el-memory")


def _memory_post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Hilfsfunktion für HTTP-POSTs an die Memory-API.
    """
    url = f"{MEMORY_API_URL}{path}"
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def classify_and_extract_metadata(text: str) -> Dict[str, Any]:
    """
    Nutzt dein Chat-Modell, um Projekt, Tags, kind, should_store
    und optionale Zusatzfelder (Schema v2) zu bestimmen.
    Gibt ein JSON-Objekt zurück.
    """
    system_prompt = (
        "Du analysierst Benutzeraussagen und entscheidest, ob sie für ein "
        "langfristiges persönliches Wissensgedächtnis (Jar-El) speicherwürdig sind. "
        "Du gibst AUSSCHLIESSLICH ein JSON-Objekt oder 'null' zurück.\n\n"
        "Speichern:\n"
        "- Biografische Infos, Rollen, Projekte, Events, Pläne, Entscheidungen,\n"
        "  Präferenzen, wichtige Fakten, Lehrinhalte.\n"
        "Nicht speichern:\n"
        "- Rückfragen des Assistenten, rein kurzfristige Organisatorik,\n"
        "  Smalltalk ohne Relevanz, Meta-Kommentare über das Modell.\n"
    )

    user_prompt = f"""
Text:
\"\"\"{text}\"\"\"

Aufgabe:
1. Erkenne, ob der Text langfristig relevant ist.
2. Ermittele ein Projektlabel (z.B. "Jar-El", "KI-Literacy", "Erendria", "Allgemein").
3. Erzeuge einige thematische Tags (max. 5).
4. Bestimme "kind" (z.B. "identity", "preference", "project", "event", "fact", "note", "task", "artifact").
5. Setze "should_store" auf true, wenn der Inhalt speicherwürdig ist, sonst false.
6. Wenn es sich um ein Event handelt, fülle nach Möglichkeit event_name, date, location, people, orgs, topics.
7. Schätze eine confidence zwischen 0 und 1.

Format (JSON):
{{
  "project": "...",
  "tags": ["...", "..."],
  "kind": "identity|preference|project|event|fact|note|task|artifact",
  "should_store": true/false,
  "event_name": null oder "...",
  "date": "YYYY-MM-DD" oder null,
  "end_date": null oder "YYYY-MM-DD",
  "location": null oder "...",
  "people": null oder ["Person A", "Person B"],
  "orgs": null oder ["Organisation A"],
  "topics": null oder ["Thema A", "Thema B"],
  "status": null,
  "deadline": null,
  "priority": null,
  "artifact_type": null,
  "file_name": null,
  "file_path": null,
  "confidence": Zahl zwischen 0 und 1,
  "visibility": "private"
}}

Wenn der Inhalt NICHT speicherwürdig ist, gib exakt:
null
(zwei Zeichen, ohne Anführungszeichen) zurück.
""".strip()

    resp = client_oa.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
    )

    content = resp.choices[0].message.content.strip()

    if content == "null":
        # explizit nichts speichern
        return {
            "project": "Allgemein",
            "tags": [],
            "kind": "note",
            "should_store": False,
        }

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # Fallback, falls das Modell kein valides JSON liefert
        data = {
            "project": "Allgemein",
            "tags": [],
            "kind": "note",
            "should_store": True,
        }

    # Defaults für wichtige Felder setzen
    data.setdefault("project", "Allgemein")
    data.setdefault("tags", [])
    data.setdefault("kind", "note")
    data.setdefault("should_store", True)
    data.setdefault("event_name", None)
    data.setdefault("date", None)
    data.setdefault("end_date", None)
    data.setdefault("location", None)
    data.setdefault("people", None)
    data.setdefault("orgs", None)
    data.setdefault("topics", None)
    data.setdefault("status", None)
    data.setdefault("deadline", None)
    data.setdefault("priority", None)
    data.setdefault("artifact_type", None)
    data.setdefault("file_name", None)
    data.setdefault("file_path", None)
    data.setdefault("confidence", 0.9)
    data.setdefault("visibility", "private")

    return data


@mcp.tool()
def memory_search(query: str, top_k: int = 5) -> str:
    """
    Semantische Suche im Jar-El Memory.
    Gibt ein lesbares Text-Listing der Treffer zurück.
    """
    payload = {"query": query, "top_k": top_k}
    result = _memory_post("/memory/search", payload)

    text_parts: List[str] = []
    for match in result.get("matches", []):
        text_val = match.get("payload", {}).get("text", "")
        meta = {k: v for k, v in match.get("payload", {}).items() if k != "text"}
        text_parts.append(
            f"Score: {match.get('score')}\nMeta: {meta}\nText: {text_val}"
        )

    if not text_parts:
        return "Keine Treffer im Memory."

    return "\n\n---\n\n".join(text_parts)


@mcp.tool()
def memory_observe(text: str, role: str = "user", channel: str = "chat") -> str:
    """
    Beobachtet eine Chat-Nachricht und speichert sie ggf. automatisch im Memory.
    Sollte vom Host nach jeder relevanten User-Nachricht im Hintergrund
    aufgerufen werden.
    """
    from datetime import datetime

    text_clean = text.strip()
    if not text_clean:
        return "Leerer Text, nichts zu speichern."

    meta = classify_and_extract_metadata(text_clean)
    if not meta.get("should_store", True):
        return "Nicht speicherwürdig, übersprungen."

    created_at = datetime.utcnow().isoformat() + "Z"
    source_host = os.getenv("MEMORY_SOURCE_HOST", "OpenWebUI")

    # Basis-Metadaten
    metadata: Dict[str, Any] = {
        "project": meta.get("project", "Allgemein"),
        "tags": meta.get("tags", []),
        "kind": meta.get("kind", "note"),
        "source_role": role,
        "source_channel": channel,
        "source_host": source_host,
        "created_at": created_at,
        "visibility": meta.get("visibility", "private"),
        "confidence": meta.get("confidence", 0.9),
    }

    # Optionale Felder aus Schema v2 übernehmen, falls gesetzt
    optional_keys = [
        "event_name",
        "date",
        "end_date",
        "location",
        "people",
        "orgs",
        "topics",
        "status",
        "deadline",
        "priority",
        "artifact_type",
        "file_name",
        "file_path",
    ]
    for key in optional_keys:
        value = meta.get(key)
        if value is not None:
            metadata[key] = value

    summarize_payload = {
        "texts": [text_clean],
        "metadata": metadata,
    }

    _memory_post("/memory/summarize_and_store", summarize_payload)

    return (
        "Im Memory gespeichert "
        f"(Projekt: {metadata.get('project')}, kind: {metadata.get('kind')}, "
        f"tags: {metadata.get('tags')})."
    )


def main() -> None:
    # MCP-Server über STDIO laufen lassen
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

