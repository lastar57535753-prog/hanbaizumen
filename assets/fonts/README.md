# 同梱フォント

| ファイル | 用途 | ライセンス |
|---|---|---|
| `NotoSerifJP[wght].ttf` | 日本語の行折り返し計測（明朝＝HGS明朝Eに近い字幅） | SIL Open Font License 1.1 |
| `NotoSansJP[wght].ttf` | ピクトグラム一覧のラベル描画 | SIL Open Font License 1.1 |

販売図面そのものに使うフォントではない。**改行位置の計算を環境に依存させないため**に同梱している。

`place_images.py` の `jp_wrap` は行幅の計測に日本語フォントを使うが、OSにフォントが
無い環境（Claude on the web のLinuxコンテナ等）では PIL の既定ビットマップフォントに
落ち、1字あたり5px（実際は14px）と誤って測る。その結果、25字しか入らない枠に
37〜47字を1行として詰めてしまう。同梱フォントを使えばどの環境でも同じ位置で折り返す。

取得元: [google/fonts](https://github.com/google/fonts) （ofl/notoserifjp, ofl/notosansjp）
