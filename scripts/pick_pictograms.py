# -*- coding: utf-8 -*-
"""物件データからピクトグラムを自動で選ぶ。

usage:
  python pick_pictograms.py <data.json> [-o pictograms_out.json] [--color gold] [--max 12]
  python pick_pictograms.py --text "オートロック・宅配ボックス・ペット可"

やること:
  1) LIFE INFORMATION の各行（SPOT1..SPOT7）に、施設種別のピクトグラムを1つずつ割り当てる
  2) POINT・備考・キャッチ・物件概要の文面を走査して、特徴ピクトグラムを拾う
  3) 「有無」で決まる項目（PET/ELEVATOR/PARKING/TRUNK 等）は値を見て判定する
     → 「不可」「無」「なし」なら**採用しない**（ペット不可の物件にペット可アイコンを出さない）

出力は images.json に差し込める形の JSON と、人が読める採用理由つきレポート。
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CATALOG = os.path.join(ROOT, "pictograms", "catalog.json")

# LIFE INFORMATION 行（施設名キー → 距離キー）
LIFE_KEYS = [(f"SPOT{i}", f"SPOT{i}_D") for i in range(1, 8)]
# 自由文として走査する項目
TEXT_KEYS = ([f"POINT{i}" for i in range(1, 7)] + [f"NOTE{i}" for i in range(1, 6)] +
             ["CATCH1", "CATCH2", "STRUCTURE", "ZONING", "STATUS", "HANDOVER", "MGMT_TYPE"])
# 「有無」で決まる項目 → (ピクトグラムkey)
FLAG_FIELDS = {"PET": "pet_ok", "ELEVATOR": "elevator", "PARKING": "parking",
               "TRUNK": "trunk_room", "BIKE": "bike_parking", "MOTO": "moto_parking"}
# 否定を表す値（これらを含む場合は採用しない）
NEGATIVE = ("不可", "無し", "なし", "無（", "×", "ありません")


def is_negative(value):
    v = str(value).strip()
    if v in ("無", "-", "―", ""):
        return True
    return any(n in v for n in NEGATIVE)


def load_catalog():
    with open(CATALOG, encoding="utf-8") as f:
        return json.load(f)


def match_terms(text, items, cats=None):
    """text に含まれる match 語からピクトグラムを拾う。(item, ヒットした語) のリスト。"""
    hits = []
    for it in items:
        if cats and it["cat"] not in cats:
            continue
        found = [m for m in it["match"] if m in text]
        if found:
            hits.append((it, found))
    return hits


def pick_line(text, items, cats=None, used=None):
    """1行につき1つだけピクトグラムを選ぶ（POINT・備考の行頭用）。

    優先順位は (rank, ヒットした語の長さ)。rank は catalog.json の任意項目で、
    「富士山眺望」「最上階」のような売りになる特徴に 2 を付けてある。
    used に既出の key を渡すと、同じ絵が1枚の図面で二度出るのを避ける。"""
    hits = match_terms(text, items, cats=cats)
    if not hits:
        return None, []
    def score(h):
        it, found = h
        return (0 if used and it["key"] in used else 1,
                it.get("rank", 1),
                max(len(m) for m in found))
    it, found = max(hits, key=score)
    return it, found


def pick_life(data, items, fallback=None):
    """LIFE INFORMATION の各行に施設アイコンを1つ割り当てる。

    施設名がどの match 語にも当たらない場合は fallback（汎用ピン）を使い、
    アイコンの無い行が出ないようにする。"""
    rows = []
    for slot, (name_key, dist_key) in enumerate(LIFE_KEYS, start=1):
        name = str(data.get(name_key, "")).strip()
        if not name:
            continue
        hits = match_terms(name, items, cats={"life", "access"})
        # 一番長い語で当たったものを採る（「小学校」＞「学校」のように具体的な方を優先）
        best = max(hits, key=lambda h: max(len(m) for m in h[1])) if hits else None
        if best is None and fallback:
            best = (fallback, [])
        rows.append({"slot": slot, "spot": name, "distance": data.get(dist_key, ""),
                     "key": best[0]["key"] if best else None,
                     "label": best[0]["label"] if best else None,
                     "icon": best[0]["icon"] if best else None,
                     "matched": best[1] if best else [],
                     "is_fallback": bool(best and not best[1])})
    return rows


def pick_features(data, items, limit):
    """POINT・備考・概要から特徴ピクトグラムを拾う。"""
    picked = {}

    def add(item, why):
        cur = picked.setdefault(item["key"], {"key": item["key"], "label": item["label"],
                                              "icon": item["icon"], "cat": item["cat"],
                                              "why": [], "score": 0})
        cur["why"].append(why)
        cur["score"] += 1

    # 1) 有無フィールド（値が否定なら採用せず、さらに拒否権を持たせる）
    #    物件概要が一次情報。他社図面から転記したPOINTに別物件の「ペット可」等が
    #    残っていても、概要が「不可」ならアイコンを出さない。
    by_key = {it["key"]: it for it in items}
    vetoed = {}
    for field, pkey in FLAG_FIELDS.items():
        if field in data and pkey in by_key:
            val = data[field]
            if is_negative(val):
                vetoed[pkey] = f"{field}={val}"
            else:
                add(by_key[pkey], f"{field}={val}")

    # 2) 自由文の走査（拒否された項目は拾わない）
    for k in TEXT_KEYS:
        text = str(data.get(k, ""))
        if not text.strip():
            continue
        for it, found in match_terms(text, items, cats={"common", "unit", "site", "deal", "access"}):
            if it["key"] in vetoed:
                continue
            add(it, f"{k}「{'・'.join(found)}」")

    ranked = sorted(picked.values(), key=lambda x: (-x["score"], x["cat"], x["key"]))
    return (ranked[:limit] if limit else ranked), vetoed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data", nargs="?", help="物件の data.json")
    ap.add_argument("--text", help="data.json の代わりに自由文から拾う")
    ap.add_argument("-o", "--out", help="結果を書き出すJSONパス")
    ap.add_argument("--color", default="gold", choices=["sumi", "gold", "gold_light", "white"])
    ap.add_argument("--max", type=int, default=12, help="特徴ピクトグラムの最大数（0で無制限）")
    args = ap.parse_args()

    if not args.data and not args.text:
        ap.error("data.json か --text のどちらかを指定してください")

    catalog = load_catalog()
    items = catalog["items"]
    data = {}
    if args.data:
        with open(args.data, encoding="utf-8") as f:
            data = json.load(f)
    if args.text:
        data["POINT1"] = args.text

    fb_key = catalog.get("life_fallback", {}).get("key")
    fallback = next((it for it in items if it["key"] == fb_key), None)
    life = pick_life(data, items, fallback) if args.data else []
    feats, vetoed = pick_features(data, items, args.max)

    def png(key):
        return os.path.join("pictograms", "png", args.color, key + ".png")

    result = {
        "color": args.color,
        "life_rows": [dict(r, png=png(r["key"]) if r["key"] else None) for r in life],
        "features": [dict(f, png=png(f["key"])) for f in feats],
        "vetoed": vetoed,
    }

    print("── LIFE INFORMATION 行のアイコン ──")
    if not life:
        print("   （SPOT1..SPOT7 が空です）")
    for r in life:
        mark = "⚠ 汎用ピン" if r.get("is_fallback") else ("✅" if r["key"] else "⚠ 該当なし")
        print(f"   {mark} SPOT{r['slot']}: {r['spot']}"
              + (f"  → {r['label']} ({r['icon']})" if r["key"] else ""))
    print(f"\n── 物件の特徴ピクトグラム（{len(feats)}件・{args.color}）──")
    for f in feats:
        print(f"   ✅ {f['label']:<14} {f['icon']:<52} ← {' / '.join(f['why'][:2])}")
    if vetoed:
        print(f"\n── 物件概要が「無」なので出さなかったもの ──")
        for k, why in vetoed.items():
            print(f"   ⛔ {k}  ({why})")
    miss = [r for r in life if not r["key"] or r.get("is_fallback")]
    if miss:
        print(f"\n⚠ {len(miss)}件のLIFE行は施設名を特定できず汎用ピンになりました"
              f"（{'、'.join(r['spot'] for r in miss)}）。"
              f"catalog.json の match に施設名を足すと専用アイコンになります。")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n保存: {args.out}")


if __name__ == "__main__":
    main()
