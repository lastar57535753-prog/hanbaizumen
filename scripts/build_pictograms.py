# -*- coding: utf-8 -*-
"""販売図面用ピクトグラムを Iconify のアイコンセットから抽出し、SVG と PNG を書き出す。

usage:
  python build_pictograms.py [--source <iconifyのjsonディレクトリ>] [--size 256]

source を省略した場合は npm から @iconify/json を取得する（要ネットワーク）。
出力先は pictograms/svg/ と pictograms/png/{色名}/。
色は販売図面テンプレートから採取したブランド色（墨・金・淡金・白）。
"""
import argparse, json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CATALOG = os.path.join(ROOT, "pictograms", "catalog.json")
OUT = os.path.join(ROOT, "pictograms")

# 販売図面テンプレート（アトラスタワー五反田30F）から実測したブランド色
COLORS = {"sumi": "#1E2328", "gold": "#8C6E3F", "gold_light": "#BEAF87", "white": "#FFFFFF"}

# 商用利用に支障のないライセンスのみ許可する（CC BY-NC / CC BY-SA / GPL は不可）
ALLOWED_LICENSES = ("mit", "apache", "cc0", "isc", "bsd", "unlicense", "public domain")


def fetch_iconify(dest):
    """npm から @iconify/json を取得して json ディレクトリのパスを返す。"""
    print("■ @iconify/json を取得中（約100MB）…")
    subprocess.run(["npm", "pack", "@iconify/json"], cwd=dest, check=True,
                   stdout=subprocess.DEVNULL)
    tgz = [f for f in os.listdir(dest) if f.endswith(".tgz")][0]
    subprocess.run(["tar", "xzf", tgz], cwd=dest, check=True)
    return os.path.join(dest, "package", "json")


def load_set(source, prefix, cache):
    if prefix not in cache:
        with open(os.path.join(source, prefix + ".json"), encoding="utf-8") as f:
            cache[prefix] = json.load(f)
    return cache[prefix]


def resolve(icon_set, name):
    """icons / aliases を辿って {body,width,height} を返す。"""
    seen = set()
    while name in icon_set.get("aliases", {}) and name not in icon_set["icons"]:
        if name in seen:
            raise ValueError(f"alias が循環しています: {name}")
        seen.add(name)
        name = icon_set["aliases"][name]["parent"]
    ic = icon_set["icons"][name]
    return (ic["body"],
            ic.get("width", icon_set.get("width", 24)),
            ic.get("height", icon_set.get("height", 24)))


# 角丸枠。販売図面では設備アイコンを枠に入れるのが通例なので、全点に同色の枠を付ける。
FRAME_PAD = 3        # 枠の外側の余白（100 を1辺としたときの値）
FRAME_RX = 20        # 角の丸み
FRAME_STROKE = 5     # 枠線の太さ
ICON_BOX = 72        # 枠の中に置く絵の大きさ


def svg_text(body, w, h, color, frame=True):
    """アイコン1点分のSVGを組み立てる。frame=True なら同色の角丸枠で囲う。"""
    if not frame:
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
                f'width="{w}" height="{h}" fill="{color}" color="{color}">{body}</svg>')
    scale = ICON_BOX / max(w, h)
    tx, ty = (100 - w * scale) / 2, (100 - h * scale) / 2
    side = 100 - FRAME_PAD * 2
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" '
            f'width="100" height="100">'
            f'<rect x="{FRAME_PAD}" y="{FRAME_PAD}" width="{side}" height="{side}" '
            f'rx="{FRAME_RX}" ry="{FRAME_RX}" fill="none" stroke="{color}" '
            f'stroke-width="{FRAME_STROKE}"/>'
            f'<g transform="translate({tx:.3f} {ty:.3f}) scale({scale:.5f})" '
            f'fill="{color}" color="{color}">{body}</g></svg>')


def check_license(collections, prefix):
    """商用利用可のライセンスか確認し、(可否, ライセンス名) を返す。"""
    info = collections.get(prefix, {})
    title = info.get("license", {}).get("title", "不明")
    ok = any(a in title.lower() for a in ALLOWED_LICENSES)
    return ok, title, info.get("name", prefix), info.get("author", {}).get("name", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", help="@iconify/json の json ディレクトリ")
    ap.add_argument("--size", type=int, default=256, help="PNGの一辺(px)")
    ap.add_argument("--keep-download", action="store_true", help="取得した元データを消さない")
    ap.add_argument("--no-frame", action="store_true", help="角丸枠を付けない")
    args = ap.parse_args()

    with open(CATALOG, encoding="utf-8") as f:
        catalog = json.load(f)

    tmp = None
    source = args.source
    if not source:
        tmp = tempfile.mkdtemp(prefix="iconify_")
        source = fetch_iconify(tmp)
    collections_path = os.path.join(os.path.dirname(source), "collections.json")
    with open(collections_path, encoding="utf-8") as f:
        collections = json.load(f)

    try:
        import cairosvg
    except ImportError:
        print("!! cairosvg が必要です: pip install cairosvg")
        sys.exit(1)

    svg_dir = os.path.join(OUT, "svg")
    os.makedirs(svg_dir, exist_ok=True)
    for c in COLORS:
        os.makedirs(os.path.join(OUT, "png", c), exist_ok=True)

    cache, used_sets, made, errors = {}, {}, 0, []
    for item in catalog["items"]:
        prefix, name = item["icon"].split(":", 1)
        ok, lic, set_name, author = check_license(collections, prefix)
        if not ok:
            errors.append(f"{item['key']}: ライセンス不許可 {prefix} = {lic}")
            continue
        used_sets[prefix] = (set_name, lic, author)
        try:
            body, w, h = resolve(load_set(source, prefix, cache), name)
        except (KeyError, ValueError) as e:
            errors.append(f"{item['key']}: アイコン解決に失敗 {item['icon']} ({e})")
            continue
        # 素の SVG（currentColor のまま。好きな色で使える）
        with open(os.path.join(svg_dir, item["key"] + ".svg"), "w", encoding="utf-8") as f:
            f.write(svg_text(body, w, h, "currentColor", frame=not args.no_frame))
        for cname, hexv in COLORS.items():
            cairosvg.svg2png(bytestring=svg_text(body, w, h, hexv,
                                                 frame=not args.no_frame).encode("utf-8"),
                             write_to=os.path.join(OUT, "png", cname, item["key"] + ".png"),
                             output_width=args.size, output_height=args.size)
        made += 1

    write_licenses(used_sets)
    print(f"✅ {made}/{len(catalog['items'])} 件を書き出しました → {OUT}")
    print(f"   SVG: {svg_dir}")
    print(f"   PNG: {os.path.join(OUT,'png')}/{{{','.join(COLORS)}}}/  ({args.size}px)")
    if errors:
        print(f"⚠ {len(errors)}件のエラー:")
        for e in errors:
            print("   -", e)
    if tmp and not args.keep_download:
        shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(1 if errors else 0)


def write_licenses(used_sets):
    lines = ["# ピクトグラムのライセンス", "",
             "本ディレクトリのピクトグラムは以下のアイコンセットから抽出したものです。",
             "いずれも商用利用が可能なライセンスのものだけを採用しています",
             "（CC BY-NC / CC BY-SA / GPL のセットは自動的に除外されます）。", "",
             "| セット | 作者 | ライセンス |", "|---|---|---|"]
    for prefix, (name, lic, author) in sorted(used_sets.items()):
        lines.append(f"| {name} (`{prefix}`) | {author} | {lic} |")
    lines += ["", "取得元: [Iconify](https://iconify.design/) の `@iconify/json` パッケージ",
              "", "再生成: `python scripts/build_pictograms.py`"]
    with open(os.path.join(OUT, "LICENSES.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
