# Topic: Writing Rule

## 結論

topic 用來承接單一主題、可重複使用的正式知識，不用來存放 issue 執行中的暫時觀察或未驗證推論。

## Scope Rule

- 一份 topic 只承接單一主題
- 只保留正式知識入口、workflow anchor 與已驗證規則
- issue 執行中的暫時觀察，不可直接寫入 topic
- 歷史文件只能作 traceability 來源，不是正式知識入口

## Recommended Structure

- `Summary`：何時使用、主要用途
- `Core Intent`：任務目的、讀者、預期輸出
- `Thinking Path`：固定判讀順序
- `Negative Constraints`：不可提前做、不可推論的事
- `Workflow`：實際執行步驟
- `Output Contract`：回覆時至少交代哪些資訊
- `Rules`：主題特有、需反覆套用的明確規則
- `Key Files`：常用關鍵路徑
- `Known Issues`：已知限制

## Evidence Rule

- 只有 codebase、正式文件、測試結果或實際輸出可作為 topic 內容依據
- 無法從 repo 直接確認的內容，不可寫成已驗證事實

## Writing Rule

- 先講結論，再講原因
- 用可重複套用的規則描述，不寫一次性 issue 筆記
- 可引用路徑、檔名與輸出契約，避免抽象口號

## Anti-Patterns

- 把 issue 的暫時觀察直接寫進 topic
- 在 create 階段提前定義 plan / implement 才會處理的內容
- 只寫原則標語，不寫輸入、輸出、邊界與判讀順序
