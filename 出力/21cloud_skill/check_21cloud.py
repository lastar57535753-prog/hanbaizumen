"""21cloud入力.json を全住戸まとめて検査し、Chrome用の貼り付けJSも書き出す。"""
import json, glob, os, re, unicodedata

import sys
ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), ".."))
LIMITS = {
    "txtSalesPointForCopy": 500, "txtSalesPoint100": 100, "txtSalesPoint80": 80,
    "txtSalesPointSheet": 72, "txtHomesSalesPoint": 50, "txtAthomeStaffComment": 100,
    "txtAthomeBukkenCharmPoint": 500, "txtYahooStaffComment": 500,
    "txtStaffCommentForCopy": 500, "txtHomesStaffComment": 400, "txtBikoForCopy": 300,
    "txtBiko300": 300, "txtHomesBikou": 160, "txtAthomeBikou": 300, "txtBikou40": 40,
    "txtBikouSheet": 100, "txtYahooOtherSummary": 1000,
}
NG = ["希少", "完璧", "万全", "日本一", "特選", "厳選", "格安", "掘り出し", "破格", "完全",
      "絶対", "最高", "一流", "抜群", "当社だけ", "業界初", "No.1", "Ｎｏ．１", "超一等",
      "仲介手数料", "激安", "最上級", "至高", "究極", "唯一", "日本初", "特級"]
INTERNAL = ["透かし", "差替", "要確認", "未確認", "要許可", "社内", "TODO", "hold", "※確認", "図面値"]
CATS = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 21, 22, 23, 37, 38, 44}


def halfwidth(s):
    return [c for c in s if c not in "\n" and unicodedata.east_asian_width(c) in ("Na", "H")]


def check(path):
    errs, warns = [], []
    d = json.load(open(path, encoding="utf-8"))
    cm = d.get("comments", {})
    for k, lim in LIMITS.items():
        v = cm.get(k)
        if not v:
            errs.append(f"{k}: 空")
            continue
        n = len(v)
        if n > lim:
            errs.append(f"{k}: {n}/{lim} 超過")
        elif n < lim * 0.9:
            warns.append(f"{k}: {n}/{lim}（90%未満）")
        for w in NG:
            if w in v:
                errs.append(f"{k}: 禁止語「{w}」")
        for w in INTERNAL:
            if w in v:
                errs.append(f"{k}: 社内向け注記「{w}」が掲載文に入っている")
    hw = halfwidth(cm.get("txtAthomeStaffComment", ""))
    if hw:
        errs.append(f"txtAthomeStaffComment: 半角文字 {''.join(sorted(set(hw)))}")
    for k in ("txtHomesStaffComment", "txtYahooStaffComment"):
        if not cm.get(k, "").startswith("担当の岩澤です。"):
            warns.append(f"{k}: 「担当の岩澤です。」で始まっていない")
    imgs = d.get("images", [])
    for im in imgs + d.get("images_pending_permission", []):
        f = im.get("file", "")
        fp = f if f.startswith("/") else os.path.join(os.path.dirname(ROOT), f)
        if not os.path.isfile(fp):
            errs.append(f"画像なし: {f}")
        uf = im.get("upload_file")
        if not uf or not os.path.isfile(os.path.join(os.path.dirname(ROOT), uf)):
            errs.append(f"アップロード用写真なし: {uf or f}")
        elif ".." in uf or "work/" in uf.replace(os.sep, "/"):
            errs.append(f"アップロード用写真がリポジトリ外: {uf}")
        if im.get("category") not in CATS:
            errs.append(f"カテゴリ値不正: {f} {im.get('category')}")
        c20, c100 = im.get("comment20", ""), im.get("comment100", "")
        if len(c20) > 20:
            errs.append(f"comment20超過 {len(c20)}: {f}")
        if len(c100) > 100:
            errs.append(f"comment100超過 {len(c100)}: {f}")
        for w in NG:
            if w in c20 + c100:
                errs.append(f"画像コメント禁止語「{w}」: {f}")
        for w in INTERNAL:
            if w in c20 + c100:
                errs.append(f"画像コメントに社内向け注記「{w}」: {f}")
    for im in imgs:
        if "他社掲載" in im.get("file", ""):
            errs.append(f"要許可写真が許可済み側に入っている: {im['file']}")
    return d, errs, warns, len(imgs), len(d.get("images_pending_permission", []))


def js_comments(d):
    body = json.dumps(d["comments"], ensure_ascii=False, indent=1)
    return ("// 21Cloud キャッチコピー登録モーダルを開いた状態で javascript_tool に貼る\n"
            "(() => {\n"
            "const doc = [...document.querySelectorAll('iframe')].filter(f => f.offsetWidth > 300 && !f.id).pop().contentDocument;\n"
            f"const V = {body};\n"
            "const r = {};\n"
            "for (const [id, v] of Object.entries(V)) {\n"
            "  const el = doc.querySelector('#' + id);\n"
            "  if (!el) { r[id] = 'NOT FOUND'; continue; }\n"
            "  el.value = v;\n"
            "  ['input','keyup','change','blur'].forEach(ev => el.dispatchEvent(new Event(ev, {bubbles: true})));\n"
            "  r[id] = el.value.length + (el.maxLength > 0 ? '/' + el.maxLength : '');\n"
            "}\n"
            "return JSON.stringify(r);\n"
            "})();\n")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    rows = []
    for p in sorted(glob.glob(f"{ROOT}/*/*/21cloud入力.json")):
        rel = os.path.relpath(p, ROOT)
        try:
            d, e, w, ni, np_ = check(p)
        except Exception as ex:
            rows.append((rel, [f"読込エラー {ex}"], [], 0, 0, 0))
            continue
        open(os.path.join(os.path.dirname(p), "21cloud_コメント貼付.js"), "w", encoding="utf-8").write(js_comments(d))
        rows.append((rel, e, w, ni, np_, len(d.get("hold", []))))
    ok = 0
    for rel, e, w, ni, np_, nh in rows:
        st = "OK" if not e else "NG"
        ok += not e
        print(f"[{st}] {rel}  画像 許可済{ni}／要許可{np_}  hold{nh}")
        for x in e:
            print("   ERR", x)
        for x in w:
            print("   warn", x)
    print(f"--- {ok}/{len(rows)} 住戸 OK")
