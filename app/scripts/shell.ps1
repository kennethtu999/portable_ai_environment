$AiEnv      = Resolve-Path "$PSScriptRoot\.."
$ProjectRoot = Resolve-Path "$AiEnv\.."

# Find a tool's executable and add its directory to PATH.
# Uses recursive search so version-bumped extractions still resolve correctly.
function Add-ToolBin([string]$dir, [string]$exe) {
  $hit = Get-ChildItem $dir -Recurse -Filter $exe -ErrorAction SilentlyContinue |
         Select-Object -First 1
  if ($hit) {
    $env:PATH = "$($hit.DirectoryName);$env:PATH"
    return $hit.FullName
  }
  return $null
}

Add-ToolBin "$AiEnv\tools\git"  "git.exe"  | Out-Null
Add-ToolBin "$AiEnv\tools\node" "node.exe" | Out-Null
Add-ToolBin "$AiEnv\tools\rg"   "rg.exe"   | Out-Null
Add-ToolBin "$AiEnv\tools\jq"   "jq.exe"   | Out-Null

# Claude installed locally under tools\npm-global\node_modules
$env:PATH = "$AiEnv\tools\npm-global\node_modules\.bin;$env:PATH"

Write-Host ""
Write-Host "Portable AI Terminal Ready"
Write-Host ""

$tools = [ordered]@{
  git    = "git --version"
  node   = "node --version"
  npm    = "npm --version"
  claude = "claude --version"
  rg     = "rg --version"
  jq     = "jq --version"
}

foreach ($name in $tools.Keys) {
  $bin = Get-Command $name -ErrorAction SilentlyContinue
  if ($bin) {
    $ver = Invoke-Expression $tools[$name] 2>&1 | Select-Object -First 1
    Write-Host "  $($name.PadRight(6)) $ver"
  } else {
    Write-Host "  $($name.PadRight(6)) (not found — run init.bat)"
  }
}

Write-Host ""

# Auto-install Claude CLI if missing
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
  Write-Host "  [setup] Claude CLI not found. Installing..."
  $installDir = "$AiEnv\tools\npm-global"
  if (-not (Test-Path $installDir)) { New-Item -ItemType Directory -Path $installDir | Out-Null }
  Push-Location $installDir
  & npm install @anthropic-ai/claude-code
  Pop-Location
  Write-Host ""
}

# Set working directory to the project folder (parent of ai-env)
Set-Location $ProjectRoot

# Launch Claude (proxy managed by launch_claude.py)
& "$AiEnv\.venv\Scripts\python.exe" "$AiEnv\scripts\launch_claude.py"
