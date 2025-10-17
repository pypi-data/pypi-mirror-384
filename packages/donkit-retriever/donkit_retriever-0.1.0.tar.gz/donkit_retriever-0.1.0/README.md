# Retriever

Unified retrieval module for RAG system with support for multiple vector databases.

## Features

- **Multiple vector database backends**: Qdrant, ChromaDB, Milvus
- **Filename search**: Separate collection for efficient filename-based search
- **Context enrichment**: Fetch neighboring chunks for better context
- **Category filtering**: Filter results by accessible categories
- **Unified interface**: Single API for all vector stores

## Installation

```bash
poetry add donkit-retriever
```

## Usage

### Basic Setup

```python
from donkit.retriever import create_vectorstore_service, RetrievalConfig
from langchain.embeddings import OpenAIEmbeddings

# Configure retrieval options
config = RetrievalConfig(
    vector_database="qdrant",
    retriever_options={
        "filename_search": True,
        "partial_search": True,
        "max_retrieved_docs": 10,
    }
)

# Create service
embeddings = OpenAIEmbeddings()
service = create_vectorstore_service(
    db_type="qdrant",
    embeddings=embeddings,
    config=config,
    collection_name="my_collection",
    database_uri="http://localhost:6333",
)

# Search documents
documents = await service.search_documents(
    query="What is RAG?",
    k=5
)
```

### Supported Vector Databases

#### Qdrant
```python
service = create_vectorstore_service(
    db_type="qdrant",
    embeddings=embeddings,
    config=config,
    database_uri="http://localhost:6333",
)
```

#### ChromaDB
```python
service = create_vectorstore_service(
    db_type="chroma",
    embeddings=embeddings,
    config=config,
    database_uri="http://localhost:8000",
)
```

#### Milvus
```python
service = create_vectorstore_service(
    db_type="milvus",
    embeddings=embeddings,
    config=config,
    database_uri="http://localhost:19530",
)
```

### Configuration Options

```python
from donkit.retriever import RetrievalConfig, RetrieverOptions

config = RetrievalConfig(
    vector_database="qdrant",  # qdrant | chroma | milvus
    retriever_options=RetrieverOptions(
        filename_search=True,  # Enable filename-based search
        partial_search=True,   # Fetch neighboring chunks
        max_retrieved_docs=10, # Max documents to retrieve
    ),
    ranker="http://ranker-service:8000",  # Optional reranker URL
)
```

## Architecture

### VectorstoreModule
Each database has its own module implementing `VectorstoreModuleAbstract`:
- `QdrantVectorstoreModule`
- `ChromaVectorstoreModule`
- `MilvusVectorstoreModule`

### VectorstoreService
Orchestrates search operations:
1. Filename search (if enabled)
2. Vector search
3. Neighbor fetching (if partial_search enabled)
4. Document combination and deduplication

## Development

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run linter
poetry run ruff check .
```

## License

Proprietary
