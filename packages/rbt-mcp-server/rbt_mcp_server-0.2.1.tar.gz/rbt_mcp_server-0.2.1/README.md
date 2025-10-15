# KnowledgeSmith MCP Server

MCP Server for **Graphiti memory and document chunking**. Previously included RBT document editing tools (now archived).

## 📦 Archive Notice

### RBT Document Editor Tools (Archived 2025-10-09)

The RBT document editing功能已於 2025-10-09 封存，改用原生 Claude Code Read/Edit/Write 工具以降低維護成本和 token 使用。

**封存內容：**
- document_service.py - 文件服務
- document_parser.py - 文件解析器
- 11 個 editor MCP 工具（get_outline, read_content, update_block 等）
- templates/ - 文件模板
- cache.py - 文件快取

**保留功能：**
- ✅ chunking/ - 文件分塊與同步功能
- ✅ graphiti_tools.py - Graphiti 記憶體功能（5 個工具）

**如何恢復封存的代碼：**
```bash
# 查看封存版本
git show v-with-editor

# 恢復特定檔案
git checkout v-with-editor -- rbt_mcp_server/document_service.py

# 或建立分支使用完整封存版本
git checkout -b restore-editor v-with-editor
```

## 🎯 Current Features

### Graphiti Knowledge Graph Integration
- **Intelligent Chunking**: Automatically split documents into semantic chunks based on document structure (sections for RBT, H3 headings for Markdown)
- **Incremental Sync**: Only update changed chunks, preserving unchanged content
- **Neo4j Backend**: Store document chunks as episodes in Graphiti knowledge graph
- **graphiti-memory Compatible**: Drop-in replacement with same search_nodes/search_facts API
- **5 Graphiti Tools**: add_memory, search_nodes, search_facts, get_episodes, delete_episode

## 📦 Installation

### Option 1: Install from source (uv)

```bash
# Clone repository
git clone https://github.com/yourusername/KnowledgeSmith.git
cd KnowledgeSmith

# Install with uv
uv pip install -e .
```

### Option 2: Direct installation

```bash
uv pip install rbt-mcp-server
```

## 🚀 Quick Start

### 1. Configure Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "graphiti-memory": {
      "type": "stdio",
      "command": "rbt-mcp-server",
      "env": {
        "RBT_ROOT_DIR": "path/to/doc/root",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "your-password",
        "OPENAI_API_KEY": "your-openai-api-key"
      }
    }
  }
}
```

**Note**:
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `OPENAI_API_KEY` are required for Graphiti tools

Or use full uv command:

```json
{
  "mcpServers": {
    "graphiti-memory": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "rbt-mcp-server"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "your-password",
        "OPENAI_API_KEY": "your-openai-api-key"
      }
    }
  }
}
```

### 2. Set Environment Variables

```bash
# Required for Graphiti integration
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=your-password
export OPENAI_API_KEY=your-openai-api-key
```

### 3. Test the Server

```bash
rbt-mcp-server
```

## 📚 Available MCP Tools

### Graphiti Memory Tools

1. **search_memory_nodes** - Search knowledge graph nodes (entities, preferences, procedures)
2. **search_memory_facts** - Search knowledge graph facts (relationships)
3. **get_episodes** - Retrieve recent memory episodes
4. **delete_episode** - Delete specific episode
5. **delete_entity_edge** - Delete entity relationship

## 🔗 Graphiti Integration Usage

### Adding Documents to Knowledge Graph

```python
# The add_memory tool automatically chunks documents
await add_memory(
    name="TASK-001-PathResolver",
    episode_body="<document content>",
    group_id="knowledge-smith",
    source="text"
)
```

### Searching Knowledge

```python
# Search for nodes (entities, preferences, procedures)
results = await search_nodes(
    query="documentation preferences",
    group_ids=["knowledge-smith"],
    entity="Preference",
    max_nodes=10
)

# Search for facts (relationships)
facts = await search_facts(
    query="task dependencies",
    group_ids=["knowledge-smith"],
    max_facts=10
)
```

### Difference from graphiti-memory MCP

This MCP server extends the original `graphiti-memory` MCP with document chunking capabilities:

- **Original graphiti-memory**: Stores entire documents as single episodes
- **This MCP (graphiti-chunk-mcp)**: Automatically chunks documents into semantic sections
  - RBT documents: Split by section (sec-*)
  - Markdown documents: Split by H3 headings (###)
  - Incremental updates: Only sync changed chunks

**API Compatibility**: All `search_nodes`, `search_facts`, `get_episodes` functions maintain the same interface as graphiti-memory.

## 🧪 Development

Install development dependencies:
```bash
uv sync --dev
```

Run tests:
```bash
RBT_ROOT_DIR=/test/root uv run pytest -v
```

Test coverage:
```bash
RBT_ROOT_DIR=/test/root uv run pytest --cov=rbt_mcp_server --cov-report=html
```

## 📝 License

MIT License

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a pull request.
