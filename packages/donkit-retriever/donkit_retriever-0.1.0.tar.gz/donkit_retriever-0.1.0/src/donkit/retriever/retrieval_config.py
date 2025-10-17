from enum import StrEnum, auto
from typing import Literal

from pydantic import BaseModel, Field


class RetrieverOptions(BaseModel):
    filename_search: bool = Field(default=False, description="Enable filename search")
    composite_query_detection: bool = Field(
        default=False, description="Split composite query into several simple questions"
    )
    partial_search: bool = Field(
        default=False, description="Search by small chunks and take it`s neighbors."
    )
    max_retrieved_docs: int = Field(
        default=10, description="Maximum number of documents to retrieve."
    )


class EmbedderType(StrEnum):
    OPENAI = auto()
    VERTEX = auto()
    AZURE_OPENAI = auto()


class Embedder(BaseModel):
    embedder_type: str = Field(default=EmbedderType.VERTEX)


class RetrievalConfig(BaseModel):
    embedder: Embedder = Field(default_factory=Embedder)
    vector_database: Literal["qdrant", "chroma", "milvus"] = Field(default="qdrant")
    retriever_options: RetrieverOptions = Field(default_factory=RetrieverOptions)
