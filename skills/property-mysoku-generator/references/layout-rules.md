# 恒久レイアウトルール（毎回必ず適用）

徳永新太郎さん指定（2026-07-20 確立）。すべて `images.json` の意匠オプションで駆動する（実装は `scripts/place_images.py`。オプション詳細は images-json-options.md）。

1. **メインキャッチ(id25)は絶対に被らせない** — 間取図等に重ねない。`resize` で幅を間取図手前（例 w12.8）まで縮め、文言も2行に収まるよう短縮。
2. **メインキャッチにスモークガラス(スクリム)を使わない** — `scrims` を入れない。視認性は `text_shadow`(id25) で確保。
3. **眺望がメインのときは範囲いっぱいに引き伸ばす** — `fullbleed_bg` に `"stretch": true`（比率が変わってOK＝フルフィル）。view_hero は `hide_ids:[116]` 併用。
4. **物件概要の背面に白板を上帯下〜下帯上まで伸ばす** — テーブル範囲でなく固定矩形で右カラム全体（物件概要+備考+LIFE）を1枚の白板に。`bg_panels` に `{"behind_id":307,"box_cm":[21.05,1.85,8.5,17.0],"color":"FFFFFF","to_back":true}`。
5. **POINT本文(id216)は写真に被らないギリギリまで箱を大きく** — `resize` で幅拡張（例 w9.8＝ヘッダ幅）＋ `point_fix.bottom_cm` を下段写真直前（例15.2）まで。フォントも詰まらない範囲で最大化（8〜9pt、QC合格まで調整）。
6. **POINTが背景に被って読みづらいときは白半透明板を背後に** — `bg_panels` で `{"behind_id":216,"color":"FFFFFF","alpha":84,"pad_cm":0.14,"round":true}`。白背景上なら不要。
7. **背景（眺望 or 和紙）は固定枠にサイズ固定** — 上帯下・下帯上・物件概要(id307)の左、の内側に固定。`fullbleed_bg.region_cm ≈ [0.15, 1.85, 20.9, 17.0]`。物件概要より右は背景に含めない。
8. **改行は語の意味が途切れないように** — `jp_wrap`（語中で切らない）を使用。箱が狭くて割れる場合は `set_font` でその箱だけ少し縮める（例：アクセスid281を10.5→9.0pt）。**set_font / resize は jp_wrap の前に実行される実装。**
9. **眺望がメインのとき → メイン兼背景**に使う（`fullbleed_bg.stretch:true` + `hide_ids:[116]`、region=上記固定枠）。
10. **眺望以外（居室等）がメインのとき → 背景は和紙** = 同梱の `assets/washi_bg.jpg` を `fullbleed_bg.photo` にして固定枠に敷く。この場合ヒーロー(116)は居室写真を通常配置（hide しない）。

## 背景モード早見

| モード | 使う条件 | images.json |
|---|---|---|
| **view_hero** | 強い眺望写真がある | `fullbleed_bg`(眺望写真, `stretch:true`, region固定) + `hide_ids:[116]` |
| **washi** | 眺望が弱い／居室がメイン | `fullbleed_bg`(`assets/washi_bg.jpg`, `stretch:true`, region固定)、116は居室を通常配置 |
| white | 旧既定（背景白・枠内ヒーロー） | `fullbleed_bg` を入れない |

## luxury_badge のサイズはメイン写真で変える

- **居室（リビング等）がメイン** → バッジを**小さめ**に（w/h を標準より縮小）。室内の情報量を邪魔しない。
- **眺望がメイン（view_hero）** → バッジは**現状サイズ**（例 w4.7 h3.6）でよい。空・街並み背景なので大きめでも成立。

badge の値は `seal`/`madori`/`area`/`sub` を差し替えるだけ（例 "30F ・ 最上階" / "3LDK" / "109.14㎡" / "北西 角部屋"）。
