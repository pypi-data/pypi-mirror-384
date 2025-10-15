"""
Data models for chunking.

@REQ: REQ-graphiti-chunk-mcp
@BP: BP-graphiti-chunk-mcp
@TASK: TASK-002-RBTChunker, TASK-004-ChunkComparator
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ChunkMetadata(BaseModel):
    """
    Metadata for a document chunk.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-002-RBTChunker

    Structure (only two top-level fields):
        metadata: Dict[str, Any]  # All identification and document information
            - chunk_id: str
            - parent_document_id: str
            - project_id: str
            - feature_id: Optional[str]
            - doc_type: str
            - section_id: Optional[str]
            - section_title: Optional[str]
            - section_summary: Optional[str]
            - document_metadata: Dict[str, Any]  # Original document YAML header
            - document_info: Dict[str, Any]      # Original document info section
        content: str  # Markdown content
    """

    metadata: Dict[str, Any] = Field(
        ...,
        description="All chunk metadata including identifiers and document information"
    )
    content: str = Field(
        ...,
        description="The actual markdown content of the chunk"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "metadata": {
                    "chunk_id": "knowledge-smith+graphiti-chunk-mcp+sec-implementation",
                    "parent_document_id": "knowledge-smith+graphiti-chunk-mcp+TASK",
                    "project_id": "knowledge-smith",
                    "feature_id": "graphiti-chunk-mcp",
                    "doc_type": "TASK",
                    "section_id": "sec-implementation",
                    "section_title": "3. 實作指引與測試規格",
                    "section_summary": "Implementation guide and test specifications",
                    "document_metadata": {
                        "id": "TASK-002-RBTChunker",
                        "title": "實作 RBTChunker"
                    },
                    "document_info": {
                        "status": "In Progress",
                        "update_date": "2025-10-09"
                    }
                },
                "content": "## 3. 實作指引與測試規格\n\n實作步驟..."
            }
        }
    )


class SyncResult(BaseModel):
    """
    Result of comparing old and new chunks to identify changes.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-004-ChunkComparator

    Attributes:
        added: List of chunk_ids that are new in new_chunks
        updated: List of chunk_ids that exist in both but have different content
        deleted: List of chunk_ids that exist in old_chunks but not in new_chunks
        unchanged: Count of chunks that are identical
        total_chunks: Total number of chunks in new_chunks
    """

    added: List[str] = Field(
        default_factory=list,
        description="List of chunk_ids that are new"
    )
    updated: List[str] = Field(
        default_factory=list,
        description="List of chunk_ids that have been updated"
    )
    deleted: List[str] = Field(
        default_factory=list,
        description="List of chunk_ids that have been deleted"
    )
    unchanged: int = Field(
        0,
        description="Count of chunks that are identical"
    )
    total_chunks: int = Field(
        0,
        description="Total number of chunks in new_chunks"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "added": ["chunk-id-1", "chunk-id-2"],
                "updated": ["chunk-id-3"],
                "deleted": ["chunk-id-4"],
                "unchanged": 5,
                "total_chunks": 8
            }
        }
    )
