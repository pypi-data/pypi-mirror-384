# Shared Utilities

Shared modules for the KnowledgeSmith MCP project.

## path_resolver

Provides simple helper functions for resolving and reading RBT and general Markdown documents.

### Features

- **Unified Interface**: Single API for both RBT and general documents
- **Partial TASK Matching**: Resolve "001" to "TASK-001-PathResolver.md"
- **.new.md Priority**: Automatically prefers .new.md versions
- **Type Hints & Docstrings**: Full Python type support and documentation
- **Tested**: Comprehensive unit tests with >90% coverage

### Quick Start

```python
from shared.path_resolver import resolve_path, read_document

# Read RBT Blueprint document
content = read_document(
    project_id="knowledge-smith",
    feature_id="graphiti-chunk-mcp",
    doc_type="BP"
)

# Read TASK document (with partial matching)
task_content = read_document(
    project_id="knowledge-smith",
    feature_id="graphiti-chunk-mcp",
    doc_type="TASK",
    file_path="001"  # Matches TASK-001-*.md
)

# Read general document (file_path is relative to docs/)
doc_content = read_document(
    project_id="knowledge-smith",
    file_path="architecture/overview.md"
)

# Just resolve path without reading
path = resolve_path(
    project_id="knowledge-smith",
    feature_id="graphiti-chunk-mcp",
    doc_type="BP"
)
print(path)  # /path/to/knowledge-smith/features/graphiti-chunk-mcp/BP-graphiti-chunk-mcp.md
```

### API Reference

#### resolve_path()

Resolve document path and return the absolute file system path.

**Parameters:**
- `project_id` (str, required): Project identifier
- `feature_id` (str, optional): Feature identifier (required for RBT docs)
- `doc_type` (str, optional): Document type ('REQ', 'BP', 'TASK')
- `file_path` (str, optional): For TASK: identifier (e.g., "001"). For general docs: relative path from docs/ (e.g., "README.md")
- `root_dir` (str, optional): Root directory (defaults to project root)

**Returns:** Absolute file system path (str)

**Raises:**
- `ValueError`: Invalid parameter combination
- `FileNotFoundError`: File doesn't exist

#### read_document()

Resolve document path and return its content as a string.

**Parameters:** Same as `resolve_path()`

**Returns:** Document content (str)

**Raises:**
- `ValueError`: Invalid parameter combination
- `FileNotFoundError`: File doesn't exist
- `IOError`: File cannot be read

### Implementation Details

This module wraps the `PathResolver` class from `rbt_mcp_server`, avoiding code duplication while providing a simpler interface. It uses a cached resolver instance for better performance.

### Testing

Run unit tests:

```bash
python -m pytest tests/shared/test_path_resolver.py -v
```

Test coverage:

```bash
python -m pytest tests/shared/test_path_resolver.py --cov=shared.path_resolver --cov-report=term-missing
```

### Related Files

- Implementation: `shared/path_resolver.py`
- Tests: `tests/shared/test_path_resolver.py`
- Base implementation: `rbt_mcp_server/path_resolver.py`

### Traceability

- **@REQ**: REQ-graphiti-chunk-mcp
- **@BP**: BP-graphiti-chunk-mcp
- **@TASK**: TASK-001-PathResolver
