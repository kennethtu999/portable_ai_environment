# Portable AI Terminal — macOS 使用指南

## 目錄結構

將 `ai-env/` 建立在你的專案資料夾內：

```
my-project/              ← 你的工作目錄（Claude 在此運作）
└── ai-env/              ← AI 環境
    ├── init.sh          ← 首次執行：建置環境
    └── cc.sh            ← 日常使用：啟動 Claude
```

---

## 安裝步驟

**前置條件：** [Homebrew](https://brew.sh)（選用，git / ripgrep / jq 透過 brew 安裝）

### 1. 進入你的專案資料夾

```bash
cd my-project
```

### 2. 建立 ai-env 資料夾、下載並解壓環境

```bash
mkdir ai-env && cd ai-env
curl -L -o env.zip https://github.com/kennethtu999/portable_ai_environment/releases/latest/download/portable_claude_env_mac.zip
tar -xf env.zip && cd ..
```

### 3. 首次執行（建置環境）

```bash
ai-env/init.sh
```

`init.sh` 會自動完成：

| 步驟 | 說明 |
|------|------|
| 偵測 Python | 使用系統 python3，不足時 brew 安裝 |
| 偵測 Node.js | 使用系統 node，不存在時下載 portable 版 |
| 安裝工具 | git / ripgrep / jq 透過 brew 安裝（若未安裝） |
| 環境建置 | 建立 Python venv、安裝套件 |
| API 設定 | 輸入連線方式與金鑰，儲存至本機（下次不再詢問） |
| 連線驗證 | 確認 Claude API 可用 |
| 安裝 Claude CLI | 安裝至 `ai-env/tools/npm-global/`（不影響系統） |

### 4. 日常使用

從專案資料夾執行：

```bash
ai-env/cc.sh
```

Claude 的工作目錄即為你的專案資料夾。

---

## 工具來源

| 工具 | 優先 | 備援 |
|------|------|------|
| Python | 系統 python3 ≥ 3.8 | `brew install python3` |
| Node.js | 系統 node | 下載 portable（自動偵測 arm64 / x64）|
| git | 系統 git | `brew install git` |
| rg | 系統 rg | `brew install ripgrep` |
| jq | 系統 jq | `brew install jq` |
| claude | `ai-env/tools/npm-global/` | 首次執行 `cc.sh` 時自動安裝 |

---

## 連線方式

首次 `init.sh` 執行時選擇：

```
1. 透過本地代理連線（建議）
2. 直接連線
```

設定儲存於 `~/.portable_ai_environment/claude.env`，下次略過。

---

## 常見問題

**Q：想切換連線方式**
→ 刪除 `~/.portable_ai_environment/claude.env`，重新執行 `ai-env/init.sh`。

**Q：想升級 Node.js 版本**
→ 修改 `ai-env/init.sh` 頂端 `NODE_VERSION`，重新執行即可。
