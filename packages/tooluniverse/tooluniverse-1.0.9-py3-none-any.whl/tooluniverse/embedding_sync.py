"""
Embedding Sync Tool for ToolUniverse

Synchronize embedding databases with HuggingFace Hub for sharing and collaboration.
Supports uploading local databases to HuggingFace and downloading databases from HuggingFace.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict
from datetime import datetime

try:
    from huggingface_hub import HfApi, upload_folder, snapshot_download
    from huggingface_hub.utils import HfHubHTTPError
except ImportError:
    raise ImportError(
        "huggingface_hub is required. Install with: pip install huggingface_hub"
    )

from .base_tool import BaseTool
from .tool_registry import register_tool
from .logging_config import get_logger


@register_tool("EmbeddingSync")
class EmbeddingSync(BaseTool):
    """
    Sync embedding databases with HuggingFace Hub.
    Supports uploading local databases and downloading shared databases.
    """

    def __init__(self, tool_config):
        super().__init__(tool_config)
        self.logger = get_logger("EmbeddingSync")

        # HuggingFace configuration
        hf_config = tool_config.get("configs", {}).get("huggingface_config", {})
        self.hf_token = hf_config.get("token") or os.getenv("HF_TOKEN")
        self.hf_endpoint = hf_config.get("endpoint", "https://huggingface.co")

        if not self.hf_token:
            self.logger.warning(
                "HuggingFace token not found. Some operations may fail."
            )

        # Initialize HF API
        self.hf_api = HfApi(endpoint=self.hf_endpoint, token=self.hf_token)

        # Storage configuration
        storage_config = tool_config.get("configs", {}).get("storage_config", {})
        self.data_dir = Path(storage_config.get("data_dir", "./data/embeddings"))
        self.export_dir = Path(storage_config.get("export_dir", "./exports"))

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def run(self, arguments):
        """Main entry point for the tool"""
        action = arguments.get("action")

        if action == "upload":
            return self._upload_to_huggingface(arguments)
        elif action == "download":
            return self._download_from_huggingface(arguments)
        else:
            return {"error": f"Unknown action: {action}"}

    def _upload_to_huggingface(self, arguments):
        """Upload local database to HuggingFace Hub"""
        database_name = arguments.get("database_name")
        repository = arguments.get("repository")
        description = arguments.get("description", "")
        private = arguments.get("private", False)
        commit_message = arguments.get(
            "commit_message", f"Upload {database_name} database"
        )

        if not database_name:
            return {"error": "database_name is required"}
        if not repository:
            return {"error": "repository is required (format: username/repo-name)"}
        if not self.hf_token:
            return {"error": "HuggingFace token required for upload operations"}

        try:
            # Check if local database exists
            db_path = self.data_dir / "embeddings.db"
            index_path = self.data_dir / f"{database_name}.faiss"

            if not db_path.exists():
                return {"error": "Local embeddings database not found"}
            if not index_path.exists():
                return {
                    "error": f"FAISS index for database '{database_name}' not found"
                }

            # Create export directory for this upload
            export_path = (
                self.export_dir
                / f"{database_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            export_path.mkdir(parents=True, exist_ok=True)

            # Copy database files to export directory
            shutil.copy2(db_path, export_path / "embeddings.db")
            shutil.copy2(index_path, export_path / f"{database_name}.faiss")

            # Create database info file
            db_info = self._get_database_info(database_name)
            if not db_info:
                return {
                    "error": f"Database '{database_name}' not found in local storage"
                }

            info_file = {
                "database_name": database_name,
                "description": description,
                "embedding_model": db_info.get("embedding_model"),
                "embedding_dimensions": db_info.get("embedding_dimensions"),
                "document_count": db_info.get("document_count"),
                "created_at": db_info.get("created_at"),
                "uploaded_at": datetime.now().isoformat(),
                "version": "1.0.0",
                "format": "tooluniverse_embedding_db",
            }

            with open(export_path / "database_info.json", "w") as f:
                json.dump(info_file, f, indent=2)

            # Create README file
            readme_content = self._generate_readme(database_name, description, db_info)
            with open(export_path / "README.md", "w") as f:
                f.write(readme_content)

            # Create repository if it doesn't exist
            try:
                self.hf_api.repo_info(repository, repo_type="dataset")
                self.logger.info(f"Repository {repository} already exists")
            except HfHubHTTPError:
                self.logger.info(f"Creating new repository: {repository}")
                self.hf_api.create_repo(
                    repo_id=repository, repo_type="dataset", private=private
                )

            # Upload files to HuggingFace
            self.logger.info(f"Uploading database to {repository}")
            upload_folder(
                folder_path=str(export_path),
                repo_id=repository,
                repo_type="dataset",
                token=self.hf_token,
                commit_message=commit_message,
            )

            # Clean up export directory
            shutil.rmtree(export_path)

            return {
                "status": "success",
                "database_name": database_name,
                "repository": repository,
                "document_count": db_info.get("document_count"),
                "upload_url": f"{self.hf_endpoint}/datasets/{repository}",
            }

        except Exception as e:
            self.logger.error(f"Error uploading to HuggingFace: {str(e)}")
            return {"error": f"Failed to upload: {str(e)}"}

    def _download_from_huggingface(self, arguments):
        """Download database from HuggingFace Hub"""
        repository = arguments.get("repository")
        local_name = arguments.get("local_name")
        overwrite = arguments.get("overwrite", False)

        if not repository:
            return {"error": "repository is required (format: username/repo-name)"}
        if not local_name:
            local_name = repository.split("/")[-1]  # Use repo name as default

        try:
            # Check if local database already exists
            if self._local_database_exists(local_name) and not overwrite:
                return {
                    "error": f"Local database '{local_name}' already exists. Use overwrite=true to replace."
                }

            # Download repository to temporary directory
            temp_dir = (
                self.export_dir / f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            self.logger.info(f"Downloading database from {repository}")
            snapshot_download(
                repo_id=repository,
                repo_type="dataset",
                local_dir=str(temp_dir),
                token=self.hf_token,
            )

            # Verify required files exist
            db_file = temp_dir / "embeddings.db"
            info_file = temp_dir / "database_info.json"

            if not db_file.exists():
                shutil.rmtree(temp_dir)
                return {"error": "Downloaded repository does not contain embeddings.db"}

            if not info_file.exists():
                shutil.rmtree(temp_dir)
                return {
                    "error": "Downloaded repository does not contain database_info.json"
                }

            # Load database info
            with open(info_file) as f:
                db_info = json.load(f)

            original_name = db_info.get("database_name")
            faiss_file = temp_dir / f"{original_name}.faiss"

            if not faiss_file.exists():
                shutil.rmtree(temp_dir)
                return {
                    "error": f"FAISS index file {original_name}.faiss not found in download"
                }

            # Copy files to local storage with new name
            local_db_path = self.data_dir / "embeddings.db"
            local_index_path = self.data_dir / f"{local_name}.faiss"

            # Handle database file (merge or replace)
            if local_db_path.exists() and not overwrite:
                # Merge databases (simplified approach - copy tables)
                self._merge_databases(
                    str(db_file), str(local_db_path), original_name, local_name
                )
            else:
                shutil.copy2(db_file, local_db_path)
                self._rename_database_in_db(
                    str(local_db_path), original_name, local_name
                )

            # Copy FAISS index
            shutil.copy2(faiss_file, local_index_path)

            # Clean up
            shutil.rmtree(temp_dir)

            return {
                "status": "success",
                "repository": repository,
                "local_name": local_name,
                "document_count": db_info.get("document_count"),
                "embedding_model": db_info.get("embedding_model"),
                "downloaded_at": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error downloading from HuggingFace: {str(e)}")
            # Clean up on error
            if "temp_dir" in locals() and temp_dir.exists():
                shutil.rmtree(temp_dir)
            return {"error": f"Failed to download: {str(e)}"}

    def _get_database_info(self, database_name: str) -> Dict:
        """Get database information from local SQLite"""
        import sqlite3

        db_path = self.data_dir / "embeddings.db"
        if not db_path.exists():
            return {}

        try:
            with sqlite3.connect(db_path) as conn:
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
        except Exception as e:
            self.logger.error(f"Error getting database info: {str(e)}")

        return {}

    def _local_database_exists(self, database_name: str) -> bool:
        """Check if database exists locally"""
        return bool(self._get_database_info(database_name))

    def _generate_readme(
        self, database_name: str, description: str, db_info: Dict
    ) -> str:
        """Generate README content for HuggingFace repository"""
        return f"""# {database_name} - Embedding Database

## Description
{description or 'Embedding database created with ToolUniverse'}

## Database Information
- **Documents**: {db_info.get('document_count', 'Unknown')}
- **Embedding Model**: {db_info.get('embedding_model', 'Unknown')}
- **Dimensions**: {db_info.get('embedding_dimensions', 'Unknown')}
- **Created**: {db_info.get('created_at', 'Unknown')}

## Usage

To use this database in ToolUniverse:

```python
from src.tooluniverse.execute_function import ToolUniverse

# Download and load the database
tu = ToolUniverse()
sync = tu.init_tool("EmbeddingSync")

# Download from HuggingFace
sync.run({{
    "action": "download",
    "repository": "username/repo-name",
    "local_name": "{database_name}"
}})

# Search the database
db = tu.init_tool("EmbeddingDatabaseSearch")
results = db.run({{
    "database_name": "{database_name}",
    "query": "your search query",
    "top_k": 5
}})
```

## Format
This database uses the ToolUniverse embedding database format with FAISS vector index and SQLite metadata storage.
"""

    def _merge_databases(
        self, source_db: str, target_db: str, source_name: str, target_name: str
    ):
        """Merge source database into target database (simplified implementation)"""
        import sqlite3

        # This is a simplified merge - in practice, you'd want more sophisticated handling
        with sqlite3.connect(source_db) as source_conn:
            with sqlite3.connect(target_db) as target_conn:
                # Copy database record
                source_conn.execute(
                    "UPDATE databases SET name = ? WHERE name = ?",
                    (target_name, source_name),
                )

                # Copy all records (simplified)
                target_conn.execute("ATTACH DATABASE ? AS source_db", (source_db,))
                target_conn.execute(
                    """
                    INSERT OR REPLACE INTO databases
                    SELECT * FROM source_db.databases WHERE name = ?
                """,
                    (target_name,),
                )
                target_conn.execute(
                    """
                    INSERT INTO documents
                    SELECT * FROM source_db.documents WHERE database_name = ?
                """,
                    (target_name,),
                )
                target_conn.execute("DETACH DATABASE source_db")

    def _rename_database_in_db(self, db_path: str, old_name: str, new_name: str):
        """Rename database in SQLite file"""
        import sqlite3

        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "UPDATE databases SET name = ? WHERE name = ?", (new_name, old_name)
            )
            conn.execute(
                "UPDATE documents SET database_name = ? WHERE database_name = ?",
                (new_name, old_name),
            )
