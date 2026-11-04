from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from modules.llm import get_llm_chain
from modules.query_handlers import query_chain
from modules.load_vectorstore import hybrid_search
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field
from typing import List, Optional
from logger import logger

router = APIRouter()


@router.post("/ask/")
async def ask_question(question: str = Form(...)):
    try:
        logger.info(f"user query: {question}")

        # Hybrid search: meaning (dense) + keywords (sparse)
        matches = hybrid_search(question, top_k=5, alpha=0.6)

        docs = [
            Document(
                page_content=m["text"],
                metadata={"source": m["source"], "page": m["page"], "score": m["score"]},
            )
            for m in matches
        ]

        class SimpleRetriever(BaseRetriever):
            tags: Optional[List[str]] = Field(default_factory=list)
            metadata: Optional[dict] = Field(default_factory=dict)

            def __init__(self, documents: List[Document]):
                super().__init__()
                self._docs = documents

            def _get_relevant_documents(self, query: str) -> List[Document]:
                return self._docs

        retriever = SimpleRetriever(docs)
        chain = get_llm_chain(retriever)
        result = query_chain(chain, question)

        logger.info("query successful")
        return result

    except Exception as e:
        logger.exception("Error processing question")
        return JSONResponse(status_code=500, content={"error": str(e)})