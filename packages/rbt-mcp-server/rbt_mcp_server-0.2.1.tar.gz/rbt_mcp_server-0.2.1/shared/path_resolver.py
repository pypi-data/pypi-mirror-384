"""
Shared path resolution utilities for RBT and general Markdown documents.

This module provides simple helper functions that wrap the PathResolver class
from rbt_mcp_server, making it easy to resolve paths and read documents
without managing PathResolver instances.

@REQ: REQ-graphiti-chunk-mcp
@BP: BP-graphiti-chunk-mcp
@TASK: TASK-001-PathResolver
"""

import os
from pathlib import Path
from typing import Optional

from rbt_mcp_server.path_resolver import PathResolver as _PathResolver


# Default root directory (can be overridden)
_DEFAULT_ROOT = str(Path(__file__).parent.parent.absolute())
_resolver_cache: Optional[_PathResolver] = None


def _get_resolver(root_dir: Optional[str] = None) -> _PathResolver:
    """
    Get or create a PathResolver instance.

    Uses a cached instance when root_dir matches the default,
    creates a new instance otherwise.

    Args:
        root_dir: Root directory for documents (defaults to project root)

    Returns:
        PathResolver instance

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-001-PathResolver
    """
    global _resolver_cache

    if root_dir is None:
        root_dir = _DEFAULT_ROOT

    # Use cached resolver if root matches default
    if root_dir == _DEFAULT_ROOT and _resolver_cache is not None:
        return _resolver_cache

    # Create new resolver
    resolver = _PathResolver(root_dir)

    # Cache it if it's the default
    if root_dir == _DEFAULT_ROOT:
        _resolver_cache = resolver

    return resolver


def resolve_path(
    project_id: str,
    feature_id: Optional[str] = None,
    doc_type: Optional[str] = None,
    file_path: Optional[str] = None,
    root_dir: Optional[str] = None
) -> str:
    """
    Resolve document path and return the absolute file system path.

    This function wraps the PathResolver class from rbt_mcp_server,
    providing a simple interface for path resolution.

    Supports:
    - RBT documents: Specify project_id, feature_id, and doc_type (REQ/BP/TASK)
    - General documents: Specify project_id and file_path (relative to docs/)
    - TASK documents: Supports partial matching (e.g., "001" matches "TASK-001-*.md")
    - .new.md priority: Prefers .new.md over .md when both exist

    Args:
        project_id: Project identifier (required)
        feature_id: Feature identifier (optional, required for RBT docs)
        doc_type: Document type ('REQ', 'BP', 'TASK') for RBT docs
        file_path: For RBT TASK docs: TASK identifier (e.g., "001")
                   For general docs: Relative path from docs/ dir (e.g., "architecture/overview.md")
        root_dir: Root directory for documents (defaults to project root)

    Returns:
        Absolute file system path to the document

    Raises:
        ValueError: If invalid parameter combination
        FileNotFoundError: If resolved file doesn't exist

    Examples:
        # RBT Blueprint document
        >>> resolve_path("knowledge-smith", "graphiti-chunk-mcp", "BP")
        '/path/to/knowledge-smith/features/graphiti-chunk-mcp/BP-graphiti-chunk-mcp.md'

        # TASK document with partial matching
        >>> resolve_path("knowledge-smith", "graphiti-chunk-mcp", "TASK", "001")
        '/path/to/knowledge-smith/features/graphiti-chunk-mcp/tasks/TASK-001-PathResolver.md'

        # General document (file_path is relative to docs/ directory)
        >>> resolve_path("knowledge-smith", file_path="architecture/overview.md")
        '/path/to/knowledge-smith/docs/architecture/overview.md'

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-001-PathResolver
    """
    resolver = _get_resolver(root_dir)

    # Use PathResolver.resolve() to get PathInfo
    path_info = resolver.resolve(
        project_id=project_id,
        feature_id=feature_id,
        doc_type=doc_type,
        file_path=file_path
    )

    # Check if file exists (for backward compatibility)
    if not path_info.file_exists:
        raise FileNotFoundError(
            f"Document not found: {path_info.file_path}\n"
            f"Parameters: project_id={project_id}, feature_id={feature_id}, "
            f"doc_type={doc_type}, file_path={file_path}"
        )

    # Return the resolved file path
    return path_info.file_path


def read_document(
    project_id: str,
    feature_id: Optional[str] = None,
    doc_type: Optional[str] = None,
    file_path: Optional[str] = None,
    root_dir: Optional[str] = None
) -> str:
    """
    Resolve document path and return its content as a string.

    This function first resolves the path using resolve_path(),
    then reads and returns the file content.

    Args:
        project_id: Project identifier (required)
        feature_id: Feature identifier (optional, required for RBT docs)
        doc_type: Document type ('REQ', 'BP', 'TASK') for RBT docs
        file_path: For RBT TASK docs: TASK identifier (e.g., "001")
                   For general docs: Relative path from docs/ dir (e.g., "README.md")
        root_dir: Root directory for documents (defaults to project root)

    Returns:
        Document content as a UTF-8 string

    Raises:
        ValueError: If invalid parameter combination
        FileNotFoundError: If resolved file doesn't exist
        IOError: If file cannot be read

    Examples:
        # Read RBT Blueprint
        >>> content = read_document("knowledge-smith", "graphiti-chunk-mcp", "BP")
        >>> print(content[:50])
        '---\nid: BP-graphiti-chunk-mcp\ngroup_id: knowledg...'

        # Read TASK document
        >>> content = read_document("knowledge-smith", "graphiti-chunk-mcp", "TASK", "001")
        >>> "PathResolver" in content
        True

        # Read general document (file_path relative to docs/)
        >>> content = read_document("knowledge-smith", file_path="README.md")

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-001-PathResolver
    """
    # Resolve the path
    resolved_path = resolve_path(
        project_id=project_id,
        feature_id=feature_id,
        doc_type=doc_type,
        file_path=file_path,
        root_dir=root_dir
    )

    # Read and return content
    try:
        with open(resolved_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Document not found: {resolved_path}")
    except Exception as e:
        raise IOError(f"Failed to read document {resolved_path}: {str(e)}")


def set_default_root(root_dir: str) -> None:
    """
    Set the default root directory for path resolution.

    This is useful for testing or when working with multiple projects.

    Args:
        root_dir: New default root directory

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-001-PathResolver
    """
    global _DEFAULT_ROOT, _resolver_cache
    _DEFAULT_ROOT = root_dir
    _resolver_cache = None  # Clear cache to force recreation
