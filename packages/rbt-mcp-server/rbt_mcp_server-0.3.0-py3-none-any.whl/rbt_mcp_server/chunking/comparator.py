"""
Chunk comparison utilities for identifying changes between old and new chunks.

@REQ: REQ-graphiti-chunk-mcp
@BP: BP-graphiti-chunk-mcp
@TASK: TASK-004-ChunkComparator
"""

from typing import Dict, List

from .models import ChunkMetadata, SyncResult


class ChunkComparator:
    """
    Compares old and new chunks to identify additions, updates, deletions, and unchanged chunks.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-004-ChunkComparator
    """

    def compare(
        self,
        old_chunks: List[ChunkMetadata],
        new_chunks: List[ChunkMetadata]
    ) -> SyncResult:
        """
        Compare old and new chunks to identify changes.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-004-ChunkComparator

        Args:
            old_chunks: List of chunks from the previous state
            new_chunks: List of chunks from the current state

        Returns:
            SyncResult containing:
                - added: chunk_ids present in new_chunks but not in old_chunks
                - updated: chunk_ids present in both but with different content
                - deleted: chunk_ids present in old_chunks but not in new_chunks
                - unchanged: count of chunks with identical content
                - total_chunks: total number of chunks in new_chunks

        Example:
            >>> comparator = ChunkComparator()
            >>> old = [ChunkMetadata(chunk_id="c1", content="old", ...)]
            >>> new = [ChunkMetadata(chunk_id="c1", content="new", ...)]
            >>> result = comparator.compare(old, new)
            >>> result.updated
            ['c1']
        """
        # Build mappings for efficient lookup
        old_map: Dict[str, ChunkMetadata] = {
            chunk.metadata["chunk_id"]: chunk for chunk in old_chunks
        }
        new_map: Dict[str, ChunkMetadata] = {
            chunk.metadata["chunk_id"]: chunk for chunk in new_chunks
        }

        # Get all chunk IDs
        old_ids = set(old_map.keys())
        new_ids = set(new_map.keys())

        # Identify additions: in new but not in old
        added = list(new_ids - old_ids)

        # Identify deletions: in old but not in new
        deleted = list(old_ids - new_ids)

        # Identify updates and unchanged: in both
        common_ids = old_ids & new_ids
        updated: List[str] = []
        unchanged_count = 0

        for chunk_id in common_ids:
            old_chunk = old_map[chunk_id]
            new_chunk = new_map[chunk_id]

            # Compare content to determine if updated
            if old_chunk.content != new_chunk.content:
                updated.append(chunk_id)
            else:
                unchanged_count += 1

        return SyncResult(
            added=added,
            updated=updated,
            deleted=deleted,
            unchanged=unchanged_count,
            total_chunks=len(new_chunks)
        )
