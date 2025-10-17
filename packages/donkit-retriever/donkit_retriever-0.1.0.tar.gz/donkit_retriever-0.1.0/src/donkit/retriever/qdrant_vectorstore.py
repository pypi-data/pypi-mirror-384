from urllib.parse import urlparse

from langchain.embeddings.base import Embeddings
from langchain_core.documents import Document
from loguru import logger
from qdrant_client import AsyncQdrantClient
from qdrant_client import models
from qdrant_client.conversions import common_types as qdrant_types

from .abstractions import VectorstoreModuleAbstract


def parse_qdrant_url(url: str) -> tuple[str, int, bool]:
    if "://" not in url:
        url = f"http://{url}"
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 6333
    use_https = parsed.scheme == "https"
    return host, port, use_https


class QdrantVectorstoreModule(VectorstoreModuleAbstract):
    """
    A wrapper around AsyncQdrantClient that implements the VectorstoreModuleAbstract interface.
    Documents are stored as vectors within a Qdrant collection; the client provides simple operations
    for search.
    """

    def __init__(
        self,
        database_url: str,
        collection_name: str,
        embeddings: Embeddings,
    ) -> None:
        self.embeddings = embeddings
        host, port, use_https = parse_qdrant_url(database_url)
        self.client = AsyncQdrantClient(
            host=host,
            port=port,
            https=use_https,
        )
        self.collection_name = collection_name

    async def perform_vector_search(
        self,
        query: str,
        k: int = 10,
        accessible_categories: list[str] | None = None,
    ) -> list[Document]:
        query_vector = await self.embeddings.aembed_query(query)
        try:
            response = await self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=k,
                with_payload=True,
                with_vectors=False,
            )
        except Exception as ex:
            logger.error(f"Error performing vector search: {ex}")
            return []
        points = getattr(response, "points", response)
        results: list[Document] = []
        for scored_point in points:
            payload = scored_point.payload or {}
            text = payload.get("text", "")
            metadata = dict(payload)
            score = getattr(scored_point, "score", None)
            if score is not None:
                try:
                    metadata["DISTANCE"] = 1.0 - float(score)
                except Exception as ex:
                    logger.error(f"Error calculating distance: {ex}")
                    metadata["DISTANCE"] = score
            results.append(Document(page_content=text, metadata=metadata))
        results.sort(key=lambda d: d.metadata.get("DISTANCE", 1.0))
        return results

    @staticmethod
    def extract_scroll_res(
        scroll_res: tuple[list[qdrant_types.Record], qdrant_types.PointId | None],
        preserve_distance: float | None = None,
    ) -> list[Document]:
        points = scroll_res[0] if isinstance(scroll_res, tuple) else scroll_res
        documents: list[Document] = []
        for p in points:
            payload = p.payload or {}
            text = payload.get("text", "")
            md = dict(payload)
            if preserve_distance is not None:
                md["DISTANCE"] = preserve_distance
            documents.append(Document(page_content=text, metadata=md))
        return documents

    async def _get_chunk_page(
        self,
        document_id: str,
        chunk_page: int,
        preserve_distance: float | None = None,
    ) -> list[Document]:
        """Common method to get full page and neighbour pages with top_chunk."""
        filtered = models.Filter(
            must=[
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=document_id),
                ),
                models.FieldCondition(
                    key="page_number",
                    range=models.Range(
                        gte=max(1, chunk_page - 1),
                        lte=chunk_page + 1,
                    ),
                ),
            ]
        )
        try:
            scroll_res = await self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filtered,
                with_payload=True,
                limit=1000,  # Большой лимит, что бы получить всю страницу
            )
        except Exception as ex:
            logger.error(f"Error getting chunk page: {ex}")
            return []
        return self.extract_scroll_res(scroll_res, preserve_distance)

    async def _get_chunk_neighbors_by_range(
        self,
        document_id: str,
        center_chunk_index: int,
        n: int = 10,
        preserve_distance: float | None = None,
    ) -> list[Document]:
        """Common method to get neighboring chunks by document_id and chunk_index range."""
        filtered = models.Filter(
            must=[
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=document_id),
                ),
                models.FieldCondition(
                    key="chunk_index",
                    range=models.Range(
                        gte=max(0, center_chunk_index - n),
                        lte=center_chunk_index + n,
                    ),
                ),
            ]
        )
        try:
            scroll_res = await self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filtered,
                with_payload=True,
                limit=2 * n + 1,
            )
        except Exception as ex:
            logger.error(f"Error getting chunk neighbors: {ex}")
            return []
        return self.extract_scroll_res(scroll_res, preserve_distance)

    async def fetch_chunk_neighbors(
        self, top_chunks: list[Document], n: int = 3
    ) -> list[Document]:
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

    async def search_context_by_document_id(
        self,
        query: str,
        k: int,
        document_id: str | None = None,
        filename: str | None = None,
    ) -> list[Document]:
        query_vector = await self.embeddings.aembed_query(query)
        must = []
        if document_id:
            must.append(
                models.FieldCondition(
                    key="document_id", match=models.MatchValue(value=document_id)
                )
            )
        if filename:
            must.append(
                models.FieldCondition(
                    key="filename", match=models.MatchValue(value=filename)
                )
            )
        try:
            response = await self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=k,
                with_payload=True,
                filter=models.Filter(must=must),
            )
        except Exception:
            return []
        points = getattr(response, "points", response)
        documents: list[Document] = []
        for scored_point in points:
            payload = scored_point.payload or {}
            text = payload.get("text", "")
            md = dict(payload)
            md["filename"] = filename
            score = getattr(scored_point, "score", None)
            if score is not None:
                try:
                    md["DISTANCE"] = 1.0 - float(score)
                except Exception:
                    md["DISTANCE"] = score
            documents.append(Document(page_content=text, metadata=md))
        # Documents will be filtered by VectorstoreService
        documents.sort(key=lambda d: d.metadata.get("DISTANCE", 1.0))
        return documents

    async def handle_filename_search(
        self, query: str, filename: str, k: int = 10
    ) -> list[Document]:
        query_vector = await self.embeddings.aembed_query(filename)
        filenames_collection = f"filenames_{self.collection_name}"
        try:
            response = await self.client.query_points(
                collection_name=filenames_collection,
                query=query_vector,
                limit=k,
                with_payload=True,
            )
        except Exception as ex:
            logger.error(f"Error performing filename search: {ex}")
            return []
        points = getattr(response, "points", response)
        result_documents: list[Document] = []
        for scored_point in points:
            payload = scored_point.payload or {}
            found_filename = payload.get("filename", "")
            score = getattr(scored_point, "score", None)
            filename_distance = 1.0 - float(score) if score is not None else 1.0
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
