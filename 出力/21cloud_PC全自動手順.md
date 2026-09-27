# 21Cloud 全自動登録：PCでやること

## 準備（最初の1回だけ）
1. **Chrome で21Cloudにログインしておく**（Claude in Chrome 拡張が入っていること）
2. **このリポジトリをPCに取り込む**（PowerShell）
   ```powershell
   cd $HOME\Desktop
   git clone -b claude/happy-archimedes-g1g1nb https://github.com/lastar57535753-prog/hanbaizumen.git
   cd hanbaizumen
   ```
   - git が使えない場合：GitHub でブランチ `claude/happy-archimedes-g1g1nb` を開き、「Code → Download ZIP」でダウンロードして展開する。
3. **Claude Code を Chrome 連携付きで起動する**
   ```powershell
   claude --chrome
   ```

## Claude Code に貼る指示文（これだけでOK）
```
出力/21cloud_skill/全自動_実行指示.md を読んで、その指示どおりに17住戸すべてを21Cloudに登録してください。
最初に python 出力/21cloud_skill/check_21cloud.py 出力 を実行し、NGがないことを確認してから始めること。
ログイン画面以外では私に確認せず、最後まで進めてください。
```

## 途中で頼まれる可能性がある操作
- **21Cloudのログイン**：セッションが切れた場合。
- **写真の自動アップロード用のChrome再起動**：Chrome拡張から写真を選べない場合に頼まれます。すべてのChromeを閉じてから、PowerShellで次を実行し、開いたChromeで21Cloudにログインしてください。
  ```powershell
  & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="$HOME\chrome-21cloud"
  ```
  あわせて `pip install playwright` を実行します（ブラウザ本体のダウンロードは不要）。

## 結果
`出力/21cloud登録ログ.md` に、住戸ごとの状態が記録されます。状態は次のいずれかです。
- 出稿済
- 一時保存（理由つき）
- 写真待ち

## 数値の食い違いについて
依頼者の指示により、数値の食い違いは**販売図面の値で入力し、出稿まで進めます**。
一時保存で止まるのは、次の2つの場合だけです。
- 必須の数値が、販売図面にもどこにもない
- システムのエラー

食い違いがあった項目は、ログに「他の値」として残します。元付と話すときの参考にしてください。
