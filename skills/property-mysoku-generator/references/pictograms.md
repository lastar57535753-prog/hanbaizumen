# ピクトグラム

販売図面の行頭に、物件の特徴に合ったピクトグラムを自動で入れる。
素材は `assets/pictograms/`（275点・角丸枠つき・商用利用可のライセンスのみ）。

同梱しているのは**アルファマスク1組だけ**で、色は使うときに着ける（PIL）。
4色分のPNGを持つと容量が6倍になるうえ、使える色もその4色に限られるため。
`--color gold`（既定）／`sumi`／`gold_light`／`white`、または `--color "#B03030"` のように
好きな色を直接指定できる。着色したPNGは出力先の `_picto/` にキャッシュされる。

## 置き方の原則

`layout-rules.md` の「**新しい意匠を勝手に足さない**」に従う。
帯・枠・見出しは**増やさない**。既にある行頭の「・」を絵に**置き換える**だけ。

| ゾーン | 場所 | 字数への影響 |
|---|---|---|
| `point` | POINT本文の行頭 | 25.9字→24.6字（折り返し行数は変わらない） |
| `note` | 備考本文の行頭 | 詰まっていると1行増える（下の余白で吸収） |
| `life` | LIFE INFORMATION の施設名の左 | 枠が埋まっているので 8.5→8.0pt に縮小が必要 |

既定は入れない。`build_all.py --pictograms point,note` のように明示したときだけ動く。

## 溢れさせない

アイコン分だけ本文が狭くなるので、行が増えるかを**先に計算する**。増える場合は

1. 本文ボックスの下に余白があればそのまま伸ばす
2. 無ければアイコンを小さくして収める（下限 0.26cm）
3. それでも無理なら**エラーで止める**

文字を縮めるのは `life` だけ、下限は **8.0pt**（A4原寸で読める大きさ）。
承知のうえで進めるときだけ `--force`。

## 1行に1つ選ぶときの優先順位

`rank`（`catalog.json` の任意項目・既定1）→ ヒットした語の長さ、の順。
売りになる特徴（最上階・角住戸・富士山眺望・夜景・タワー・新築・リフォーム済・空室など）
に 2 を付けてある。同じ絵が1枚の図面で二度出ないよう、既出のキーは後回しになる。

> 「お部屋から東京タワー、富士山へ抜ける眺望」はタワー／眺望／富士山／夜景の
> 4つが当たるが、**富士山眺望**を選ぶ。

## 「無い設備」を出さない

物件概要が「不可・無・なし」なら、そのピクトグラムは**拒否**される。
POINT文に「ペット可」と書いてあっても、概要が `PET=不可` なら出さない。
他社図面のPOINTを丸写しすると別物件の残骸が混じる、という `content-rules.md` の
警告への対応。

## 施設名が当たらないとき

`assets/pictograms/catalog.json` の該当項目の `match` に語を足すだけ。
画像の作り直しは不要（`match` はピック時にしか使わない）。

## 使い方

```bash
# ビルドに組み込む
python scripts/build_all.py テンプレ.pptx data.json images.json out.pptx --pictograms point,note

# 単体で掛ける／掛け直す（何度実行しても増えない）
python scripts/place_pictograms.py 図面.pptx -o 図面_icon.pptx --zones point,note,life
python scripts/place_pictograms.py 図面.pptx --dry-run          # 置く場所だけ見る

# 物件データから何が選ばれるか確認する
python scripts/pick_pictograms.py data.json --color gold
```

素材の作り直し（アイコンを増やす・枠の形を変える）はリポジトリ側の
`scripts/build_pictograms.py` で行う。

```bash
python scripts/build_pictograms.py --size 128 --png-only --mask-only \
       --out skills/property-mysoku-generator/assets/pictograms
```
