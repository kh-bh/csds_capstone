import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

# 1. Load environment variables
load_dotenv()

# 2. Vector Store & Embeddings Initialization
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
index_name = "hospital-reviews-hf"

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(index_name)
vectorstore = PineconeVectorStore(index=index, embedding=embedding_model)

# 3. Load Hugging Face LLM directly
model_id = "meta-llama/Llama-3.2-1B-Instruct" 
# Alternative (no token required): model_id = "Qwen/Qwen2.5-1.5B-Instruct"

# 1. Determine optimal device for Mac (Metal Performance Shaders / MPS, or CPU)
if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"

print(f"Loading model onto device: {device}")

tokenizer = AutoTokenizer.from_pretrained(
    model_id, 
    token=os.getenv("HF_TOKEN")
)

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.float16 if device != "cpu" else torch.float32,
    low_cpu_mem_usage=True,
    token=os.getenv("HF_TOKEN")
).to(device)

# 3. Build HuggingFace Pipeline
pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=512,
    temperature=0.1,
    return_full_text=False
)

llm = HuggingFacePipeline(pipeline=pipe)


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
    filters = {}

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
        review_id = doc.id
        hospital = meta.get("google_name", "Unknown Hospital")
        rating = meta.get("review_rating", "N/A")
        category = meta.get("operational_category", "N/A")

        chunk = (
            f"--- START REVIEW ---\n"
            f"Review ID: {review_id}\n"
            f"Hospital: {hospital}\n"
            f"Rating: {rating} Stars\n"
            f"Category: {category}\n"
            f"Content: {doc.page_content}\n"
            f"--- END REVIEW ---"
        )
        formatted_chunks.append(chunk)

    return "\n\n".join(formatted_chunks)


def answer_question_with_rag(
    question: str,
    top_k: int = 4,
    google_name: Optional[List[str]] = None,
    city: Optional[List[str]] = None,
    state: Optional[List[str]] = None,
    zip_code: Optional[List[str]] = None,
    max_rating: Optional[float] = None,
    min_rating: Optional[float] = None,
    operational_category: Optional[List[str]] = None,
):
    """Retrieves filtered documents and generates an answer cited with source reviews."""
    filter_dict = build_pinecone_filter(
        google_name=google_name,
        city=city,
        state=state,
        zip_code=zip_code,
        max_rating=max_rating,
        min_rating=min_rating,
        operational_category=operational_category,
    )

    docs = vectorstore.similarity_search(
        query=question,
        k=top_k,
        filter=filter_dict if filter_dict else None
    )

    if not docs:
        print("No relevant reviews matched your question and metadata filter criteria.")
        return

    context = format_context(docs)

    prompt = f"""You are a helpful assistant analyzing hospital reviews. 
Answer the user's question using ONLY the provided reviews below. Summarize the response in 1-2 short paragraphs that discuess hospital performance generally, citing specfic hospital names using the (Hospital) citation format when necessary.

Question: {question}

Context Reviews:
{context}

Answer:"""

    response = llm.invoke(prompt)

    print("=== RAG Response ===")
    print(response)
    print("\n=== Retrived Review Citations ===")
    for d in docs:
        print(f"- ID: {d.id} | {d.metadata.get('google_name')} ({d.metadata.get('city')}, {d.metadata.get('state')}) | Rating: {d.metadata.get('review_rating')} | Text: {d.page_content[:100]}...")  # Print first 100 chars of review


if __name__ == "__main__":
    user_query = "What complaints do patients have regarding billing and rude staff?"
    
    answer_question_with_rag(
        question=user_query,
        state=["OH"],
        max_rating=2.0,
        operational_category=[
            "Admin, Billing & Communication",
            "Staffing & Operational Delays"
        ],
        top_k=3
    )