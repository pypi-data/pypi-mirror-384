"""
Unit tests for shared.path_resolver module.

@REQ: REQ-graphiti-chunk-mcp
@BP: BP-graphiti-chunk-mcp
@TASK: TASK-001-PathResolver
"""

import os
import tempfile
import pytest
from pathlib import Path

from shared.path_resolver import resolve_path, read_document, set_default_root


class TestPathResolver:
    """
    Test cases for path_resolver shared module.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-001-PathResolver
    """

    @pytest.fixture
    def temp_project_root(self):
        """
        Create a temporary project structure for testing.

        Structure:
        - knowledge-smith/
          - features/
            - graphiti-chunk-mcp/
              - BP-graphiti-chunk-mcp.md
              - tasks/
                - TASK-001-PathResolver.md
          - docs/
            - architecture/
              - overview.md

        @TASK: TASK-001-PathResolver
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Create RBT structure
            feature_dir = root / "knowledge-smith" / "features" / "graphiti-chunk-mcp"
            feature_dir.mkdir(parents=True)

            # Create Blueprint document
            bp_path = feature_dir / "BP-graphiti-chunk-mcp.md"
            bp_path.write_text(
                "---\nid: BP-graphiti-chunk-mcp\n---\n# Blueprint\nThis is a test blueprint.",
                encoding='utf-8'
            )

            # Create TASK directory and document
            tasks_dir = feature_dir / "tasks"
            tasks_dir.mkdir()
            task_path = tasks_dir / "TASK-001-PathResolver.md"
            task_path.write_text(
                "---\nid: TASK-001-PathResolver\n---\n# Task\nImplement PathResolver.",
                encoding='utf-8'
            )

            # Create general docs structure
            docs_dir = root / "knowledge-smith" / "docs" / "architecture"
            docs_dir.mkdir(parents=True)
            overview_path = docs_dir / "overview.md"
            overview_path.write_text(
                "# Architecture Overview\nThis is the overview document.",
                encoding='utf-8'
            )

            # Set as default root for testing
            set_default_root(str(root))

            yield str(root)

            # Cleanup is automatic with TemporaryDirectory

    def test_resolve_rbt_blueprint(self, temp_project_root):
        """
        Test Case 1: Resolve RBT Blueprint document path.

        Given: project_id='knowledge-smith', feature_id='graphiti-chunk-mcp', doc_type='BP'
        When: Call resolve_path()
        Then: Returns correct path to BP-graphiti-chunk-mcp.md

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-001-PathResolver
        """
        result = resolve_path(
            project_id="knowledge-smith",
            feature_id="graphiti-chunk-mcp",
            doc_type="BP"
        )

        # Verify path is correct
        expected_path = os.path.join(
            temp_project_root,
            "knowledge-smith",
            "features",
            "graphiti-chunk-mcp",
            "BP-graphiti-chunk-mcp.md"
        )
        assert result == expected_path
        assert os.path.exists(result)

    def test_resolve_task_document_partial_match(self, temp_project_root):
        """
        Test Case 2: Resolve TASK document with partial matching.

        Given: project_id='knowledge-smith', feature_id='graphiti-chunk-mcp',
               doc_type='TASK', file_path='001'
        When: Call resolve_path()
        Then: Returns correct path to TASK-001-PathResolver.md

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-001-PathResolver
        """
        result = resolve_path(
            project_id="knowledge-smith",
            feature_id="graphiti-chunk-mcp",
            doc_type="TASK",
            file_path="001"
        )

        # Verify path is correct
        expected_path = os.path.join(
            temp_project_root,
            "knowledge-smith",
            "features",
            "graphiti-chunk-mcp",
            "tasks",
            "TASK-001-PathResolver.md"
        )
        assert result == expected_path
        assert os.path.exists(result)
        assert "PathResolver" in Path(result).name

    def test_resolve_general_document(self, temp_project_root):
        """
        Test Case 3: Resolve general Markdown document.

        Given: project_id='knowledge-smith', file_path='architecture/overview.md'
               (file_path is relative to docs/ directory)
        When: Call resolve_path()
        Then: Returns correct path to overview.md

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-001-PathResolver
        """
        result = resolve_path(
            project_id="knowledge-smith",
            file_path="architecture/overview.md"
        )

        # Verify path is correct
        expected_path = os.path.join(
            temp_project_root,
            "knowledge-smith",
            "docs",
            "architecture",
            "overview.md"
        )
        assert result == expected_path
        assert os.path.exists(result)

    def test_resolve_path_file_not_found(self, temp_project_root):
        """
        Test Case 4: Handle file not found error.

        Given: Invalid feature_id
        When: Call resolve_path()
        Then: Raises FileNotFoundError

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-001-PathResolver
        """
        with pytest.raises(FileNotFoundError) as exc_info:
            resolve_path(
                project_id="knowledge-smith",
                feature_id="non-existent-feature",
                doc_type="BP"
            )

        assert "not found" in str(exc_info.value).lower()

    def test_read_rbt_blueprint(self, temp_project_root):
        """
        Test Case 5: Read RBT Blueprint document content.

        Given: project_id='knowledge-smith', feature_id='graphiti-chunk-mcp', doc_type='BP'
        When: Call read_document()
        Then: Returns full content of BP-graphiti-chunk-mcp.md

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-001-PathResolver
        """
        content = read_document(
            project_id="knowledge-smith",
            feature_id="graphiti-chunk-mcp",
            doc_type="BP"
        )

        # Verify content is correct
        assert "BP-graphiti-chunk-mcp" in content
        assert "Blueprint" in content
        assert "test blueprint" in content

    def test_read_task_document(self, temp_project_root):
        """
        Test Case 6: Read TASK document with partial matching.

        Given: project_id='knowledge-smith', feature_id='graphiti-chunk-mcp',
               doc_type='TASK', file_path='001'
        When: Call read_document()
        Then: Returns full content of TASK-001-PathResolver.md

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-001-PathResolver
        """
        content = read_document(
            project_id="knowledge-smith",
            feature_id="graphiti-chunk-mcp",
            doc_type="TASK",
            file_path="001"
        )

        # Verify content is correct
        assert "TASK-001-PathResolver" in content
        assert "PathResolver" in content

    def test_read_general_document(self, temp_project_root):
        """
        Test Case 7: Read general document content.

        Given: project_id='knowledge-smith', file_path='architecture/overview.md'
               (file_path is relative to docs/ directory)
        When: Call read_document()
        Then: Returns full content of overview.md

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-001-PathResolver
        """
        content = read_document(
            project_id="knowledge-smith",
            file_path="architecture/overview.md"
        )

        # Verify content is correct
        assert "Architecture Overview" in content
        assert "overview document" in content

    def test_read_document_file_not_found(self, temp_project_root):
        """
        Test Case 8: Handle file not found when reading.

        Given: Invalid file_path
        When: Call read_document()
        Then: Raises FileNotFoundError

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-001-PathResolver
        """
        with pytest.raises(FileNotFoundError) as exc_info:
            read_document(
                project_id="knowledge-smith",
                file_path="non-existent.md"
            )

        assert "not found" in str(exc_info.value).lower()

    def test_invalid_parameter_combination(self, temp_project_root):
        """
        Test Case 9: Handle invalid parameter combination.

        Given: Neither doc_type nor file_path provided
        When: Call resolve_path()
        Then: Raises ValueError

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-001-PathResolver
        """
        with pytest.raises(ValueError) as exc_info:
            resolve_path(project_id="knowledge-smith")

        assert "doc_type or file_path" in str(exc_info.value).lower()

    def test_consistency_with_rbt_mcp_server(self, temp_project_root):
        """
        Test Case 10: Verify consistency with rbt_mcp_server behavior.

        Given: Various parameter combinations
        When: Call resolve_path()
        Then: Paths match expected rbt_mcp_server behavior

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-001-PathResolver
        """
        # Test RBT path format
        bp_path = resolve_path(
            project_id="knowledge-smith",
            feature_id="graphiti-chunk-mcp",
            doc_type="BP"
        )
        assert "features/graphiti-chunk-mcp/BP-graphiti-chunk-mcp.md" in bp_path

        # Test TASK path format
        task_path = resolve_path(
            project_id="knowledge-smith",
            feature_id="graphiti-chunk-mcp",
            doc_type="TASK",
            file_path="001"
        )
        assert "features/graphiti-chunk-mcp/tasks/TASK-001" in task_path

        # Test general docs path format (file_path relative to docs/)
        doc_path = resolve_path(
            project_id="knowledge-smith",
            file_path="architecture/overview.md"
        )
        assert "knowledge-smith/docs/architecture/overview.md" in doc_path


class TestNewMdPriority:
    """
    Test .new.md file priority behavior.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-001-PathResolver
    """

    @pytest.fixture
    def temp_root_with_new_md(self):
        """
        Create temp structure with .new.md files.

        @TASK: TASK-001-PathResolver
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Create feature directory
            feature_dir = root / "knowledge-smith" / "features" / "test-feature"
            feature_dir.mkdir(parents=True)

            # Create both .md and .new.md versions
            bp_path = feature_dir / "BP-test-feature.md"
            bp_path.write_text("Original BP content", encoding='utf-8')

            bp_new_path = feature_dir / "BP-test-feature.new.md"
            bp_new_path.write_text("Updated BP content (.new.md)", encoding='utf-8')

            set_default_root(str(root))

            yield str(root)

    def test_prefers_new_md_version(self, temp_root_with_new_md):
        """
        Test that .new.md is preferred when both exist.

        Given: Both BP-test-feature.md and BP-test-feature.new.md exist
        When: Call resolve_path() and read_document()
        Then: Returns .new.md version

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-001-PathResolver
        """
        # Resolve path should return .new.md
        path = resolve_path(
            project_id="knowledge-smith",
            feature_id="test-feature",
            doc_type="BP"
        )
        assert path.endswith(".new.md")

        # Read should return .new.md content
        content = read_document(
            project_id="knowledge-smith",
            feature_id="test-feature",
            doc_type="BP"
        )
        assert "Updated BP content" in content
        assert ".new.md" in content
