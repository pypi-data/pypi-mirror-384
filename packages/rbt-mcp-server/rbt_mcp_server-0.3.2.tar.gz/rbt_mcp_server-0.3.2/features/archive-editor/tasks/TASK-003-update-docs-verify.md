---
id: TASK-003-update-docs-verify
group_id: knowledge-smith
type: Task
title: 更新文件並驗證保留功能
blueprint: BP-archive-editor
requirement: REQ-archive-editor
---

<!-- info-section -->
> status: Done
> update_date: 2025-10-09
> dependencies: [TASK-002-delete-editor-code]

<!-- id: sec-root -->
# Task: 更新文件並驗證保留功能

<!-- id: sec-goal-dependencies -->
### 1. 任務目標與前置 (Goal & Dependencies)

<!-- id: blk-goal, type: list -->
**目標 (Goal)**
  - 更新 README.md 說明 editor 已封存及如何恢復
  - 驗證 MCP server 能正常啟動
  - 驗證 add_document 和 graphiti 功能正常運作

<!-- id: blk-dependencies, type: list -->
**前置任務 (Dependencies)**
  - TASK-002-delete-editor-code（必須先完成代碼清理）

<!-- id: blk-target-modules, type: list -->
**目標模組/檔案**
  - 修改：`README.md`
  - 驗證：MCP server 啟動
  - 驗證：add_document 功能
  - 驗證：graphiti 功能

<!-- id: sec-change-history -->
### 2. 變更記錄與風險 (Change History & Risks)

<!-- id: blk-change-history-table, type: table -->
**變更歷史追溯**
| 版本 | 變更原因 | 影響範圍 | 重新實作日期 |
|---|---|---|---|
| v1.0 | 初始版本 | N/A | 2025-10-09 |

<!-- id: blk-risks, type: list -->
**風險與關注點**
  - **風險**: 文件說明不夠清楚，未來無法恢復
  - **緩解**: 提供明確的恢復步驟和 git 指令範例

<!-- id: sec-implementation -->
### 3. 實作指引與測試規格 (Implementation Guide & Test Specifications)

<!-- id: blk-implementation-steps, type: list -->
**實作指引 (Implementation Guide)**
  - **步驟 1**: 更新 README.md 加入封存說明區塊
    ```markdown
    ## 封存說明

    ### RBT Document Editor MCP

    rbt-document-editor MCP 功能已於 2025-10-09 封存，改用原生 Read/Edit/Write 以降低成本。

    **封存內容：**
    - document_parser.py - 文件解析器
    - path_resolver.py - 路徑解析器
    - tools/ - 所有 editor 工具（get_outline, read_section, update_block 等）

    **保留功能：**
    - ✅ chunking/add_document.py - 文件新增與分塊功能（重點功能）
    - ✅ graphiti_tools.py - RAG 記憶體功能

    **如何恢復封存的代碼：**
    ```bash
    # 查看封存版本
    git show v-with-editor

    # 恢復特定檔案
    git checkout v-with-editor -- rbt_mcp_server/document_parser.py

    # 或建立分支使用完整封存版本
    git checkout -b restore-editor v-with-editor
    ```
    ```
  - **步驟 2**: 驗證 MCP server 啟動
    - 執行 `uv run mcp dev rbt_mcp_server/server.py` 或對應的啟動指令
    - 確認無錯誤訊息，server 正常運行
  - **步驟 3**: 驗證 add_document 功能
    - 使用 MCP client 呼叫 add_document 工具
    - 確認功能正常運作
  - **步驟 4**: 驗證 graphiti 功能
    - 使用 MCP client 呼叫 search_memory_nodes 或 search_memory_facts
    - 確認 RAG 查詢正常運作

<!-- id: blk-test-spec, type: list -->
**測試規格 (Test Specifications)**
  - **Test Case 1**: README 更新完成
    - **Given**: README.md 已編輯
    - **When**: 檢查 README 內容
    - **Then**: 包含封存說明、保留功能清單、恢復方法
  - **Test Case 2**: MCP Server 正常啟動
    - **Given**: 代碼清理完成
    - **When**: 啟動 MCP server
    - **Then**: 無錯誤訊息，server 正常運行
  - **Test Case 3**: add_document 功能正常
    - **Given**: MCP server 已啟動
    - **When**: 呼叫 add_document 工具
    - **Then**: 功能正常執行，無錯誤
  - **Test Case 4**: Graphiti 功能正常
    - **Given**: MCP server 已啟動
    - **When**: 呼叫 search_memory_nodes 或 search_memory_facts
    - **Then**: RAG 查詢正常返回結果

<!-- id: sec-completion -->
### 4. 實作完成記錄 (Implementation Completion)

<!-- id: blk-execution-summary, type: list -->
**執行摘要與產出**
  - **實際耗時**: 0.3 小時 (預估: 0.5 小時)
  - **執行狀態**: ✅ 完成
  - **關鍵產出**: 更新後的 README.md，已驗證 server 啟動
  - **程式碼變更統計**: +32 lines, -50 lines in README.md（加入封存說明，移除 editor 工具描述）
  - **完成日期**: 2025-10-09

<!-- id: blk-problems-table, type: table -->
**問題與解決記錄**
| 問題描述 | 解決方案 | 耗時 | 可預防? |
|----------|----------|------|---------|
| 無問題 | N/A | 0min | N/A |

<!-- id: blk-technical-debt, type: list -->
**技術債務與重構建議**
  - **技術債務**: 無
  - **重構建議**: 無
  - **關鍵檔案清單**: README.md - 已更新封存說明
