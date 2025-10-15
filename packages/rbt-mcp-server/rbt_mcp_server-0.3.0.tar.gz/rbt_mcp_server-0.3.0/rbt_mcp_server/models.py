"""
Data models for RBT MCP Server.

@REQ: REQ-rbt-mcp-tool
@BP: BP-rbt-mcp-tool
@TASK: TASK-001-PathResolver
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PathInfo:
    """
    Path information for a resolved document.

    Attributes:
        project_id: Project identifier (e.g., 'knowledge-smith')
        feature_id: Optional feature identifier (e.g., 'rbt-mcp-tool')
        doc_type: Optional document type ('REQ', 'BP', 'TASK')
        file_path: Complete absolute file path
        is_rbt: True if RBT standard document, False if general document
        file_exists: True if the file exists at file_path (default: True for RBT documents)

    @REQ: REQ-rbt-mcp-tool
    @BP: BP-rbt-mcp-tool
    @TASK: TASK-001-PathResolver
    """
    project_id: str
    feature_id: Optional[str]
    doc_type: Optional[str]
    file_path: str
    is_rbt: bool
    file_exists: bool = True
