# 21Cloud 全自動登録：PCでやること

## 準備（最初の1回だけ）
1. **Python 3 と git が入っていること**を確認する（PowerShell で `python --version` と `git --version`）
2. **このリポジトリをPCに取り込む**（PowerShell）
   ```powershell
   cd $HOME\Desktop
   git clone -b claude/happy-archimedes-g1g1nb https://github.com/lastar57535753-prog/hanbaizumen.git
   cd hanbaizumen
   ```
   - git が使えない場合：GitHub でブランチ `claude/happy-archimedes-g1g1nb` を開き、「Code → Download ZIP」でダウンロードして展開する。
3. **Python の Playwright を入れる**（ブラウザ本体のダウンロードは不要）
   ```powershell
   pip install playwright pillow
   ```
4. **自動操作用のChromeを起動し、そのChromeで21Cloudにログインする**
   - 普段のChromeとは別の窓で開きます。初回だけログインが必要です。
   ```powershell
   & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="$HOME\chrome-21cloud" https://sfa.century21.ne.jp/chukaio/21cloud/bukken_TypeSelectBaibai
   ```
5. **Claude Code を起動する**（hanbaizumen フォルダで実行）
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
- **21Cloudへの再ログイン**：セッションが切れた場合。手順4のChromeでログインしてください。

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
