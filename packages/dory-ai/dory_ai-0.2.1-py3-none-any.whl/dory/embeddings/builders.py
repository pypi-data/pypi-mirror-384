"""Builder functions for embeddings service.

This module follows the Dependency Injection pattern:
- Creates all dependencies externally
- Injects them into the components that need them
"""

from mem0 import Memory

from .adapters.mem0 import Mem0Adapter
from .config import EmbeddingsConfig
from .service import Embeddings

__all__ = [
    "build_embeddings",
]


def build_embeddings(
    api_key: str | None = None,
    store: str = "chroma",
    store_path: str | None = None,
    connection_string: str | None = None,
    collection: str = "memories",
) -> Embeddings:
    """Build embeddings service with simplified configuration."""

    config = EmbeddingsConfig(
        api_key=api_key,
        store=store,
        store_path=store_path,
        connection_string=connection_string,
        collection=collection,
    )

    mem0_config = config.to_mem0_config()
    memory = Memory.from_config(mem0_config)

    adapter = Mem0Adapter(config=config, memory=memory)

    return Embeddings(adapter=adapter)
