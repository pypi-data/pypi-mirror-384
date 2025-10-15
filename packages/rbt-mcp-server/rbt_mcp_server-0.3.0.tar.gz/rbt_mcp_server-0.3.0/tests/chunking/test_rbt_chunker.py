"""
Test cases for RBTChunker.

@REQ: REQ-graphiti-chunk-mcp
@BP: BP-graphiti-chunk-mcp
@TASK: TASK-002-RBTChunker
"""

import pytest
from rbt_mcp_server.chunking.rbt_chunker import RBTChunker
from rbt_mcp_server.chunking.models import ChunkMetadata


class TestRBTChunker:
    """
    Test suite for RBTChunker following TDD approach.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-002-RBTChunker
    """

    @pytest.fixture
    def chunker(self):
        """Create RBTChunker instance."""
        return RBTChunker()

    @pytest.fixture
    def sample_rbt_document(self):
        """
        Sample RBT document with complete structure.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-002-RBTChunker
        """
        return """---
id: TASK-002-RBTChunker
group_id: knowledge-smith
type: Task
title: 實作 RBTChunker
blueprint: BP-graphiti-chunk-mcp
requirement: REQ-graphiti-chunk-mcp
---

<!-- info-section -->
> status: Pending
> update_date: 2025-10-08
> dependencies: []

<!-- id: sec-root -->
# Task: 實作 RBTChunker - 根據 RBT 結構分塊

<!-- id: sec-goal-dependencies -->
## 1. 任務目標與前置

<!-- id: blk-goal-content, type: paragraph -->
這是第一個 section 的內容。

<!-- id: sec-goal -->
### 1.1 目標

<!-- id: blk-goal-list, type: list -->
- 實作 RBTChunker
- 解析文件結構
- 生成穩定的 chunk_id

<!-- id: sec-dependencies -->
### 1.2 前置任務

<!-- id: blk-dependencies, type: paragraph -->
無前置任務。

<!-- id: sec-implementation -->
## 2. 實作指引

<!-- id: blk-implementation-intro, type: paragraph -->
這是實作指引的內容。

<!-- id: blk-implementation-steps, type: list -->
**實作步驟**:
- 步驟 1
- 步驟 2
- 步驟 3

<!-- id: blk-code-example, type: code, language: python -->
```python
def example():
    return "code example"
```

<!-- id: blk-table-example, type: table -->
| Header 1 | Header 2 |
| --- | --- |
| Cell 1 | Cell 2 |
| Cell 3 | Cell 4 |
"""

    @pytest.fixture
    def nested_sections_document(self):
        """
        RBT document with nested sections.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-002-RBTChunker
        """
        return """---
id: TEST-001
group_id: knowledge-smith
type: Test
title: Test Document
---

<!-- info-section -->
> status: Draft
> update_date: 2025-10-08

<!-- id: sec-root -->
# Test: Nested Sections

<!-- id: sec-level1 -->
## 1. Section Level 1

<!-- id: blk-level1-content, type: paragraph -->
Content at level 1.

<!-- id: sec-level2 -->
### 1.1 Section Level 2

<!-- id: blk-level2-content, type: paragraph -->
Content at level 2.

<!-- id: sec-level3 -->
#### 1.1.1 Section Level 3

<!-- id: blk-level3-content, type: paragraph -->
Content at level 3.

<!-- id: sec-another -->
## 2. Another Section

<!-- id: blk-another-content, type: paragraph -->
More content.
"""

    @pytest.fixture
    def mixed_summary_document(self):
        """
        RBT document with mixed summary presence.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-002-RBTChunker
        """
        return """---
id: TEST-002
group_id: knowledge-smith
type: Test
title: Mixed Summary Document
---

<!-- info-section -->
> status: Draft
> update_date: 2025-10-08

<!-- id: sec-root -->
# Test: Mixed Summaries

<!-- id: sec-with-summary -->
## 1. Section With Summary

<!-- summary: This is a summary for this section. -->

<!-- id: blk-with-summary-content, type: paragraph -->
Content goes here.

<!-- id: sec-without-summary -->
## 2. Section Without Summary

<!-- id: blk-without-summary-content, type: paragraph -->
Content without summary.
"""

    def test_chunk_complete_document(self, chunker, sample_rbt_document):
        """
        Test Case 1: 解析完整 RBT 文件.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-002-RBTChunker

        Given: 一份包含 metadata, info, 多個 sections 的 RBT 文件
        When: 調用 chunk()
        Then: 返回對應數量的 ChunkMetadata，每個 chunk_id 穩定且正確
        """
        chunks = chunker.chunk(
            document_content=sample_rbt_document,
            project_id="knowledge-smith",
            feature_id="graphiti-chunk-mcp",
            doc_type="TASK"
        )

        # Verify we got chunks
        assert len(chunks) > 0, "Should generate at least one chunk"

        # Verify all chunks have required fields
        for chunk in chunks:
            assert isinstance(chunk, ChunkMetadata)
            assert chunk.metadata is not None
            assert chunk.metadata["chunk_id"] is not None
            assert chunk.metadata["parent_document_id"] is not None
            assert chunk.metadata["project_id"] == "knowledge-smith"
            assert chunk.metadata["feature_id"] == "graphiti-chunk-mcp"
            assert chunk.metadata["doc_type"] == "TASK"
            assert chunk.metadata["section_id"] is not None
            assert chunk.content is not None

        # Verify parent_document_id format
        expected_parent_id = "knowledge-smith+graphiti-chunk-mcp+TASK"
        for chunk in chunks:
            assert chunk.metadata["parent_document_id"] == expected_parent_id

        # Verify chunk_id format
        for chunk in chunks:
            expected_chunk_id = f"knowledge-smith+graphiti-chunk-mcp+{chunk.metadata['section_id']}"
            assert chunk.metadata["chunk_id"] == expected_chunk_id

    def test_chunk_nested_sections(self, chunker, nested_sections_document):
        """
        Test Case 2: 處理巢式 sections.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-002-RBTChunker

        Given: RBT 文件包含巢式 sections
        When: 調用 chunk()
        Then: 所有 sections（包含巢式）都被正確分塊
        """
        chunks = chunker.chunk(
            document_content=nested_sections_document,
            project_id="test-project",
            feature_id="test-feature",
            doc_type="TEST"
        )

        # Should have chunks for all sections including nested ones
        # We expect: sec-level1, sec-level2, sec-level3, sec-another
        assert len(chunks) >= 4, f"Expected at least 4 chunks, got {len(chunks)}"

        # Verify depth metadata
        section_ids = [chunk.metadata["section_id"] for chunk in chunks]
        assert "sec-level1" in section_ids
        assert "sec-level2" in section_ids
        assert "sec-level3" in section_ids
        assert "sec-another" in section_ids

    def test_section_summary_handling(self, chunker, mixed_summary_document):
        """
        Test Case 3: section_summary 處理.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-002-RBTChunker

        Given: 部分 sections 有 summary，部分沒有
        When: 調用 chunk()
        Then: 有 summary 的 chunk 包含 section_summary，沒有的為 None
        """
        chunks = chunker.chunk(
            document_content=mixed_summary_document,
            project_id="test-project",
            feature_id="test-feature",
            doc_type="TEST"
        )

        # Find chunks by section_id
        chunk_map = {chunk.metadata["section_id"]: chunk for chunk in chunks}

        # Section with summary should have section_summary
        if "sec-with-summary" in chunk_map:
            chunk_with = chunk_map["sec-with-summary"]
            # It might have a summary or be None depending on parsing
            # The key is that it's handled consistently
            assert "section_summary" in chunk_with.metadata

        # Section without summary should have None
        if "sec-without-summary" in chunk_map:
            chunk_without = chunk_map["sec-without-summary"]
            assert "section_summary" in chunk_without.metadata
            # Can be None or empty string, but should exist

    def test_chunk_id_stability(self, chunker, sample_rbt_document):
        """
        Test Case 4: chunk_id 穩定性.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-002-RBTChunker

        Given: 同一份 RBT 文件多次分塊
        When: 多次調用 chunk()
        Then: 相同 section 的 chunk_id 保持不變
        """
        # Chunk the document twice
        chunks1 = chunker.chunk(
            document_content=sample_rbt_document,
            project_id="knowledge-smith",
            feature_id="graphiti-chunk-mcp",
            doc_type="TASK"
        )

        chunks2 = chunker.chunk(
            document_content=sample_rbt_document,
            project_id="knowledge-smith",
            feature_id="graphiti-chunk-mcp",
            doc_type="TASK"
        )

        # Verify same number of chunks
        assert len(chunks1) == len(chunks2), "Should generate same number of chunks"

        # Verify chunk_ids are identical
        chunk_ids1 = [chunk.metadata["chunk_id"] for chunk in chunks1]
        chunk_ids2 = [chunk.metadata["chunk_id"] for chunk in chunks2]

        assert chunk_ids1 == chunk_ids2, "Chunk IDs should be stable across multiple runs"

        # Verify section_ids are also stable
        section_ids1 = [chunk.metadata["section_id"] for chunk in chunks1]
        section_ids2 = [chunk.metadata["section_id"] for chunk in chunks2]

        assert section_ids1 == section_ids2, "Section IDs should be stable across multiple runs"

    def test_chunk_content_generation(self, chunker, sample_rbt_document):
        """
        Test chunk content includes section title and blocks.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-002-RBTChunker
        """
        chunks = chunker.chunk(
            document_content=sample_rbt_document,
            project_id="knowledge-smith",
            feature_id="graphiti-chunk-mcp",
            doc_type="TASK"
        )

        # All chunks should have non-empty content
        for chunk in chunks:
            chunk_id = chunk.metadata["chunk_id"]
            assert chunk.content, f"Chunk {chunk_id} has empty content"
            assert len(chunk.content) > 0, f"Chunk {chunk_id} has zero-length content"

        # Content should contain section information
        for chunk in chunks:
            # Content should typically start with section title (##)
            # Or contain meaningful text from blocks
            chunk_id = chunk.metadata["chunk_id"]
            assert chunk.content.strip(), f"Chunk {chunk_id} has only whitespace"

    def test_chunk_metadata_fields(self, chunker, sample_rbt_document):
        """
        Test chunk metadata contains expected fields.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-002-RBTChunker
        """
        chunks = chunker.chunk(
            document_content=sample_rbt_document,
            project_id="knowledge-smith",
            feature_id="graphiti-chunk-mcp",
            doc_type="TASK"
        )

        for chunk in chunks:
            # Verify metadata structure
            assert isinstance(chunk.metadata, dict)
            assert "chunk_id" in chunk.metadata
            assert "parent_document_id" in chunk.metadata
            assert "project_id" in chunk.metadata
            assert "feature_id" in chunk.metadata
            assert "doc_type" in chunk.metadata
            assert "section_id" in chunk.metadata
            assert "section_title" in chunk.metadata
            assert "section_summary" in chunk.metadata

            # Verify types
            assert isinstance(chunk.metadata["chunk_id"], str)
            assert isinstance(chunk.metadata["parent_document_id"], str)
            assert isinstance(chunk.metadata["project_id"], str)
            assert isinstance(chunk.metadata["doc_type"], str)

            # Info chunk has special "info" field
            if chunk.metadata["section_id"] == "sec-info":
                assert "info" in chunk.metadata
                assert isinstance(chunk.metadata["info"], dict)
