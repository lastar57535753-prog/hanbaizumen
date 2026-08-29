# -*- coding: utf-8 -*-
"""物件フォルダの素材を種類ごとに仕分けて列挙する。

usage:
    python collect_assets.py "<物件フォルダの絶対パス>"
    python collect_assets.py "<パス>" --json

やること（機械的な仕分けだけ）:
  - 写真候補（採用フォルダがあればそこ優先。無ければ全体スキャン＋除外フィルタ）
  - 間取図 / QR / レインズ図面(既存マイソク) / 謄本(登記) / カンテイ / その他資料
  中身の判定（外観かリビングか等）や本文の読み取りはしない。それはClaudeが画像/PDFを
  見て行う。このスクリプトは「どのファイルがどのバケツか」を確定するだけ。
"""
import sys, io, os, re, json, argparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

IMG_EXT = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".heic", ".tif", ".tiff"}
MIN_PHOTO_BYTES = 50 * 1024

RE_QR       = re.compile(r"^QR[_\-]", re.I)
RE_AI       = re.compile(r"^(Gemini_Generated|ChatGPT|DALL)", re.I)
RE_MADORI   = re.compile(r"(間取|マドリ|madori|平面図|room\s*plan)", re.I)
RE_KYOGO    = re.compile(r"(競合|マイソク|他社|事例|成約|周辺)")
RE_PICT     = re.compile(r"[\\/](◆ピクト◆|エイカツ)[\\/]")
RE_QR_ANY   = re.compile(r"(^|[\\/])QR[_\-]", re.I)

# 資料PDF/pptxの判定
RE_KANTEI   = re.compile(r"(カンテイ|kantei|東京カンテイ)", re.I)
RE_TOHON    = re.compile(r"(全部事項|登記|謄本|要約書|地積測量)")
RE_REINS    = re.compile(r"(レインズ|reins|販売図面|マイソク|物件概要)", re.I)
RE_CONTRACT = re.compile(r"(媒介契約|委任状|活動計画|活動報告|重要事項|重説|契約書|査定書?)")


def walk_files(root):
    for dp, _dn, fn in os.walk(root):
        for f in fn:
            yield os.path.join(dp, f)


def rel(p, root):
    try:
        return os.path.relpath(p, root)
    except ValueError:
        return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    root = os.path.abspath(args.folder)
    if not os.path.isdir(root):
        print(f"フォルダが見つからない: {root}"); sys.exit(1)

    saiyo = None
    for dp, dn, _fn in os.walk(root):
        for d in dn:
            if d.strip() == "採用":
                saiyo = os.path.join(dp, d)
                break
        if saiyo:
            break

    buckets = {"photos": [], "photos_excluded": [], "floorplan": [], "qr": [],
               "reins_mysoku": [], "tohon": [], "kantei": [], "contracts": [], "other": []}

    for p in walk_files(root):
        name = os.path.basename(p)
        ext = os.path.splitext(name)[1].lower()
        try:
            size = os.path.getsize(p)
        except OSError:
            continue
        r = rel(p, root)
        item = {"name": name, "path": p, "rel": r, "size": size}

        # 間取図・QR は拡張子問わず名前で先取り
        if RE_QR.search(name) or RE_QR_ANY.search(r):
            buckets["qr"].append(item); continue
        if RE_MADORI.search(name):
            buckets["floorplan"].append(item); continue

        if ext in IMG_EXT:
            reason = None
            if RE_AI.search(name):            reason = "AI生成"
            elif RE_PICT.search(r):           reason = "素材庫/エイカツ"
            elif RE_KYOGO.search(name) or RE_KYOGO.search(r): reason = "競合/事例/成約"
            elif size < MIN_PHOTO_BYTES:      reason = f"{size//1024}KB(小)"
            if reason:
                item["excluded_reason"] = reason
                buckets["photos_excluded"].append(item)
            else:
                buckets["photos"].append(item)
            continue

        # 資料系（pdf / pptx / docx / xlsx など）
        if RE_KANTEI.search(name):            buckets["kantei"].append(item)
        elif RE_TOHON.search(name):           buckets["tohon"].append(item)
        elif RE_REINS.search(name):           buckets["reins_mysoku"].append(item)
        elif RE_CONTRACT.search(name):        buckets["contracts"].append(item)
        else:                                 buckets["other"].append(item)

    # 採用フォルダがあれば、写真バケツは採用配下だけに絞る
    saiyo_note = ""
    if saiyo:
        in_saiyo = [x for x in buckets["photos"] if os.path.commonpath([x["path"], saiyo]) == saiyo]
        buckets["photos"] = in_saiyo
        saiyo_note = f"採用フォルダあり → 写真は採用配下のみ採用: {rel(saiyo, root)}"
    else:
        saiyo_note = "採用フォルダ無し → 全体スキャン結果を提示（新太郎さんの選別が未実施の可能性）"

    for k in buckets:
        buckets[k].sort(key=lambda x: (x["rel"]))

    if args.json:
        print(json.dumps({"root": root, "saiyo": saiyo, "saiyo_note": saiyo_note,
                          "buckets": buckets}, ensure_ascii=False, indent=2))
        return

    def show(title, key, cap=None):
        items = buckets[key]
        print(f"\n■ {title}（{len(items)}）")
        for x in (items[:cap] if cap else items):
            kb = x["size"] // 1024
            extra = f"  ×{x['excluded_reason']}" if x.get("excluded_reason") else ""
            print(f"   {x['rel']}  [{kb}KB]{extra}")
        if cap and len(items) > cap:
            print(f"   … 他 {len(items)-cap} 件")

    print(f"物件フォルダ: {root}")
    print(saiyo_note)
    show("写真候補（枠割当の対象）", "photos")
    show("間取図", "floorplan")
    show("QRコード", "qr")
    show("レインズ図面／既存マイソク（共用部の転記元・専有部は転記禁止）", "reins_mysoku")
    show("謄本／登記（※専有面積は内法。壁芯を転記しないこと）", "tohon")
    show("カンテイ", "kantei")
    show("写真から除外したもの", "photos_excluded")
    show("契約・報告書など（マイソク非対象）", "contracts", cap=10)
    show("その他", "other", cap=10)
    print("\n→ 写真の外観/リビング/浴室…の判定と枠割当はこのあとClaudeが画像を見て行う。")


if __name__ == "__main__":
    main()
