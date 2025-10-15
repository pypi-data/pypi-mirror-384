---
id: REQ-archive-editor
group_id: knowledge-smith
type: Requirement
feature: archive-editor
---

<!-- info-section -->
> status: Draft
> update_date: 2025-10-09
> summary_context: 封存不再使用的 rbt-document-editor MCP 實作，改用原生 Read/Edit/Write 以降低成本

<!-- id: sec-root -->
# 需求文件 (Requirement): 封存 RBT Document Editor MCP

<!-- id: sec-goal-context -->
### 1. 核心目標與背景 (Goal & Context)

<!-- id: blk-goal, type: list -->
**目標 (Goal)**
  - 封存不再使用的 rbt-document-editor MCP 實作，保留完整歷史記錄以便未來需要時可以恢復
  - 清理相關代碼和測試，簡化專案結構
  - 降低維護成本和運行時的 token 消耗

<!-- id: blk-user-story, type: list -->
**使用者故事 (User Story)**
  - 身為一個專案維護者，我想要封存不再使用的代碼，以便於保持專案乾淨且降低維護成本
  - 身為一個未來的開發者，我想要能夠找回被封存的實作，以便於在需要時重新啟用

<!-- id: blk-context-desc, type: list -->
**背景說明**
  - rbt-document-editor MCP 原本用於提供結構化的文件編輯介面（按 block/section 操作）
  - 實際使用中發現高頻調用（讀一份文件需要 10+ 次 tool 調用）導致成本過高
  - 決定改用原生 Read/Edit/Write，一次讀寫完成，大幅降低調用頻率
  - 但不能完全刪除，需保留完整實作以便未來可能重新啟用

<!-- id: sec-functional-scope -->
### 2. 功能與邊界定義 (Functional Scope)

<!-- id: blk-func-req-list, type: list -->
**功能規格 (Functional Requirements)**
  - 使用 git tag 標記包含完整 editor 實作的版本
  - 刪除 rbt_mcp_server/tools/ 中所有 editor 工具
  - 刪除 rbt_mcp_server/document_parser.py 和 path_resolver.py
  - 刪除 tests/tools/ 中所有 editor 測試
  - 更新 README.md 說明 editor 已封存及如何找回
  - **保留** rbt_mcp_server/chunking/ 中的 add_document 功能（重點功能）
  - **保留** rbt_mcp_server/graphiti_tools.py 和相關的 RAG 功能

<!-- id: blk-out-of-scope-list, type: list -->
**範圍外 (Out of Scope)**
  - 不涉及 graphiti MCP 功能（保留）
  - 不修改 CLAUDE.md 或 slash commands（已在其他任務完成）
  - 不刪除 RBT 文件模板（features/ 和 rbt_mcp_server/templates/）

<!-- id: sec-non-functional -->
### 3. 非功能規格與限制 (Non-Functional Requirements & Constraints)

<!-- id: blk-non-func-req-list, type: list -->
**非功能規格 (Non-Functional Requirements)**
  - **可恢復性**: 必須能夠從 git tag 完整恢復 editor 實作
  - **文件完整性**: README 必須清楚說明如何找回封存的代碼
  - **向後相容**: 保留的 graphiti 功能不受影響

<!-- id: blk-tech-constraints-list, type: list -->
**技術限制**
  - 使用 git tag 進行版本標記
  - 確保 git history 完整保留

<!-- id: sec-use-cases -->
### 4. 使用場景與驗收標準 (Use Cases & Acceptance)

<!-- id: blk-use-cases-list, type: list -->
**使用場景 (Use Cases)**
  - 開發者執行 MCP server，只有 graphiti 相關工具，沒有 editor 工具
  - 未來需要 editor 時，查看 README 找到 git tag，checkout 該版本恢復代碼
  - 查看專案結構時，看不到 editor 相關的複雜實作

<!-- id: blk-acceptance-list, type: list -->
**驗收標準 (Acceptance Criteria)**
  - ✅ Git tag `v-with-editor` 已建立並包含完整 editor 實作
  - ✅ rbt_mcp_server/ 中所有 editor 相關代碼已刪除
  - ✅ tests/ 中所有 editor 相關測試已刪除
  - ✅ README.md 已更新，說明封存情況和恢復方法
  - ✅ MCP server 能正常啟動，graphiti 功能正常運作
  - ✅ 可以從 git tag 完整恢復 editor 實作
