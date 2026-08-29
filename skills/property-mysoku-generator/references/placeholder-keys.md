# data.json のキー一覧（66キー）

穴あきテンプレ `assets/template_mansion.pptx` の `{{KEY}}` に対応。値が空／キー無しの項目は `fill.py` が **`【要確認】` 赤字**で残す（＝推測で埋めない）。実例は `assets/sample_data.json`。

## ヘッダー
| キー | 内容 | 例 |
|---|---|---|
| BUILDING | マンション名 | アトラスタワー五反田 |
| FLOOR_SHORT | 階（短） | 30F |
| PRICE | 価格（万円・カンマ区切り、単位なし） | 54,800 |

## アクセス（最大3路線）
`LINE1/STATION1/WALK1` 〜 `LINE3/STATION3/WALK3`。WALK は分数のみ（数字）。
例: `"LINE1":"JR山手線","STATION1":"五反田駅","WALK1":"4"`

## キャッチ・見出し
| キー | 内容 |
|---|---|
| CATCH1 / CATCH2 | メインキャッチ2行（id25。**間取図に被らせない**＝簡潔に） |
| DIRECTION | 向き（例 南向き） |
| MADORI | 間取り（例 3LDK） |
| AREA_MINI | 面積（ヘッダ近くの小表示、例 109.14㎡） |
| TERRACE | バルコニー面積（例 29.73㎡） |

## 写真キャプション
`CAP_MAIN`（ヒーロー）, `CAP1`〜`CAP6`。写真の内容に合わせる（外観／眺望／リビング／浴室／内廊下／ラウンジ 等）。

## POINT（訴求文・最大8）
`POINT1`〜`POINT8`。箱(id216)に収まるよう**簡潔に**。事実ベースで自前作成（他社の創作文を丸写ししない）。

## 物件概要（23項目）
| キー | 内容 |
|---|---|
| ADDRESS | 所在地 |
| RIGHT | 権利（所有権 等） |
| LAND_AREA | 敷地面積（㎡＋坪） |
| ZONING | 用途地域 |
| AREA | 専有面積（**壁芯**、㎡＋坪。坪=㎡×0.3025） |
| STRUCTURE | 構造・規模 |
| FLOOR | 所在階 |
| BUILT | 築年月（西暦＋和暦） |
| UNITS | 総戸数 |
| DEVELOPER | 分譲会社 |
| BUILDER | 施工会社 |
| MGMT_CO | 管理会社 |
| MGMT_TYPE | 管理形態（全部委託（日勤）等） |
| MGMT_FEE | 管理費（月額） |
| REPAIR_FEE | 修繕積立金（月額） |
| PARKING | 駐車場 |
| PET | ペット（不明なら空欄→要確認） |
| ELEVATOR | エレベーター |
| TRUNK | トランクルーム |
| STATUS | 現況（空室／居住中 等） |
| HANDOVER | 引渡（即時／相談 等） |

## 備考（最大4行）
`NOTE1`〜`NOTE4`。**折り返さない短い行**にする（1行1項目）。

## LIFE INFORMATION（周辺4施設）
`SPOT1`〜`SPOT4`（施設名）と `SPOT1_D`〜`SPOT4_D`（距離、例「徒歩 2分 （約160m）」）。資料に無ければ埋めない。
