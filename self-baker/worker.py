import os
import time
from collections import defaultdict
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "GPT-OSS20B")

QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "jar_el_memory")

MEMORY_API_URL = os.getenv("MEMORY_API_URL", "http://memory-api:8000")

if not OPENAI_API_KEY or not OPENAI_BASE_URL:
    raise RuntimeError("OPENAI_API_KEY oder OPENAI_BASE_URL fehlt")

client_oa = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
client_qd = QdrantClient(url=QDRANT_URL)


def fetch_unbaked(limit: int = 100) -> List[Dict[str, Any]]:
    f = Filter(
        must=[
            FieldCondition(
                key="baked",
                match=MatchValue(value=False),
            )
        ]
    )
    points, _ = client_qd.scroll(
        collection_name=QDRANT_COLLECTION,
        scroll_filter=f,
        limit=limit,
        with_payload=True,
    )
    return [{"id": p.id, "payload": p.payload} for p in points]


def mark_baked(ids: List[Any]) -> None:
    if not ids:
        return
    client_qd.set_payload(
        collection_name=QDRANT_COLLECTION,
        payload={"baked": True},
        points=ids,
    )


def summarize_for_project(project: str, entries: List[Dict[str, Any]]) -> str:
    texts = [e["payload"].get("text", "") for e in entries]
    joined = "\n\n".join(texts)
    messages = [
        {
            "role": "system",
            "content": (
                "Du bist ein Langzeit-Speicheragent. "
                "Fasse die folgenden Notizen für das Projekt zu einer kompakten Memory-Notiz zusammen. "
                "Behalte nur langfristig relevante Fakten, Entscheidungen, Präferenzen und To-Dos."
            ),
        },
        {
            "role": "user",
            "content": f"Projekt: {project}\n\nNotizen:\n{joined}",
        },
    ]
    resp = client_oa.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.2,
    )
    return resp.choices[0].message.content


def upsert_summary_to_memory(project: str, summary: str) -> None:
    payload = {
        "text": summary,
        "metadata": {
            "project": project,
            "kind": "summary",
            "baked": True,
            "tags": ["auto-summary", "self-baked"],
        },
    }
    url = f"{MEMORY_API_URL}/memory/upsert"
    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    print(f"Self-Baker: Summary für Projekt {project} im Memory gespeichert.")


def run_once() -> None:
    unbaked = fetch_unbaked(limit=200)
    if not unbaked:
        print("Self-Baker: nichts zu tun.")
        return

    by_project: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for e in unbaked:
        project = e["payload"].get("project", "Allgemein")
        by_project[project].append(e)

    for project, entries in by_project.items():
        try:
            summary = summarize_for_project(project, entries)
        except Exception as exc:
            print(f"Fehler beim Zusammenfassen für Projekt {project}: {exc}")
            continue

        try:
            upsert_summary_to_memory(project, summary)
        except Exception as exc:
            print(f"Fehler beim Schreiben der Summary für Projekt {project}: {exc}")
            continue

        ids = [e["id"] for e in entries]
        mark_baked(ids)

        print(f"Self-Baker: Projekt {project}, {len(entries)} Einträge gebacken.")


def main_loop() -> None:
    interval_seconds = int(os.getenv("SELF_BAKER_INTERVAL", "600"))
    while True:
        try:
            run_once()
        except Exception as exc:
            print(f"Self-Baker Fehler: {exc}")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    main_loop()
