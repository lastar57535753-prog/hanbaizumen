---
name: property-mysoku-generator
description: Use when creating a Japanese condominium (マンション区分) sales flyer / マイソク / 販売図面 (A4 landscape, 1 page) at consistent quality from property materials — e.g. "○○マンションの販売図面を作って", "マイソク作成", "販売図面を作りたい". Condominium units only (not 戸建・土地). Runs on Windows (PowerPoint) or macOS/Linux (LibreOffice).
---

# 販売図面（マイソク）自動生成システム

## Overview

マンション区分の販売図面（マイソク・A4横1枚）を、**どの物件でも同一クオリティ**で再現するシステム。新太郎さんが手作業で仕上げた完成デザインを穴あきテンプレ化し、物件ごとに `data.json`（文字値）と `images.json`（写真割当＋意匠）の2ファイルを用意するだけで、あとは1コマンドで pptx + PDF が出る。

**核心原則:** 新しい意匠を勝手に足さない。既存の意匠部品（バッジ・キャプション・スマート写真充填・背景モード）を**設定JSONで駆動する**だけ。レイアウトはテンプレ固定でズラさない。

## 動作要件（別アカウントでの初回セットアップ）

**Windows でも macOS/Linux でも動く**（PDF書き出しの方式が自動で切り替わる）。

- **Python** と共通依存: `pip install python-pptx Pillow PyMuPDF`
  - python-pptx=流し込み / Pillow=写真処理 / PyMuPDF(fitz)=他社PDFから間取図抽出
- **PDF書き出し（OSで方式が自動選択）:**
  - **Windows:** Microsoft PowerPoint ＋ `pip install pywin32`（COMで書き出し）
  - **macOS / Linux:** **LibreOffice**（`soffice`）。mac は `brew install --cask libreoffice`。環境変数 `SOFFICE_BIN` でパス明示も可。mac は PowerPoint があれば LibreOffice無しでもフォールバック動作。
- **右カラム自動整列 / 自動QC:** Windows は PowerPoint実測で高精度。**mac/Linux は python-pptx推定で整列し、preflight（自動QC）はスキップ** → 生成物を PowerPoint/LibreOffice で**目視確認**する。
- **フォント:** `HGS明朝E`（日本語Win/Office標準）。無い環境（mac等）は明朝系に自動代替（ヒラギノ等）。行折り返し計測用フォントもOS別に自動解決。
- **物件素材フォルダのルート**（`find_property.py` 用）はアカウントごとに違う。環境変数 `MYSOKU_ROOT` に設定するか、`--root "パス"` で毎回渡す（find_property はあくまで補助）。

`assets/` に穴あきテンプレ本体・和紙背景・サンプル2本・仕上がり見本PDFを同梱済み。

## When to Use / NOT

- **Use:** マンション区分の販売図面／マイソクを作る依頼。
- **NOT:** 戸建・土地（別テンプレ想定・未対応）、冊子版、価格改定のみ、帯替えだけ（それは obi-replace スキル）。

## 作り方（1コマンド）

内部で fill → 画像/意匠 → 右カラム整列 → 出力前セルフQC → PDF を自動実行する。

```bash
python scripts/build_all.py assets/template_mansion.pptx 物件_data.json 物件_images.json 出力.pptx
```

- preflight が **✅合格** なら QR以外は一発納品OK。**⚠要確認** なら設定JSONを直して再実行。
- PDFを省くなら末尾に `--no-pdf`。

## 手順（Step 0〜6）

0. **依存確認**（初回のみ）: 上記 pip install と PowerPoint。`MYSOKU_ROOT` を設定。
1. **物件フォルダ特定:** `python scripts/find_property.py "物件名"` → パスを見せて**1回だけ確認**を取る（誤字・表記ゆれ対応のあいまい一致）。
2. **取引態様を1問だけ聞く**（専任／専属専任／一般／代理）。※担当・社名・TEL等は固定値（下記）。
3. **素材仕分け:** `python scripts/collect_assets.py "物件フォルダ"` で写真/間取図/QR/レインズ/謄本/カンテイを自動仕分け（AI生成画像・競合図面は除外）。
4. **資料を実際に開いて読み、物件概要を埋める**（レインズ図面・謄本・東京カンテイ・管理規約）。
   - ★**専有面積は必ず壁芯**（謄本の内法を転記しない）。坪数 = ㎡ × 0.3025。
   - ★**不明は推測せず空欄** → fill が `【要確認】` 赤字で残す。資料が矛盾したら**両方採らず**【要確認】。
   - 詳細ルールは **references/content-rules.md**。
5. **写真を各枠に割当**（画像を見て種類判定）。強い眺望写真あり→ **view_hero**（眺望を全面背景）／無ければ **washi**（和紙背景）。背景モードは references/layout-rules.md。
6. **サンプル2本をコピーして差し替え → ビルド → QC合格まで直す:**
   - `assets/sample_data.json` → 文字値を差し替え（キー一覧は **references/placeholder-keys.md**）
   - `assets/sample_images.json` → 写真パス・バッジ値(seal/madori/area/sub)・背景・意匠を差し替え（オプション一覧は **references/images-json-options.md**）
   - `build_all.py` 実行 → preflight ✅合格まで設定を調整。
     **QCで違反が出るとビルドは止まる**（承知のうえで進めるなら `--qc-warn`）。
     QCは Windows なら PowerPoint の実描画座標、mac/Linux なら python-pptx で走る。
     どちらの環境でも検査される。

## 自動で担保される品質（`place_images.py` が設定JSONで毎回同じに）

高級バッジ（金メタリック・面取り・箔文字）／統一キャプション（固定サイズ・金の極細罫）／スマート写真充填（比率差で 中央/アンカー/ぼかし背景 を自動選択＝切れ0）／間取り自動最大化＋細枠／POINTの・箇条書き＋語中で切らない日本語改行／物件概要→備考→LIFE を実測高さで自動整列。**恒久レイアウトルール10項は references/layout-rules.md（毎回必ず適用）。**

## 固定値（変えない）

センチュリー21ラスターハウス ／ TEL 03-5753-0021 ／ 東京都大田区大森北1-14-1 ／ 東京都知事免許(4)第87972号 ／ フォントは全部 **HGS明朝E**。※取引態様のみ Step2 で確認。

**担当者だけは可変。** 名前・携帯・メールは `assets/agents.json` から入る（既定は徳永新太郎）。
別の担当なら `--agent iwasawa`、または data.json に `"AGENT": "iwasawa"`。
data.json に `AGENT_NAME` 等を直接書けばそれが優先。

## 写真の渡し方

`images.json` の `path` には**ローカルパスでも共有URLでも**書ける。
Dropbox / Google Drive の共有リンクはそのまま貼ってよい（`?dl=0` は自動で直リンクに変換）。
一度取得したものはキャッシュするので、作り直しても再ダウンロードしない。

**取れない写真があればビルドは止まる。** 写真の抜けた図面がそのまま出来てしまうのを
防ぐため。穴を承知で進めるときだけ `--allow-missing`。

## ピクトグラム（任意）

`--pictograms point,note,life` を付けると、行頭の「・」を物件の特徴に合った
ピクトグラムに置き換える（275点・角丸枠つき・`assets/pictograms/`）。
帯や枠は増やさず、既にあるものの中に納める。字数が足りなければ自動で縮め、
それでも無理なら止まる。詳細は `references/pictograms.md`。

## 出力先・締め

素材を入れた**物件フォルダ直下**に `{物件名}_販売図面.pptx / .pdf`。最後に必ず **「写真の枠割当一覧」** と **「【要確認】リスト」** を提示。**QRコードは手動でPowerPointで差す**（自動化対象外）。

## Common Mistakes

- 専有面積に謄本の**内法**を書く → ✗。必ず壁芯。
- 他社図面のPOINT/戸数/築年を**丸写し** → 別物件の残骸が混じる。物件概要と矛盾したら除外。
- 間取図を**引き伸ばす** → ✗ 縦横比厳守（`is_floorplan`+`region_cm`で比率保持最大化）。写真は多少の引き伸ばしOK。
- `resize`/`set_font` は `jp_wrap` の**前**に効く実装。幅を変えたのに改行が直らない時は順序を確認。
- テンプレは `assets/template_mansion.pptx`（68箇所穴・66キー）。もう一方の template_mansion 系は使わない。
- 書体は **HGS明朝E のみ**。HGP明朝E は禁止（字送りが変わる）。preflight が検出して止める。
- 日本語の折り返しは全角1em換算で計算する。実フォントで測ると HGS明朝E の無い
  mac/Linux で折返し位置が変わり、レイアウトが崩れる。
