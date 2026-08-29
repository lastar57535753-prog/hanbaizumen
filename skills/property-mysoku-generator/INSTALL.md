# インストール手順（別アカウント／別PCで使う）

## どこで動かすか（先に決める）

このスキルは物件フォルダの写真・PDFを**ファイルとして読む**。だから
**Dropboxがローカルフォルダとして見えているPC**で動かす必要がある。

| 動かす場所 | ローカルフォルダ | 使えるか |
|---|---|---|
| 自分のPCの Claude Code（CLI / デスクトップアプリ） | 見える | **○ これが本命** |
| claude.ai / Claude Code on the web | 見えない（別のサーバー上で動く） | ✗ 写真を毎回アップロードするか、共有URLを許可リストに追加する必要がある |

→ **`C:\Users\Surface\.claude\skills\` に置いて、自分のPCの Claude Code から使う。**
Dropbox のパスはそのまま `C:/Users/Surface/Dropbox/★媒介物件フォルダ/...` と書けばよい。

## 置き場所

このフォルダ `property-mysoku-generator/` を丸ごと、personal skills フォルダに置くだけ。

```
~/.claude/skills/property-mysoku-generator/
```
Windowsなら `C:\Users\<ユーザー名>\.claude\skills\property-mysoku-generator\`。
（`~/.agents/skills/` でも可＝Codex/Gemini等と共有の場所）

配置後、`SKILL.md` がフォルダ直下にあることを確認。チャットで「○○マンションの販売図面を作って」と言えば起動する。

## 前提ソフト（初回のみ）

**共通:**
```
pip install python-pptx Pillow PyMuPDF cairosvg
```
（cairosvg はピクトグラムを作り直すときだけ必要。同梱のPNGを使う分には不要）

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

**mac/Linux での挙動差:**
- 右カラム（物件概要→備考→LIFE）の自動整列は **python-pptx推定**（Windowsは PowerPoint実測で高精度）。
- 出力前の自動QC（preflight）は **どの環境でも走る**。Windowsは PowerPoint の実描画座標、
  mac/Linux は python-pptx＋全角1em換算。違反があればビルドが止まる。
- 日本語の折り返しは実フォントではなく全角1em換算で計算するので、
  **どの環境でも同じ位置で折り返す**（HGS明朝E が無くてもレイアウトは崩れない）。
- → 最終確認は PowerPoint で開いて目視すること。QCは近似なので万能ではない。

## アカウント固有の設定
- 物件素材フォルダのルートが人によって違う。環境変数を設定するのが楽：
  - PowerShell: `setx MYSOKU_ROOT "D:\path\to\媒介物件フォルダ"`
  - 未設定でも、物件フォルダのパスを直接指定すれば動く（`find_property.py` は補助ツール）。

## 動作確認（同梱サンプルで）
```
cd ~/.claude/skills/property-mysoku-generator
python scripts/fill.py assets/template_mansion.pptx assets/sample_data.json test_filled.pptx
python scripts/preflight.py test_filled.pptx
```
→ `test_filled.pptx` ができ、QCが ✅合格 と出れば流し込みはOK。
写真まで通すには `assets/sample_images.json` の写真パスを手元の画像（かDropbox共有リンク）に
差し替えてから `scripts/build_all.py` を実行。

## 担当者の切り替え

名前・携帯・メールは `assets/agents.json` に登録しておき、実行時に選ぶ。

```bash
python scripts/build_all.py ... --agent iwasawa
```
data.json に `"AGENT": "iwasawa"` と書いても同じ。指定が無ければ `default`（徳永）。
新しい担当を足すときは `agents.json` の `agents` に1件追加するだけ。

## 固定値（この会社専用）
社名=センチュリー21ラスターハウス／TEL 03-5753-0021／東京都大田区大森北1-14-1／
東京都知事免許(4)第87972号 はテンプレに埋め込み済み。
別会社で使う場合は `assets/template_mansion.pptx` のフッター等を編集すること。

## 写真の渡し方
`images.json` の `path` はローカルパスでも共有URL（Dropbox / Google Drive）でもよい。
共有リンクはそのまま貼ってよく、`?dl=0` は自動で直リンクに変換される。
取得できない写真があるとビルドは止まる（`--allow-missing` で穴を許容）。

## ピクトグラム
`--pictograms point,note,life` を付けると、行頭の「・」を物件の特徴に合った
ピクトグラム（275点・同梱）に置き換える。詳細は `references/pictograms.md`。
