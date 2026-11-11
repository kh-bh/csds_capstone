"""
FastAPI backend that exposes the hospital-review RAG pipeline as a streaming API.

Run with:
    pip install fastapi uvicorn
    uvicorn rag_server:app --reload --port 8000

The React page POSTs to /api/rag/stream and receives newline-delimited JSON:
    {"type": "sources", "sources": [...]}   (sent first, once retrieval finishes)
    {"type": "token",   "text": "..."}      (many, as the LLM generates)
    {"type": "done"}                        (end of stream)
    {"type": "error",   "message": "..."}   (on failure)
"""
import json
import os
import threading
from typing import Any, Dict, Iterator, List, Optional

import torch
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from pydantic import BaseModel, Field
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

# ---------------------------------------------------------------------------
# 1. Environment + vector store
# ---------------------------------------------------------------------------
load_dotenv()

embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
index_name = "hospital-reviews-hf"

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(index_name)
vectorstore = PineconeVectorStore(index=index, embedding=embedding_model)

# ---------------------------------------------------------------------------
# 2. LLM (loaded once at startup)
# ---------------------------------------------------------------------------
model_id = "meta-llama/Llama-3.2-1B-Instruct"
# Alternative (no token required): model_id = "Qwen/Qwen2.5-1.5B-Instruct"

if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"

print(f"Loading model onto device: {device}")

tokenizer = AutoTokenizer.from_pretrained(model_id, token=os.getenv("HF_TOKEN"))
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.float16 if device != "cpu" else torch.float32,
    low_cpu_mem_usage=True,
    token=os.getenv("HF_TOKEN"),
).to(device)
model.eval()

# One generation at a time: a small local model can't safely serve concurrent requests.
generation_lock = threading.Lock()


# ---------------------------------------------------------------------------
# 3. RAG helpers (same logic as RAG_query.py)
# ---------------------------------------------------------------------------
def build_pinecone_filter(
    google_name: Optional[List[str]] = None,
    city: Optional[List[str]] = None,
    state: Optional[List[str]] = None,
    zip_code: Optional[List[str]] = None,
    max_rating: Optional[float] = None,
    min_rating: Optional[float] = None,
    operational_category: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Dynamically builds Pinecone filter dictionary handling 0, 1, or multiple criteria."""
    filters: Dict[str, Any] = {}

    def add_list_filter(field_name: str, values: Optional[List[str]]):
        if values:
            if len(values) == 1:
                filters[field_name] = {"$eq": values[0]}
            else:
                filters[field_name] = {"$in": values}

    add_list_filter("google_name", google_name)
    add_list_filter("city", city)
    add_list_filter("state", state)
    add_list_filter("zip", zip_code)
    add_list_filter("operational_category", operational_category)

    rating_filter = {}
    if min_rating is not None:
        rating_filter["$gte"] = float(min_rating)
    if max_rating is not None:
        rating_filter["$lte"] = float(max_rating)
    if rating_filter:
        filters["review_rating"] = rating_filter

    return filters


def format_context(docs) -> str:
    """Formats retrieved documents into a structured string with citation tags."""
    formatted_chunks = []
    for doc in docs:
        meta = doc.metadata
        chunk = (
            f"--- START REVIEW ---\n"
            f"Review ID: {doc.id}\n"
            f"Hospital: {meta.get('google_name', 'Unknown Hospital')}\n"
            f"Rating: {meta.get('review_rating', 'N/A')} Stars\n"
            f"Category: {meta.get('operational_category', 'N/A')}\n"
            f"Content: {doc.page_content}\n"
            f"--- END REVIEW ---"
        )
        formatted_chunks.append(chunk)
    return "\n\n".join(formatted_chunks)


def build_prompt(question: str, context: str) -> str:
    return f"""You are a helpful assistant analyzing hospital reviews.
Answer the user's question using ONLY the provided reviews below. Summarize the response in 1-2 short paragraphs that discuss hospital performance generally, citing specific hospital names using the (Hospital) citation format when necessary.

Question: {question}

Context Reviews:
{context}

Answer:"""


def ndjson(payload: Dict[str, Any]) -> str:
    return json.dumps(payload) + "\n"


# ---------------------------------------------------------------------------
# 4. API
# ---------------------------------------------------------------------------
class RagRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(4, ge=1, le=10)
    google_name: Optional[List[str]] = None
    city: Optional[List[str]] = None
    state: Optional[List[str]] = None
    zip_code: Optional[List[str]] = None
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    max_rating: Optional[float] = Field(None, ge=0, le=5)
    operational_category: Optional[List[str]] = None


app = FastAPI(title="ClearCare RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # add your deployed origin
    allow_methods=["*"],
    allow_headers=["*"],
)


def stream_rag_answer(req: RagRequest) -> Iterator[str]:
    try:
        filter_dict = build_pinecone_filter(
            google_name=req.google_name,
            city=req.city,
            state=req.state,
            zip_code=req.zip_code,
            max_rating=req.max_rating,
            min_rating=req.min_rating,
            operational_category=req.operational_category,
        )

        docs = vectorstore.similarity_search(
            query=req.question,
            k=req.top_k,
            filter=filter_dict or None,
        )

        sources = [
            {
                "id": d.id,
                "hospital": d.metadata.get("google_name"),
                "city": d.metadata.get("city"),
                "state": d.metadata.get("state"),
                "rating": d.metadata.get("review_rating"),
                "category": d.metadata.get("operational_category"),
                "text": d.page_content,
            }
            for d in docs
        ]
        yield ndjson({"type": "sources", "sources": sources})

        if not docs:
            yield ndjson(
                {
                    "type": "token",
                    "text": "No relevant reviews matched your question and filter criteria. "
                    "Try loosening the filters.",
                }
            )
            yield ndjson({"type": "done"})
            return

        prompt = build_prompt(req.question, format_context(docs))
        messages = [{"role": "user", "content": prompt}]
        input_ids = tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, return_tensors="pt"
        ).to(device)

        streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
        gen_kwargs = dict(
            input_ids=input_ids,
            attention_mask=torch.ones_like(input_ids),
            streamer=streamer,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.1,
            pad_token_id=tokenizer.eos_token_id,
        )

        with generation_lock:
            thread = threading.Thread(target=model.generate, kwargs=gen_kwargs, daemon=True)
            thread.start()
            for text in streamer:
                if text:
                    yield ndjson({"type": "token", "text": text})
            thread.join()

        yield ndjson({"type": "done"})
    except Exception as exc:  # surface errors to the UI instead of dropping the stream
        yield ndjson({"type": "error", "message": str(exc)})


@app.post("/api/rag/stream")
def rag_stream(req: RagRequest):
    return StreamingResponse(
        stream_rag_answer(req),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "device": device, "model": model_id}
