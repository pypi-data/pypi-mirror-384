"""
Path resolution and validation for RBT documents.

@REQ: REQ-rbt-mcp-tool
@BP: BP-rbt-mcp-tool
@TASK: TASK-001-PathResolver
"""

import os
from pathlib import Path
from typing import Optional
from glob import glob

from .models import PathInfo


class PathResolver:
    """
    Resolves and validates file paths for RBT documents and general files.

    Supports:
    - RBT standard paths: {root}/{project_id}/features/{feature_id}/{doc_type}-{feature_id}.md
    - TASK paths: {root}/{project_id}/features/{feature_id}/tasks/TASK-{index}-{name}.md
    - General file paths: {root}/{project_id}/docs/{file_path}
    - .new.md priority: Prefers .new.md over .md when both exist
    - TASK partial matching: Resolves TASK-001 to full filename

    @REQ: REQ-rbt-mcp-tool
    @BP: BP-rbt-mcp-tool
    @TASK: TASK-001-PathResolver
    """

    def __init__(self, root_dir: str):
        """
        Initialize PathResolver with root directory.

        Args:
            root_dir: Root directory for all documents
        """
        self.root_dir = root_dir

    def resolve(
        self,
        project_id: str,
        feature_id: Optional[str] = None,
        doc_type: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> PathInfo:
        """
        Resolve document path based on provided parameters.

        Args:
            project_id: Project identifier (required)
            feature_id: Feature identifier (optional, required for RBT docs)
            doc_type: Document type ('REQ', 'BP', 'TASK') for RBT docs
            file_path: Relative path for general files or TASK name

        Returns:
            PathInfo with resolved path information

        Raises:
            ValueError: If invalid parameter combination
            FileNotFoundError: If resolved file doesn't exist

        @REQ: REQ-rbt-mcp-tool
        @BP: BP-rbt-mcp-tool
        @TASK: TASK-001-PathResolver
        """
        # Validate parameters
        if doc_type is None and file_path is None:
            raise ValueError("Either doc_type or file_path must be provided")

        # Handle RBT document types
        if doc_type:
            return self._resolve_rbt_document(project_id, feature_id, doc_type, file_path)

        # Handle general files
        return self._resolve_general_file(project_id, file_path)

    def _resolve_rbt_document(
        self,
        project_id: str,
        feature_id: Optional[str],
        doc_type: str,
        file_path: Optional[str]
    ) -> PathInfo:
        """
        Resolve RBT standard document path.

        @TASK: TASK-001-PathResolver
        """
        # TASK type has special handling
        if doc_type == "TASK":
            return self._resolve_task_document(project_id, feature_id, file_path)

        # REQ and BP types require feature_id
        if not feature_id:
            raise ValueError(f"feature_id is required for doc_type={doc_type}")

        # Build standard RBT path
        base_path = Path(self.root_dir) / project_id / "features" / feature_id
        filename = f"{doc_type}-{feature_id}.md"
        full_path = base_path / filename

        # Check for .new.md version first (priority)
        new_md_path = base_path / f"{doc_type}-{feature_id}.new.md"
        if os.path.exists(new_md_path):
            full_path = new_md_path
            file_exists = True
        else:
            # Check if regular .md file exists
            file_exists = os.path.exists(full_path)

        return PathInfo(
            project_id=project_id,
            feature_id=feature_id,
            doc_type=doc_type,
            file_path=str(full_path),
            is_rbt=True,
            file_exists=file_exists
        )

    def _resolve_task_document(
        self,
        project_id: str,
        feature_id: Optional[str],
        file_path: Optional[str]
    ) -> PathInfo:
        """
        Resolve TASK document within specified feature with partial matching support.

        Requirements:
        - feature_id: Can be either:
            1. Full feature name (e.g., "rbt-mcp-tool") → searches in that specific feature
            2. Task number only (e.g., "001" or "TASK-001") → searches across all features (fuzzy match)
        - file_path: Optional, specifies TASK identifier with partial matching support
                    Examples: "014" → TASK-014-*.md, "014-CreateDocumentTool" → TASK-014-CreateDocumentTool.md
                    If not provided, uses feature_id as task number

        Path format: {root}/{project_id}/features/{feature_id}/tasks/TASK-{file_path}.md

        @TASK: TASK-001-PathResolver
        """
        # feature_id is required
        if not feature_id:
            raise ValueError("feature_id is required for TASK doc_type")

        # Check if feature_id looks like a task number (fuzzy match mode)
        # Task number pattern: pure digits, or TASK-digits
        task_number_pattern = feature_id.replace("TASK-", "")
        is_task_number = task_number_pattern.isdigit()

        if is_task_number:
            # Fuzzy match mode: search across all features
            return self._resolve_task_fuzzy(project_id, task_number_pattern)

        # Normal mode: feature_id is a feature folder name
        feature_path = Path(self.root_dir) / project_id / "features" / feature_id

        # file_path is required to identify specific TASK
        if not file_path:
            raise ValueError("file_path is required to specify TASK identifier (e.g., '014' or '014-CreateDocumentTool')")

        # Build TASK path
        base_path = feature_path / "tasks"

        # Try exact match first
        filename = f"TASK-{file_path}.md"
        full_path = base_path / filename

        if os.path.exists(full_path):
            return PathInfo(
                project_id=project_id,
                feature_id=feature_id,
                doc_type="TASK",
                file_path=str(full_path),
                is_rbt=True,
                file_exists=True
            )

        # Exact match failed, try glob matching for partial IDs (e.g., "006" → TASK-006-*.md)
        search_pattern = str(base_path / f"TASK-{file_path}-*.md")
        matches = glob(search_pattern)

        if len(matches) == 1:
            # Single match found
            return PathInfo(
                project_id=project_id,
                feature_id=feature_id,
                doc_type="TASK",
                file_path=str(matches[0]),
                is_rbt=True,
                file_exists=True
            )
        elif len(matches) > 1:
            raise ValueError(
                f"Ambiguous TASK identifier '{file_path}'\n"
                f"Found {len(matches)} matches:\n" +
                "\n".join(f"  - {Path(m).name}" for m in matches) +
                "\n\nPlease provide full TASK filename to disambiguate."
            )

        # No matches found - return path for new document
        return PathInfo(
            project_id=project_id,
            feature_id=feature_id,
            doc_type="TASK",
            file_path=str(full_path),
            is_rbt=True,
            file_exists=False
        )

    def _resolve_task_fuzzy(self, project_id: str, task_number: str) -> PathInfo:
        """
        Fuzzy search for TASK document across all features.

        Note: Fuzzy mode does NOT support creating new documents since we can't
        determine which feature the new TASK should belong to. Use explicit
        feature_id for new documents.

        Args:
            project_id: Project identifier
            task_number: Task number (e.g., "001")

        Returns:
            PathInfo for the found task

        Raises:
            FileNotFoundError: If no matching task found
            ValueError: If multiple matching tasks found (ambiguous)

        @TASK: TASK-001-PathResolver
        """
        features_base = Path(self.root_dir) / project_id / "features"

        if not os.path.exists(features_base):
            raise FileNotFoundError(f"Features directory not found: {features_base}")

        # Search pattern: features/*/tasks/TASK-{task_number}-*.md
        search_pattern = str(features_base / "*" / "tasks" / f"TASK-{task_number}-*.md")
        matches = glob(search_pattern)

        if len(matches) == 0:
            raise FileNotFoundError(
                f"TASK document not found\n"
                f"Searched for: TASK-{task_number}-*.md in any feature\n"
                f"Search base: {features_base}\n"
                f"Please verify TASK number is correct: {task_number}\n\n"
                f"Note: To create a new TASK document, please specify the feature_id explicitly."
            )

        if len(matches) > 1:
            raise ValueError(
                f"Ambiguous TASK ID '{task_number}'\n"
                f"Found {len(matches)} matches:\n" +
                "\n".join(f"  - {Path(m).relative_to(features_base)}" for m in matches) +
                "\n\nPlease specify feature_id to disambiguate."
            )

        # Single match found
        resolved_path = matches[0]

        # Extract feature_id from path
        # Path format: .../features/{feature_id}/tasks/TASK-{task_number}-*.md
        path_parts = Path(resolved_path).parts
        features_idx = path_parts.index("features")
        feature_id = path_parts[features_idx + 1]

        return PathInfo(
            project_id=project_id,
            feature_id=feature_id,
            doc_type="TASK",
            file_path=str(resolved_path),
            is_rbt=True,
            file_exists=True
        )

    def _resolve_general_file(self, project_id: str, file_path: str) -> PathInfo:
        """
        Resolve general file path (non-RBT).

        Automatically handles "docs/" prefix in file_path:
        - "docs/todos/xxx.md" → {root}/{project_id}/docs/todos/xxx.md
        - "todos/xxx.md" → {root}/{project_id}/docs/todos/xxx.md

        @TASK: TASK-001-PathResolver
        """
        # Automatically handle "docs/" prefix
        if file_path.startswith("docs/"):
            # Remove "docs/" prefix to avoid duplication
            relative_path = file_path[5:]
        else:
            # No "docs/" prefix, use as-is
            relative_path = file_path

        # Build general file path (always under docs/)
        full_path = Path(self.root_dir) / project_id / "docs" / relative_path

        # Check if file exists (but don't raise error)
        file_exists = os.path.exists(full_path)

        return PathInfo(
            project_id=project_id,
            feature_id=None,
            doc_type=None,
            file_path=str(full_path),
            is_rbt=False,
            file_exists=file_exists
        )

