import os
import pandas as pd
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
from pinecone import Pinecone, ServerlessSpec

# 1. Load environment variables
load_dotenv()

# 2. Initialize open-source embedding model (runs locally on CPU/GPU)
# Default model: 'sentence-transformers/all-MiniLM-L6-v2' (384 dimensions)
embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2"
embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)

# 3. Create Pinecone Serverless Index with 384 dimensions
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "hospital-reviews-hf"

existing_indexes = [idx.name for idx in pc.list_indexes()]
if index_name not in existing_indexes:
    pc.create_index(
        name=index_name,
        dimension=384,  # Matches all-MiniLM-L6-v2 vector dimension
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

# 4. Load dataset and clean missing values
df = pd.read_csv("../Large_Data/reviews_with_topics.csv").dropna(subset=["review_text"]).reset_index(drop=True)

# 5. Build Document list with metadata
documents = [
    Document(
        page_content=str(row["review_text"]),
        metadata={
            "google_name": str(row["google_name"]) if pd.notna(row["google_name"]) else "Unknown",
            "city": str(row["city"]) if pd.notna(row["city"]) else "Unknown",
            "state": str(row["state"]) if pd.notna(row["state"]) else "Unknown",
            "zip": str(row["zip"]) if pd.notna(row["zip"]) else "",
            "review_rating": float(row["review_rating"]) if pd.notna(row["review_rating"]) else 0.0,
            "operational_category": str(row["operational_category"]) if pd.notna(row["operational_category"]) else "Uncategorized"
        },
        id=str(f"review_{row['review_id']}" if pd.notna(row.get("review_id")) else f"review_{idx}")
    )
    for idx, row in df.iterrows()
]

# 6. Ingest documents into Pinecone VectorStore
vectorstore = PineconeVectorStore.from_documents(
    documents=documents,
    embedding=embeddings,
    index_name=index_name
)

print(f"Successfully ingested {len(documents)} documents using '{embedding_model_name}'.")