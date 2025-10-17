import re
from abc import ABC
from abc import abstractmethod
from typing import Any

from langchain.schema import Document
from loguru import logger


class VectorstoreModuleAbstract(ABC):
    """
    Interface for vectorstore database implementation
    """

    @abstractmethod
    async def handle_filename_search(
        self, query: str, filename: str, k: int
    ) -> list[Document]:
        raise NotImplementedError

    @abstractmethod
    async def perform_vector_search(
        self, query: str, k: int = 10, accessible_categories: list[str] | None = None
    ) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def fetch_chunk_neighbors(
        self, top_chunks: list[Document], n: int = 3
    ) -> list[Document]:
        """Fetch neighboring chunks for context enrichment."""
        raise NotImplementedError

    @staticmethod
    def generate_tensor_vector(query: list[str], max_features: int = 8) -> list[float]:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            logger.error("sentence_transformers not installed")
            return []
        model = SentenceTransformer(
            model_name_or_path="paraphrase-multilingual-MiniLM-L12-v2",
            cache_folder="./sentence_model",
            truncate_dim=max_features,
        )
        embeddings = model.encode(
            query, convert_to_tensor=True, output_dimension=max_features
        )
        return embeddings.tolist()

    @staticmethod
    def generate_sparse_vectors(
        document: str, max_features: int = 128
    ) -> tuple[dict[str, float], Any]:
        """
        Generate sparse vectors from a list of documents using TF-IDF and convert them
        into a list of dictionaries.
            Each dictionary represents a document's sparse vector
        with keys as column indices (as strings) and values as TF-IDF weights (floats).

        Args:
            document (str): The text query
            max_features (Optional[int]): The maximum number of features to extract.

        Returns:
            Tuple[List[Dict[str, float]], TfidfVectorizer]: A tuple containing:
                - a list of dictionaries representing
                    the sparse vectors for each document,
                - the fitted TfidfVectorizer.
        """
        try:
            import scipy as sp
            from sklearn.feature_extraction.text import TfidfVectorizer
        except ImportError:
            logger.error("scipy or sklearn not installed")
            return {"0": 0.0}, None
        vectorizer = TfidfVectorizer(max_features=max_features)
        sparse_matrix: sp.spmatrix = vectorizer.fit_transform([document])
        row = sparse_matrix[0]
        coo = row.tocoo()
        sparse_dict = {str(col): value for col, value in zip(coo.col, coo.data)}
        return sparse_dict, vectorizer

    @staticmethod
    def clean_text(text: str) -> str:
        """Очищает текст от мусора, разметки и лишних символов"""
        text = re.sub(r"\|+", "", text)  # Убираем столбцы типа "|||||"
        text = re.sub(r"\+{2,}", "", text)  # Убираем длинные ряды плюсов
        text = re.sub(r"-{2,}", "", text)  # Убираем повторяющиеся тире "--"
        text = re.sub(r"_{2,}", "", text)  # Убираем длинные ряды подчеркиваний "__"
        text = re.sub(r"\s+", " ", text).strip()  # Убираем лишние пробелы
        text = re.sub(r"\\", "", text)  # Убираем экранированные символы
        return text


class VectorstoreServiceAbstract(ABC):
    __accessible_categories: list[str] | None = None

    @property
    def accessible_categories(self) -> list[str] | None:
        """Get or set accessible categories for the vectorstore service."""
        return self.__accessible_categories

    @accessible_categories.setter
    def accessible_categories(self, categories: list[str] | None = None) -> None:
        self.__accessible_categories = categories

    @abstractmethod
    async def search_documents(self, query: str, k: int) -> list[Document]:
        raise NotImplementedError
