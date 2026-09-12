# 土地版（template_land.pptx）のキー一覧

マンション版とは **物件概要表23行と左上ラベル・間取図脇の小表示だけ** が違う。
意匠（座標・書体・色・帯・バッジ・キャプション）は共通なので、
`images.json` の書き方も `references/images-json-options.md` のまま使える。

テンプレは `scripts/make_land_template.py` が `template_mansion.pptx` から生成する。
マンション版のテンプレを直したら、こちらも作り直すこと。

```bash
python scripts/make_land_template.py assets/template_mansion.pptx assets/template_land.pptx
```

## 物件概要表（23行）

| キー | ラベル | 例 |
|---|---|---|
| ADDRESS | 所 在 地 | 大田区大森本町二丁目6477番338 |
| RIGHT | 権　利 | 所有権 |
| LAND_AREA | 敷地面積 | 49.01㎡ （約14.83坪） |
| TSUBO_PRICE | 坪 単 価 | 320万円 |
| CHIMOKU | 地　目 | 宅地 |
| TOPOGRAPHY | 地　勢 | 平坦 |
| ZONING | 用途地域 | 近隣商業地域 |
| BUILDING_RATIO | 建ぺい率 | 80％ |
| FLOOR_RATIO | 容 積 率 | 300％ |
| FIRE_ZONE | 防火指定 | 準防火地域 |
| HEIGHT_ZONE | 高度地区 | 第3種高度地区 |
| CITY_PLAN | 都市計画 | 市街化区域 |
| ROAD_DIR | 接道方位 | 南西 |
| ROAD_WIDTH | 接道幅員 | 4.0m |
| ROAD_FRONT | 接面距離 | 5.2m |
| PRIVATE_ROAD | 私道負担 | 無 |
| SETBACK | セットバック | 要（約0.5m） |
| BUILD_COND | 建築条件 | 無 |
| WATER_SEWER | 上下水道 | 公営・本管引込済 |
| GAS | ガ　ス | 都市ガス |
| SPECIAL | 特　記 | 隣棟間の確認書あり |
| STATUS | 現　況 | 更地 |
| HANDOVER | 引　渡 | 相談 |

## 間取図脇の小表示（id28）

`LAND_TSUBO`（約14.83坪）／`AREA_MINI`（49.01㎡）／`BUILDING_RATIO`・`FLOOR_RATIO`。

## 字数の上限（実測値・これを超えると崩れる）

枠は増やせないので、**入る長さに収める**のが前提。全角=1字、半角=0.5字。

| 場所 | 上限 | 超えると |
|---|---|---|
| 物件概要表の値（8.5pt・幅6.1cm） | **19.7字** | 行が2行になって表が伸び、備考がLIFEに突っ込む |
| 備考 NOTE1〜4（8pt・幅5.8cm） | **19.7字** | 同上。preflight が「LIFE見出し×備考本文」の被りで止める |
| キャッチ CATCH1/2（幅は間取図の左端まで） | **約22字** | 右の写真枠の下に潜って読めなくなる |

`scripts/textfit.py` で事前に測れる。

```python
import textfit; textfit.em("49.01㎡ （約14.83坪）")   # -> 18.5
```

## マンション版と共通のキー

BUILDING / FLOOR_SHORT（区画名に流用）/ PRICE / LINE・STATION・WALK /
CATCH1・2 / POINT1〜8 / NOTE1〜4 / SPOT1〜4・SPOT1_D〜 / CAP_MAIN・CAP1〜6 / AGENT_*。

## 土地で気をつけること

- **接道・私道負担・セットバック・上下水道・ガスは役所調査と現地確認が要る。**
  古い重要事項説明書の記載をそのまま載せない。用途地域や容積率は改定されている
  ことがあるので、取得年が古い資料は備考に「要再確認」と明記する。
- 間取図の枠（id139）は土地では空くので、**公図・区画図・現地写真**のどれかを入れる。
  空のままにすると、テンプレの見本写真が残って `place_images.py` が止める。
- 現況が更地かどうかは、固定資産税課税明細の家屋欄と「非住宅用地」表記で裏が取れる。
