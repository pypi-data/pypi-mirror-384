"""
Embedding Database Tool for ToolUniverse

A unified tool for managing embedding databases with FAISS vector search and SQLite metadata storage.
Supports creating databases from documents, adding documents, searching, and loading existing databases.
Uses OpenAI's embedding models for text-to-vector conversion, with support for Azure OpenAI.
"""

import os
import json
import sqlite3
import numpy as np
from pathlib import Path
from typing import List, Dict
import hashlib

try:
    import faiss
except ImportError:
    raise ImportError("faiss-cpu is required. Install with: pip install faiss-cpu")

try:
    from openai import OpenAI, AzureOpenAI
except ImportError:
    raise ImportError("openai is required. Install with: pip install openai")

from .base_tool import BaseTool
from .tool_registry import register_tool
from .logging_config import get_logger


@register_tool("EmbeddingDatabase")
class EmbeddingDatabase(BaseTool):
    """
    Unified embedding database tool supporting multiple operations:
    - create_from_docs: Create new database from documents
    - add_docs: Add documents to existing database
    - search: Search for similar documents
    - load_database: Load existing database from path
    """

    def __init__(self, tool_config):
        super().__init__(tool_config)
        self.logger = get_logger("EmbeddingDatabase")

        # OpenAI configuration
        openai_config = tool_config.get("configs", {}).get("openai_config", {})
        azure_config = tool_config.get("configs", {}).get("azure_openai_config", {})

        # Initialize OpenAI client (regular or Azure)
        self.openai_client = None
        self.azure_client = None

        # Initialize both clients for flexibility
        if openai_config.get("api_key") or os.getenv("OPENAI_API_KEY"):
            self.openai_client = self._init_openai_client(openai_config)

        if azure_config.get("api_key") or os.getenv("AZURE_OPENAI_API_KEY"):
            self.azure_client = self._init_azure_client(azure_config)

        if not self.openai_client and not self.azure_client:
            raise ValueError(
                "Either OpenAI or Azure OpenAI API credentials must be provided"
            )

        # Storage configuration
        storage_config = tool_config.get("configs", {}).get("storage_config", {})
        self.data_dir = Path(storage_config.get("data_dir", "./data/embeddings"))
        self.faiss_index_type = storage_config.get("faiss_index_type", "IndexFlatIP")

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Database paths
        self.db_path = self.data_dir / "embeddings.db"

        # Initialize SQLite database
        self._init_database()

    def _init_openai_client(self, config):
        """Initialize OpenAI client with configuration"""
        # Handle environment variable substitution
        api_key = self._substitute_env_vars(config.get("api_key")) or os.getenv(
            "OPENAI_API_KEY"
        )
        if not api_key:
            return None

        base_url = self._substitute_env_vars(config.get("base_url")) or os.getenv(
            "OPENAI_BASE_URL", "https://api.openai.com/v1"
        )

        return OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=config.get("timeout", 60),
            max_retries=config.get("max_retries", 3),
        )

    def _substitute_env_vars(self, value):
        """Substitute environment variables in configuration values"""
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            # Handle default values like ${VAR:default}
            if ":" in value:
                var_part = value[2:-1]  # Remove ${ and }
                var_name, default_value = var_part.split(":", 1)
                return os.getenv(var_name, default_value)
            else:
                var_name = value[2:-1]  # Remove ${ and }
                return os.getenv(var_name)
        return value

    def _init_azure_client(self, config):
        """Initialize Azure OpenAI client with configuration"""
        # Handle environment variable substitution
        api_key = self._substitute_env_vars(config.get("api_key")) or os.getenv(
            "AZURE_OPENAI_API_KEY"
        )
        endpoint = self._substitute_env_vars(config.get("azure_endpoint")) or os.getenv(
            "AZURE_OPENAI_ENDPOINT"
        )
        api_version = self._substitute_env_vars(config.get("api_version")) or os.getenv(
            "AZURE_OPENAI_API_VERSION", "2024-02-01"
        )

        if not api_key or not endpoint:
            return None

        return AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version,
            timeout=120,  # Increased timeout for Azure
            max_retries=5,  # Increased retries for Azure
        )

    def _init_database(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS databases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    embedding_model TEXT,
                    embedding_dimensions INTEGER,
                    document_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    database_name TEXT NOT NULL,
                    faiss_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    metadata_json TEXT,
                    text_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (database_name) REFERENCES databases (name)
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_database_name ON documents (database_name)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_text_hash ON documents (text_hash)
            """
            )

    def run(self, arguments):
        """Main entry point for the tool"""
        action = arguments.get("action")

        if action == "create_from_docs":
            return self._create_from_documents(arguments)
        elif action == "add_docs":
            return self._add_documents(arguments)
        elif action == "search":
            return self._search(arguments)
        elif action == "load_database":
            return self._load_database(arguments)
        else:
            return {"error": f"Unknown action: {action}"}

    def _create_from_documents(self, arguments):
        """Create new embedding database from documents"""
        database_name = arguments.get("database_name")
        documents = arguments.get("documents", [])
        metadata = arguments.get("metadata", [])
        model = arguments.get("model", "text-embedding-3-small")
        description = arguments.get("description", "")
        use_azure = arguments.get("use_azure", False)

        if not database_name:
            return {"error": "database_name is required"}
        if not documents:
            return {"error": "documents list cannot be empty"}

        # Check if database already exists
        if self._database_exists(database_name):
            return {
                "error": f"Database '{database_name}' already exists. Use 'add_docs' to add more documents."
            }

        try:
            # Generate embeddings
            self.logger.info(
                f"Generating embeddings for {len(documents)} documents using {model}"
            )
            embeddings = self._generate_embeddings(documents, model, use_azure)

            if not embeddings:
                return {"error": "Failed to generate embeddings"}

            # Get embedding dimensions
            dimensions = len(embeddings[0])

            # Create FAISS index
            if self.faiss_index_type == "IndexFlatIP":
                index = faiss.IndexFlatIP(dimensions)
            elif self.faiss_index_type == "IndexFlatL2":
                index = faiss.IndexFlatL2(dimensions)
            else:
                index = faiss.IndexFlatIP(dimensions)  # Default fallback

            # Add embeddings to FAISS index
            embedding_matrix = np.array(embeddings, dtype=np.float32)

            # Normalize embeddings for cosine similarity if using IndexFlatIP
            if self.faiss_index_type == "IndexFlatIP":
                # Normalize the embeddings to unit vectors for cosine similarity
                norms = np.linalg.norm(embedding_matrix, axis=1, keepdims=True)
                embedding_matrix = embedding_matrix / norms
                self.logger.info(
                    f"Normalized embeddings for IndexFlatIP. Norms: {norms.flatten()[:3]}..."
                )

            index.add(embedding_matrix)

            # Save FAISS index
            index_path = self.data_dir / f"{database_name}.faiss"
            faiss.write_index(index, str(index_path))

            # Store database info and documents in SQLite
            with sqlite3.connect(self.db_path) as conn:
                # Insert database record
                conn.execute(
                    """
                    INSERT INTO databases (name, description, embedding_model, embedding_dimensions, document_count)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (database_name, description, model, dimensions, len(documents)),
                )

                # Insert document records
                for i, (doc, meta) in enumerate(
                    zip(documents, metadata + [{}] * len(documents))
                ):
                    text_hash = hashlib.md5(doc.encode()).hexdigest()
                    metadata_json = json.dumps(meta)

                    conn.execute(
                        """
                        INSERT INTO documents (database_name, faiss_index, text, metadata_json, text_hash)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (database_name, i, doc, metadata_json, text_hash),
                    )

            self.logger.info(
                f"Created database '{database_name}' with {len(documents)} documents"
            )

            return {
                "status": "success",
                "database_name": database_name,
                "documents_added": len(documents),
                "embedding_model": model,
                "dimensions": dimensions,
                "index_path": str(index_path),
            }

        except Exception as e:
            self.logger.error(f"Error creating database: {str(e)}")
            return {"error": f"Failed to create database: {str(e)}"}

    def _add_documents(self, arguments):
        """Add documents to existing database"""
        database_name = arguments.get("database_name")
        documents = arguments.get("documents", [])
        metadata = arguments.get("metadata", [])
        use_azure = arguments.get("use_azure", False)

        if not database_name:
            return {"error": "database_name is required"}
        if not documents:
            return {"error": "documents list cannot be empty"}

        if not self._database_exists(database_name):
            return {
                "error": f"Database '{database_name}' does not exist. Use 'create_from_docs' first."
            }

        try:
            # Get database info
            db_info = self._get_database_info(database_name)
            model = db_info["embedding_model"]

            # Generate embeddings for new documents
            self.logger.info(
                f"Generating embeddings for {len(documents)} new documents"
            )
            new_embeddings = self._generate_embeddings(documents, model, use_azure)

            if not new_embeddings:
                return {"error": "Failed to generate embeddings"}

            # Load existing FAISS index
            index_path = self.data_dir / f"{database_name}.faiss"
            index = faiss.read_index(str(index_path))

            # Get current document count for new indices
            current_count = index.ntotal

            # Add new embeddings to index
            new_embedding_matrix = np.array(new_embeddings, dtype=np.float32)

            # Normalize embeddings for cosine similarity if using IndexFlatIP
            if self.faiss_index_type == "IndexFlatIP":
                norms = np.linalg.norm(new_embedding_matrix, axis=1, keepdims=True)
                new_embedding_matrix = new_embedding_matrix / norms
                self.logger.info(
                    f"Normalized new embeddings for IndexFlatIP. Norms: {norms.flatten()[:3]}..."
                )

            index.add(new_embedding_matrix)

            # Save updated index
            faiss.write_index(index, str(index_path))

            # Add documents to SQLite
            with sqlite3.connect(self.db_path) as conn:
                for i, (doc, meta) in enumerate(
                    zip(documents, metadata + [{}] * len(documents))
                ):
                    text_hash = hashlib.md5(doc.encode()).hexdigest()
                    metadata_json = json.dumps(meta)
                    faiss_index = current_count + i

                    conn.execute(
                        """
                        INSERT INTO documents (database_name, faiss_index, text, metadata_json, text_hash)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (database_name, faiss_index, doc, metadata_json, text_hash),
                    )

                # Update document count
                conn.execute(
                    """
                    UPDATE databases
                    SET document_count = document_count + ?, updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                """,
                    (len(documents), database_name),
                )

            self.logger.info(
                f"Added {len(documents)} documents to database '{database_name}'"
            )

            return {
                "status": "success",
                "database_name": database_name,
                "documents_added": len(documents),
                "total_documents": current_count + len(documents),
            }

        except Exception as e:
            self.logger.error(f"Error adding documents: {str(e)}")
            return {"error": f"Failed to add documents: {str(e)}"}

    def _search(self, arguments):
        """Search for similar documents in database"""
        database_name = arguments.get("database_name")
        query = arguments.get("query")
        top_k = arguments.get("top_k", 5)
        filters = arguments.get(
            "metadata_filter", arguments.get("filters", {})
        )  # Support both parameter names
        use_azure = arguments.get("use_azure", False)

        if not database_name:
            return {"error": "database_name is required"}
        if not query:
            return {"error": "query is required"}

        if not self._database_exists(database_name):
            return {"error": f"Database '{database_name}' does not exist"}

        try:
            # Get database info
            db_info = self._get_database_info(database_name)
            model = db_info["embedding_model"]

            # Generate query embedding
            query_embedding = self._generate_embeddings([query], model, use_azure)
            if not query_embedding:
                return {"error": "Failed to generate query embedding"}

            # Load FAISS index
            index_path = self.data_dir / f"{database_name}.faiss"
            index = faiss.read_index(str(index_path))

            # Search for similar vectors
            query_vector = np.array([query_embedding[0]], dtype=np.float32)

            # Normalize query vector if using IndexFlatIP for cosine similarity
            if self.faiss_index_type == "IndexFlatIP":
                query_norm = np.linalg.norm(query_vector, axis=1, keepdims=True)
                query_vector = query_vector / query_norm
                self.logger.info(
                    f"Normalized query vector. Query norm: {query_norm[0][0]:.3f}"
                )

            scores, indices = index.search(query_vector, min(top_k, index.ntotal))
            self.logger.info(
                f"FAISS search results - Scores: {scores[0][:3]}, Indices: {indices[0][:3]}"
            )

            # Get document details from SQLite
            results = []
            with sqlite3.connect(self.db_path) as conn:
                for score, idx in zip(scores[0], indices[0]):
                    if idx == -1:  # FAISS returns -1 for unfilled positions
                        continue

                    cursor = conn.execute(
                        """
                        SELECT text, metadata_json FROM documents
                        WHERE database_name = ? AND faiss_index = ?
                    """,
                        (database_name, int(idx)),
                    )

                    row = cursor.fetchone()
                    if row:
                        text, metadata_json = row
                        metadata = json.loads(metadata_json) if metadata_json else {}

                        # Apply metadata filters if specified
                        if self._matches_filters(metadata, filters):
                            results.append(
                                {
                                    "text": text,
                                    "metadata": metadata,
                                    "similarity_score": float(score),
                                }
                            )

            # Sort by similarity score (descending)
            results.sort(key=lambda x: x["similarity_score"], reverse=True)

            return {
                "status": "success",
                "database_name": database_name,
                "query": query,
                "results": results[:top_k],
                "total_found": len(results),
            }

        except Exception as e:
            self.logger.error(f"Error searching database: {str(e)}")
            return {"error": f"Failed to search database: {str(e)}"}

    def _load_database(self, arguments):
        """Load existing database from path"""
        database_path = arguments.get("database_path")
        database_name = arguments.get("database_name")

        if not database_path:
            return {"error": "database_path is required"}
        if not database_name:
            return {"error": "database_name is required"}

        # This is a placeholder for loading external databases
        # Implementation would depend on the specific format of the external database
        return {"error": "load_database not yet implemented"}

    def _generate_embeddings(
        self, texts: List[str], model: str, use_azure: bool = False
    ) -> List[List[float]]:
        """Generate embeddings using OpenAI or Azure OpenAI API"""
        import time

        try:
            # Choose which client to use
            client = None
            if use_azure and self.azure_client:
                client = self.azure_client
                self.logger.info("Using Azure OpenAI for embeddings")
            elif not use_azure and self.openai_client:
                client = self.openai_client
                self.logger.info("Using OpenAI for embeddings")
            elif self.azure_client:  # Fallback to Azure if available
                client = self.azure_client
                self.logger.info("Falling back to Azure OpenAI")
            elif self.openai_client:  # Fallback to OpenAI if available
                client = self.openai_client
                self.logger.info("Falling back to OpenAI")
            else:
                raise ValueError("No OpenAI or Azure OpenAI client available")

            # Process in smaller batches for Azure OpenAI
            batch_size = 10 if use_azure else 100
            all_embeddings = []

            for _i in range(0, len(texts), batch_size):
                batch = texts[_i : _i + batch_size]
                retry_count = 0
                max_retries = 3

                while retry_count < max_retries:
                    try:
                        response = client.embeddings.create(input=batch, model=model)
                        batch_embeddings = [
                            embedding.embedding for embedding in response.data
                        ]
                        all_embeddings.extend(batch_embeddings)

                        # Small delay between batches for Azure
                        if use_azure and _i + batch_size < len(texts):
                            time.sleep(0.5)
                        break

                    except Exception as batch_error:
                        retry_count += 1
                        if retry_count >= max_retries:
                            raise batch_error

                        self.logger.warning(
                            f"Batch {_i//batch_size + 1} failed, retrying ({retry_count}/{max_retries})"
                        )
                        time.sleep(retry_count * 2)  # Exponential backoff

            return all_embeddings

        except Exception as e:
            self.logger.error(f"Error generating embeddings: {str(e)}")
            return []

    def _database_exists(self, database_name: str) -> bool:
        """Check if database exists"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM databases WHERE name = ?", (database_name,)
            )
            return cursor.fetchone() is not None

    def _get_database_info(self, database_name: str) -> Dict:
        """Get database information"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT name, description, embedding_model, embedding_dimensions, document_count, created_at
                FROM databases WHERE name = ?
            """,
                (database_name,),
            )
            row = cursor.fetchone()
            if row:
                return {
                    "name": row[0],
                    "description": row[1],
                    "embedding_model": row[2],
                    "embedding_dimensions": row[3],
                    "document_count": row[4],
                    "created_at": row[5],
                }
            return {}

    def _matches_filters(self, metadata: Dict, filters: Dict) -> bool:
        """Check if metadata matches the given filters"""
        if not filters:
            return True

        for key, filter_value in filters.items():
            if key not in metadata:
                return False

            meta_value = metadata[key]

            # Handle different filter types
            if isinstance(filter_value, dict):
                # Range filters like {"$gte": 2022, "$lt": 2025}
                if "$gte" in filter_value and meta_value < filter_value["$gte"]:
                    return False
                if "$gt" in filter_value and meta_value <= filter_value["$gt"]:
                    return False
                if "$lte" in filter_value and meta_value > filter_value["$lte"]:
                    return False
                if "$lt" in filter_value and meta_value >= filter_value["$lt"]:
                    return False
                if "$in" in filter_value and meta_value not in filter_value["$in"]:
                    return False
                if "$contains" in filter_value:
                    if isinstance(meta_value, list):
                        if filter_value["$contains"] not in meta_value:
                            return False
                    else:
                        if filter_value["$contains"] not in str(meta_value):
                            return False
            else:
                # Exact match
                if meta_value != filter_value:
                    return False

        return True
