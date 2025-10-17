from urllib.parse import urlparse

import chromadb
from chromadb.config import Settings
from langchain.embeddings.base import Embeddings
from langchain_core.documents import Document
from loguru import logger

from .abstractions import VectorstoreModuleAbstract
from .retrieval_config import RetrievalConfig


def parse_chroma_url(url: str) -> tuple[str, int]:
    """Parse ChromaDB URL to extract host and port."""
    if "://" not in url:
        url = f"http://{url}"
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 8000
    return host, port


class ChromaVectorstoreModule(VectorstoreModuleAbstract):
    """
    A wrapper around ChromaDB client that implements the VectorstoreModuleAbstract interface.
    Documents are stored as vectors within a Chroma collection; the client provides simple operations
    for search.
    """

    def __init__(
        self,
        database_url: str,
        collection_name: str,
        config: RetrievalConfig,
        embeddings: Embeddings,
    ) -> None:
        self.config = config
        self.embeddings = embeddings
        host, port = parse_chroma_url(database_url)
        self.client = chromadb.HttpClient(
            host=host, port=port, settings=Settings(allow_reset=True)
        )
        self.collection_name = collection_name
        self.collection = self._ensure_collection(self.collection_name)

    def _ensure_collection(self, name: str):
        """Create or get existing collection."""
        try:
            collection = self.client.get_collection(name=name)
            logger.info(f"Using existing ChromaDB collection: {name}")
        except Exception:
            collection = self.client.create_collection(
                name=name, metadata={"description": "RAG document chunks"}
            )
            logger.info(f"Created ChromaDB collection: {name}")
        return collection

    async def search_context_by_document_id(
        self,
        query: str,
        k: int,
        document_id: str | None = None,
        filename: str | None = None,
    ) -> list[Document]:
        """Search for documents by document_id or filename."""
        query_vector = await self.embeddings.aembed_query(query)

        # Build where clause
        where_clause = None
        if document_id and filename:
            where_clause = {
                "$and": [
                    {"document_id": {"$eq": document_id}},
                    {"filename": {"$eq": filename}},
                ]
            }
        elif document_id:
            where_clause = {"document_id": {"$eq": document_id}}
        elif filename:
            where_clause = {"filename": {"$eq": filename}}
        else:
            return []

        try:
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=k,
                where=where_clause,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.error(f"Error searching by document_id/filename: {e}")
            return []

        documents: list[Document] = []
        if results["documents"] and results["documents"][0]:
            for doc, metadata, distance in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                metadata["DISTANCE"] = distance
                if filename:
                    metadata["filename"] = filename
                documents.append(Document(page_content=doc, metadata=metadata))

        documents.sort(key=lambda d: d.metadata.get("DISTANCE", 1.0))
        return documents

    async def handle_filename_search(
        self, query: str, filename: str, k: int = 10
    ) -> list[Document]:
        """
        Search for documents by filename using separate filenames collection.
        """
        query_vector = await self.embeddings.aembed_query(filename)
        filenames_collection_name = f"filenames_{self.collection_name}"

        try:
            filenames_collection = self.client.get_collection(
                name=filenames_collection_name
            )
        except Exception:
            logger.warning(
                f"Filenames collection '{filenames_collection_name}' does not exist"
            )
            return []

        try:
            results = filenames_collection.query(
                query_embeddings=[query_vector],
                n_results=k,
                include=["metadatas", "distances"],
            )
        except Exception as e:
            logger.error(f"Error performing filename search: {e}")
            return []

        result_documents: list[Document] = []
        if results["metadatas"] and results["metadatas"][0]:
            for metadata, distance in zip(
                results["metadatas"][0], results["distances"][0]
            ):
                found_filename = metadata.get("filename", "")
                filename_distance = distance
                # Search for documents with this filename
                doc_results = await self.search_context_by_document_id(
                    query=query, filename=found_filename, k=k
                )
                # Preserve the filename search distance
                for doc in doc_results:
                    if (
                        "DISTANCE" not in doc.metadata
                        or doc.metadata["DISTANCE"] > filename_distance
                    ):
                        doc.metadata["DISTANCE"] = filename_distance
                result_documents.extend(doc_results)

        result_documents.sort(key=lambda d: d.metadata.get("DISTANCE", 1.0))
        return result_documents

    async def perform_vector_search(
        self,
        query: str,
        k: int = 10,
        accessible_categories: list[str] | None = None,
    ) -> list[Document]:
        """
        Performs vector search in ChromaDB.
        Returns the top matching chunks.
        """
        try:
            # Generate query embedding
            query_vector = await self.embeddings.aembed_query(query)

            # Prepare where clause for category filtering
            where_clause = None
            if accessible_categories:
                where_clause = {"category": {"$in": accessible_categories}}

            # Perform search
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=k,
                where=where_clause,
                include=["documents", "metadatas", "distances"],
            )

            documents: list[Document] = []
            if results["documents"] and results["documents"][0]:
                for i, (doc, metadata, distance) in enumerate(
                    zip(
                        results["documents"][0],
                        results["metadatas"][0],
                        results["distances"][0],
                    )
                ):
                    # Add distance to metadata
                    metadata["DISTANCE"] = distance
                    documents.append(Document(page_content=doc, metadata=metadata))

            # Sort by distance (lower is better)
            documents.sort(key=lambda d: d.metadata.get("DISTANCE", 1.0))
            return documents

        except Exception as e:
            logger.error(f"Error during ChromaDB search: {e}")
            return []

    async def _get_chunk_page(
        self,
        document_id: str,
        chunk_page: int,
        preserve_distance: float | None = None,
    ) -> list[Document]:
        """Get full page and neighbor pages with top_chunk."""
        try:
            results = self.collection.get(
                where={
                    "$and": [
                        {"document_id": {"$eq": document_id}},
                        {"page_number": {"$gte": max(1, chunk_page - 1)}},
                        {"page_number": {"$lte": chunk_page + 1}},
                    ]
                },
                include=["documents", "metadatas"],
            )
        except Exception as ex:
            logger.error(f"Error getting chunk page: {ex}")
            return []

        documents: list[Document] = []
        if results["documents"]:
            for doc, metadata in zip(results["documents"], results["metadatas"]):
                if preserve_distance is not None:
                    metadata["DISTANCE"] = preserve_distance
                documents.append(Document(page_content=doc, metadata=metadata))
        return documents

    async def _get_chunk_neighbors_by_range(
        self,
        document_id: str,
        center_chunk_index: int,
        n: int = 10,
        preserve_distance: float | None = None,
    ) -> list[Document]:
        """Get neighboring chunks by document_id and chunk_index range."""
        try:
            results = self.collection.get(
                where={
                    "$and": [
                        {"document_id": {"$eq": document_id}},
                        {"chunk_index": {"$gte": max(0, center_chunk_index - n)}},
                        {"chunk_index": {"$lte": center_chunk_index + n}},
                    ]
                },
                include=["documents", "metadatas"],
            )
        except Exception as ex:
            logger.error(f"Error getting chunk neighbors: {ex}")
            return []

        documents: list[Document] = []
        if results["documents"]:
            for doc, metadata in zip(results["documents"], results["metadatas"]):
                if preserve_distance is not None:
                    metadata["DISTANCE"] = preserve_distance
                documents.append(Document(page_content=doc, metadata=metadata))
        return documents

    async def fetch_chunk_neighbors(
        self, top_chunks: list[Document], n: int = 3
    ) -> list[Document]:
        """Fetch neighboring chunks for context enrichment."""
        neighbors: list[Document] = []
        loaded_pages = set()
        for chunk in top_chunks:
            document_id = chunk.metadata.get("document_id")
            chunk_index = chunk.metadata.get("chunk_index")
            chunk_page = chunk.metadata.get("page_number", 0)
            if chunk_page != 0 and (document_id, chunk_page) in loaded_pages:
                continue
            original_distance = chunk.metadata.get("DISTANCE", 0)
            if document_id and chunk_index is not None:
                if chunk_page == 0:
                    chunk_neighbors = await self._get_chunk_neighbors_by_range(
                        document_id,
                        int(chunk_index),
                        n,
                        original_distance,
                    )
                else:
                    chunk_neighbors = await self._get_chunk_page(
                        document_id, chunk_page, original_distance
                    )
                    loaded_pages.add((document_id, chunk_page))
                neighbors.extend(chunk_neighbors)
        return neighbors
