import os
import uuid
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

load_dotenv()

# OpenAI-kompatibler Client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

if not OPENAI_API_KEY or not OPENAI_BASE_URL:
    raise RuntimeError("OPENAI_API_KEY oder OPENAI_BASE_URL fehlt")

EMBED_MODEL = os.getenv(
    "OPENAI_EMBED_MODEL", "jeffh/intfloat-multilingual-e5-large:q8_0"
)
CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "GPT-OSS20B")

client_oa = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

# Qdrant-Konfiguration
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "jar_el_memory")
VECTOR_SIZE = int(os.getenv("QDRANT_VECTOR_SIZE", "1024"))
DISTANCE = os.getenv("QDRANT_DISTANCE", "cosine").lower()

if DISTANCE == "cosine":
    DISTANCE_ENUM = Distance.COSINE
elif DISTANCE == "euclid":
    DISTANCE_ENUM = Distance.EUCLID
else:
    DISTANCE_ENUM = Distance.COSINE

client_qd = QdrantClient(url=QDRANT_URL)

app = FastAPI(title="Jar-El Memory API", version="0.2.0")


class MemoryItem(BaseModel):
    id: Optional[str] = Field(default=None)
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    filter: Optional[Dict[str, Any]] = None


class SummarizeRequest(BaseModel):
    texts: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)


def ensure_collection() -> None:
    collections = client_qd.get_collections().collections
    if not any(c.name == QDRANT_COLLECTION for c in collections):
        client_qd.recreate_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=DISTANCE_ENUM),
        )


def embed_text(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    resp = client_oa.embeddings.create(
        model=EMBED_MODEL,
        input=texts,
    )
    return [d.embedding for d in resp.data]


def summarize_texts(texts: List[str]) -> str:
    joined = "\n\n".join(texts)
    messages = [
        {
            "role": "system",
            "content": (
                "Du bist ein präziser Notiz- und Zusammenfassungsassistent. "
                "Extrahiere nur speicherwürdige, langfristig relevante Informationen."
            ),
        },
        {
            "role": "user",
            "content": joined,
        },
    ]
    resp = client_oa.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.2,
    )
    return resp.choices[0].message.content


@app.on_event("startup")
def on_startup() -> None:
    ensure_collection()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/memory/upsert")
def upsert_item(item: MemoryItem) -> Dict[str, Any]:
    text = item.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text darf nicht leer sein")

    item_id = item.id or str(uuid.uuid4())
    vec = embed_text([text])[0]

    payload = {"text": text, "baked": item.metadata.get("baked", False), **item.metadata}

    point = PointStruct(
        id=item_id,
        vector=vec,
        payload=payload,
    )

    client_qd.upsert(collection_name=QDRANT_COLLECTION, points=[point])

    return {"status": "stored", "id": item_id}


@app.post("/memory/batch_upsert")
def batch_upsert(items: List[MemoryItem]) -> Dict[str, Any]:
    if not items:
        raise HTTPException(status_code=400, detail="Leere Liste")

    texts = [it.text.strip() for it in items]
    if any(not t for t in texts):
        raise HTTPException(status_code=400, detail="Alle Texte müssen gefüllt sein")

    vectors = embed_text(texts)
    points: List[PointStruct] = []

    for it, vec in zip(items, vectors):
        item_id = it.id or str(uuid.uuid4())
        payload = {"text": it.text, "baked": it.metadata.get("baked", False), **it.metadata}
        points.append(
            PointStruct(
                id=item_id,
                vector=vec,
                payload=payload,
            )
        )

    client_qd.upsert(collection_name=QDRANT_COLLECTION, points=points)

    return {"status": "stored", "count": len(points)}


@app.post("/memory/search")
def search(req: QueryRequest) -> Dict[str, Any]:
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query darf nicht leer sein")

    qvec = embed_text([query])[0]

    results = client_qd.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=qvec,
        limit=req.top_k,
        with_payload=True,
    )

    matches = []
    for res in results:
        matches.append(
            {
                "id": res.id,
                "score": res.score,
                "payload": res.payload,
            }
        )

    return {"matches": matches}


def _summarize_and_store(texts: List[str], metadata: Dict[str, Any]) -> None:
    summary = summarize_texts(texts)
    meta = {**metadata, "kind": metadata.get("kind", "summary"), "baked": True}
    item = MemoryItem(text=summary, metadata=meta)
    upsert_item(item)


@app.post("/memory/summarize_and_store")
def summarize_and_store(
    req: SummarizeRequest, background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    if not req.texts:
        raise HTTPException(status_code=400, detail="texts darf nicht leer sein")

    background_tasks.add_task(_summarize_and_store, req.texts, req.metadata)
    return {"status": "scheduled", "items": len(req.texts)}
