"""
Unit tests for add_document functionality.

@REQ: REQ-graphiti-chunk-mcp
@BP: BP-graphiti-chunk-mcp
@TASK: TASK-006-AddDocument
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

from rbt_mcp_server.chunking import (
    add_document,
    ChunkMetadata,
    SyncResult,
    GraphitiClient
)


@pytest.fixture
def mock_graphiti_client():
    """Create a mock GraphitiClient for testing."""
    client = AsyncMock(spec=GraphitiClient)
    client.add_episode = AsyncMock(return_value={"uuid": "test-uuid", "entities_created": 1, "edges_created": 1})
    client.delete_episode = AsyncMock(return_value=True)
    client.search_nodes = AsyncMock(return_value=[])
    client.get_episodes = AsyncMock(return_value=[])
    return client


@pytest.fixture
def sample_rbt_document():
    """Sample RBT document content."""
    return """---
id: TASK-001-TestTask
group_id: knowledge-smith
type: Task
title: Test Task
blueprint: BP-test-feature
requirement: REQ-test-feature
---

<!-- info-section -->
> status: Pending
> update_date: 2025-10-08

<!-- id: sec-root -->
# Task: Test Task

<!-- id: sec-goal-dependencies -->
## 1. 任務目標與前置

<!-- id: blk-goal, type: list -->
**目標 (Goal)**

- Implement test functionality
- Verify integration

<!-- id: sec-implementation -->
## 2. 實作指引

<!-- id: blk-steps, type: list -->
**實作步驟**

1. Step 1: Do something
2. Step 2: Do something else
"""


@pytest.fixture
def sample_markdown_document():
    """Sample general Markdown document content."""
    return """# General Document

## Introduction

This is an introduction section.

### First Topic

Content about the first topic.

### Second Topic

Content about the second topic.
"""


@pytest.mark.asyncio
async def test_add_document_rbt_new_document(mock_graphiti_client, sample_rbt_document, tmp_path):
    """
    Test Case 1: 完整流程 - 新增 RBT 文件

    Given: 空的 ROOT 原始檔案，新檔案有內容
    When: 調用 add_document()
    Then: 所有 chunks 被新增

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-006-AddDocument
    """
    # Setup ROOT directory with empty original file
    root_dir = tmp_path / "root"
    project_dir = root_dir / "knowledge-smith"
    feature_dir = project_dir / "features" / "test-feature"
    tasks_dir = feature_dir / "tasks"
    tasks_dir.mkdir(parents=True)
    original_file = tasks_dir / "TASK-001-TestTask.md"

    # Empty original file (or minimal placeholder)
    original_file.write_text("""---
id: TASK-001-TestTask
group_id: knowledge-smith
type: Task
title: Test Task
---

<!-- id: sec-root -->
# Task: Test Task
""")

    # Setup new file (modified version)
    new_file = tmp_path / "new" / "TASK-001-TestTask.md"
    new_file.parent.mkdir(parents=True)
    new_file.write_text(sample_rbt_document)

    # Execute: Add the document
    result = await add_document(
        new_file_path=str(new_file),
        project_id="knowledge-smith",
        feature_id="test-feature",
        doc_type="TASK",
        file_path="001",
        root_dir=str(root_dir),
        graphiti_client=mock_graphiti_client,
        sync_mode=True  # Use sync mode for testing
    )

    # Assert: Should have added chunks (sections from new file that don't exist in original)
    assert isinstance(result, SyncResult)
    assert len(result.added) > 0, "Should have added chunks"
    assert result.total_chunks > 0, "Should have total chunks"

    # Verify add_episode was called for each added chunk
    assert mock_graphiti_client.add_episode.call_count == len(result.added)


@pytest.mark.asyncio
async def test_add_document_rbt_update_section(mock_graphiti_client, sample_rbt_document, tmp_path):
    """
    Test Case 2: 完整流程 - 更新文件

    Given: ROOT 原始檔案有舊內容，新檔案修改了某個 section
    When: 調用 add_document()
    Then: 只有變更的 section 被標記為 updated

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-006-AddDocument
    """
    # Setup ROOT directory with original file (old content)
    root_dir = tmp_path / "root"
    project_dir = root_dir / "knowledge-smith"
    feature_dir = project_dir / "features" / "test-feature"
    tasks_dir = feature_dir / "tasks"
    tasks_dir.mkdir(parents=True)
    original_file = tasks_dir / "TASK-001-TestTask.md"

    # Original file with OLD content in one section
    original_file.write_text("""---
id: TASK-001-TestTask
group_id: knowledge-smith
type: Task
title: Test Task
---

<!-- id: sec-root -->
# Task: Test Task

<!-- id: sec-goal-dependencies -->
## 1. 任務目標與前置

<!-- id: blk-goal, type: list -->
**目標 (Goal)**

- OLD CONTENT HERE

<!-- id: sec-implementation -->
## 2. 實作指引

<!-- id: blk-steps, type: list -->
**實作步驟**

1. Step 1: Do something
2. Step 2: Do something else
""")

    # Setup new file with UPDATED content
    new_file = tmp_path / "new" / "TASK-001-TestTask.md"
    new_file.parent.mkdir(parents=True)
    new_file.write_text(sample_rbt_document)

    # Mock: get_episodes needs to return episodes for update/delete to work
    mock_graphiti_client.get_episodes.return_value = [
        {
            'uuid': 'episode-uuid-1',
            'name': 'knowledge-smith+test-feature+sec-goal-dependencies',
            'content': 'OLD CONTENT',
            'group_id': 'knowledge-smith'
        }
    ]

    # Execute: Add the document
    result = await add_document(
        new_file_path=str(new_file),
        project_id="knowledge-smith",
        feature_id="test-feature",
        doc_type="TASK",
        file_path="001",
        root_dir=str(root_dir),
        graphiti_client=mock_graphiti_client,
        sync_mode=True  # Use sync mode for testing
    )

    # Assert: Should have updates
    assert isinstance(result, SyncResult)
    assert len(result.updated) > 0, "Should have updated chunks"

    # Verify delete and add were called for updated chunks (delete old + add new)
    assert mock_graphiti_client.delete_episode.call_count >= len(result.updated)


@pytest.mark.asyncio
async def test_add_document_rbt_delete_section(mock_graphiti_client, tmp_path):
    """
    Test Case 3: 完整流程 - 刪除 section

    Given: ROOT 原始檔案有多個 sections，新檔案刪除了一個 section
    When: 調用 add_document()
    Then: 對應的 chunk 被標記為 deleted

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-006-AddDocument
    """
    # Setup ROOT directory with original file (multiple sections)
    root_dir = tmp_path / "root"
    project_dir = root_dir / "knowledge-smith"
    feature_dir = project_dir / "features" / "test-feature"
    tasks_dir = feature_dir / "tasks"
    tasks_dir.mkdir(parents=True)
    original_file = tasks_dir / "TASK-001-TestTask.md"

    # Original file with TWO sections
    original_file.write_text("""---
id: TASK-001-TestTask
group_id: knowledge-smith
type: Task
title: Test Task
---

<!-- id: sec-root -->
# Task: Test Task

<!-- id: sec-goal-dependencies -->
## 1. 任務目標與前置

<!-- id: blk-goal, type: paragraph -->
Section one content.

<!-- id: sec-implementation -->
## 2. 實作指引

<!-- id: blk-steps, type: paragraph -->
This section will be deleted.
""")

    # Setup new file with ONE section (deleted sec-implementation)
    minimal_doc = """---
id: TASK-001-TestTask
group_id: knowledge-smith
type: Task
title: Test Task
---

<!-- id: sec-root -->
# Task: Test Task

<!-- id: sec-goal-dependencies -->
## 1. 任務目標與前置

<!-- id: blk-goal, type: paragraph -->
Section one content.
"""
    new_file = tmp_path / "new" / "TASK-001-TestTask.md"
    new_file.parent.mkdir(parents=True)
    new_file.write_text(minimal_doc)

    # Mock: get_episodes needs to return episode for sec-implementation to be deleted
    mock_graphiti_client.get_episodes.return_value = [
        {
            'uuid': 'episode-uuid-implementation',
            'name': 'knowledge-smith+test-feature+sec-implementation',
            'content': 'This section will be deleted.',
            'group_id': 'knowledge-smith'
        }
    ]

    # Execute: Add the document (with deleted section)
    result = await add_document(
        new_file_path=str(new_file),
        project_id="knowledge-smith",
        feature_id="test-feature",
        doc_type="TASK",
        file_path="001",
        root_dir=str(root_dir),
        graphiti_client=mock_graphiti_client,
        sync_mode=True  # Use sync mode for testing
    )

    # Assert: Should have deletions
    assert isinstance(result, SyncResult)
    assert len(result.deleted) > 0, "Should have deleted chunks"

    # Verify delete was called for deleted chunks
    assert mock_graphiti_client.delete_episode.called


@pytest.mark.asyncio
async def test_add_document_general_markdown(mock_graphiti_client, sample_markdown_document, tmp_path):
    """
    Test Case 4: 完整流程 - 一般 MD 文件

    Given: ROOT 原始 MD 文件為空，新檔案有內容
    When: 調用 add_document()
    Then: 按 h3 標題分塊並新增所有 chunks

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-006-AddDocument
    """
    # Setup ROOT directory with empty original file
    root_dir = tmp_path / "root"
    docs_dir = root_dir / "knowledge-smith" / "docs"
    docs_dir.mkdir(parents=True)
    original_file = docs_dir / "guide.md"
    original_file.write_text("# Empty Guide\n")  # Minimal content

    # Setup new file with content
    new_file = tmp_path / "new" / "guide.md"
    new_file.parent.mkdir(parents=True)
    new_file.write_text(sample_markdown_document)

    # Execute: Add the document
    result = await add_document(
        new_file_path=str(new_file),
        project_id="knowledge-smith",
        feature_id=None,
        doc_type=None,  # None for general documents (will default to "General")
        file_path="guide.md",
        root_dir=str(root_dir),
        graphiti_client=mock_graphiti_client,
        sync_mode=True  # Use sync mode for testing
    )

    # Assert: Should chunk by h3 headings and add them
    assert isinstance(result, SyncResult)
    assert len(result.added) == 2, "Should have 2 added chunks (2 h3 headings)"
    assert result.total_chunks == 2


@pytest.mark.asyncio
async def test_add_document_file_not_found(mock_graphiti_client, tmp_path):
    """
    Test: File not found error handling (new file doesn't exist).

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-006-AddDocument
    """
    # Execute: Try to add with non-existent new file
    with pytest.raises(FileNotFoundError):
        await add_document(
            new_file_path="/non/existent/file.md",
            project_id="knowledge-smith",
            feature_id="test-feature",
            doc_type="TASK",
            file_path="001",
            root_dir=str(tmp_path),
            graphiti_client=mock_graphiti_client,
            sync_mode=True  # Use sync mode for testing
        )


@pytest.mark.asyncio
async def test_add_document_invalid_params(mock_graphiti_client, tmp_path):
    """
    Test: Invalid parameter handling (ROOT file not found).

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-006-AddDocument
    """
    # Setup new file
    new_file = tmp_path / "new.md"
    new_file.write_text("# Test")

    # Execute: Try with parameters that can't resolve ROOT file
    with pytest.raises((ValueError, FileNotFoundError)):
        await add_document(
            new_file_path=str(new_file),
            project_id="knowledge-smith",
            feature_id=None,
            doc_type=None,  # Missing both doc_type and file_path
            file_path=None,
            root_dir=str(tmp_path),
            graphiti_client=mock_graphiti_client,
            sync_mode=True  # Use sync mode for testing
        )


@pytest.mark.asyncio
async def test_add_document_unchanged_chunks(mock_graphiti_client, sample_rbt_document, tmp_path):
    """
    Test: Document with no changes should result in all unchanged chunks.

    Given: ROOT 原始檔案和新檔案內容完全相同
    When: 調用 add_document()
    Then: 所有 chunks 標記為 unchanged

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-006-AddDocument
    """
    # Setup ROOT directory with original file (same content)
    root_dir = tmp_path / "root"
    project_dir = root_dir / "knowledge-smith"
    feature_dir = project_dir / "features" / "test-feature"
    tasks_dir = feature_dir / "tasks"
    tasks_dir.mkdir(parents=True)
    original_file = tasks_dir / "TASK-001-TestTask.md"
    original_file.write_text(sample_rbt_document)

    # Setup new file with SAME content
    new_file = tmp_path / "new" / "TASK-001-TestTask.md"
    new_file.parent.mkdir(parents=True)
    new_file.write_text(sample_rbt_document)  # Identical content

    # Execute: Add the document (no changes)
    result = await add_document(
        new_file_path=str(new_file),
        project_id="knowledge-smith",
        feature_id="test-feature",
        doc_type="TASK",
        file_path="001",
        root_dir=str(root_dir),
        graphiti_client=mock_graphiti_client,
        sync_mode=True  # Use sync mode for testing
    )

    # Assert: All chunks should be unchanged
    assert isinstance(result, SyncResult)
    assert len(result.added) == 0, "Should have no added chunks"
    assert len(result.updated) == 0, "Should have no updated chunks"
    assert len(result.deleted) == 0, "Should have no deleted chunks"
    assert result.unchanged > 0, "Should have unchanged chunks"

    # Verify no modifications were made to Graphiti
    assert mock_graphiti_client.add_episode.call_count == 0
    assert mock_graphiti_client.delete_episode.call_count == 0


@pytest.mark.asyncio
async def test_add_document_root_not_exists_new_file(mock_graphiti_client, sample_markdown_document, tmp_path):
    """
    Test: ROOT file does not exist (new file scenario).

    Given: New file exists, but ROOT does not have corresponding file
    When: Call add_document()
    Then: All chunks are marked as added (no old chunks to compare)

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-006-AddDocument
    """
    # Setup ROOT directory (but don't create the target file)
    root_dir = tmp_path / "root"
    docs_dir = root_dir / "General" / "docs" / "todos"
    docs_dir.mkdir(parents=True)
    # Note: We intentionally do NOT create the file at ROOT

    # Setup new file with content
    new_file = tmp_path / "new" / "TODO-001.md"
    new_file.parent.mkdir(parents=True)
    new_file.write_text(sample_markdown_document)

    # Execute: Add document (ROOT doesn't exist)
    result = await add_document(
        new_file_path=str(new_file),
        project_id="General",
        feature_id=None,
        doc_type=None,
        file_path="todos/TODO-001.md",
        root_dir=str(root_dir),
        graphiti_client=mock_graphiti_client,
        sync_mode=True  # Use sync mode for testing
    )

    # Assert: All chunks should be added (no old chunks)
    assert isinstance(result, SyncResult)
    assert len(result.added) == 2, "Should have 2 added chunks (new file)"
    assert len(result.updated) == 0, "Should have no updated chunks"
    assert len(result.deleted) == 0, "Should have no deleted chunks"
    assert result.unchanged == 0, "Should have no unchanged chunks"


@pytest.mark.asyncio
async def test_add_document_file_path_with_docs_prefix(mock_graphiti_client, sample_markdown_document, tmp_path):
    """
    Test: file_path with "docs/" prefix should work.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-006-AddDocument
    """
    # Setup ROOT with file
    root_dir = tmp_path / "root"
    docs_dir = root_dir / "General" / "docs" / "todos"
    docs_dir.mkdir(parents=True)
    original_file = docs_dir / "TODO-001.md"
    original_file.write_text("# Empty")

    # Setup new file
    new_file = tmp_path / "new" / "TODO-001.md"
    new_file.parent.mkdir(parents=True)
    new_file.write_text(sample_markdown_document)

    # Execute: Use file_path WITH "docs/" prefix
    result = await add_document(
        new_file_path=str(new_file),
        project_id="General",
        feature_id=None,
        doc_type=None,
        file_path="docs/todos/TODO-001.md",  # WITH docs/
        root_dir=str(root_dir),
        graphiti_client=mock_graphiti_client,
        sync_mode=True  # Use sync mode for testing
    )

    # Assert: Should work correctly
    assert isinstance(result, SyncResult)
    assert result.total_chunks > 0


@pytest.mark.asyncio
async def test_add_document_file_path_without_docs_prefix(mock_graphiti_client, sample_markdown_document, tmp_path):
    """
    Test: file_path without "docs/" prefix should also work.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-006-AddDocument
    """
    # Setup ROOT with file
    root_dir = tmp_path / "root"
    docs_dir = root_dir / "General" / "docs" / "todos"
    docs_dir.mkdir(parents=True)
    original_file = docs_dir / "TODO-001.md"
    original_file.write_text("# Empty")

    # Setup new file
    new_file = tmp_path / "new" / "TODO-001.md"
    new_file.parent.mkdir(parents=True)
    new_file.write_text(sample_markdown_document)

    # Execute: Use file_path WITHOUT "docs/" prefix
    result = await add_document(
        new_file_path=str(new_file),
        project_id="General",
        feature_id=None,
        doc_type=None,
        file_path="todos/TODO-001.md",  # WITHOUT docs/
        root_dir=str(root_dir),
        graphiti_client=mock_graphiti_client,
        sync_mode=True  # Use sync mode for testing
    )

    # Assert: Should work correctly
    assert isinstance(result, SyncResult)
    assert result.total_chunks > 0


@pytest.mark.asyncio
async def test_add_document_invalid_doc_type(mock_graphiti_client, tmp_path):
    """
    Test: Invalid doc_type should raise clear error.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-006-AddDocument
    """
    # Setup new file
    new_file = tmp_path / "new.md"
    new_file.write_text("# Test")

    # Execute: Try with invalid doc_type
    with pytest.raises(ValueError) as exc_info:
        await add_document(
            new_file_path=str(new_file),
            project_id="General",
            feature_id=None,
            doc_type="todos",  # Invalid! Should be None for general docs
            file_path="todos/xxx.md",
            root_dir=str(tmp_path),
            graphiti_client=mock_graphiti_client,
            sync_mode=True  # Use sync mode for testing
        )

    # Assert: Error message should be helpful
    assert "Invalid doc_type" in str(exc_info.value)
    assert "todos" in str(exc_info.value)
    assert "REQ" in str(exc_info.value) or "BP" in str(exc_info.value)


@pytest.mark.asyncio
async def test_add_document_root_update_and_reupload(mock_graphiti_client, sample_rbt_document, tmp_path):
    """
    Test: ROOT file is automatically updated after sync, second upload shows unchanged.

    Given:
        1. First upload: new file with content, ROOT is minimal
        2. Second upload: same file again
    When: Call add_document() twice
    Then:
        1. First call: chunks are added
        2. ROOT file is updated automatically
        3. Second call: all chunks are unchanged

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-006-AddDocument
    """
    # Setup ROOT directory with minimal original file
    root_dir = tmp_path / "root"
    project_dir = root_dir / "knowledge-smith"
    feature_dir = project_dir / "features" / "test-feature"
    tasks_dir = feature_dir / "tasks"
    tasks_dir.mkdir(parents=True)
    original_file = tasks_dir / "TASK-001-TestTask.md"

    # Minimal ROOT file
    minimal_content = """---
id: TASK-001-TestTask
group_id: knowledge-smith
type: Task
title: Test Task
---

<!-- id: sec-root -->
# Task: Test Task
"""
    original_file.write_text(minimal_content)

    # Setup new file with full content
    new_file = tmp_path / "new" / "TASK-001-TestTask.md"
    new_file.parent.mkdir(parents=True)
    new_file.write_text(sample_rbt_document)

    # First upload: Should add chunks
    result1 = await add_document(
        new_file_path=str(new_file),
        project_id="knowledge-smith",
        feature_id="test-feature",
        doc_type="TASK",
        file_path="001",
        root_dir=str(root_dir),
        graphiti_client=mock_graphiti_client,
        sync_mode=True  # Use sync mode for testing
    )

    # Assert: First upload should have added chunks
    assert isinstance(result1, SyncResult)
    assert len(result1.added) > 0, "First upload should have added chunks"
    assert result1.unchanged == 0, "First upload should have no unchanged chunks"

    # Verify ROOT file was updated
    root_content = original_file.read_text()
    assert root_content == sample_rbt_document, "ROOT file should be updated with new content"

    # Reset mock call counts for second upload
    mock_graphiti_client.add_episode.reset_mock()
    mock_graphiti_client.delete_episode.reset_mock()

    # Second upload: Same file again, should be unchanged
    result2 = await add_document(
        new_file_path=str(new_file),
        project_id="knowledge-smith",
        feature_id="test-feature",
        doc_type="TASK",
        file_path="001",
        root_dir=str(root_dir),
        graphiti_client=mock_graphiti_client,
        sync_mode=True  # Use sync mode for testing
    )

    # Assert: Second upload should show all unchanged
    assert isinstance(result2, SyncResult)
    assert len(result2.added) == 0, "Second upload should have no added chunks"
    assert len(result2.updated) == 0, "Second upload should have no updated chunks"
    assert len(result2.deleted) == 0, "Second upload should have no deleted chunks"
    assert result2.unchanged > 0, "Second upload should have unchanged chunks"

    # Verify no Graphiti operations were performed in second upload
    assert mock_graphiti_client.add_episode.call_count == 0, "No episodes should be added in second upload"
    assert mock_graphiti_client.delete_episode.call_count == 0, "No episodes should be deleted in second upload"
