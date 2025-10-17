from urllib.parse import urlparse

from langchain.embeddings.base import Embeddings
from langchain_core.documents import Document
from loguru import logger
from pymilvus import Collection
from pymilvus import connections

from .abstractions import VectorstoreModuleAbstract


def parse_milvus_url(url: str) -> tuple[str, str, str]:
    """Parse Milvus URL to extract URI, user, and password."""
    if "://" not in url:
        # Simple host:port format without credentials
        return f"http://{url}", "", ""

    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 19530
    user = parsed.username or ""
    password = parsed.password or ""
    uri = f"{parsed.scheme}://{host}:{port}"
    return uri, user, password


class MilvusVectorstoreModule(VectorstoreModuleAbstract):
    """
    A wrapper around Milvus client that implements the VectorstoreModuleAbstract interface.
    Documents are stored as vectors within a Milvus collection; the client provides simple operations
    for search.
    """

    def __init__(
        self,
        database_url: str,
        collection_name: str,
        embeddings: Embeddings,
    ) -> None:
        self.embeddings = embeddings
        uri, user, password = parse_milvus_url(database_url)
        connections.connect(uri=uri, user=user, password=password)
        self.collection_name = collection_name
        self.collection = Collection(collection_name)
        try:
            self.collection.load()
            logger.info(f"Loaded Milvus collection: {collection_name}")
        except Exception as e:
            logger.warning(f"Could not load Milvus collection: {e}")

    async def search_context_by_document_id(
        self,
        query: str,
        k: int,
        document_id: str | None = None,
        filename: str | None = None,
    ) -> list[Document]:
        """Search for documents by document_id or filename."""
        query_vector = await self.embeddings.aembed_query(query)

        # Build filter expression
        expr_parts = []
        if document_id:
            expr_parts.append(f'document_id == "{document_id}"')
        if filename:
            expr_parts.append(f'filename == "{filename}"')

        if not expr_parts:
            return []

        expr = " && ".join(expr_parts)

        try:
            search_params = {
                "metric_type": "IP",
                "params": {"nprobe": 10},
            }
            search_result = self.collection.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=k,
                expr=expr,
                output_fields=[
                    "text",
                    "document_id",
                    "chunk_index",
                    "page_number",
                    "category",
                    "additional_info",
                    "filename",
                ],
            )
        except Exception as e:
            logger.error(f"Error searching by document_id/filename: {e}")
            return []

        documents: list[Document] = []
        first_batch = (
            search_result[0]
            if search_result and isinstance(search_result, list)
            else []
        )
        for result in first_batch:
            payload = {
                "document_id": result.entity.get("document_id"),
                "chunk_index": result.entity.get("chunk_index"),
                "page_number": result.entity.get("page_number"),
                "category": result.entity.get("category"),
                "additional_info": result.entity.get("additional_info"),
                "filename": result.entity.get("filename", filename),
                "DISTANCE": result.distance,
            }
            text = result.entity.get("text", "")
            documents.append(Document(page_content=text, metadata=payload))

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
            filenames_collection = Collection(filenames_collection_name)
            filenames_collection.load()
        except Exception as e:
            logger.warning(
                f"Filenames collection '{filenames_collection_name}' does not exist: {e}"
            )
            return []

        try:
            search_params = {
                "metric_type": "IP",
                "params": {"nprobe": 10},
            }
            search_result = filenames_collection.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=k,
                output_fields=["filename"],
            )
        except Exception as e:
            logger.error(f"Error performing filename search: {e}")
            return []

        result_documents: list[Document] = []
        first_batch = (
            search_result[0]
            if search_result and isinstance(search_result, list)
            else []
        )
        for result in first_batch:
            found_filename = result.entity.get("filename", "")
            filename_distance = result.distance
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
        Performs vector search in Milvus.
        Returns the top matching chunks.
        """
        try:
            query_vector = await self.embeddings.aembed_query(query)
            search_params = {
                "metric_type": "IP",
                "params": {"nprobe": 10},
            }

            # Build filter expression for categories if provided
            expr = None
            if accessible_categories:
                category_list = ", ".join([f'"{cat}"' for cat in accessible_categories])
                expr = f"category in [{category_list}]"

            search_result = self.collection.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=k,
                expr=expr,
                output_fields=[
                    "text",
                    "document_id",
                    "chunk_index",
                    "page_number",
                    "category",
                    "additional_info",
                ],
            )

            documents: list[Document] = []
            first_batch = (
                search_result[0]
                if search_result and isinstance(search_result, list)
                else []
            )
            for result in first_batch:
                payload = {
                    "document_id": result.entity.get("document_id"),
                    "chunk_index": result.entity.get("chunk_index"),
                    "page_number": result.entity.get("page_number"),
                    "category": result.entity.get("category"),
                    "additional_info": result.entity.get("additional_info"),
                    "DISTANCE": result.distance,
                }
                text = result.entity.get("text", "")
                documents.append(Document(page_content=text, metadata=payload))
            documents.sort(key=lambda d: d.metadata.get("DISTANCE", 1.0))
            return documents
        except Exception as e:
            logger.error(f"Error during Milvus search: {e}")
            return []

    async def _get_chunk_page(
        self,
        document_id: str,
        chunk_page: int,
        preserve_distance: float | None = None,
    ) -> list[Document]:
        """Get full page and neighbor pages with top_chunk."""
        try:
            expr = f'document_id == "{document_id}" && page_number >= {max(1, chunk_page - 1)} && page_number <= {chunk_page + 1}'
            results = self.collection.query(
                expr=expr,
                output_fields=[
                    "text",
                    "document_id",
                    "chunk_index",
                    "page_number",
                    "category",
                    "additional_info",
                ],
            )
        except Exception as ex:
            logger.error(f"Error getting chunk page: {ex}")
            return []

        documents: list[Document] = []
        for result in results:
            payload = {
                "document_id": result.get("document_id"),
                "chunk_index": result.get("chunk_index"),
                "page_number": result.get("page_number"),
                "category": result.get("category"),
                "additional_info": result.get("additional_info"),
                "DISTANCE": preserve_distance if preserve_distance is not None else 0,
            }
            text = result.get("text", "")
            documents.append(Document(page_content=text, metadata=payload))
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
            expr = f'document_id == "{document_id}" && chunk_index >= {max(0, center_chunk_index - n)} && chunk_index <= {center_chunk_index + n}'
            results = self.collection.query(
                expr=expr,
                output_fields=[
                    "text",
                    "document_id",
                    "chunk_index",
                    "page_number",
                    "category",
                    "additional_info",
                ],
            )
        except Exception as ex:
            logger.error(f"Error getting chunk neighbors: {ex}")
            return []

        documents: list[Document] = []
        for result in results:
            payload = {
                "document_id": result.get("document_id"),
                "chunk_index": result.get("chunk_index"),
                "page_number": result.get("page_number"),
                "category": result.get("category"),
                "additional_info": result.get("additional_info"),
                "DISTANCE": preserve_distance if preserve_distance is not None else 0,
            }
            text = result.get("text", "")
            documents.append(Document(page_content=text, metadata=payload))
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
