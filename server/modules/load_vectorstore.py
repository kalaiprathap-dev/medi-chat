import os
import math
import time
from pathlib import Path
from dotenv import load_dotenv
from tqdm.auto import tqdm
from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = "us-east-1"
PINECONE_INDEX_NAME = "medicalindex-hybrid"   # new index: hybrid search needs dotproduct

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

UPLOAD_DIR = "./uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

SPARSE_MODEL = "pinecone-sparse-english-v0"

# initialize pinecone instance
pc = Pinecone(api_key=PINECONE_API_KEY)
spec = ServerlessSpec(cloud="aws", region=PINECONE_ENV)
existing_indexes = [i["name"] for i in pc.list_indexes()]

if PINECONE_INDEX_NAME not in existing_indexes:
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=768,
        metric="dotproduct",   # required for hybrid (dense + sparse) in one index
        spec=spec,
    )
    while not pc.describe_index(PINECONE_INDEX_NAME).status["ready"]:
        time.sleep(1)

index = pc.Index(PINECONE_INDEX_NAME)

embed_model = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    output_dimensionality=768,
)


# ---------- helpers ----------
def _normalize(vec):
    """Scale a dense vector to length 1 (dotproduct then behaves like cosine)."""
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def sparse_embed(texts, input_type):
    """Keyword (sparse) vectors from Pinecone's hosted model. input_type: 'passage' or 'query'."""
    out = []
    for i in range(0, len(texts), 32):
        res = pc.inference.embed(
            model=SPARSE_MODEL,
            inputs=texts[i:i + 32],
            parameters={"input_type": input_type, "return_tokens": True},
        )
        for r in res:
            out.append({"indices": r["sparse_indices"], "values": r["sparse_values"]})
    return out


def _clean_metadata(meta):
    """Pinecone metadata only allows str, number, bool or list of str."""
    return {k: v for k, v in meta.items() if isinstance(v, (str, int, float, bool))}


# ---------- upload: load, split, embed (dense + sparse) and upsert ----------
def load_vectorstore(uploaded_files):
    file_paths = []

    for file in uploaded_files:
        save_path = Path(UPLOAD_DIR) / file.filename
        with open(save_path, "wb") as f:
            f.write(file.file.read())
        file_paths.append(str(save_path))

    for file_path in file_paths:
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_documents(documents)

        texts = [chunk.page_content for chunk in chunks]
        metadatas = [{**_clean_metadata(chunk.metadata), "text": chunk.page_content} for chunk in chunks]
        ids = [f"{Path(file_path).stem}-{i}" for i in range(len(chunks))]

        print(f"Embedding {len(texts)} chunks (dense + sparse)...")
        dense = [_normalize(v) for v in embed_model.embed_documents(texts)]
        sparse = sparse_embed(texts, "passage")

        vectors = [
            {"id": i, "values": d, "sparse_values": s, "metadata": m}
            for i, d, s, m in zip(ids, dense, sparse, metadatas)
        ]

        print("Uploading to Pinecone...")
        for n in tqdm(range(0, len(vectors), 50), desc="Upserting to Pinecone"):
            index.upsert(vectors=vectors[n:n + 50])

        print(f"Upload complete for {file_path}")


# ---------- query: hybrid search ----------
def hybrid_search(question, top_k=5, alpha=0.6):
    """Return the best chunks as dicts: {"text", "source", "page", "score"}.

    alpha = 1.0 -> pure meaning (dense). alpha = 0.0 -> pure keywords (sparse).
    """
    dense = _normalize(embed_model.embed_query(question))
    sparse = sparse_embed([question], "query")[0]

    dense = [v * alpha for v in dense]
    sparse = {"indices": sparse["indices"], "values": [v * (1 - alpha) for v in sparse["values"]]}

    res = index.query(
        vector=dense,
        sparse_vector=sparse,
        top_k=top_k,
        include_metadata=True,
    )
    return [
        {
            "text": (m.metadata or {}).get("text", ""),
            "source": (m.metadata or {}).get("source", ""),
            "page": (m.metadata or {}).get("page"),
            "score": m.score,
        }
        for m in res.matches
    ]