"""Package-visible server implementation entrypoints.

This module re-exports the implementation from `_server_impl` so that
consumers can `import mcp_rag.server` and get the usual symbols. The
actual implementation lives in `_server_impl.py` which is packaged with
the distribution.
"""
from ._server_impl import (
    mcp,
    initialize_rag,
    save_processed_copy,
    warm_up_rag_system,
)

__all__ = [
    'mcp', 'initialize_rag', 'save_processed_copy', 'warm_up_rag_system'
]
