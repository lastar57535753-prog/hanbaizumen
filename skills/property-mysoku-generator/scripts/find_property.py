# -*- coding: utf-8 -*-
"""★媒介物件フォルダ から物件フォルダを「あいまい一致」で探す。

usage:
    python find_property.py "シェトワ大森"
    python find_property.py "大森海岸パークハウス" --root "C:/Users/Surface/Dropbox/★媒介物件フォルダ"
    python find_property.py "シェトワ大森" --json      # 機械可読出力

なぜ glob 単独で不可能か:
  物件フォルダの深さが 2/3/4 で不揃い。区分階層(マンション/収益物件等/土地戸建て)が
  有る枝と無い枝(４．動き有・５．他社OP)が混在。さらにアーカイブ中間コンテナ
  (★契約済 等)の"子"が物件フォルダになる枝がある。

方針:
  候補になり得る「物件フォルダ」を列挙 → 正規化した名前でスコアリング → 上位を提示。
  完全一致は誤字・表記ゆれで機能しないので、必ず人が1回確認する前提。
"""
import sys, io, os, re, json, argparse, unicodedata

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# 物件素材フォルダのルート。アカウントごとに異なるので環境変数で上書きできる。
#   優先順位: --root 引数 > 環境変数 MYSOKU_ROOT > 既定値(下記)
# 別アカウントで使うときは MYSOKU_ROOT に「媒介物件フォルダ」等のパスを設定するか
# --root で毎回渡すこと。
DEFAULT_ROOT = os.environ.get("MYSOKU_ROOT", r"C:/Users/Surface/Dropbox/★媒介物件フォルダ")

# ルート直下の非物件コンテナ（物件フォルダではない）
ROOT_SKIP = {
    "◆ピクト◆", "スキャン資料", "販売図面2025", "販売図面素材集", "営業活動報告書",
    "外部依頼（販売図面、間取りなど）", "購入お客様情報", "重要事項に係る調査報告書",
    "バクったファイル　大田区　品川区", "★媒介物件フォルダ",
}
# 種別（区分）階層の名前
CATEGORY = {"マンション", "収益物件等", "土地戸建て"}
# アーカイブ中間コンテナ（この"子"が物件フォルダ）。表記ゆれ6種。
ARCHIVE = re.compile(r"^(★契約済|★契約終了|★成約|◎契約済|・成約|成約・媒介終了)")
# どこでも除外
NAME_SKIP = re.compile(r"^(名称未設定フォルダ|新しいフォルダ)")

# 名寄せ（重複物件）: ４．動き有 側を従とする → 主(区マンション側)を優先表示
DUP_PREFER_MAIN = ["デュオヴェール大森山王502", "ジオ品川天王洲510", "秀和御殿山レジデンス204"]


def norm(s):
    """あいまい一致用の正規化。実在の誤字・表記ゆれを吸収する。"""
    s = unicodedata.normalize("NFKC", s)
    s = s.lower()
    # 実在の誤字・ゆれ
    s = s.replace("太田", "大田")          # グランフォルム太田/大田中央
    s = s.replace("シェトア", "シェトワ")   # シェトワ/シェトア大森
    s = s.replace("ケ", "ヶ")              # 雪ケ谷/雪ヶ谷
    # 記号・空白・長音・中黒を除去
    s = re.sub(r"[\s　・･\-ー－_,、。／/（）()【】\[\]]+", "", s)
    return s


def norm_query(q):
    # 先にNFKC（全角英数→半角）してからノイズ（号室・様・取引態様・英数字）を落とす
    q = unicodedata.normalize("NFKC", q)
    q = re.sub(r"(専属専任|専任|一般)(媒介)?", "", q)
    q = re.sub(r"[0-9A-Za-z]*号(室)?", "", q)
    q = q.replace("様", "")
    return norm(q)


def has_content(path):
    """空フォルダ除外。ファイル or サブフォルダが1つでもあれば内容あり。"""
    try:
        for _ in os.scandir(path):
            return True
    except OSError:
        pass
    return False


def collect_candidates(root):
    """物件フォルダ候補を列挙する。ルート直下の各枝を種別ごとに歩く。"""
    cands = []
    if not os.path.isdir(root):
        return cands
    for top in os.scandir(root):
        if not top.is_dir() or top.name in ROOT_SKIP:
            continue
        # top = 「１．大田区」「４．動き有」「５．他社OP」など
        _walk_branch(top.path, cands, depth=0)
    return cands


def _walk_branch(path, cands, depth, max_depth=4):
    """各エントリを見て、物件フォルダなら候補に、コンテナなら再帰する。"""
    if depth > max_depth:
        return
    try:
        entries = list(os.scandir(path))
    except OSError:
        return
    for e in entries:
        if not e.is_dir():
            continue
        name = e.name
        if NAME_SKIP.match(name):
            continue
        # 区分階層 / アーカイブコンテナ は"素通り"して中を歩く（候補にしない）
        if name in CATEGORY or ARCHIVE.match(name):
            _walk_branch(e.path, cands, depth + 1, max_depth)
            continue
        # ここは物件フォルダ候補
        if has_content(e.path):
            cands.append(e.path)


def score(query_n, name_n):
    """正規化済み同士の一致度。包含を最優先し、共通文字割合で補う。"""
    if not query_n or not name_n:
        return 0.0
    if query_n == name_n:
        return 1.0
    if query_n in name_n:
        return 0.9 + 0.1 * (len(query_n) / len(name_n))
    if name_n in query_n:
        return 0.85
    # 文字bigramの重なり（順不同のゆれに強い）
    def grams(s):
        return {s[i:i+2] for i in range(len(s) - 1)} or {s}
    a, b = grams(query_n), grams(name_n)
    inter = len(a & b)
    if not inter:
        return 0.0
    return 0.7 * (2 * inter / (len(a) + len(b)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args()

    qn = norm_query(args.query)
    cands = collect_candidates(args.root)
    scored = []
    for p in cands:
        base = os.path.basename(p)
        s = score(qn, norm_query(base))
        if s > 0:
            scored.append((s, p, base))
    scored.sort(key=lambda x: (-x[0], len(x[2])))
    top = scored[: args.top]

    if args.json:
        print(json.dumps(
            {"query": args.query, "root": args.root, "count": len(cands),
             "matches": [{"score": round(s, 3), "path": p, "name": b} for s, p, b in top]},
            ensure_ascii=False, indent=2))
        return

    print(f"検索語: {args.query}   （候補フォルダ {len(cands)}件を走査）")
    if not top:
        print("一致なし。表記ゆれの可能性 → 別の呼び方で再検索するか、直接パスを指定してください。")
        return
    print("候補（スコア降順）:")
    for i, (s, p, b) in enumerate(top, 1):
        mark = "★" if s >= 0.9 else "  "
        rel = os.path.relpath(p, args.root)
        print(f" {mark}{i}. [{s:.2f}] {b}")
        print(f"        {rel}")
    print("\n→ このパスで合っているか必ず1回確認してから素材収集に進むこと。")


if __name__ == "__main__":
    main()
