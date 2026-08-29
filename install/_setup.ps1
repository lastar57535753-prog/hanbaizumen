$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}

function Line($t = '') { Write-Host $t }

$script:pyKind = $null
function Py {
  param([Parameter(ValueFromRemainingArguments = $true)] $a)
  if ($script:pyKind -eq 'py3') { & py -3 @a } else { & python @a }
}

Line '=================================================='
Line '  販売図面（マイソク）スキル インストール'
Line '=================================================='
Line

$dest  = Join-Path $env:USERPROFILE '.claude\skills'
$skill = Join-Path $dest 'property-mysoku-generator'
$here  = Split-Path -Parent $MyInvocation.MyCommand.Path

# ---------- [1/5] zip を探す ----------
Line '[1/5] zip を探しています...'
$dirs = @(
  $here,
  (Join-Path $env:USERPROFILE 'Downloads'),
  (Join-Path $env:USERPROFILE 'Desktop'),
  (Join-Path $env:USERPROFILE 'OneDrive\Downloads'),
  (Join-Path $env:USERPROFILE 'OneDrive\Desktop'),
  (Join-Path $env:USERPROFILE 'OneDrive\デスクトップ')
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique

$zip = $null
foreach ($d in $dirs) {
  $f = Get-ChildItem -Path $d -Filter 'property-mysoku-generator*.zip' -File -ErrorAction SilentlyContinue |
       Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if ($f) { $zip = $f.FullName; break }
}

if (-not $zip) {
  Line '   [エラー] property-mysoku-generator.zip が見つかりませんでした。'
  Line
  Line '   下のフォルダを探しました:'
  foreach ($d in $dirs) { Line ('     ' + $d) }
  Line
  Line '   チャットから zip をダウンロードして、上のどれかに置いてから'
  Line '   もう一度このファイルをダブルクリックしてください。'
  return
}
Line ('   OK  ' + $zip)

# ---------- [2/5] Python ----------
Line
Line '[2/5] Python を確認しています...'
$ver = ''
if (Get-Command python -ErrorAction SilentlyContinue) {
  try {
    $v = (& python --version 2>&1 | Out-String).Trim()
    if ($v -match 'Python 3') { $script:pyKind = 'python'; $ver = $v }
  } catch {}
}
if (-not $script:pyKind -and (Get-Command py -ErrorAction SilentlyContinue)) {
  try {
    $v = (& py -3 --version 2>&1 | Out-String).Trim()
    if ($v -match 'Python 3') { $script:pyKind = 'py3'; $ver = $v }
  } catch {}
}
if (-not $script:pyKind) {
  Line '   [エラー] Python が入っていません。'
  Line
  Line '   https://www.python.org/downloads/windows/ から入れてください。'
  Line '   途中の「Add python.exe to PATH」に必ずチェックを入れること。'
  Line '   入れ終わったら、またこのファイルをダブルクリックしてください。'
  return
}
Line ('   OK  ' + $ver)

# ---------- [3/5] 配置 ----------
Line
Line '[3/5] スキルを置いています...'
try { Unblock-File -LiteralPath $zip -ErrorAction SilentlyContinue } catch {}
if (-not (Test-Path $dest)) { New-Item -ItemType Directory -Path $dest -Force | Out-Null }
if (Test-Path $skill) {
  Line '   古い版があるので入れ替えます'
  Remove-Item -LiteralPath $skill -Recurse -Force
}
try {
  Expand-Archive -LiteralPath $zip -DestinationPath $dest -Force
} catch {
  Line ('   [エラー] zip を展開できませんでした: ' + $_.Exception.Message)
  return
}
if (-not (Test-Path (Join-Path $skill 'SKILL.md'))) {
  Line '   [エラー] 展開はできましたが SKILL.md が見当たりません。zip が壊れている可能性があります。'
  return
}
Line ('   OK  ' + $skill)

# ---------- [4/5] 部品 ----------
Line
Line '[4/5] 必要な部品を入れています（数分かかります）...'
Py -m pip install --quiet --upgrade pip 2>&1 | Out-Null
Py -m pip install --quiet python-pptx Pillow PyMuPDF 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
  Line '   [エラー] 部品を入れられませんでした。理由をもう一度出します:'
  Py -m pip install python-pptx Pillow PyMuPDF
  Line
  Line '   この画面をスクショして Claude に見せてください。'
  return
}
# pywin32 は PDF書き出し（PowerPoint操作）にだけ要る。無くても PPTX までは作れるので止めない。
Py -m pip install --quiet pywin32 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
  Line '   OK（ただし pywin32 が入りませんでした → PDF書き出しは使えません。PPTXまでは作れます）'
} else {
  Line '   OK'
}

# ---------- [5/5] 動作確認 ----------
Line
Line '[5/5] 動作確認をしています...（PowerPoint が一瞬起動することがあります）'
Push-Location $skill
try {
  $test = Join-Path $skill '_test.pptx'
  if (Test-Path $test) { Remove-Item -LiteralPath $test -Force }
  Py scripts/fill.py assets/template_mansion.pptx assets/sample_data.json _test.pptx 2>&1 | Out-Null
  if (-not (Test-Path $test)) {
    Line '   [エラー] お試し生成に失敗しました。理由をもう一度出します:'
    Py scripts/fill.py assets/template_mansion.pptx assets/sample_data.json _test.pptx
    Line
    Line '   この画面をスクショして Claude に見せてください。'
    return
  }
  Py scripts/preflight.py _test.pptx
  Remove-Item -LiteralPath $test -Force -ErrorAction SilentlyContinue
} finally { Pop-Location }

Line
Line '  Claude Code を確認しています...'
if (Get-Command claude -ErrorAction SilentlyContinue) {
  Line '   OK'
} else {
  Line '   [注意] Claude Code がこのPCに見つかりません。'
  Line '   スキルは置けましたが、動かすには Claude Code が要ります。'
  Line '   https://claude.com/claude-code'
}

Line
Line '=================================================='
Line '  完了しました。'
Line
Line '  Claude Code を開いて、こう言ってください:'
Line
Line '    ガーデンホーム大森303の販売図面作って'
Line
Line '  Dropbox の物件フォルダは自動で探しに行きます。'
Line '=================================================='
