# 系統代理人最高指導原則

> **[重要指示]** 以下為系統最高級別之行動與資料標準，請嚴格遵守約束條件。

## 1. Core Rules (核心守則)
- 先講結論再講原因，異動前先說明根因。
- 以繁體中文回覆，絕不處理範圍外工作。

## 2. Action Rules (行動守則)
- **腳本觸發條件**：高頻、大量或 OS 層異動優先建立腳本；簡單讀寫直接執行。
- **語言優先級**：優先使用 Node.js，其次為 Python。
- **腳本格式**：腳本用途與使用方式強制置於頂部。

## 3. Engineering Workflow (工程工作流)

### 3.1 Principles (開發原則)
- 先讀檔再修改。
- 業務邏輯處理講求 Top-Down 由大至小的分層抓解，並做拆解點的必要說明。
- 先做最小修復再考慮重構，修畢必列風險點。
- Contract First Development.
- Must have Happy Path Test.

### 3.2 Clean Code (整潔程式碼)
- 可讀性優先於技巧性。
- 命名需表達業務意圖與語意，禁用模糊縮寫。
- 直白流程優先，僅於重複、變動點或隔離風險明確時進行抽象化。

## 4. Workflow Contract (工作流契約)
- **生命週期**：嚴格遵循 `create` -> `plan` -> `implement` 階段。
- **執行觸發**：預設等待人工確認；明確要求「直接執行」方可自動推進。
- **條件式階段**：
  - **Validation**：若任務要求驗證，需於 implement 後執行。
  - **Feedback**：遇卡關且具通用價值時啟動，處理完畢整理回對應 topic。

### 4.1 Issue Layout (任務目錄結構)
所有任務需放置於基礎路徑 `ai-doc/issues/{no}/` 下，包含以下產出物：
- `issue.md`：create 階段使用。
- `plan.yaml`：plan 階段使用。
- `impl.md`：implement 階段使用 (含執行中之暫時觀察)。
- `backlog.yaml`：本次不處理之追蹤事項。

## 4.2 Telemetry Contract (數據回報契約)
- **日誌隔離原則**：任務結束（無論成功或失敗）或推進至 `implement` 最終階段時，Agent **嚴禁**直接修改 Topic 檔案本體，必須將本次引用Topic成效獨立輸出至專屬度量目錄。
- **輸出路徑**：`ai-doc/metrics/raw/issue_{no}.yaml`
- **強制輸出 schema**：必須使用標準 YAML 格式，結構如下：
  ```yaml
  issue_no: {no}
  timestamp: "YYYY-MM-DDTHH:mm:ssZ"
  final_status: "success" # 可選值: success (驗證通過) | failed (卡關/出錯)
  tracked_topics:
    - topic_name: "topic_writing_rule"
      retrieved: true  # 是否有被檢索載入 context
      selected: true   # 是否有實質採用其規則
      execution_result: "passed" # 可選值: passed | violated | unverified
  ```

## 5. Global Data Standards (全局資料標準)
- **[YAML 1.2 Spec]**：處理所有資料結構僅允許標準 Parser 讀寫；執行檔案操作前強制進行路徑拼接 (base_path + 相對路徑)。
- **[Dense Markdown]**：Logs、清單、高濃度資訊優先採用緊密格式；內聯 code、多連結一行呈現；禁用於需詳細說明之文件。
- **[DRY 原則]**：強制提取公因式，同質邏輯與路徑前綴必須收斂集中，嚴禁跨節點重複。
- **[SoC 原則]**：嚴格區分結構與文本。YAML 類檔案僅收錄索引、路由、限制與設定；業務長文、Logs、未驗證觀察強制隔離寫入 Markdown。
- **[Snake_case]**：所有 YAML/JSON 等結構化檔案的鍵名 (Key) 強制使用小寫英文與底線。

## 6. System Memory Management (系統記憶體管理)
- **Active Memory**：入口為 `ai-doc/MEMORY.md`。
- **Topic Files**：承接單一主題重用細節；僅允許寫入具 codebase/文件/測試支撐之已驗證規則。
- **History Files**：僅作 traceability 來源，嚴禁作為正式知識入口。
- **[Topic 價值評估機制]**：系統以「實質轉換率 (CVR)」及「時間衰減」作為 Topic 檢索權重基準，由背景服務統一聚合 → 見 4.2 Telemetry Contract。
