from langchain.schema import Document
from loguru import logger

from .abstractions import VectorstoreServiceAbstract
from .abstractions import VectorstoreModuleAbstract

from .retrieval_config import RetrievalConfig


class VectorstoreService(VectorstoreServiceAbstract):
    def __init__(
        self,
        config: RetrievalConfig,
        vectorstore_module: VectorstoreModuleAbstract,
    ):
        self.config = config
        self.vectorstore_module = vectorstore_module

    async def search_documents(
        self,
        query: str,
        k: int = 10,
    ) -> list[Document]:
        """
        Searches for documents in the index based on the input query.
        This is the main orchestrator method that coordinates the search process.
        """
        try:
            # Step 1: Handle filename search if enabled
            filename_results = (
                (await self.vectorstore_module.handle_filename_search(query, k))
                if self.config.retriever_options.filename_search
                else []
            )
            # Step 2: Perform vector search to get top chunks
            top_chunks = await self.vectorstore_module.perform_vector_search(query, k)
            logger.info(f"Top chunks: {len(top_chunks)}")
            # Step 3: Fetch neighboring chunks for context enrichment
            neighbors = (
                await self.vectorstore_module.fetch_chunk_neighbors(top_chunks, 10)
                if self.config.retriever_options.partial_search
                else []
            )
            if self.config.retriever_options.partial_search:
                logger.info(f"Neighbors: {len(neighbors)}")
            # Step 4: Combine all chunks and group by document
            all_chunks = top_chunks + neighbors + filename_results
            documents = self.combine_document_chunks(all_chunks)
            if self.accessible_categories:
                documents = self.filter_documents_by_category(documents)
            return documents
        except Exception as e:
            logger.error(f"Error during search: {e}")
            raise

    @staticmethod
    def combine_document_chunks(chunks: list[Document]) -> list[Document]:
        """Combine chunks from the same document."""
        documents_map = {}
        chunks.sort(key=lambda x: x.metadata.get("chunk_index", 0))
        for chunk in chunks:
            document_id = chunk.metadata.get("document_id")
            if not document_id:
                continue
            if document_id not in documents_map:
                documents_map[document_id] = {
                    "text": chunk.page_content,
                    "metadata": chunk.metadata.copy(),
                    "DISTANCE": chunk.metadata.get(
                        "DISTANCE", 1.0
                    ),  # Default to 1.0 if no distance
                }
            else:
                # Append text content
                documents_map[document_id]["text"] += f"\n\n{chunk.page_content}"

                # Keep track of the best distance from any chunk
                chunk_distance = chunk.metadata.get("DISTANCE", 1.0)
                if chunk_distance < documents_map[document_id]["DISTANCE"]:
                    documents_map[document_id]["DISTANCE"] = chunk_distance

        # Convert combined chunks to Document objects
        combined_documents = []
        for doc_id, doc_data in documents_map.items():
            metadata = doc_data["metadata"]
            metadata["DISTANCE"] = doc_data.get("DISTANCE", 1.0)
            combined_documents.append(
                Document(
                    page_content=doc_data["text"],
                    metadata=metadata,
                )
            )

        # Sort by distance (lower is better)
        combined_documents.sort(key=lambda doc: doc.metadata.get("DISTANCE", 1.0))
        return combined_documents

    def filter_documents_by_category(self, documents: list[Document]) -> list[Document]:
        other_categories_clean = {c.replace(" ", "") for c in self.other_categories}
        filtered_documents = []
        for doc in documents:
            category = doc.metadata.get("category")
            category_clean = (
                category.strip().lower().replace(" ", "") if category else None
            )
            if (
                category is None
                or category in self.accessible_categories
                or (
                    category_clean is not None
                    and category_clean in other_categories_clean
                )
            ):
                filtered_documents.append(doc)
            else:
                logger.debug(
                    f"Document filtered out by category: "
                    f"doc_id={doc.metadata.get('document_id')}, "
                    f"category={category}, "
                    f"allowed={self.accessible_categories}"
                )
        logger.debug(
            f"Filtered {len(documents) - len(filtered_documents)} "
            f"documents by category, returned {len(filtered_documents)}"
        )
        return filtered_documents
