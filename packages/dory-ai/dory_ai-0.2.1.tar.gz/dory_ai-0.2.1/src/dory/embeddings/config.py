"""Configuration for embeddings service."""

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

__all__ = ["EmbeddingsConfig"]


class EmbeddingsConfig(BaseModel):
    """Configuration for embeddings service."""

    api_key: str | None = Field(
        default=None,
        description="OpenAI API key (used for both LLM and embeddings)",
    )

    store: str = Field(
        default="memory",
        description="Store type: 'memory', 'chroma', or 'mongodb'",
    )

    store_path: str | None = Field(
        default=None,
        description="Path for Chroma storage (when using Chroma)",
    )

    connection_string: str | None = Field(
        default=None,
        description="MongoDB connection string (when using MongoDB)",
    )

    database_name: str = Field(
        default="dory",
        description="Database name for MongoDB",
    )

    collection: str = Field(
        default="memories",
        description="Collection name for vectors",
    )

    model: str = Field(
        default="gpt-4o-mini",
        description="LLM model to use",
    )

    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model to use",
    )

    @field_validator("store")
    @classmethod
    def validate_store(cls, valid_store: str) -> str:
        """Validate store type."""
        valid_stores = {"memory", "chroma", "mongodb"}
        if valid_store not in valid_stores:
            raise ValueError(f"Store must be one of {valid_stores}, got: {valid_store}")
        return valid_store

    @model_validator(mode="after")
    def validate_mongodb_config(self) -> "EmbeddingsConfig":
        """Validate MongoDB configuration."""
        if self.store == "mongodb" and not self.connection_string:
            raise ValueError("MongoDB store requires connection_string")
        return self

    def to_mem0_config(self) -> dict[str, Any]:
        """Convert to mem0's expected configuration format."""
        config: dict[str, Any] = {}

        if self.api_key:
            config["llm"] = {
                "provider": "openai",
                "config": {
                    "api_key": self.api_key,
                    "model": self.model,
                },
            }
            config["embedder"] = {
                "provider": "openai",
                "config": {
                    "api_key": self.api_key,
                    "model": self.embedding_model,
                },
            }

        # Configure vector store
        if self.store == "memory":
            # In-memory store
            config["vector_store"] = {
                "provider": "chroma",
                "config": {
                    "collection_name": self.collection,
                    "path": ":memory:",  # Special Chroma in-memory mode
                },
            }

            if not self.api_key:
                config["embedder"] = {
                    "provider": "huggingface",
                    "config": {
                        "model": "sentence-transformers/all-MiniLM-L6-v2",
                    },
                }
                config["llm"] = {
                    "provider": "openai",
                    "config": {
                        "api_key": "dummy-key-for-testing",
                        "model": "gpt-4o-mini",
                    },
                }
        elif self.store == "chroma":
            config["vector_store"] = {
                "provider": "chroma",
                "config": {
                    "collection_name": self.collection,
                    "path": self.store_path or "./chroma_db",
                },
            }
        elif self.store == "mongodb":
            if not self.connection_string:
                raise ValueError("MongoDB requires connection_string")
            config["vector_store"] = {
                "provider": "mongodb_atlas",
                "config": {
                    "connection_string": self.connection_string,
                    "database_name": self.database_name,
                    "collection_name": self.collection,
                    "index_name": f"{self.collection}_index",
                },
            }

        return config

    def create_embeddings_config(self) -> dict[str, Any]:
        """Create a separate config for embeddings collection."""
        config = self.to_mem0_config()

        if "vector_store" in config and "config" in config["vector_store"]:
            config["vector_store"]["config"]["collection_name"] = (
                f"{self.collection}_embeddings"
            )

            if "index_name" in config["vector_store"]["config"]:
                config["vector_store"]["config"]["index_name"] = (
                    f"{self.collection}_embeddings_index"
                )

        return config
