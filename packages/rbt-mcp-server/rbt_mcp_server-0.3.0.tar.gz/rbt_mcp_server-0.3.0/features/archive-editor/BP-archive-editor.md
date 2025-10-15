---
id: BP-archive-editor
group_id: knowledge-smith
type: Blueprint
feature: archive-editor
requirement: REQ-archive-editor
---

<!-- info-section -->
> status: Done
> update_date: 2025-10-09
> summary_context: 透過 git tag 封存 editor 實作，清理相關代碼，保留完整恢復能力

<!-- id: sec-root -->
# 專案藍圖 (Blueprint): 封存 RBT Document Editor MCP

<!-- id: sec-data-structures -->
### 1. 核心資料結構 (Core Data Structures)

<!-- id: blk-data-struct-desc, type: paragraph -->
本功能主要涉及檔案系統操作和 git 版本控制，不需要定義新的資料結構

<!-- id: blk-data-struct-list, type: list -->
**資料結構定義**
  - 無新增資料結構

<!-- id: sec-components -->
### 2. 組件規格 (Component Specifications)

<!-- id: blk-components-desc, type: paragraph -->
本藍圖包含三個主要操作組件：Git 標記、代碼清理、文件更新

<!-- id: blk-component-spec-table, type: table -->
| 組件名稱 | 簡介 | 輸入 | 輸出 | 實作 Tasks | 技術驗收標準 |
|---------|------|------|------|-----------|-------------|
| Git Tag 建立與驗證 | 建立包含完整 editor 實作的版本標記並驗證可恢復 | 當前 git 狀態 | tag `v-with-editor` | TASK-001 | tag 存在且可 checkout 恢復完整代碼 |
| Editor 代碼清理 | 刪除 rbt_mcp_server 中所有 editor 相關模組和測試 | 檔案清單 | 清理後的 repo | TASK-002 | editor 相關檔案已刪除，保留功能完整 |
| 文件更新與功能驗證 | 更新 README.md 說明封存情況並驗證保留功能正常 | 封存資訊 | 更新後的 README | TASK-003 | README 包含封存說明，add_document 和 graphiti 功能正常 |

<!-- id: sec-processing-logic -->
### 3. 核心處理邏輯 (Core Processing Logic)

<!-- id: blk-processing-desc, type: paragraph -->
封存流程按照順序執行，確保在清理代碼前已建立完整備份

<!-- id: blk-processing-steps, type: list -->
**處理流程**
  - **步驟 1**: 建立 git tag `v-with-editor` 標記當前版本（包含完整 editor 實作）
  - **步驟 2**: 識別並刪除 editor 相關檔案：
    - `rbt_mcp_server/document_parser.py`
    - `rbt_mcp_server/path_resolver.py`
    - `rbt_mcp_server/tools/` 中所有 editor 工具
    - `tests/tools/` 中所有 editor 測試
    - `tests/test_server.py` 中 editor 相關測試
  - **步驟 3**: **保留**以下重點功能（不刪除）：
    - `rbt_mcp_server/chunking/` - add_document 功能
    - `rbt_mcp_server/graphiti_tools.py` - RAG 功能
  - **步驟 4**: 更新 `rbt_mcp_server/server.py` 移除 editor 工具註冊
  - **步驟 5**: 更新 README.md 加入封存說明區塊
  - **步驟 6**: 驗證 MCP server 能正常啟動，add_document 和 graphiti 功能正常

<!-- id: sec-risks-decisions -->
### 4. 風險、待辦事項與決策 (Risks, Open Questions & Decisions)

<!-- id: blk-adr-table, type: table -->
**設計決策記錄 (ADR)**
| 決策點 | 變更原因 | 最終實作選擇 | 記錄日期 |
|--------|----------|----------|----------|
| 封存方式 | 需要可恢復且不佔用空間 | Git tag + 刪除代碼 | 2025-10-09 |
| Tag 命名 | 需要清楚表達用途 | `v-with-editor` | 2025-10-09 |

<!-- id: blk-risks-list, type: list -->
**風險與待辦**
  - **風險**: 刪除代碼後可能影響其他模組依賴
  - **緩解**: 先檢查 import 依賴，確保只有 server.py 引用 editor
  - **風險**: Git tag 可能被誤刪
  - **緩解**: 在 README 中明確記錄 tag 名稱和用途

<!-- id: sec-task-tracking -->
### 5. Task 拆解與追蹤 (Task Breakdown & Tracking)

<!-- id: blk-task-tracking-table, type: table -->
**實作進度追蹤**
| 組件名稱 | 對應 Tasks | 實作狀態 | 完成度 | 備註 |
|----------|------------|--------|--------|------|
| Git Tag 建立與驗證 | TASK-001 | Done | 100% | Tag v-with-editor 已建立並推送至 remote |
| Editor 代碼清理 | TASK-002 | Done | 100% | 刪除 27 個檔案，9000+ 行代碼 |
| 文件更新與功能驗證 | TASK-003 | Done | 100% | README 已更新，server 啟動驗證通過 |

<!-- id: blk-effort-estimate, type: list -->
**工時估算**
  - **預估總工時**: 1 小時
  - **實際總工時**: 0.9 小時

<!-- id: sec-validation -->
### 6. 實作後驗證與總結 (Post-Implementation Validation)

<!-- id: blk-lessons-learned, type: list -->
**知識沉澱與教訓 (Lessons Learned)**
  - **設計負債與技術債務**:
    - 無新增技術債務
    - 建議：清理 pyproject.toml 中可能不再需要的 editor 相關依賴
  - **低估與過度設計**:
    - 最初未預期 path_resolver、models.py、errors.py 會被保留功能依賴
    - 應在規劃階段先進行完整的依賴分析
  - **可復用模式/組件**:
    - Git tag 封存模式：適用於需要暫時移除但保留恢復能力的功能
    - 依賴保留策略：保留被其他模組依賴的基礎設施（path_resolver, models, errors）
    - 完整性驗證：使用 `python -m module --help` 快速驗證 import 完整性
  - **實作亮點**:
    - 成功刪除 27 個檔案，9000+ 行代碼，顯著降低維護成本
    - Tag v-with-editor 提供完整恢復路徑，風險可控
    - Server 重寫後只保留 5 個 graphiti 工具，API 簡潔清晰
    - README 封存說明完整，包含恢復指令範例
  - **遇到的挑戰與解決方案**:
    - **挑戰**: 刪除 path_resolver 後發現 add_document 依賴它
    - **解決**: 保留 path_resolver.py（chunking 功能需要）
    - **挑戰**: 刪除 models.py 和 errors.py 後出現 import 錯誤
    - **解決**: 恢復這些基礎模組（被 path_resolver 和 graphiti_tools 依賴）
  - **後續建議**:
    - 定期檢查並清理未使用的依賴套件
    - 考慮將 path_resolver 移至 shared/ 或 chunking/ 中，更清楚表達其用途
    - 如未來需要恢復 editor，優先考慮使用原生 Read/Edit/Write 工具而非自建 MCP
