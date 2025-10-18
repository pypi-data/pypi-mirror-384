__all__ = [
	"__version__",
	"JSONEmbeddingModel",
	"embed_documents",
	"search_documents",
]

try:
	from ._version import version as __version__
except Exception:
	__version__ = "0.0.0"

# High-level API
from .api import JSONEmbeddingModel, embed_documents, search_documents
