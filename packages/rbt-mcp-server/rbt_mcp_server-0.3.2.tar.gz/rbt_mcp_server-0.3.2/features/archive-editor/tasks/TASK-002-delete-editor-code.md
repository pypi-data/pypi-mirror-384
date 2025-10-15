---
id: TASK-002-delete-editor-code
group_id: knowledge-smith
type: Task
title: 刪除 Editor 相關代碼和測試
blueprint: BP-archive-editor
requirement: REQ-archive-editor
---

<!-- info-section -->
> status: Done
> update_date: 2025-10-09
> dependencies: [TASK-001-git-tag-backup]

<!-- id: sec-root -->
# Task: 刪除 Editor 相關代碼和測試

<!-- id: sec-goal-dependencies -->
### 1. 任務目標與前置 (Goal & Dependencies)

<!-- id: blk-goal, type: list -->
**目標 (Goal)**
  - 刪除 rbt_mcp_server 中所有 editor 相關的代碼和模組
  - 刪除對應的測試檔案
  - 更新 server.py 移除 editor 工具註冊
  - 確保保留 add_document 和 graphiti 功能

<!-- id: blk-dependencies, type: list -->
**前置任務 (Dependencies)**
  - TASK-001-git-tag-backup（必須先建立備份）

<!-- id: blk-target-modules, type: list -->
**目標模組/檔案**
  - 刪除：`rbt_mcp_server/document_parser.py`
  - 刪除：`rbt_mcp_server/path_resolver.py`
  - 刪除：`rbt_mcp_server/tools/` 目錄
  - 刪除：`tests/tools/` 目錄
  - 刪除：`tests/test_server.py` 中 editor 相關測試
  - 修改：`rbt_mcp_server/server.py` 移除 editor 工具註冊
  - 保留：`rbt_mcp_server/chunking/` 和 `rbt_mcp_server/graphiti_tools.py`

<!-- id: sec-change-history -->
### 2. 變更記錄與風險 (Change History & Risks)

<!-- id: blk-change-history-table, type: table -->
**變更歷史追溯**
| 版本 | 變更原因 | 影響範圍 | 重新實作日期 |
|---|---|---|---|
| v1.0 | 初始版本 | N/A | 2025-10-09 |

<!-- id: blk-risks, type: list -->
**風險與關注點**
  - **風險**: 可能誤刪 add_document 或 graphiti 相關代碼
  - **緩解**: 仔細檢查刪除清單，確保只刪除 editor 相關檔案
  - **風險**: server.py 更新後可能有 import 錯誤
  - **緩解**: 刪除後執行 server 確認無 import 錯誤

<!-- id: sec-implementation -->
### 3. 實作指引與測試規格 (Implementation Guide & Test Specifications)

<!-- id: blk-implementation-steps, type: list -->
**實作指引 (Implementation Guide)**
  - **步驟 1**: 刪除 editor 相關主要檔案
    - `rm rbt_mcp_server/document_parser.py`
    - `rm rbt_mcp_server/path_resolver.py`
  - **步驟 2**: 刪除 editor 工具目錄
    - `rm -rf rbt_mcp_server/tools/`
  - **步驟 3**: 刪除 editor 測試目錄
    - `rm -rf tests/tools/`
  - **步驟 4**: 更新 `rbt_mcp_server/server.py`
    - 移除 editor 相關的 import
    - 移除 editor 工具的註冊
    - 保留 add_document 和 graphiti 相關註冊
  - **步驟 5**: 檢查 `tests/test_server.py`
    - 移除或註解 editor 相關測試
    - 保留 graphiti 相關測試
  - **步驟 6**: 驗證沒有殘留的 import 錯誤
    - 執行 `python -m rbt_mcp_server.server --help` 確認無錯誤

<!-- id: blk-test-spec, type: list -->
**測試規格 (Test Specifications)**
  - **Test Case 1**: Editor 檔案已刪除
    - **Given**: 執行刪除指令
    - **When**: 檢查檔案系統
    - **Then**: document_parser.py, path_resolver.py, tools/, tests/tools/ 都不存在
  - **Test Case 2**: 保留功能完整
    - **Given**: 刪除完成
    - **When**: 檢查檔案系統
    - **Then**: chunking/, graphiti_tools.py 都存在
  - **Test Case 3**: Server 可正常載入
    - **Given**: 更新 server.py
    - **When**: 執行 `python -m rbt_mcp_server.server --help`
    - **Then**: 無 import 錯誤，正常顯示幫助訊息

<!-- id: sec-completion -->
### 4. 實作完成記錄 (Implementation Completion)

<!-- id: blk-execution-summary, type: list -->
**執行摘要與產出**
  - **實際耗時**: 0.4 小時 (預估: 0.3 小時)
  - **執行狀態**: ✅ 完成
  - **關鍵產出**: 清理後的 codebase，只保留 graphiti 和 chunking 功能
  - **程式碼變更統計**: ~900 lines removed (server.py 重寫), 9 files deleted
  - **完成日期**: 2025-10-09

<!-- id: blk-problems-table, type: table -->
**問題與解決記錄**
| 問題描述 | 解決方案 | 耗時 | 可預防? |
|----------|----------|------|---------|
| path_resolver 被 add_document 依賴 | 保留 path_resolver.py（add_document 需要） | 5min | ✅ 應提前檢查依賴 |
| models.py 和 errors.py 被保留功能依賴 | 保留這些模組（path_resolver 和 graphiti_tools 需要） | 5min | ✅ 應提前檢查依賴 |

<!-- id: blk-technical-debt, type: list -->
**技術債務與重構建議**
  - **技術債務**: 無
  - **重構建議**: 考慮清理 pyproject.toml 中可能不再需要的 editor 相關依賴
  - **關鍵檔案清單**:
    - rbt_mcp_server/server.py - 已重寫，只保留 graphiti 工具
    - 已刪除：document_service.py, cache.py, templates/, tests/tools/, tests/test_*.py
    - 保留：path_resolver.py, models.py, errors.py, converter/（被 chunking 依賴）
