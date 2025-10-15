"""
Shared utilities for KnowledgeSmith MCP project.

@REQ: REQ-graphiti-chunk-mcp
@BP: BP-graphiti-chunk-mcp
@TASK: TASK-001-PathResolver
"""

from .path_resolver import resolve_path, read_document

__all__ = ["resolve_path", "read_document"]
