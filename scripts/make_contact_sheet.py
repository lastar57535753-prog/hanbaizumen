# -*- coding: utf-8 -*-
"""ピクトグラム一覧（コントラクトシート）を1枚のPNGにする。

usage:
  python make_contact_sheet.py [--color gold] [--out pictograms/contact_sheet.png]

カタログのカテゴリごとに区切って並べ、日本語ラベルを付ける。
どのピクトグラムがあるかを人が一目で確認するためのもの。
"""
import argparse, json, os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CATALOG = os.path.join(ROOT, "pictograms", "catalog.json")
FONT = os.path.join(ROOT, "assets", "fonts", "NotoSansJP[wght].ttf")

BG = (244, 240, 234)      # 生成り F4F0EA（テンプレートの背景色）
INK = (30, 35, 40)        # 墨 1E2328
GOLD = (140, 110, 63)     # 金 8C6E3F

CELL, ICON, PAD = 128, 76, 28


def font(size, weight=400):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--color", default="gold")
    ap.add_argument("--cols", type=int, default=14)
    ap.add_argument("--out", default=os.path.join(ROOT, "pictograms", "contact_sheet.png"))
    args = ap.parse_args()
    global COLS
    COLS = args.cols

    with open(CATALOG, encoding="utf-8") as f:
        cat = json.load(f)
    cats = cat["categories"]
    groups = {k: [it for it in cat["items"] if it["cat"] == k] for k in cats}

    rows = sum(-(-len(v) // COLS) for v in groups.values() if v)
    height = PAD * 2 + 92 + sum((-(-len(v) // COLS)) * CELL + 54 for v in groups.values() if v)
    width = PAD * 2 + COLS * CELL
    img = Image.new("RGB", (width, height), BG)
    d = ImageDraw.Draw(img)

    d.text((PAD, PAD), "販売図面用ピクトグラム", font=font(38, 700), fill=INK)
    d.text((PAD, PAD + 48), f"{len(cat['items'])}点 / 色: {args.color} / 商用利用可のライセンスのみ",
           font=font(20), fill=GOLD)
    y = PAD + 92

    for ckey, clabel in cats.items():
        items = groups.get(ckey) or []
        if not items:
            continue
        d.line([(PAD, y + 8), (width - PAD, y + 8)], fill=GOLD, width=2)
        d.text((PAD, y + 16), f"{clabel}（{len(items)}）", font=font(23, 700), fill=GOLD)
        y += 54
        for i, it in enumerate(items):
            cx = PAD + (i % COLS) * CELL
            cy = y + (i // COLS) * CELL
            p = os.path.join(ROOT, "pictograms", "png", args.color, it["key"] + ".png")
            if os.path.exists(p):
                ic = Image.open(p).convert("RGBA").resize((ICON, ICON), Image.LANCZOS)
                img.paste(ic, (cx + (CELL - ICON) // 2, cy + 4), ic)
            lab = it["label"]
            fnt = font(17)
            while d.textlength(lab, font=fnt) > CELL - 6 and fnt.size > 10:
                fnt = font(fnt.size - 1)
            d.text((cx + (CELL - d.textlength(lab, font=fnt)) / 2, cy + ICON + 10),
                   lab, font=fnt, fill=INK)
        y += (-(-len(items) // COLS)) * CELL

    img.save(args.out)
    print(f"✅ {args.out}  ({img.width}x{img.height})")


if __name__ == "__main__":
    main()
