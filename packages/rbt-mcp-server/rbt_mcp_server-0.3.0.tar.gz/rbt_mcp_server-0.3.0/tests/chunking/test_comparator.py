"""
Unit tests for ChunkComparator.

@REQ: REQ-graphiti-chunk-mcp
@BP: BP-graphiti-chunk-mcp
@TASK: TASK-004-ChunkComparator
"""

import pytest
from rbt_mcp_server.chunking.comparator import ChunkComparator
from rbt_mcp_server.chunking.models import ChunkMetadata, SyncResult


class TestChunkComparator:
    """
    Test suite for ChunkComparator.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-004-ChunkComparator
    """

    @pytest.fixture
    def comparator(self) -> ChunkComparator:
        """Fixture to create a ChunkComparator instance."""
        return ChunkComparator()

    @pytest.fixture
    def sample_chunk_1(self) -> ChunkMetadata:
        """Create a sample chunk for testing."""
        return ChunkMetadata(
            metadata={
                "chunk_id": "chunk-1",
                "parent_document_id": "doc-1",
                "project_id": "test-project",
                "feature_id": "test-feature",
                "doc_type": "TASK",
                "section_id": "sec-1",
                "section_title": None,
                "section_summary": None,
                "document_metadata": {},
                "document_info": {}
            },
            content="Content 1"
        )

    @pytest.fixture
    def sample_chunk_2(self) -> ChunkMetadata:
        """Create another sample chunk for testing."""
        return ChunkMetadata(
            metadata={
                "chunk_id": "chunk-2",
                "parent_document_id": "doc-1",
                "project_id": "test-project",
                "feature_id": "test-feature",
                "doc_type": "TASK",
                "section_id": "sec-2",
                "section_title": None,
                "section_summary": None,
                "document_metadata": {},
                "document_info": {}
            },
            content="Content 2"
        )

    @pytest.fixture
    def sample_chunk_3(self) -> ChunkMetadata:
        """Create a third sample chunk for testing."""
        return ChunkMetadata(
            metadata={
                "chunk_id": "chunk-3",
                "parent_document_id": "doc-1",
                "project_id": "test-project",
                "feature_id": "test-feature",
                "doc_type": "TASK",
                "section_id": "sec-3",
                "section_title": None,
                "section_summary": None,
                "document_metadata": {},
                "document_info": {}
            },
            content="Content 3"
        )

    def test_identify_added_chunks(
        self,
        comparator: ChunkComparator,
        sample_chunk_1: ChunkMetadata,
        sample_chunk_2: ChunkMetadata,
        sample_chunk_3: ChunkMetadata
    ):
        """
        Test Case 1: 識別新增 chunks

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-004-ChunkComparator

        Given: new_chunks 有 3 個，old_chunks 有 1 個
        When: 調用 compare()
        Then: SyncResult.added 包含 2 個新 chunk_id
        """
        # Given
        old_chunks = [sample_chunk_1]
        new_chunks = [sample_chunk_1, sample_chunk_2, sample_chunk_3]

        # When
        result = comparator.compare(old_chunks, new_chunks)

        # Then
        assert len(result.added) == 2
        assert "chunk-2" in result.added
        assert "chunk-3" in result.added
        assert result.total_chunks == 3

    def test_identify_deleted_chunks(
        self,
        comparator: ChunkComparator,
        sample_chunk_1: ChunkMetadata,
        sample_chunk_2: ChunkMetadata,
        sample_chunk_3: ChunkMetadata
    ):
        """
        Test Case 2: 識別刪除 chunks

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-004-ChunkComparator

        Given: old_chunks 有 3 個，new_chunks 有 1 個
        When: 調用 compare()
        Then: SyncResult.deleted 包含 2 個舊 chunk_id
        """
        # Given
        old_chunks = [sample_chunk_1, sample_chunk_2, sample_chunk_3]
        new_chunks = [sample_chunk_1]

        # When
        result = comparator.compare(old_chunks, new_chunks)

        # Then
        assert len(result.deleted) == 2
        assert "chunk-2" in result.deleted
        assert "chunk-3" in result.deleted
        assert result.total_chunks == 1

    def test_identify_updated_chunks(
        self,
        comparator: ChunkComparator,
        sample_chunk_1: ChunkMetadata
    ):
        """
        Test Case 3: 識別更新 chunks

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-004-ChunkComparator

        Given: chunk_id 相同但 content 不同
        When: 調用 compare()
        Then: SyncResult.updated 包含該 chunk_id
        """
        # Given
        old_chunk = sample_chunk_1
        new_chunk = ChunkMetadata(
            metadata={
                "chunk_id": "chunk-1",
                "parent_document_id": "doc-1",
                "project_id": "test-project",
                "feature_id": "test-feature",
                "doc_type": "TASK",
                "section_id": "sec-1",
                "section_title": None,
                "section_summary": None,
                "document_metadata": {},
                "document_info": {}
            },
            content="Content 1 - UPDATED"  # Different content
        )
        old_chunks = [old_chunk]
        new_chunks = [new_chunk]

        # When
        result = comparator.compare(old_chunks, new_chunks)

        # Then
        assert len(result.updated) == 1
        assert "chunk-1" in result.updated
        assert result.total_chunks == 1

    def test_identify_unchanged_chunks(
        self,
        comparator: ChunkComparator,
        sample_chunk_1: ChunkMetadata,
        sample_chunk_2: ChunkMetadata
    ):
        """
        Test Case 4: 識別未變更 chunks

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-004-ChunkComparator

        Given: chunk_id 和 content 完全相同
        When: 調用 compare()
        Then: SyncResult.unchanged 正確統計數量
        """
        # Given
        old_chunks = [sample_chunk_1, sample_chunk_2]
        new_chunks = [sample_chunk_1, sample_chunk_2]

        # When
        result = comparator.compare(old_chunks, new_chunks)

        # Then
        assert result.unchanged == 2
        assert len(result.added) == 0
        assert len(result.updated) == 0
        assert len(result.deleted) == 0
        assert result.total_chunks == 2

    def test_mixed_changes(
        self,
        comparator: ChunkComparator,
        sample_chunk_1: ChunkMetadata,
        sample_chunk_2: ChunkMetadata,
        sample_chunk_3: ChunkMetadata
    ):
        """
        Test comprehensive scenario with mixed changes.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-004-ChunkComparator

        Given: Mix of added, deleted, updated, and unchanged chunks
        When: 調用 compare()
        Then: All categories are correctly identified
        """
        # Given
        # Old: chunk-1 (will be unchanged), chunk-2 (will be updated), chunk-4 (will be deleted)
        old_chunk_2 = ChunkMetadata(
            metadata={
                "chunk_id": "chunk-2",
                "parent_document_id": "doc-1",
                "project_id": "test-project",
                "feature_id": "test-feature",
                "doc_type": "TASK",
                "section_id": "sec-2",
                "section_title": None,
                "section_summary": None,
                "document_metadata": {},
                "document_info": {}
            },
            content="Old Content 2"
        )
        old_chunk_4 = ChunkMetadata(
            metadata={
                "chunk_id": "chunk-4",
                "parent_document_id": "doc-1",
                "project_id": "test-project",
                "feature_id": "test-feature",
                "doc_type": "TASK",
                "section_id": "sec-4",
                "section_title": None,
                "section_summary": None,
                "document_metadata": {},
                "document_info": {}
            },
            content="Content 4"
        )
        old_chunks = [sample_chunk_1, old_chunk_2, old_chunk_4]

        # New: chunk-1 (unchanged), chunk-2 (updated), chunk-3 (added)
        new_chunk_2 = ChunkMetadata(
            metadata={
                "chunk_id": "chunk-2",
                "parent_document_id": "doc-1",
                "project_id": "test-project",
                "feature_id": "test-feature",
                "doc_type": "TASK",
                "section_id": "sec-2",
                "section_title": None,
                "section_summary": None,
                "document_metadata": {},
                "document_info": {}
            },
            content="Updated Content 2"
        )
        new_chunks = [sample_chunk_1, new_chunk_2, sample_chunk_3]

        # When
        result = comparator.compare(old_chunks, new_chunks)

        # Then
        assert len(result.added) == 1
        assert "chunk-3" in result.added
        assert len(result.updated) == 1
        assert "chunk-2" in result.updated
        assert len(result.deleted) == 1
        assert "chunk-4" in result.deleted
        assert result.unchanged == 1  # chunk-1
        assert result.total_chunks == 3

    def test_empty_old_chunks(
        self,
        comparator: ChunkComparator,
        sample_chunk_1: ChunkMetadata
    ):
        """
        Test with empty old_chunks.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-004-ChunkComparator
        """
        # Given
        old_chunks = []
        new_chunks = [sample_chunk_1]

        # When
        result = comparator.compare(old_chunks, new_chunks)

        # Then
        assert len(result.added) == 1
        assert "chunk-1" in result.added
        assert len(result.deleted) == 0
        assert result.unchanged == 0
        assert result.total_chunks == 1

    def test_empty_new_chunks(
        self,
        comparator: ChunkComparator,
        sample_chunk_1: ChunkMetadata
    ):
        """
        Test with empty new_chunks.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-004-ChunkComparator
        """
        # Given
        old_chunks = [sample_chunk_1]
        new_chunks = []

        # When
        result = comparator.compare(old_chunks, new_chunks)

        # Then
        assert len(result.added) == 0
        assert len(result.deleted) == 1
        assert "chunk-1" in result.deleted
        assert result.unchanged == 0
        assert result.total_chunks == 0

    def test_both_empty(self, comparator: ChunkComparator):
        """
        Test with both old_chunks and new_chunks empty.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-004-ChunkComparator
        """
        # Given
        old_chunks = []
        new_chunks = []

        # When
        result = comparator.compare(old_chunks, new_chunks)

        # Then
        assert len(result.added) == 0
        assert len(result.updated) == 0
        assert len(result.deleted) == 0
        assert result.unchanged == 0
        assert result.total_chunks == 0
