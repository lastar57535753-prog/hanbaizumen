# インストール手順（別アカウント／別PCで使う）

このフォルダ `property-mysoku-generator/` を丸ごと、使いたい環境の **personal skills フォルダ**に置くだけ。

## 置き場所（Claude Code）
```
~/.claude/skills/property-mysoku-generator/
```
Windowsなら `C:\Users\<ユーザー名>\.claude\skills\property-mysoku-generator\`。
（`~/.agents/skills/` でも可＝Codex/Gemini等と共有の場所）

配置後、`SKILL.md` がフォルダ直下にあることを確認。チャットで「○○マンションの販売図面を作って」と言えば起動する。

## 前提ソフト（初回のみ）

**共通:**
```
pip install python-pptx Pillow PyMuPDF
```

**Windows:**
- Microsoft PowerPoint（PDF書き出しに使用）
- `pip install pywin32`

**macOS / Linux:**
- **LibreOffice**（PDF書き出しに使用）
  - mac: `brew install --cask libreoffice`
  - Linux: `sudo apt install libreoffice`（等）
  - `soffice` が特殊な場所にある場合は環境変数 `SOFFICE_BIN` にフルパスを設定
  - ※mac は Microsoft PowerPoint があれば LibreOffice 無しでも自動フォールバック
- 日本語フォントはヒラギノ等が自動で使われる（`HGS明朝E` は無くても明朝系に代替）

**mac/Linux での挙動差（重要）:**
- 右カラム（物件概要→備考→LIFE）の自動整列は **python-pptx推定**（Windowsは PowerPoint実測で高精度）。
- 出力前の自動QC（preflight）は **スキップ**される。
- → **生成PDF/pptxを必ず目視確認**すること。ズレがあれば data/images.json のフォント・幅を微調整して再実行。

## アカウント固有の設定
- 物件素材フォルダのルートが人によって違う。環境変数を設定するのが楽：
  - PowerShell: `setx MYSOKU_ROOT "D:\path\to\媒介物件フォルダ"`
  - 未設定でも、物件フォルダのパスを直接指定すれば動く（`find_property.py` は補助ツール）。

## 動作確認（同梱サンプルで）
```
cd ~/.claude/skills/property-mysoku-generator
python scripts/fill.py assets/template_mansion.pptx assets/sample_data.json test_filled.pptx
```
→ `test_filled.pptx` ができれば流し込みはOK。写真まで通すには `assets/sample_images.json` の写真パスを手元の画像に差し替えてから `scripts/build_all.py` を実行。

## 固定値（この会社専用）
社名=センチュリー21ラスターハウス／担当=徳永新太郎／TEL 03-5753-0021 等はテンプレに埋め込み済み。別会社で使う場合は `assets/template_mansion.pptx` のフッター等を編集すること。
