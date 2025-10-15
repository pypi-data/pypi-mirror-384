---
id: mcp-installation-guide
group_id: Public
type: Guide
title: KnowledgeSmith MCP 安裝使用指南
author: System
update_date: 2025-10-15
---

# KnowledgeSmith MCP 安裝使用指南

本文件說明如何安裝和使用 KnowledgeSmith MCP Server，它提供 Graphiti 知識圖譜整合和文件 chunking 功能。

### 系統需求

**必須：**
- Python 3.11+
- uv (Python 套件管理工具)
- Neo4j 資料庫 (用於 Graphiti)
- OpenAI API key

**建議：**
- Claude Desktop (用於 MCP 整合)
- Docker (用於執行 Neo4j)

### Neo4j 資料庫設置

使用 Docker 快速啟動 Neo4j：

```bash
docker run \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  --name neo4j \
  neo4j:latest
```

**驗證連線：**
- 瀏覽器開啟: `http://localhost:7474`
- 使用帳號密碼登入: `neo4j` / `your-password`

### 安裝 MCP Server

**方法一：從原始碼安裝（開發用）**

```bash
# Clone repository
git clone https://github.com/yourusername/KnowledgeSmith-MCP.git
cd KnowledgeSmith-MCP

# 安裝
uv pip install -e .

# 測試安裝
rbt-mcp-server --help
```

**方法二：直接安裝**

```bash
# 安裝套件
uv pip install rbt-mcp-server

# 測試安裝
rbt-mcp-server --help
```

### 環境變數設定

建立 `.env` 檔案或直接匯出環境變數：

```bash
# Neo4j 連線資訊
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=your-password

# OpenAI API Key (用於 Graphiti)
export OPENAI_API_KEY=your-openai-api-key
```

### Claude Desktop 整合設定

編輯 Claude Desktop 設定檔：
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**設定範例一：使用已安裝的指令**

```json
{
  "mcpServers": {
    "graphiti-memory-server": {
      "type": "stdio",
      "command": "rbt-mcp-server",
      "env": {
        "RBT_ROOT_DIR": "/path/to/your/document/root",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "your-password",
        "OPENAI_API_KEY": "your-openai-api-key"
      }
    }
  }
}
```

**設定範例二：使用 uv run**

```json
{
  "mcpServers": {
    "graphiti-memory-server": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "rbt-mcp-server"],
      "env": {
        "RBT_ROOT_DIR": "/path/to/your/document/root",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "your-password",
        "OPENAI_API_KEY": "your-openai-api-key"
      }
    }
  }
}
```

**環境變數說明：**
- `RBT_ROOT_DIR`: 文件根目錄（用於比對原始檔案，add_document 工具必須）
- `NEO4J_URI`: Neo4j 資料庫連線位址
- `NEO4J_USER`: Neo4j 使用者名稱
- `NEO4J_PASSWORD`: Neo4j 密碼
- `OPENAI_API_KEY`: OpenAI API 金鑰（用於 Graphiti embeddings）

**設定完成後：**
1. 重新啟動 Claude Desktop
2. 確認 MCP 伺服器已連線（查看 Claude Desktop 狀態列）

### 可用的 MCP Tools

**文件管理：**
1. `add_document` - 同步文件到知識圖譜（自動 chunking）

**知識圖譜查詢：**
2. `search_memory_nodes` - 搜尋節點（entities, preferences, procedures）
3. `search_memory_facts` - 搜尋事實關係
4. `get_episodes` - 取得最近的記憶片段

**資料管理：**
5. `delete_episode` - 刪除指定 episode
6. `get_entity_edge` - 取得實體關係邊
7. `delete_entity_edge` - 刪除實體關係邊
8. `clear_graph` - 清空整個知識圖譜（危險操作）

### 使用範例

**範例一：新增文件到知識圖譜**

```python
# 使用 Claude Code 或 Claude Desktop
# 直接呼叫 MCP tool: add_document

add_document(
    new_file_path="/path/to/document.md",
    project_id="my-project",
    feature_id="my-feature",  # RBT 文件必填
    rbt_type="REQ",  # REQ/BP/TASK，一般文件不填
    file_path="relative/path.md"  # 一般文件必填
)
```

**範例二：搜尋相關知識**

```python
# 搜尋節點（偏好、程序等）
search_memory_nodes(
    query="文件撰寫規範",
    group_ids=["my-project", "Public"],
    entity="Preference",
    max_nodes=10
)

# 搜尋事實關係
search_memory_facts(
    query="chunker 實作細節",
    group_ids=["my-project", "Public"],
    max_facts=10
)
```

**範例三：取得最近的記憶**

```python
get_episodes(
    group_id="my-project",
    last_n=5
)
```

### 文件 Chunking 機制

MCP Server 會自動將文件切分成小塊 (chunks) 再存入知識圖譜：

**Markdown 文件：**
- 以 h3 (`###`) 標題為分段依據
- 每個 section 成為一個 chunk
- 自動過濾程式碼區塊內的假標題

**RBT 文件：**
- 以 section (`## {#sec-id}`) 為分段依據
- 每個 section 成為一個 chunk

**優點：**
- 增量更新：只同步變更的 chunks
- 精確搜尋：可以定位到具體段落
- 穩定 ID：相同段落產生相同 chunk ID

### 疑難排解

**問題：MCP Server 無法啟動**

檢查事項：
1. 確認環境變數都已設定
2. 確認 Neo4j 資料庫正在執行
3. 確認 OpenAI API key 有效
4. 查看 Claude Desktop logs

**問題：add_document 失敗**

檢查事項：
1. 檔案路徑是否正確（必須是絕對路徑）
2. 文件格式是否符合 Markdown 規範
3. project_id 是否正確
4. 對於 RBT 文件，確認 feature_id 和 rbt_type 正確

**問題：搜尋結果為空**

檢查事項：
1. 確認 group_ids 正確（區分大小寫）
2. 確認已有文件同步到該 group
3. 嘗試使用更通用的查詢關鍵字
4. 檢查 Neo4j 資料庫內容

### 開發與測試

**安裝開發依賴：**
```bash
uv sync --dev
```

**執行測試：**
```bash
RBT_ROOT_DIR=/test/root uv run pytest -v
```

**測試涵蓋率：**
```bash
RBT_ROOT_DIR=/test/root uv run pytest --cov=rbt_mcp_server --cov-report=html
```

### 相關文件

- [Markdown 文件撰寫規範](./markdown-writing-guide.md)
- [專案 README](../../README.md)
- [Graphiti 官方文件](https://github.com/getzep/graphiti)

### 注意事項

**安全性：**
- 不要在公開的配置檔中儲存 API keys
- 建議使用環境變數或密碼管理工具
- Neo4j 資料庫應設置適當的存取控制

**效能：**
- 大型文件會產生較多 chunks，搜尋時間較長
- 建議合理使用 max_nodes 和 max_facts 參數
- 定期清理不需要的 episodes

**資料管理：**
- `clear_graph` 會刪除所有資料，使用前務必確認
- 刪除 episode 或 edge 後無法恢復
- 建議定期備份 Neo4j 資料庫
