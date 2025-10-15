"""
Unit tests for MarkdownChunker.

@REQ: REQ-graphiti-chunk-mcp
@BP: BP-graphiti-chunk-mcp
@TASK: TASK-003-MarkdownChunker
"""

import pytest
from rbt_mcp_server.chunking.markdown_chunker import MarkdownChunker
from rbt_mcp_server.chunking.models import ChunkMetadata


@pytest.fixture
def chunker():
    """
    Create a MarkdownChunker instance for testing.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-003-MarkdownChunker
    """
    return MarkdownChunker()


class TestMarkdownChunker:
    """
    Test suite for MarkdownChunker.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-003-MarkdownChunker
    """

    def test_chunk_with_multiple_h3_headings(self, chunker):
        """
        Test Case 1: Parse Markdown document with multiple h3 headings.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-003-MarkdownChunker

        Given: Markdown document contains 3 ### headings
        When: Call chunk()
        Then: Return 3 ChunkMetadata objects, each corresponding to one h3 section
        """
        # Arrange
        document_content = """# Main Title

Some introduction text.

### Introduction

This is the introduction section with some content.

### Implementation

This is the implementation section with code examples.

### Testing

This is the testing section with test cases.
"""
        project_id = "knowledge-smith"
        feature_id = "test-feature"
        doc_type = "Guide"
        file_path = "docs/guide.md"

        # Act
        chunks = chunker.chunk(document_content, project_id, feature_id, doc_type, file_path)

        # Assert
        assert len(chunks) == 3

        # Check first chunk
        assert chunks[0].metadata["section_title"] == "Introduction"
        assert chunks[0].metadata["section_id"] == "introduction"
        assert chunks[0].metadata["chunk_id"] == "knowledge-smith+test-feature+introduction"
        assert chunks[0].metadata["parent_document_id"] == "knowledge-smith+test-feature+Guide"
        assert "introduction section" in chunks[0].content.lower()

        # Check second chunk
        assert chunks[1].metadata["section_title"] == "Implementation"
        assert chunks[1].metadata["section_id"] == "implementation"
        assert chunks[1].metadata["chunk_id"] == "knowledge-smith+test-feature+implementation"
        assert "implementation section" in chunks[1].content.lower()

        # Check third chunk
        assert chunks[2].metadata["section_title"] == "Testing"
        assert chunks[2].metadata["section_id"] == "testing"
        assert chunks[2].metadata["chunk_id"] == "knowledge-smith+test-feature+testing"
        assert "testing section" in chunks[2].content.lower()

    def test_chunk_without_h3_headings(self, chunker):
        """
        Test Case 2: Handle Markdown document without h3 headings.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-003-MarkdownChunker

        Given: Markdown document has no h3 headings
        When: Call chunk()
        Then: Return 1 ChunkMetadata containing the entire document
        """
        # Arrange
        document_content = """# Main Title

This is a document without any h3 headings.

## Section 1

Some content here.

## Section 2

More content here.
"""
        project_id = "knowledge-smith"
        feature_id = None
        doc_type = "Guide"
        file_path = "docs/simple.md"

        # Act
        chunks = chunker.chunk(document_content, project_id, feature_id, doc_type, file_path)

        # Assert
        assert len(chunks) == 1
        assert chunks[0].metadata["chunk_id"] == "knowledge-smith+general+document"
        assert chunks[0].metadata["parent_document_id"] == "knowledge-smith+general+Guide"
        assert chunks[0].metadata["section_id"] is None
        assert chunks[0].metadata["section_title"] is None
        assert chunks[0].content == document_content

    def test_heading_slug_generation(self, chunker):
        """
        Test Case 3: Verify heading_slug generation correctness.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-003-MarkdownChunker

        Given: h3 heading contains special characters, spaces, and mixed case
        When: Generate slug
        Then: Slug is lowercase, hyphen-separated, with special characters removed
        """
        # Test various heading formats
        test_cases = [
            ("Hello World!", "hello-world"),
            ("Implementation & Testing", "implementation-testing"),
            ("1. 任務目標與前置", "1-任務目標與前置"),
            ("API Reference: v2.0", "api-reference-v20"),
            ("Multiple   Spaces", "multiple-spaces"),
            ("Trailing-Hyphen--", "trailing-hyphen"),
            ("UPPERCASE TEXT", "uppercase-text"),
            ("under_score_test", "under-score-test"),
        ]

        for heading, expected_slug in test_cases:
            # Act
            slug = chunker._generate_slug(heading)

            # Assert
            assert slug == expected_slug, f"Failed for heading: {heading}"

    def test_chunk_id_stability(self, chunker):
        """
        Test Case 4: Verify chunk_id stability across multiple runs.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-003-MarkdownChunker

        Given: Same Markdown document chunked multiple times
        When: Call chunk() multiple times
        Then: chunk_id for same heading remains unchanged
        """
        # Arrange
        document_content = """### First Section

Content for first section.

### Second Section

Content for second section.
"""
        project_id = "knowledge-smith"
        feature_id = "stable-test"
        doc_type = "Guide"
        file_path = "docs/stability.md"

        # Act - chunk the same document 3 times
        chunks_run1 = chunker.chunk(document_content, project_id, feature_id, doc_type, file_path)
        chunks_run2 = chunker.chunk(document_content, project_id, feature_id, doc_type, file_path)
        chunks_run3 = chunker.chunk(document_content, project_id, feature_id, doc_type, file_path)

        # Assert - all runs should produce identical chunk_ids
        assert len(chunks_run1) == 2
        assert len(chunks_run2) == 2
        assert len(chunks_run3) == 2

        # Check first chunk
        assert chunks_run1[0].metadata["chunk_id"] == chunks_run2[0].metadata["chunk_id"] == chunks_run3[0].metadata["chunk_id"]
        assert chunks_run1[0].metadata["chunk_id"] == "knowledge-smith+stable-test+first-section"

        # Check second chunk
        assert chunks_run1[1].metadata["chunk_id"] == chunks_run2[1].metadata["chunk_id"] == chunks_run3[1].metadata["chunk_id"]
        assert chunks_run1[1].metadata["chunk_id"] == "knowledge-smith+stable-test+second-section"

    def test_chunk_with_no_feature_id(self, chunker):
        """
        Test chunking general documents without feature_id.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-003-MarkdownChunker

        Given: Document has no feature_id (general document)
        When: Call chunk()
        Then: chunk_id and parent_document_id use "general" as feature part
        """
        # Arrange
        document_content = """### Overview

This is a general document.
"""
        project_id = "knowledge-smith"
        feature_id = None
        doc_type = "Architecture"
        file_path = "docs/architecture/overview.md"

        # Act
        chunks = chunker.chunk(document_content, project_id, feature_id, doc_type, file_path)

        # Assert
        assert len(chunks) == 1
        assert chunks[0].metadata["chunk_id"] == "knowledge-smith+general+overview"
        assert chunks[0].metadata["parent_document_id"] == "knowledge-smith+general+Architecture"
        assert chunks[0].metadata["feature_id"] is None

    def test_chunk_preserves_content_boundaries(self, chunker):
        """
        Test that content boundaries are preserved correctly.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-003-MarkdownChunker

        Given: Document with multiple h3 sections with distinct content
        When: Call chunk()
        Then: Each chunk contains only its section's content
        """
        # Arrange
        document_content = """### Section A

Content for A.
More A content.

### Section B

Content for B.
More B content.

### Section C

Content for C.
"""
        project_id = "test-project"
        feature_id = "test-feature"
        doc_type = "Doc"
        file_path = "test.md"

        # Act
        chunks = chunker.chunk(document_content, project_id, feature_id, doc_type, file_path)

        # Assert
        assert len(chunks) == 3

        # Section A should not contain Section B or C content
        assert "Content for A" in chunks[0].content
        assert "More A content" in chunks[0].content
        assert "Content for B" not in chunks[0].content
        assert "Content for C" not in chunks[0].content

        # Section B should not contain Section A or C content
        assert "Content for B" in chunks[1].content
        assert "More B content" in chunks[1].content
        assert "Content for A" not in chunks[1].content
        assert "Content for C" not in chunks[1].content

        # Section C should not contain Section A or B content
        assert "Content for C" in chunks[2].content
        assert "Content for A" not in chunks[2].content
        assert "Content for B" not in chunks[2].content

    def test_empty_document(self, chunker):
        """
        Test handling of empty document.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-003-MarkdownChunker

        Given: Document is empty or only whitespace
        When: Call chunk()
        Then: Return 1 chunk with empty or whitespace content
        """
        # Arrange
        document_content = ""
        project_id = "test-project"
        feature_id = "test-feature"
        doc_type = "Doc"
        file_path = "empty.md"

        # Act
        chunks = chunker.chunk(document_content, project_id, feature_id, doc_type, file_path)

        # Assert
        assert len(chunks) == 1
        assert chunks[0].content == ""
