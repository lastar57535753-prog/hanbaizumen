@echo off
chcp 65001 >nul
setlocal
title 販売図面スキル インストール

echo ==================================================
echo   販売図面（マイソク）スキル インストール
echo ==================================================
echo.

set "SRC=%~dp0property-mysoku-generator.zip"
set "DEST=%USERPROFILE%\.claude\skills"
set "SKILL=%DEST%\property-mysoku-generator"

if not exist "%SRC%" (
  echo [エラー] property-mysoku-generator.zip が見つかりません。
  echo.
  echo    このファイルと zip を「同じフォルダ」に置いてから、
  echo    もう一度このファイルをダブルクリックしてください。
  echo.
  echo    いまの場所: %~dp0
  goto :end
)

echo [1/5] Python を確認しています...
where python >nul 2>&1
if errorlevel 1 (
  echo    [エラー] Python が入っていません。
  echo.
  echo    https://www.python.org/downloads/windows/ から入れてください。
  echo    途中の「Add python.exe to PATH」に必ずチェックを入れること。
  echo    入れ終わったら、またこのファイルをダブルクリックしてください。
  goto :end
)
for /f "delims=" %%v in ('python --version 2^>^&1') do echo    OK %%v

echo.
echo [2/5] スキルを置いています...
if not exist "%DEST%" mkdir "%DEST%"
if exist "%SKILL%" (
  echo    古い版があるので入れ替えます
  rmdir /s /q "%SKILL%"
)
powershell -NoProfile -Command "Expand-Archive -LiteralPath '%SRC%' -DestinationPath '%DEST%' -Force"
if not exist "%SKILL%\SKILL.md" (
  echo    [エラー] zip の展開に失敗しました。
  goto :end
)
echo    OK %SKILL%

echo.
echo [3/5] 必要な部品を入れています（数分かかります）...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet python-pptx Pillow PyMuPDF pywin32
if errorlevel 1 (
  echo    [エラー] 部品を入れられませんでした。この画面を Claude に見せてください。
  goto :end
)
echo    OK

echo.
echo [4/5] 動作確認をしています...
pushd "%SKILL%"
python scripts\fill.py assets\template_mansion.pptx assets\sample_data.json _test.pptx >nul 2>&1
if not exist "_test.pptx" (
  echo    [エラー] お試し生成に失敗しました。この画面を Claude に見せてください。
  popd
  goto :end
)
python scripts\preflight.py _test.pptx
del /q _test.pptx >nul 2>&1
popd

echo.
echo [5/5] Claude Code を確認しています...
where claude >nul 2>&1
if errorlevel 1 (
  echo    [注意] Claude Code がこのPCに見つかりません。
  echo    スキル自体は置けましたが、動かすには Claude Code が要ります。
  echo    https://claude.com/claude-code から入れてください。
) else (
  echo    OK
)

echo.
echo ==================================================
echo   完了しました。
echo.
echo   Claude Code を開いて、こう言ってください:
echo.
echo     ガーデンホーム大森303の販売図面作って
echo.
echo   Dropbox の物件フォルダは自動で探しに行きます。
echo ==================================================

:end
echo.
pause
