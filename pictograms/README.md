# 販売図面用ピクトグラム

センチュリー21 ラスターハウスの販売図面（マイソク）で使うピクトグラム一式。
物件データを渡すと、その物件の特徴に合うものが**自動で選ばれる**。

![一覧](contact_sheet.png)

## 中身

| パス | 内容 |
|---|---|
| `catalog.json` | 86項目の対応表。`key`(正規名) / `label`(表示名) / `icon`(Iconify ID) / `match`(日本語の表記ゆれ) / `cat`(分類) |
| `svg/` | 86点のSVG（`currentColor` なので好きな色で使える） |
| `png/sumi/` | 墨 `#1E2328`（本文と同じ色） |
| `png/gold/` | 金 `#8C6E3F`（見出し・罫と同じ色） |
| `png/gold_light/` | 淡金 `#BEAF87` |
| `png/white/` | 白（写真の上に載せる用） |
| `contact_sheet.png` | 全点の一覧（金）／`contact_sheet_sumi.png`（墨） |
| `LICENSES.md` | 採用したアイコンセットとライセンス |

色は販売図面テンプレート（アトラスタワー五反田30F）のXMLから実測したブランド色。
PNGは256px。A4横の図面で使う0.4〜0.8cmの枠なら300dpiでも十分足りる。

## 分類（86点）

| 分類 | 点数 | 例 |
|---|---|---|
| 交通・アクセス | 6 | 駅／地下鉄／バス停／複数路線／空港／高速IC |
| 周辺施設（LIFE INFORMATION） | 22 | スーパー／コンビニ／ドラッグストア／病院／小学校／保育園／公園／銀行 |
| 共用部・建物設備 | 16 | オートロック／宅配ボックス／エレベーター／コンシェルジュ／ペット可／タワー |
| 専有部・住戸設備 | 22 | システムキッチン／食洗機／ディスポーザー／浴室乾燥機／床暖房／WIC |
| 立地・方位・眺望 | 12 | 角住戸／最上階／南向き／眺望良好／富士山眺望／夜景／閑静 |
| 取引・状態 | 8 | 新築／築浅／リフォーム済／空室・即入居／所有権／ローン相談 |

## 使い方

### 物件データから自動で選ぶ

```bash
python scripts/pick_pictograms.py 物件_data.json --color gold -o 物件_pictograms.json
```

実際の物件（アトラスタワー五反田30F）で走らせた結果:

```
── LIFE INFORMATION 行のアイコン ──
   ✅ SPOT1: まいばすけっと 西五反田2丁目店  → スーパー
   ✅ SPOT2: ファミリーマート 西五反田二丁目店  → コンビニ
   ✅ SPOT3: トモズ 五反田店  → ドラッグストア
   ✅ SPOT4: 品川区立 第一日野小学校  → 小学校

── 物件の特徴ピクトグラム（12件・gold）──
   ✅ タワー      ← POINT2「タワー・地上30階」
   ✅ 最上階      ← POINT2「最上階」 / CATCH1「最上階」
   ✅ 富士山眺望   ← POINT2「富士山」 / CATCH2「富士山」
   ✅ コンシェルジュ ← POINT4「コンシェルジュ」
   …
```

拾い方は3系統:

1. **LIFE INFORMATION の各行**（`SPOT1`〜`SPOT7`）— 施設名から種別を判定して1行1アイコン。
   チェーン名（まいばすけっと・トモズ・ファミマ等）も登録済み。当たらない場合は汎用ピンにする。
2. **自由文**（`POINT1`〜`POINT6` / `NOTE` / `CATCH` / `STRUCTURE` 等）— 特徴語で拾う。
3. **有無で決まる項目**（`PET` / `ELEVATOR` / `PARKING` / `TRUNK`）— 値を見て判定。

### 「無い設備」を出さない仕組み

物件概要が「不可・無・なし」なら、そのピクトグラムは**拒否**される。
POINT文に「ペット可」と書いてあっても、概要が `PET=不可` なら出さない。

> 他社図面のPOINTを丸写しすると別物件の残骸（設備・戸数・築年）が混じる、という
> `content-rules.md` の警告に対応したもの。事実と違う設備アイコンは出さない。

```
── 物件概要が「無」なので出さなかったもの ──
   ⛔ pet_ok    (PET=不可)
   ⛔ elevator  (ELEVATOR=無)
   ⛔ parking   (PARKING=無（近隣に月極有）)
```

### 施設名が当たらないとき

`catalog.json` の該当項目の `match` に語を足すだけ。再ビルドは不要
（`match` はピック時にしか使わない）。

### アイコンを増やす・差し替える

`catalog.json` に項目を足すか `icon` を書き換えて、再生成する:

```bash
python scripts/build_pictograms.py            # @iconify/json を取得して生成
python scripts/make_contact_sheet.py          # 一覧を作り直す
```

`build_pictograms.py` は**商用利用できないライセンスのセットを自動で弾く**
（MIT / Apache / CC0 / ISC / BSD / Unlicense のみ通す）。
CC BY-NC・CC BY-SA・GPL のセットを指定するとエラーで止まる。

## 出どころ

[Iconify](https://iconify.design/) の `@iconify/json`（236セット・334,712点）から、
商用利用可の304,084点を候補として、販売図面に必要な86点を選んだもの。
基調は **Material Symbols Outlined**（Apache-2.0・Google）。
無いものだけ **Material Design Icons**（Apache-2.0）で補完している。

詳細は [LICENSES.md](LICENSES.md)。
