---
id: markdown-writing-guide
group_id: Public
type: Guide
title: Markdown 文件撰寫規範
author: System
update_date: 2025-10-15
---

# Markdown 文件撰寫規範

本文件說明如何撰寫符合 KnowledgeSmith MCP 系統 chunk 處理的 Markdown 文件。

### 文件結構總覽

符合規範的 Markdown 文件包含以下結構（由上到下）：

1. **YAML Front Matter**（可選）：文件元資料
2. **Info Section**（可選）：結構化資訊區塊
3. **主要內容**：使用 h3 (###) 標題進行分段

### YAML Front Matter

Front Matter 是文件開頭的元資料區塊，使用 YAML 格式，由 `---` 包圍。

**格式：**
```markdown
---
id: document-identifier
group_id: project-name
type: Guide
title: 文件標題
author: 作者名稱
update_date: 2025-10-15
---
```

**欄位說明：**
- `id`: 文件唯一識別碼（kebab-case）
- `group_id`: 專案或群組名稱（用於 RAG 分組）
- `type`: 文件類型（Guide, REQ, BP, TASK 等）
- `title`: 文件標題
- `author`: 作者
- `update_date`: 最後更新日期（YYYY-MM-DD）

**注意事項：**
- Front Matter 必須放在文件最開頭
- 所有欄位都是可選的，但建議填寫以利管理
- 日期格式必須是 ISO 8601 格式

### Info Section

Info Section 是緊接在 Front Matter 之後的結構化資訊區塊，使用特殊註解標記。

**格式：**
```markdown
<!-- info-section -->
> status: active
> priority: high
> tags: [documentation, guide]
> version: 1.0.0
```

**特性：**
- 以 `<!-- info-section -->` 註解開頭
- 每行以 `> ` 開頭（大於符號 + 空格）
- 內容為 YAML 格式的 key-value pairs
- Info Section 會被抽取為獨立 chunk，metadata 中會包含 `info` 欄位

**使用時機：**
- 需要結構化的文件狀態資訊
- 需要在 RAG 中快速過濾的欄位
- 與內容本身無關但對文件管理重要的資訊

### 主要內容分段

使用 h3 標題 (`###`) 作為主要分段單位。每個 h3 section 會成為一個獨立的 chunk。

**格式：**
```markdown
### 章節標題

章節內容...

### 另一個章節

更多內容...
```

**重要規則：**
1. **必須使用 h3 (`###`)**：h1、h2、h4 等不會觸發分段
2. **標題命名**：清晰、具描述性，避免特殊符號（會被轉為 slug）
3. **內容完整性**：每個 section 應該是自包含的邏輯單元
4. **分段粒度**：建議每個 section 長度適中（200-1000 字）

**標題 Slug 轉換規則：**
- 轉為小寫
- 空格和底線轉為連字號 `-`
- 移除特殊符號
- 保留 Unicode 字元（中文等）
- 範例：
  - `Hello World!` → `hello-world`
  - `API Reference: v2.0` → `api-reference-v20`
  - `任務目標與前置` → `任務目標與前置`

### 無 h3 分段的文件

如果文件沒有任何 h3 標題，整份文件會被視為單一 chunk。

**適用場景：**
- 簡短的說明文件
- 單一主題的筆記
- 不需要細分的內容

### Chunk ID 生成規則

系統會為每個 chunk 自動生成穩定的 ID：

**格式：**
```
{project_id}+{feature_id|general}+{section_slug}
```

**範例：**
- 有 feature_id：`knowledge-smith+graphiti-chunk+introduction`
- 無 feature_id：`knowledge-smith+general+overview`
- Info section：`knowledge-smith+my-feature+info`
- 無 h3 文件：`knowledge-smith+general+document`

**特性：**
- 同樣的標題在相同專案/功能下會產生相同 ID
- 保證跨次處理的穩定性
- 方便追蹤 chunk 的變更

### 完整範例

```markdown
---
id: example-guide
group_id: knowledge-smith
type: Guide
title: 範例指南
author: System
update_date: 2025-10-15
---

<!-- info-section -->
> status: draft
> priority: medium
> version: 0.1.0

### 簡介

這是一個符合規範的 Markdown 文件範例。

本文件展示如何正確使用 h3 標題來分段內容。

### 安裝步驟

1. 下載套件
2. 執行安裝腳本
3. 驗證安裝

### 使用說明

詳細的使用方法說明...

### 疑難排解

常見問題與解決方案...
```

**此範例會產生 5 個 chunks：**
1. Info section chunk
2. 簡介 chunk
3. 安裝步驟 chunk
4. 使用說明 chunk
5. 疑難排解 chunk

### 最佳實踐

**DO：建議做法**
- 使用有意義的 h3 標題
- 保持 section 長度適中
- Front Matter 填寫完整資訊
- Info Section 用於結構化 metadata
- 每個 section 內容自包含

**DON'T：避免做法**
- 不要使用 h1/h2/h4 作為主要分段
- 不要在標題中使用過多特殊符號
- 不要讓 section 過長或過短
- 不要在 Info Section 放內容文字
- 不要省略重要的 metadata

### 文件類型建議

**RBT 文件（REQ/BP/TASK）：**
- 必須包含 Front Matter
- 建議使用 Info Section 記錄狀態
- 使用 h3 按需求/設計/任務分段

**一般指南文件：**
- 建議包含 Front Matter
- 使用 h3 按主題分段
- Info Section 可選

**筆記/TODO：**
- Front Matter 可選
- 可以不使用 h3（單一 chunk）
- Info Section 通常不需要

### 驗證與測試

撰寫完文件後，建議：

1. 確認 YAML Front Matter 格式正確
2. 確認 Info Section 格式正確（如有）
3. 確認使用了 h3 標題
4. 預覽 chunk 切分是否符合預期
5. 使用 `add_document` 工具同步到 RAG

### 相關工具

- `add_document`: 同步文件到 RAG
- `search_memory_facts`: 搜尋已同步的 chunks
- `search_memory_nodes`: 搜尋節點關係
