# 21Cloud フォームフィールド対応表

実機（2026年7月時点）で確認したID・文字数制限。画面改修で変わる可能性があるため、
入力前に `doc.querySelector('#ID')` で存在確認し、無ければ類似name/placeholderで探し直すこと。

## キャッチコピー登録モーダル（iframe内）

| フィールドID | 内容 | 文字数上限 |
|---|---|---|
| txtSalesPointForCopy | セールスポイント（基本・コピー元） | 500 |
| txtSalesPoint100 | セールスポイント100 | 100 |
| txtSalesPoint80 | セールスポイント80 | 80 |
| txtSalesPointSheet | 物件シート用セールスポイント | 72 |
| txtHomesSalesPoint | HOME'S物件の特徴 | 50 |
| txtAthomeStaffComment | at homeおすすめコメント | 100 |
| txtAthomeBukkenCharmPoint | at home ネット向けアピール | 500 |
| txtYahooStaffComment | Yahoo!スタッフおすすめポイント | 500 |
| txtStaffCommentForCopy | スタッフコメント（コピー元） | 500 |
| txtHomesStaffComment | HOME'Sスタッフコメント | 400 |
| txtBikoForCopy | 備考（コピー元） | 300 |
| txtBiko300 | 備考300 | 300 |
| txtHomesBikou | HOME'S備考 | 160 |
| txtAthomeBikou | at home備考 | 300 |
| txtBikou40 | 備考40 | 40 |
| txtBikouSheet | 物件シート備考 | 100 |
| txtYahooOtherSummary | Yahoo!その他物件概要 | 1000 |

※基本の500字を書いてから各制限向けに要約・切り詰めていくと効率的。
※HOME'SスタッフコメントとYahoo!スタッフおすすめポイントには担当者名を入れる形式
（例:「担当の岩澤です。〜」）が通例。

## 画像登録モーダル（iframe内）

- スロットNのコメント: `#imageComment_N`（20字textarea）、`#imageComment100_N`（100字textarea）
- スロットNのカテゴリ: スロット行内の最初のselect（idなし。imageComment100_Nから親を遡り、selectを含む行で `querySelectorAll('select')[0]`）
- 2番目のselectはYahoo!画像カテゴリ（任意）
- サムネイル: `img.left-icon`（src末尾 `…th.jpg`）
- 保存ボタン: テキスト「画像登録完了」のaタグ

### 画像カテゴリselectの値

| 値 | ラベル | 値 | ラベル |
|---|---|---|---|
| 7 | 玄関 | 21 | 洋室 |
| 4 | リビング | 22 | 和室 |
| 6 | バス | 37 | その他居室 |
| 5 | キッチン | 38 | その他内観 |
| 10 | トイレ | 16 | エントランス |
| 11 | 洗面台・洗面所 | 44 | ロビー |
| 12 | 収納 | 17 | 庭 |
| 9 | バルコニー | 18 | 駐車場 |
| 8 | 寝室 | 19 | その他共用部分 |
| 23 | 子供部屋 | 13 | 現地からの眺望 |
| 15 | その他 | 3 | 現地案内図 |

（間取り=1、外観=2 は専用スロットで固定されていることが多い）

## メインページ（iframe外）

| 要素 | 内容 |
|---|---|
| kakakuF | 価格（万円） |
| kyakuMark-0 / 1 / 2 | 客付可否ラジオ（1=客付可） |
| terraceMenseki | テラス面積㎡ |
| terraceShiyouryou | テラス使用料（無料=0） |

## 禁止文言（確認済み）

- 「希少」→ NG。保存時にチェックされ確認ダイアログが出る。
- 「穴場」→ OK（通過実績あり）。
- 不動産公取の禁止用語（完璧・万全・日本一・特選・厳選・格安・掘り出し・破格・完全・絶対等）は最初から使わない。
