# hanbaizumen

センチュリー21 ラスターハウスの**販売図面（マイソク）**を作るためのリポジトリ。

| ディレクトリ | 中身 |
|---|---|
| `skills/property-mysoku-generator/` | 販売図面スキル本体（A4横1枚）。これを配れば単体で動く |
| `pictograms/` | ピクトグラム275点のマスター（SVG＋PNG＋一覧） |
| `scripts/` | 素材の作り直しと確認用のツール |
| `assets/fonts/` | 折り返し確認用の日本語フォント（Noto Sans/Serif JP・SIL OFL） |

## 使う

```bash
cd skills/property-mysoku-generator
python scripts/build_all.py assets/template_mansion.pptx 物件_data.json 物件_images.json 出力.pptx \
       --pictograms point,note --agent tokunaga
```

詳しくは `skills/property-mysoku-generator/SKILL.md`。

## この環境について

- PDF書き出しには LibreOffice Impress が要る。無ければ `--no-pdf` で PPTX まで作れる。
- 写真を Dropbox の共有リンクで渡すには、環境のネットワーク許可リストに
  `dropbox.com` / `dropboxusercontent.com` を足す必要がある
  （[設定方法](https://code.claude.com/docs/en/claude-code-on-the-web)）。
- セッション開始時に `.claude/hooks/session_start.sh` が不足パッケージを入れ、
  上の2点が使えるかを報告する。
