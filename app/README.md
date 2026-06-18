# Portable AI Terminal — 使用指南

## 目錄結構

將 `ai-env\` 建立在你的專案資料夾內：

```
my-project\              ← 你的工作目錄（Claude 在此運作）
└── ai-env\              ← AI 環境（本說明的操作範圍）
    ├── init.bat         ← 首次執行：建置環境
    └── cc.bat           ← 日常使用：開啟 AI terminal
```

---

## 安裝步驟

### 1. 進入你的專案資料夾

```cmd
cd my-project
```

### 2. 建立 ai-env 資料夾、下載並解壓環境

```cmd
mkdir ai-env
cd ai-env
curl -L -o env.zip https://github.com/<repo>/releases/latest/download/portable_claude_env.zip
tar -xf env.zip
cd ..
```

### 3. 首次執行（建置環境）

從專案資料夾執行：

```cmd
ai-env\init.bat
```

`init.bat` 會自動完成：

| 步驟 | 說明 |
|------|------|
| 下載工具 | 自動下載 Python、Node.js、Git、ripgrep、jq |
| 環境建置 | 建立 Python venv、安裝套件、文件轉換健康檢查 |
| API 設定 | 輸入連線方式與金鑰，儲存至本機（下次不再詢問） |
| 連線驗證 | 確認 Claude API 可用、安裝 Claude CLI |

首次執行完成後，`ai-env\` 內會自動建立：

```
ai-env\
├── python\     ← WinPython（自動下載解壓）
├── tools\      ← Node.js、Git、ripgrep、jq（自動下載解壓）
└── .venv\      ← Python 虛擬環境
```

### 4. 日常使用

從 `ai-env\` 執行 `cc.bat`：

```cmd
cd ai-env
cc.bat
```

Terminal 開啟後，工作目錄自動切換至你的專案資料夾：

```
Portable AI Terminal Ready

  git    git version 2.49.0.windows.1
  node   v24.16.0
  npm    10.x.x
  rg     ripgrep 14.1.1
  jq     jq-1.7.1

PS C:\my-project>
```

直接使用 Claude：

```powershell
claude
```

---

## 連線方式

首次 `init.bat` 執行時選擇：

```
1. 透過本地代理連線（建議）
2. 直接連線
```

設定儲存於 `C:\Users\<帳號>\.portable-markitdown-claude\claude.env`，下次略過。

---

## 常見問題

**Q：想切換連線方式**
→ 刪除 `C:\Users\<帳號>\.portable-markitdown-claude\claude.env`，重新執行 `ai-env\init.bat`。

**Q：想升級工具版本**
→ 修改 `ai-env\init.bat` 頂端 VERSION CONFIG 的版本號，重新執行 `ai-env\init.bat` 即可（舊版自動替換）。

---

## macOS 快速設定

**前置條件：** [Homebrew](https://brew.sh)（選用，git / ripgrep / jq 透過 brew 安裝）

```bash
# 進入你的專案資料夾
cd my-project

# 建立 ai-env 資料夾、下載並解壓環境
mkdir ai-env && cd ai-env
curl -L -o env.zip https://github.com/kennethtu999/portable_ai_environment/releases/latest/download/portable_claude_env_mac.zip
tar -xf env.zip
cd ..

# 首次設定（偵測或下載 Python/Node.js，設定 API Token，驗證連線）
ai-env/init.sh

# 日常使用（從專案資料夾執行，Claude 在此運作）
ai-env/cc.sh
```

`init.sh` 策略：

| 工具 | 優先 | 備援 |
|------|------|------|
| Python | 系統 python3 ≥ 3.8 | `brew install python3` |
| Node.js | 系統 node | 下載 portable tar.gz |
| git / rg / jq | 系統已有 | `brew install` |

設定儲存於 `~/.portable-markitdown-claude/claude.env`（同 Windows，跨專案共用）。

**Q：想切換連線方式**
→ 刪除 `~/.portable-markitdown-claude/claude.env`，重新執行 `ai-env/init.sh`。
