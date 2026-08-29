# images.json 意匠オプション一覧

`scripts/place_images.py` が読む設定。実例は `assets/sample_images.json`。座標は cm、色は RRGGBB(16進)、`alpha` は不透明度%。shape id はテンプレ固定（下の代表IDを参照）。

## 代表 shape id（テンプレ固定）
| id | 役割 |
|---|---|
| 116 | ヒーロー写真枠 |
| 32/33/119/120/124/128 | サブ写真枠 |
| 139 | 間取図枠 |
| 25 | メインキャッチ | 216 | POINT本文 | 313 | 備考 | 281 | アクセス |
| 307 | 物件概要テーブル | 31 | 旧バッジ（luxury_badge で置換） |
| 85/34/35/267/268/269/272 | 写真キャプションタグ |

## 写真割当 `images`
`{ "<id>": { "path": "...", "mode":"smart", "kind":"living|exterior|view|bath|hall|facility" } }`
- `mode:"smart"` = 比率差で 中央クロップ / アンカークロップ / ぼかし背景フィル を自動選択（切れ0）。`kind` でアンカー方向を調整（外観は上寄せ等）。
- 間取図は `{ "region_cm":[x,y,w,h], "align":"center", "is_floorplan":true, "border":{"color":"CFCFCF","pt":0.75} }`（比率保持でエリア内最大化＋細枠）。

## 背景 `fullbleed_bg`
`{ "photo":"...", "region_cm":[0.15,1.85,20.9,17.0], "stretch":true }`
- view_hero=眺望写真、washi=同梱 `assets/washi_bg.jpg`。`hide_ids:[116]` と併用（view_hero時）。詳細は layout-rules.md。

## 高級バッジ `luxury_badge`
`{ "remove_id":31, "x":0.7,"y":5.4,"w":4.7,"h":3.6, "seal":"30F ・ 最上階","madori":"3LDK","area":"109.14㎡","sub":"北西 角部屋" }`
金メタリック・面取り・箔文字・四隅飾り罫・金シール。サイズは居室ヒーロー時は縮小（layout-rules.md）。

## 統一キャプション `caption_uniform`
`{ "ids":[85,34,35,...], "w_cm":2.35,"h_cm":0.52,"off_cm":0.16,"font_pt":8, "fill":"14161B","alpha":68,"gold_line":true, "hero_id":85,"hero_photo_id":116 }`
全タグ固定サイズ＋スモークガラス＋金の極細罫（文字数が変わっても枠不変）。

## テキスト箱の調整（**jp_wrap の前に実行される**）
- `resize`: `[{"id":216,"w_cm":9.8}, {"id":25,"w_cm":12.8}]` 位置/サイズ変更（x_cm/y_cm/w_cm/h_cm）。
- `set_font`: `[{"id":281,"size_pt":9.0}]` その箱だけフォント縮小。
- `jp_wrap`: `{ "font":"C:/Windows/Fonts/msmincho.ttc", "items":[{"id":216,"size_pt":8.0,"space_after":1.5}] }` 語中で切らない日本語改行＋禁則。
- `point_fix`: `{"id":216,"bottom_cm":15.0}` POINT箱の下端を下段写真直前まで。
- `bullets`: `{"ids":[216]}` ・箇条書き化。
- `drop_paragraphs`: `{"281":[2]}` 不要段落を削除。

## 背面パネル `bg_panels`
配列。各要素は次のどちらか：
- 明示座標: `{"behind_id":307,"box_cm":[21.05,1.85,8.5,17.0],"color":"FFFFFF","to_back":true}`（右カラム白板）
- 対象の背後: `{"behind_id":216,"color":"FFFFFF","alpha":84,"pad_cm":0.14,"round":true}`（POINT視認性）

## その他
- `hide_ids`: `[116]` 指定id非表示。
- `text_shadow`: `[{"ids":[25],"alpha":85,"blur":5,"dist":3}]` 文字影（キャッチ視認性）。
- `relabels`: `{"307":{"5,0":"バルコニー面積"}}` テーブルのラベル差し替え（"行,列"）。
- `bring_front`: `[139]` 最前面へ。
- `scrims`: 写真上の半透明帯（**恒久ルールでメインキャッチには使わない**）。
- `caption_style` / `point_panel` / `badge_snap` / `move`: 追加微調整（sample と place_images.py 参照）。
