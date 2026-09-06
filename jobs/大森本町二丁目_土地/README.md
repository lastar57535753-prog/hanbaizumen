# 大森本町二丁目 売地（販売図面ジョブ）

前セッション（2026-09-06）で土地テンプレを作るときに通した実物件。
写真と一部の値（価格・駅・周辺施設）はまだ入っていない。

```bash
cd jobs/大森本町二丁目_土地
S=../../skills/property-mysoku-generator
python3 $S/scripts/build_all.py $S/assets/template_land.pptx data.json images.json 大森本町二丁目_販売図面.pptx --pictograms point,note
```

写真が揃うまでは `--allow-missing --qc-warn` を付けると穴あきのまま出せる。

## 残り
- 写真（現地・前面道路・周辺）を images.json の 116 / 32 / 33 に、公図か区画図を 139 に入れて hide_ids から外す
- data.json の PRICE / TSUBO_PRICE / STATION1 / WALK1 / SPOT1〜4
- 物件概要の値は references/land-keys.md の例から復元したもの。資料で再確認する
