# AGENTS.md

## CORE RULE

- 先講結論，再講原因
- 異動前先說根因
- 以繁體中文回覆
- 絕不處理範圍外工作

## ACTION RULE

- 異動前判斷是否為高頻或大量異動，是的話優先建立腳本處理，否則直接執行
- 腳本語言優先順序為 Node.js，其次才是 Python
- 腳本用途與使用方式應置於腳本上方
- OS 層異動優先落成腳本後再執行
- 簡單的讀取、查詢與小型更新可直接執行

## ENGINEERING WORKFLOW

- 先讀相關檔案，再修改
- 先做最小修復，再考慮重構
- 修完要列出風險點
- Contract First Development
- Must have Happy Path Test

## CLEAN CODE

- 核心理念：程式應先讓下一位維護者容易理解，再追求技巧性寫法
- 命名要表達業務意圖與資料語意，不用模糊縮寫或只描述型別的名稱
- 先用直白流程解決問題；只有在重複、變動點或隔離風險明確時才抽象化

## WORKFLOW CONTRACT

- 需求（issue）處理依 `create -> plan -> implement` 按步執行
- issue 開立後預設等待人工確認後才執行；除非使用者明確要求「直接執行」
- 若任務明確要求驗證，`validation` 為 `implement` 後的條件式階段
- 處理很卡且未來同類任務都需要知道時，需啟動 feedback 並整理回對應 topic

### Issue Layout

- 每張 issue 使用單一目錄：`ai-doc/issues/{no}/`
- `issue.md`：create 階段
- `plan.md`：plan 階段
- `impl.md`：implement 階段
- `backlog.md`：本次不處理但需追蹤的事項

### Memory Write Rules

- 僅可把有 codebase、文件、測試或實際輸出支撐的內容寫入記憶系統
- issue 執行中的暫時觀察，先寫在對應 `impl.md`
- 只有已驗證的規則可回寫 topic

## GUIDE

- `ai-doc/MEMORY.md` 是 active memory 索引入口
- topic files 承接單一主題、可重複使用的細節
- 歷史文件只可作 traceability 來源，不是正式知識入口
