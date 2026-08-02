"""RAG pipeline package.

Houses the FAISS vector store, document parsing helpers (PDF/DOCX/TXT with
OCR fallback), the MCQ extractor, and the Groq LLM client wiring that
previously lived inside ``backend/app.py``.

Per-subject vector store isolation (design.md §5) lands in task 4.1; for
now the package exposes a single global :class:`~.store.VectorStore`
instance via :data:`smartkcet.rag.store.store` to preserve current behaviour.

NOTE: Python 3.14 compatibility
-------

Both ``pytesseract`` and ``groq`` libraries have compatibility issues with
Python 3.14:
- ``pytesseract`` depends on removed internal APIs (``pkgutil.find_loader``)
- ``groq`` library itself hangs during import on Python 3.14

Rather than making the entire RAG package unavailable, we gracefully degrade:

- ``store`` and ``mcq_extractor`` are always available (no problematic imports)
- ``groq_client`` and ``parsing`` are NOT imported here to avoid hangs
- Modules that need these should import with try/except in their own code

This allows the admin dashboard to function fully without OCR/LLM/generation features.
"""

from . import store  # noqa: F401 (always available, no pytesseract dependency)
from . import mcq_extractor  # noqa: F401 (MCQ extraction from existing questions)

# NOTE: groq_client and parsing are NOT imported here to avoid hangs on Python 3.14
# Both groq and pytesseract have compatibility issues that cause import to hang
# Modules that need these should import with try/except in their own code:
#   try:
#       from ..rag.groq_client import ...
#   except ImportError:
#       # groq unavailable

__all__ = ["store", "mcq_extractor"]
