# MCP Server Configuration Guide

@REQ: REQ-graphiti-chunk-mcp
@BP: BP-graphiti-chunk-mcp
@TASK: TASK-008-TestsAndDocs

This document provides detailed configuration instructions for the RBT MCP Server with Graphiti integration.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Variables](#environment-variables)
3. [Claude Desktop Configuration](#claude-desktop-configuration)
4. [Neo4j Setup](#neo4j-setup)
5. [OpenAI API Configuration](#openai-api-configuration)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### Software Requirements

- Python 3.10 or higher
- Claude Desktop application
- (Optional) Neo4j 5.x or higher (for Graphiti features)
- (Optional) OpenAI API account (for Graphiti features)

### Installation

Install the RBT MCP Server:

```bash
# Using uv (recommended)
uv pip install rbt-mcp-server

# Or from source
git clone https://github.com/yourusername/KnowledgeSmith.git
cd KnowledgeSmith
uv pip install -e .
```

## Environment Variables

The MCP server requires different environment variables depending on which features you use:

### Required for RBT Document Editing

| Variable | Description | Example |
|----------|-------------|---------|
| `RBT_ROOT_DIR` | Root directory containing your RBT documents | `/Users/you/projects/docs` |

### Required for Graphiti Features

| Variable | Description | Example |
|----------|-------------|---------|
| `NEO4J_URI` | Neo4j database connection URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `your-secure-password` |
| `OPENAI_API_KEY` | OpenAI API key for embeddings | `sk-...` |

### Optional Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `CACHE_SIZE` | Document cache size | `100` |
| `CACHE_TTL_SECONDS` | Cache TTL in seconds | `3600` |

## Claude Desktop Configuration

### Configuration File Location

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Configuration Examples

#### Minimal Configuration (RBT editing only)

```json
{
  "mcpServers": {
    "rbt-document-editor": {
      "type": "stdio",
      "command": "rbt-mcp-server",
      "env": {
        "RBT_ROOT_DIR": "/path/to/your/documents"
      }
    }
  }
}
```

#### Full Configuration (RBT + Graphiti)

```json
{
  "mcpServers": {
    "rbt-document-editor": {
      "type": "stdio",
      "command": "rbt-mcp-server",
      "env": {
        "RBT_ROOT_DIR": "/path/to/your/documents",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "your-password",
        "OPENAI_API_KEY": "sk-your-api-key"
      }
    }
  }
}
```

#### Using uv Runtime

If you want to use uv to manage the Python environment:

```json
{
  "mcpServers": {
    "rbt-document-editor": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "rbt-mcp-server"],
      "env": {
        "RBT_ROOT_DIR": "/path/to/your/documents",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "your-password",
        "OPENAI_API_KEY": "sk-your-api-key"
      }
    }
  }
}
```

#### Multiple MCP Servers

You can run multiple MCP servers simultaneously:

```json
{
  "mcpServers": {
    "rbt-document-editor": {
      "type": "stdio",
      "command": "rbt-mcp-server",
      "env": {
        "RBT_ROOT_DIR": "/path/to/project1/docs"
      }
    },
    "graphiti-memory": {
      "type": "stdio",
      "command": "uvx",
      "args": ["--from", "graphiti-core", "mcp-server-graphiti"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "your-password",
        "OPENAI_API_KEY": "sk-your-api-key"
      }
    }
  }
}
```

## Neo4j Setup

### Using Docker (Recommended)

```bash
# Start Neo4j container
docker run -d \
  --name neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  -v neo4j-data:/data \
  neo4j:5.16

# Access Neo4j Browser at http://localhost:7474
```

### Using Neo4j Desktop

1. Download Neo4j Desktop from https://neo4j.com/download/
2. Create a new database
3. Start the database
4. Note the Bolt URL (usually `bolt://localhost:7687`)
5. Set a password

### Using Neo4j AuraDB (Cloud)

1. Create a free account at https://neo4j.com/cloud/aura/
2. Create a new instance
3. Save the connection URI and credentials
4. Use the connection details in your configuration

### Verifying Neo4j Connection

```bash
# Test connection using cypher-shell
cypher-shell -a bolt://localhost:7687 -u neo4j -p your-password

# Or use Python
python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'your-password'))
driver.verify_connectivity()
print('Connected successfully!')
driver.close()
"
```

## OpenAI API Configuration

### Getting an API Key

1. Go to https://platform.openai.com/
2. Sign up or log in
3. Navigate to API keys section
4. Create a new secret key
5. Copy the key (it won't be shown again)

### Setting Usage Limits

1. Go to https://platform.openai.com/account/billing/limits
2. Set monthly spending limits
3. Enable email notifications for usage alerts

### Model Selection

The Graphiti integration uses OpenAI models for:
- **Embeddings**: `text-embedding-3-small` (default)
- **Entity extraction**: `gpt-4o-mini` (configurable)

### Cost Estimation

Approximate costs for document chunking:

| Document Size | Chunks | Embedding Cost | LLM Cost | Total |
|---------------|--------|----------------|----------|-------|
| 1 TASK (5KB) | 3-5 | $0.0001 | $0.001 | $0.0011 |
| 1 Blueprint (20KB) | 10-15 | $0.0003 | $0.003 | $0.0033 |
| 100 documents | 500-1000 | $0.03 | $0.30 | $0.33 |

## Troubleshooting

### Common Issues

#### 1. RBT_ROOT_DIR not set

**Error**: `ValueError: RBT_ROOT_DIR environment variable is required`

**Solution**: Add `RBT_ROOT_DIR` to your Claude Desktop configuration:
```json
"env": {
  "RBT_ROOT_DIR": "/path/to/your/documents"
}
```

#### 2. Neo4j connection failed

**Error**: `Failed to establish connection with Neo4j`

**Solutions**:
- Verify Neo4j is running: `docker ps` or check Neo4j Desktop
- Test connection: `cypher-shell -a bolt://localhost:7687 -u neo4j -p password`
- Check firewall settings for port 7687
- Verify credentials are correct

#### 3. OpenAI API authentication failed

**Error**: `AuthenticationError: Invalid API key`

**Solutions**:
- Verify API key is correct
- Check API key has not expired
- Ensure sufficient API credits
- Visit https://platform.openai.com/account/api-keys

#### 4. MCP Server not starting

**Error**: Server fails to start in Claude Desktop

**Solutions**:
1. Check Claude Desktop logs:
   - macOS: `~/Library/Logs/Claude/mcp-server-rbt-document-editor.log`
   - Windows: `%APPDATA%\Claude\Logs\mcp-server-rbt-document-editor.log`

2. Test server manually:
   ```bash
   export RBT_ROOT_DIR=/path/to/docs
   rbt-mcp-server
   ```

3. Verify Python environment:
   ```bash
   which rbt-mcp-server
   python --version
   ```

#### 5. Document not found errors

**Error**: `FileNotFoundError: RBT document not found`

**Solutions**:
- Verify `RBT_ROOT_DIR` points to correct directory
- Check document path structure:
  ```
  RBT_ROOT_DIR/
  ├── project-id/
  │   ├── features/
  │   │   ├── feature-id/
  │   │   │   ├── REQ-feature-id.md
  │   │   │   ├── BP-feature-id.md
  │   │   │   └── TASK-001-TaskName.md
  ```
- Use fuzzy search for TASK documents: just provide "001" instead of full filename

### Debug Mode

Enable debug logging:

```bash
# Set log level
export LOG_LEVEL=DEBUG

# Run server with debug output
rbt-mcp-server 2>&1 | tee server.log
```

### Getting Help

1. Check GitHub Issues: https://github.com/yourusername/KnowledgeSmith/issues
2. Review documentation: https://github.com/yourusername/KnowledgeSmith/docs
3. Discord community: [link to Discord]

## Performance Tuning

### Cache Configuration

Adjust cache settings based on your usage:

```json
"env": {
  "RBT_ROOT_DIR": "/path/to/docs",
  "CACHE_SIZE": "200",
  "CACHE_TTL_SECONDS": "7200"
}
```

### Neo4j Performance

For large knowledge graphs (>10,000 nodes):

```cypher
// Create indexes for better search performance
CREATE INDEX node_name_idx FOR (n:Entity) ON (n.name);
CREATE INDEX node_uuid_idx FOR (n:Entity) ON (n.uuid);
CREATE INDEX episode_created_idx FOR (n:Episodic) ON (n.created_at);
```

### OpenAI Rate Limits

To avoid rate limiting:
- Implement request batching
- Use exponential backoff
- Consider caching embeddings
- Use `gpt-4o-mini` for cost-effective processing

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables** for sensitive data
3. **Rotate API keys** regularly
4. **Set Neo4j authentication** (don't use default password)
5. **Restrict network access** to Neo4j (firewall rules)
6. **Monitor API usage** to detect anomalies
7. **Use HTTPS** for Neo4j connections in production

## Migration Guide

### From graphiti-memory MCP

If you're currently using the original `graphiti-memory` MCP:

1. Install `rbt-mcp-server`
2. Update Claude Desktop config to use `rbt-mcp-server` instead
3. Keep same environment variables (NEO4J_*, OPENAI_API_KEY)
4. All `search_nodes`, `search_facts` calls work the same way
5. New `add_memory` tool automatically chunks documents

### From Manual Document Management

1. Install `rbt-mcp-server`
2. Set `RBT_ROOT_DIR` to your documents root
3. Use `get_outline` to verify document structure
4. Start using `read_content`, `update_block` for editing
5. Optionally enable Graphiti for knowledge graph features

## License

MIT License - see LICENSE file for details.
