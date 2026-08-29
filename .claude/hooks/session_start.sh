#!/usr/bin/env bash
# 販売図面スキルが動くのに必要なものを揃える（Claude Code on the web のセッション開始時）。
# 足りないものだけ入れる。ネットワークが塞がっていても失敗で止めない。
set -u

log() { printf '  %s\n' "$*"; }

echo "■ 販売図面スキルの準備"

need=""
for m in pptx PIL cairosvg; do
  python3 - "$m" <<'PY' 2>/dev/null || need="$need $m"
import importlib, sys
importlib.import_module(sys.argv[1])
PY
done

if [ -n "$need" ]; then
  log "不足パッケージ:$need → pip で入れます"
  pip install --quiet --disable-pip-version-check python-pptx Pillow cairosvg 2>&1 | tail -2
else
  log "python-pptx / Pillow / cairosvg … OK"
fi

# PDF書き出しには LibreOffice Impress が要る（無くてもPPTXまでは作れる）
if command -v soffice >/dev/null 2>&1 && [ -e /usr/lib/libreoffice/program/libsdlo.so ]; then
  log "LibreOffice Impress … OK（PDF書き出し可）"
else
  log "LibreOffice Impress が無いので PDF 書き出しは使えません（--no-pdf で PPTX まで作れます）"
fi

# 写真を共有リンクから取るには Dropbox 等への通信許可が要る
python3 - <<'PY'
import urllib.request
try:
    urllib.request.urlopen(urllib.request.Request(
        "https://www.dropbox.com/", method="HEAD"), timeout=8)
    print("  Dropbox への通信 … OK")
except Exception as e:
    print("  Dropbox へ通信できません:", str(e)[:60])
    print("  → 写真を共有リンクで渡す場合は、環境のネットワーク許可リストに")
    print("     dropbox.com / dropboxusercontent.com を追加してください")
    print("     https://code.claude.com/docs/en/claude-code-on-the-web")
PY

echo "  準備完了"
