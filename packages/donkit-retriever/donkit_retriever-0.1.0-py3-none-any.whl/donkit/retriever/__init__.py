from langchain.embeddings.base import Embeddings
from loguru import logger

from .abstractions import VectorstoreServiceAbstract
from .chroma_vectorstore import ChromaVectorstoreModule
from .milvus_vectorstore import MilvusVectorstoreModule
from .qdrant_vectorstore import QdrantVectorstoreModule
from .retrieval_config import RetrievalConfig
from .vectorstore_service import VectorstoreService


def create_vectorstore_service(
    db_type: str,
    embeddings: Embeddings,
    config: RetrievalConfig,
    collection_name: str = "my_collection",
    database_uri: str | None = None,
) -> VectorstoreServiceAbstract:
    """
    Factory function to create a VectorstoreService with the appropriate vectorstore module.

    Args:
        db_type: Type of vector database ('qdrant', 'chroma', or 'milvus')
        embeddings: Embeddings instance for encoding text
        config: Retrieval configuration
        collection_name: Name of the collection to use
        database_uri: URI of the database (defaults per db_type)

    Returns:
        VectorstoreService instance

    Raises:
        ValueError: If db_type is not supported
    """
    db_type = db_type.lower()

    match db_type:
        case "qdrant":
            database_uri = database_uri or "http://localhost:6333"
            vectorstore_module = QdrantVectorstoreModule(
                database_url=database_uri,
                collection_name=collection_name,
                embeddings=embeddings,
            )
        case "chroma":
            database_uri = database_uri or "http://localhost:8000"
            vectorstore_module = ChromaVectorstoreModule(
                database_url=database_uri,
                collection_name=collection_name,
                embeddings=embeddings,
            )
        case "milvus":
            database_uri = database_uri or "http://localhost:19530"
            vectorstore_module = MilvusVectorstoreModule(
                database_url=database_uri,
                collection_name=collection_name,
                embeddings=embeddings,
            )
        case _:
            raise ValueError(
                f"Unsupported database type: {db_type}. "
                f"Supported types: qdrant, chroma, milvus"
            )

    logger.info(
        f"Created {db_type} vectorstore service for collection '{collection_name}'"
    )

    return VectorstoreService(config=config, vectorstore_module=vectorstore_module)


__all__ = [
    "VectorstoreService",
    "QdrantVectorstoreModule",
    "ChromaVectorstoreModule",
    "MilvusVectorstoreModule",
    "RetrievalConfig",
    "create_vectorstore_service",
]
