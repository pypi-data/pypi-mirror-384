---
description: Execute a Blueprint - sequential task execution in main conversation
---

你現在要執行一個 Blueprint，在主對話中依序完成所有 Tasks。

## 輸入參數
- feature_id: {{feature_id}}
- project_id: 從 CLAUDE.md 取得

## 執行流程

### 1. RAG 查詢（使用 graphiti-memory MCP）
使用 `search_memory_nodes` 和 `search_memory_facts` 查詢：
- 偏好 (Preference)：專案開發偏好、命名規範、工具使用習慣
- 程序 (Procedure)：TDD 流程、文件更新規範、Blueprint 執行標準
- 相關事實：與此 feature 相關的先前決策、技術選型

查詢範圍：`group_ids = [project_id, "Public"]`

### 2. 驗證階段（使用 Read + Glob）
使用 Read tool 檢查：
- `BP-{feature_id}.md` 的 status 是否為 "Finalized" 或 "In Progress"（讀取 info-section）
- `REQ-{feature_id}.md` 的 status 是否為 "Finalized"
- 使用 Glob 列出所有 `TASK-{feature_id}-*.md` 檔案（通常在 features/{feature_id}/tasks/ 目錄）

如果 status 不符合，詢問是否要更新後繼續。

### 3. 任務執行（主對話序列處理）

**對於每個 TASK，依序執行以下步驟**：

#### Phase 1: 規劃
1. 讀取 Task 文件中的實作需求 (如果找不到文件，則直接中斷)
2. 更新 info-section：`status: Pending → In Progress`
3. 更新 `update_date` 為今天日期

#### Phase 2: 實作
1. 根據 Task 指引修改程式碼

#### Phase 3: 測試（最多 2 次）
1. 執行相關測試

#### Phase 4: 更新文件
1. 填寫 Task 文件中的 `Implementation Completion`
2. 技術債務與重構建議 中 以簡潔摘要為主，目的是讓看的人知道發生了什麼事
3. 更新 info-section：`status: Pending → In Progress`
4. 更新 `update_date` 為今天日期

### 4. 執行約束

**務實原則**：
- 搜尋定位：使用 Grep/Glob 快速找到目標文件和內容
- 如果是更新任務，可以搜尋 @TASK/@REQ/@BP 加上對應id，快速找到修改位置

**成本控制**：
- 每個 Task 目標：< 15k tokens
- 10 個 Tasks 總成本目標：< $3
- 避免重複讀取相同檔案（依賴 cache）

**錯誤處理**：
- 找不到檔案 → 用 Glob 搜尋一次，找不到就 Blocked
- 不確定怎麼做 → 先問用戶，不要瞎猜浪費 token

### 5. 進度追蹤

使用 TodoWrite 追蹤所有 Tasks：
```
- [pending] TASK-001-PathResolver
- [in_progress] TASK-002-DocumentCache  ← 當前
- [pending] TASK-003-DocumentService
...
```

每完成一個，立即標記為 completed。

### 6. 完成報告

所有 tasks 完成後：
1. 統計執行結果（成功/失敗/Blocked）
2. 彙總實際 token 消耗
3. 更新 Blueprint 文件：
   - 更新實作進度追蹤表（Task status 和完成度）
   - 填寫 Post-Implementation Validation 區塊
   - 更新 BP status: In Progress → Done
4. 可選：使用 `add_memory` 將執行經驗儲存到 RAG（graphiti-memory MCP）

## 成本預估
- 序列執行（主對話）：~$3-6（2-4 小時）
- 優勢：累積學習、共享 cache、可觀察、可介入

## 範例對話

```
你：/execute-BP feature_id=rbt-mcp-tool

我：
開始執行 BP-rbt-mcp-tool...

1. RAG 查詢完成，找到 3 個相關 Procedures
2. 驗證：BP status = In Progress, REQ status = Finalized ✓
3. 找到 10 個 Tasks

開始執行 TASK-001-PathResolver...
[實作過程]
✓ TASK-001 完成

開始執行 TASK-002-DocumentCache...
[實作過程]
✓ TASK-002 完成

...
```
