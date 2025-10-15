---
id: BP-ios-notification-image
group_id: ai-magic-editor
type: Blueprint
feature: ios-notification-image
requirement: REQ-ios-notification-image
---

<!-- info-section -->
> status: Implemented
> update_date: 2025-10-01
> implementation_date: 2025-10-01
> summary_context: iOS Notification Service Extension 的技術架構，定義圖片下載、附加流程和組件設計。已完成實作並通過所有實機測試驗證。

<!-- id: sec-root -->
# 專案藍圖 (Blueprint): iOS Push Notification 圖片顯示

<!-- id: sec-core-data-structures -->
### 1. 核心資料結構 (Core Data Structures)

[SUMMARY: 定義圖片下載ＲＢＴ和通知處理所需的核心資料結構。]

<!-- id: blk-ds-imageinfo, type: code -->
**NotificationImageInfo**
```
struct NotificationImageInfo {
    let imageUrl: URL          // 圖片 URL
    let contentType: String?   // MIME type (可選)
}
```

<!-- id: blk-ds-result, type: code -->
**DownloadResult**
```
enum DownloadResult {
    case success(URL)  // 本地暫存檔案 URL
    case failure       // 下載失敗（含 timeout）
}
```

<!-- id: sec-component-specs -->
### 2. 組件規格 (Component Specifications)

[SUMMARY: 定義實現 Notification Service Extension 所需的三大核心組件。]

<!-- id: sec-spec-notificationservice -->
#### NotificationService (Extension 主體)

<!-- id: blk-ns-intro, type: list -->
**簡介**
  - Notification Service Extension 的主要類別，繼承 `UNNotificationServiceExtension`

<!-- id: blk-ns-duty, type: list -->
**職責**
  - 接收系統調用 `didReceive(_:withContentHandler:)`
  - 解析 FCM payload 取得圖片 URL
  - 協調 Downloader 和 Modifier 完成圖片附加
  - 處理 30 秒系統超時

<!-- id: blk-ns-input, type: list -->
**輸入**
  - `request: UNNotificationRequest` (通知請求)
  - `contentHandler: (UNNotificationContent) -> Void` (完成回調)

<!-- id: blk-ns-output, type: list -->
**輸出**
  - 修改後的 `UNNotificationContent`（含圖片附件或原始內容）

<!-- id: blk-ns-tasks, type: list -->
**實作 Tasks**
  - `TASK-001-notification-service`

<!-- id: blk-ns-acceptance, type: list -->
**技術驗收標準**
  - 成功解析 FCM payload 中的圖片 URL
  - 正確協調 Downloader 和 Modifier
  - 下載/附加失敗時退回原始通知
  - 處理 `serviceExtensionTimeWillExpire()` 超時情況

<!-- id: sec-spec-downloader -->
#### NotificationImageDownloader (圖片下載器)

<!-- id: blk-dl-intro, type: list -->
**簡介**
  - 負責從 HTTPS URL 下載圖片到本地暫存

<!-- id: blk-dl-duty, type: list -->
**職責**
  - 使用 `URLSession.shared.downloadTask` 下載圖片
  - 設定 5 秒 timeout
  - 驗證 URL 為 HTTPS
  - 錯誤處理與日誌記錄

<!-- id: blk-dl-input, type: list -->
**輸入**
  - `imageUrl: URL` (圖片 URL)
  - `timeout: TimeInterval` (預設 5 秒)

<!-- id: blk-dl-output, type: list -->
**輸出**
  - 成功: 本地暫存檔案 `URL`
  - 失敗: `nil`（並記錄 log）

<!-- id: blk-dl-tasks, type: list -->
**實作 Tasks**
  - `TASK-002-image-downloader`

<!-- id: blk-dl-acceptance, type: list -->
**技術驗收標準**
  - 只接受 HTTPS URL（HTTP 拒絕）
  - 5 秒 timeout 正確觸發
  - 下載成功返回有效的本地檔案 URL
  - 失敗時正確記錄錯誤日誌

<!-- id: sec-spec-modifier -->
#### NotificationContentModifier (通知內容修改器)

<!-- id: blk-mod-intro, type: list -->
**簡介**
  - 負責建立 `UNNotificationAttachment` 並附加到通知內容

<!-- id: blk-mod-duty, type: list -->
**職責**
  - 從本地檔案 URL 建立 `UNNotificationAttachment`
  - 附加到 `UNMutableNotificationContent.attachments`
  - 錯誤處理與日誌記錄

<!-- id: blk-mod-input, type: list -->
**輸入**
  - `content: UNMutableNotificationContent` (可修改的通知內容)
  - `imageFileUrl: URL` (本地圖片檔案 URL)

<!-- id: blk-mod-output, type: list -->
**輸出**
  - 成功: 附加圖片後的 `UNMutableNotificationContent`
  - 失敗: 原始 `content`（並記錄 log）

<!-- id: blk-mod-tasks, type: list -->
**實作 Tasks**
  - `TASK-003-content-modifier`

<!-- id: blk-mod-acceptance, type: list -->
**技術驗收標準**
  - 成功建立 `UNNotificationAttachment`
  - 正確附加到 `content.attachments`
  - 附加失敗時不影響原始 content
  - 失敗時正確記錄錯誤日誌

<!-- id: sec-core-logic -->
### 3. 核心處理邏輯 (Core Processing Logic)

[SUMMARY: 詳細描述從收到通知到顯示圖片的完整處理流程。]

<!-- id: sec-logic-mainflow -->
#### 主流程 (NotificationService)

<!-- id: blk-mf-step1, type: code -->
**階段 1: 接收通知**
```
iOS 系統收到 FCM 推播
  ↓
檢查 payload 是否含 mutable-content: 1
  ↓
系統啟動 NotificationService Extension
  ↓
調用 didReceive(_:withContentHandler:)
```

<!-- id: blk-mf-step2, type: code -->
**階段 2: 解析 Payload**
```
取得 request.content.userInfo
  ↓
優先解析: userInfo["fcm_options"]["image"] (iOS 專用)
  ↓
備用解析: userInfo["notification"]["image"] (通用)
  ↓
驗證 URL 格式 (必須是 HTTPS)
```

<!-- id: blk-mf-step2-note, type: list -->
**⚠️ 待確認**
  - FCM payload 的實際欄位名稱（待後端提供實際格式）

<!-- id: blk-mf-step3, type: code -->
**階段 3: 下載圖片**
```
有效的圖片 URL？
  ├─ NO  → 跳到階段 5（回傳原始內容）
  └─ YES → 調用 NotificationImageDownloader.download(imageUrl)
             ↓
           URLSession.downloadTask (5秒 timeout)
             ↓
           成功？
             ├─ NO  → 跳到階段 5（回傳原始內容 + log）
             └─ YES → 繼續階段 4
```

<!-- id: blk-mf-step4, type: code -->
**階段 4: 附加圖片**
```
NotificationContentModifier.attach(imageFileUrl, to: content)
  ↓
建立 UNNotificationAttachment
  ↓
成功？
  ├─ NO  → 跳到階段 5（回傳原始內容 + log）
  └─ YES → content.attachments.append(attachment)
```

<!-- id: blk-mf-step5, type: code -->
**階段 5: 回傳結果**
```
調用 contentHandler(modifiedContent)
  ↓
iOS 系統顯示通知
  ↓
有圖片附件 → Rich Notification（可展開查看圖片）
無圖片附件 → 純文字通知
```

<!-- id: sec-logic-timeout -->
#### 超時處理

<!-- id: blk-to-flow, type: code -->
```
30 秒內未完成（系統限制）
  ↓
iOS 調用 serviceExtensionTimeWillExpire()
  ↓
立即回傳當前的 bestAttemptContent
  ↓
即使圖片未下載完成，也顯示通知（不阻斷用戶）
```

<!-- id: sec-tech-details -->
### 4. 技術架構細節

<!-- id: sec-td-files -->
#### 檔案結構

<!-- id: blk-td-files-code, type: code -->
```
MagicEditor/
└── Sources/
    └── Extensions/
        └── NotificationService/
            ├── NotificationService.swift          // 主體 (TASK-001)
            ├── NotificationImageDownloader.swift  // 下載器 (TASK-002)
            └── NotificationContentModifier.swift  // 修改器 (TASK-003)
```

<!-- id: sec-td-tuist -->
#### Tuist 專案配置

<!-- id: blk-td-tuist-list, type: list -->
  - 新增 `NotificationServiceExtension` target
  - Bundle ID: `{PRODUCT_BUNDLE_IDENTIFIER}.NotificationServiceExtension`
  - Deployment Target: iOS 14.0+
  - 依賴: Foundation, UserNotifications
  - Info.plist 配置: `NSExtension` 相關設定
  - App Groups 共享（未來可能需要）

<!-- id: blk-td-tuist-tasks, type: list -->
**實作 Tasks**
  - `TASK-004-tuist-configuration`

<!-- id: sec-td-formats -->
#### 圖片格式支援

<!-- id: blk-td-formats-list, type: list -->
  - PNG (.png)
  - JPEG (.jpg, .jpeg)
  - GIF (.gif)
  - 其他格式由 `UNNotificationAttachment` 自動判斷

<!-- id: sec-td-security -->
#### 安全性考量

<!-- id: blk-td-security-list, type: list -->
  - **只接受 HTTPS URL**（HTTP 拒絕）
  - **驗證 Content-Type**（僅接受 image/* MIME types）
  - **自動清理暫存檔案**（系統管理）

<!-- id: sec-risks -->
### 5. 風險、待辦事項與決策 (Risks, Open Questions & Decisions)

<!-- id: sec-risks-adr -->
#### 設計決策記錄 (ADR)

<!-- id: blk-risks-adr-table, type: table -->
| 決策點 | 變更原因 | 最終實作選擇 | 記錄日期 |
|--------|----------|----------|----------|
| 組件拆分策略 | 未來擴充性（按鈕、自訂 UI） | 拆分為 3 個獨立檔案 | 2025-09-30 |
| 圖片下載工具 | Extension 輕量化，不依賴第三方 | 原生 URLSession | 2025-09-30 |
| 錯誤處理方式 | 不阻斷通知顯示 | 失敗退回純文字 + log | 2025-09-30 |
| Timeout 時間 | 平衡速度與成功率 | 5 秒（系統總限制 30 秒） | 2025-09-30 |
| 前景通知處理 | 降低複雜度 | 不處理（保持現有行為） | 2025-09-30 |
| Completion Flag | 防止雙重回調風險 | 新增 isCompleted flag 和統一完成方法 | 2025-10-01 |
| Content-Type 驗證 | 安全性與相容性平衡 | 驗證 image/* MIME type（寬鬆策略） | 2025-10-01 |

<!-- id: sec-risks-tech -->
#### 技術風險

<!-- id: blk-risks-tech-1, type: list -->
  - 1. **FCM Payload 格式不確定** (優先級: 高)
  - * 風險: 解析欄位錯誤導致無法取得圖片 URL
  - * 緩解: 待後端確認實際格式後更新程式碼
  - * 備用方案: 同時嘗試多個可能的欄位名稱

<!-- id: blk-risks-tech-2, type: list -->
  - 2. **圖片下載速度不穩定** (優先級: 中)
  - * 風險: 網路不佳時 5 秒 timeout 不足
  - * 緩解: 可調整 timeout 參數，或後端提供縮圖
  - * 備用方案: 使用者仍收到純文字通知

<!-- id: blk-risks-tech-3, type: list -->
  - 3. **30 秒系統超時** (優先級: 低)
  - * 風險: 極慢網路可能觸發系統超時
  - * 緩解: 5 秒下載 timeout 保留足夠緩衝
  - * 備用方案: serviceExtensionTimeWillExpire 處理

<!-- id: sec-risks-open -->
#### 待辦事項 (Open Questions)

<!-- id: blk-risks-open-list, type: list -->
  - [ ] **FCM Payload 格式確認**: 等待後端提供實際的 payload JSON 範例
  - [ ] **後端 mutable-content 設定**: 確認後端已在 FCM 發送時設定此欄位
  - [ ] **測試推播工具**: 準備測試用的圖片 URL 和推播發送方式
  - [ ] **App Groups 配置**: 如果需要與主 App 共享資料（未來擴充）

<!-- id: sec-integration -->
### 6. 與現有架構的整合

<!-- id: sec-int-fcm -->
#### 現有 FCM 整合點

<!-- id: blk-int-fcm-appdelegate, type: list -->
**AppDelegate (不需修改)**
  - `Messaging.messaging().delegate = self` 已設定
  - `didReceiveRegistrationToken` 已處理 token 更新
  - `UNUserNotificationCenter.delegate = self` 已設定

<!-- id: blk-int-fcm-manager, type: list -->
**MessagingManager (不需修改)**
  - Token 管理已完善
  - Extension 不直接與此互動

<!-- id: blk-int-fcm-foreground, type: list -->
**前景通知處理 (不修改)**
  - `willPresent` 保持現有邏輯
  - 繼續顯示 `.banner, .sound, .badge`

<!-- id: sec-int-backend -->
#### 後端 API 依賴

<!-- id: blk-int-backend-api, type: list -->
**push-notification-api**
  - 需確認 `REQ-push-notification-api` 是否已包含圖片支援
  - 需確認後端發送 FCM 時的 payload 格式
  - 需確認 `mutable-content: 1` 是否已設定

<!-- id: sec-task-breakdown -->
### Task 拆解與追蹤 (Post Task Breakdown & Tracking)

<!-- id: sec-tb-overview -->
#### Task 概覽

<!-- id: blk-tb-overview-table, type: table -->
| Task ID | 標題 | 預估工時 | 依賴 | 優先級 |
|---------|------|---------|------|--------|
| TASK-001 | NotificationService 主體實作 | 1.5h | - | 高 |
| TASK-002 | NotificationImageDownloader 實作 | 1h | - | 高 |
| TASK-003 | NotificationContentModifier 實作 | 1h | - | 高 |
| TASK-004 | Tuist 專案配置 | 2h | TASK-001, TASK-002, TASK-003 | 高 |
| TASK-005 | 整合測試與除錯 | 1.5h | TASK-004 | 中 |

<!-- id: blk-tb-overview-total, type: list -->
**預估總工時**
  - 7 小時

<!-- id: sec-tb-tracking -->
#### 實作進度追蹤

<!-- id: blk-tb-tracking-table, type: table -->
| 組件名稱 | 對應 Tasks | 實作狀態 | 完成度 | 備註 |
|----------|------------|--------|--------|------|
| NotificationImageDownloader | TASK-002 | Done | 100% | 已實作完成 |
| NotificationContentModifier | TASK-003 | Done | 100% | 已實作完成 |
| NotificationService | TASK-001 | Done | 100% | 已實作完成（123 行）|
| Tuist 專案配置 | TASK-004 | Done | 100% | 已完成，Extension target 配置成功並編譯通過 |
| 整合測試 | TASK-005 | Done | 100% | 已完成實機測試，所有測試項目通過（2025-10-01）|

---

<!-- id: sec-post-validation -->
### 實作後驗證與總結 (Post-Implementation Validation & Summary)

<!-- id: sec-pv-completion -->
#### 實作完成度

<!-- id: blk-pv-completion-code, type: list -->
**程式碼實作: 100% ✅**
  - NotificationImageDownloader (105 lines)
  - NotificationContentModifier (47 lines)
  - NotificationService (123 lines)
  - Tuist 專案配置完成
  - Bundle ID: `com.cardinalblue.magiceditor.notificationserviceextension`

<!-- id: blk-pv-completion-test, type: list -->
**整合測試: 50% 🔄**
  - 測試計畫已完成
  - 等待 Apple Developer Portal 配置
  - 需實機測試環境

<!-- id: blk-pv-completion-total, type: list -->
**總進度: 90%**
  - （程式碼完成，待實機驗證）

<!-- id: sec-pv-acceptance -->
#### 技術驗收

<!-- id: sec-pv-acceptance-done -->
##### 已驗收項目 ✅

<!-- id: blk-pv-acceptance-done-list, type: list -->
  - ✅ NotificationService 成功解析 FCM payload（支援雙格式）
  - ✅ NotificationImageDownloader 正確協調 Downloader 和 Modifier
  - ✅ HTTPS-only URL 驗證機制
  - ✅ 5 秒 timeout 設定
  - ✅ 失敗降級機制（退回純文字通知）
  - ✅ 30 秒系統超時處理
  - ✅ Extension target 成功編譯
  - ✅ 所有程式碼包含追溯註解

<!-- id: sec-pv-acceptance-pending -->
##### 待驗收項目 ⏳

<!-- id: blk-pv-acceptance-pending-list, type: list -->
  - ⏳ 實機推播圖片顯示測試
  - ⏳ PNG/JPG/GIF 格式支援驗證
  - ⏳ 錯誤場景實機測試（HTTP URL, 404, 超時）
  - ⏳ 前景行為驗證
  - ⏳ FCM payload 實際格式確認（待後端提供）

<!-- id: sec-pv-lessons -->
#### 知識沉澱與教訓 (Lessons Learned)

<!-- id: sec-pv-lessons-debts -->
##### 設計負債與技術債務

<!-- id: blk-pv-lessons-debts-list, type: list -->
  - **FCM Payload 格式待確認**: 當前使用假設格式實作，需後端提供實際 payload 範例
  - **日誌機制**: 使用 print 而非 os_log，未來可統一改為結構化日誌
  - **Timeout 值硬編碼**: 5 秒 timeout 寫死在程式碼中，未來可考慮可配置

<!-- id: sec-pv-lessons-design -->
##### 低估與過度設計

<!-- id: blk-pv-lessons-design-list, type: list -->
  - **Bundle ID 格式**: 初期使用動態變數，後改為硬編碼（實際問題較預期簡單）
  - **拆分設計正確**: 三個組件（Downloader, Modifier, Service）拆分得宜，利於測試和維護
  - **無過度設計**: 實作保持簡潔，未引入不必要的複雜度

<!-- id: sec-pv-lessons-reusable -->
##### 可復用模式/組件

<!-- id: blk-pv-lessons-reusable-1, type: list -->
**Notification Service Extension 架構模式**
  - 組件拆分: Downloader → Modifier → Service
  - 錯誤處理: 失敗降級機制
  - 超時管理: 雙層 timeout（5s 下載 + 30s 系統）

<!-- id: blk-pv-lessons-reusable-2, type: list -->
**URLSession 下載處理模式**
  - HTTPS-only 驗證
  - Timeout 控制
  - 檔案暫存管理

<!-- id: blk-pv-lessons-reusable-3, type: list -->
**UNNotificationAttachment 建立模式**
  - do-catch 錯誤處理
  - 優雅降級

<!-- id: sec-pv-suggestions -->
#### 後續建議

<!-- id: sec-pv-suggestions-immediate -->
##### 立即行動（實機測試前）

<!-- id: blk-pv-suggestions-immediate-1, type: list -->
**Apple Developer Portal 配置**
  - 建立 App ID: `com.cardinalblue.magiceditor.notificationserviceextension`
  - 啟用 Push Notifications capability
  - 建立 Development Provisioning Profile

<!-- id: blk-pv-suggestions-immediate-2, type: list -->
**後端協調**
  - 確認 FCM payload 實際格式
  - 確認後端發送時已設定 `mutable-content: 1`
  - 提供測試用圖片 URL

<!-- id: sec-pv-suggestions-testing -->
##### 實機測試階段 ✅

<!-- id: blk-pv-suggestions-testing-list, type: list -->
  - ✅ 安裝 App 到測試設備
  - ✅ 執行完整測試套件（正常 + 錯誤場景）
  - ✅ 記錄測試結果和截圖
  - ✅ 更新 TASK-005 測試覆蓋清單

<!-- id: blk-pv-suggestions-results, type: list -->
**測試結果 (2025-10-01)**
  - ✅ 實機推播圖片顯示測試通過
  - ✅ PNG/JPG/GIF 格式支援驗證通過
  - ✅ 錯誤場景實機測試通過（HTTP URL, 404, 超時）
  - ✅ 前景/背景行為驗證通過
  - ✅ FCM payload 實際格式確認通過

<!-- id: sec-pv-suggestions-future -->
##### 未來擴充建議

<!-- id: blk-pv-suggestions-future-list, type: list -->
  - **App Groups 支援**: 如需與主 App 共享圖片快取
  - **通知 Action 按鈕**: 自訂操作按鈕
  - **圖片大小驗證**: 防止下載過大檔案
  - **進階日誌**: 整合 Firebase Analytics 或 Crashlytics

<!-- id: sec-pv-summary -->
#### 開發效率總結

<!-- id: blk-pv-summary-hours, type: list -->
**預估工時**
  - 7 小時

<!-- id: blk-pv-summary-actual, type: list -->
**實際工時**
  - ~3 小時（程式碼實作 + 實機測試 + bug 修復）

<!-- id: blk-pv-summary-reasons, type: list -->
**效率提升原因**
  - Task 拆分清晰，無相依阻塞
  - 使用 task-coding-agent 並行執行 TASK-001~003
  - Tuist 配置已預先準備
  - SwiftLint 自動修正節省時間

<!-- id: blk-pv-summary-factors, type: list -->
**關鍵成功因素**
  - Blueprint 設計完整，減少返工
  - 組件拆分得宜，易於實作
  - 追溯註解完整，便於未來維護
  - 實機測試發現並修復 URL-encoded 路徑問題

<!-- id: blk-pv-summary-timeline, type: list -->
**實作完成時間線**
  - 2025-09-30: 完成 TASK-001~004 程式碼實作
  - 2025-10-01: 完成 TASK-005 實機測試與驗證
  - 2025-10-01: 修復檔名解析 bug 並移除 debug logs

<!-- id: sec-pv-deploy -->
#### 生產環境部署狀態 ✅

<!-- id: blk-pv-deploy-prs, type: list -->
**Pull Requests**
  - PR #377: iOS NotificationServiceExtension → `dev` branch
  - PR #378: Backend Push Notification System → `dev` branch

<!-- id: blk-pv-deploy-checklist, type: list -->
**部署檢查清單**
  - ✅ 程式碼實作完成
  - ✅ 所有測試通過
  - ✅ SwiftLint 驗證通過
  - ✅ Apple Developer Portal 配置完成
  - ✅ Provisioning Profiles 建立完成
  - ✅ 實機測試驗證完成
  - ✅ 文檔更新完成

<!-- id: blk-pv-deploy-final, type: paragraph -->
**功能已達到生產環境標準，可以準備上線。**