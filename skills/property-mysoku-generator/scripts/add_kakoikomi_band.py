# -*- coding: utf-8 -*-
"""下帯に「囲い込み防止」帯（QR＋文言＋C21ロゴ／92×27mm）を入れる。

全物件に必ず入れる運用なので build_all.py から既定で呼ばれる（外すときは --no-kakoikomi）。
帯は元からある案内文(id318)とQR空枠(id229)の場所に置く。両者は役割が重複する
（どちらも「QRから問い合わせ」の案内）ため削除する。

usage: python add_kakoikomi_band.py <図面.pptx> [--band 別の帯.png]
"""
import os
import sys

from pptx import Presentation
from pptx.util import Cm

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BAND = os.path.join(HERE, "..", "assets", "kakoikomi_band.png")

RATIO = 92.0 / 27.0      # 帯の原寸（mm）
BAND_H = 1.95            # 下帯(高さ2.07cm)に収まる高さ(cm)
NOTE_ID, QRBOX_ID = 318, 229
FOOTER_ID, CONTACT_ID, TORIHIKI_ID = 146, 314, 319

args = sys.argv[1:]
band = DEFAULT_BAND
if "--band" in args:
    i = args.index("--band")
    band = args[i + 1]
    del args[i:i + 2]
if not args:
    print(__doc__); sys.exit(1)
path = args[0]
if not os.path.exists(band):
    sys.exit(f"!! 囲い込み防止帯の画像がありません: {band}")

prs = Presentation(path)
slide = prs.slides[0]
byid = {sh.shape_id: sh for sh in slide.shapes}

for sid in (NOTE_ID, QRBOX_ID):                 # 役割が重複する案内文とQR空枠を外す
    if sid in byid:
        byid[sid]._element.getparent().remove(byid[sid]._element)

w, h = Cm(BAND_H * RATIO), Cm(BAND_H)
left_edge = byid[CONTACT_ID].left + byid[CONTACT_ID].width if CONTACT_ID in byid else Cm(17.40)
right_edge = byid[TORIHIKI_ID].left if TORIHIKI_ID in byid else Cm(25.60)
x = left_edge + (right_edge - left_edge - w) // 2          # 連絡先と取引態様の間で中央に
if FOOTER_ID in byid:                                       # 下帯の中で上下中央に
    f = byid[FOOTER_ID]
    y = f.top + (f.height - h) // 2
else:
    y = Cm(18.95)

slide.shapes.add_picture(band, x, y, w, h)
prs.save(path)
print(f"囲い込み防止帯を配置: {os.path.basename(band)} "
      f"（{w / 360000:.2f}×{h / 360000:.2f}cm ／ x={x / 360000:.2f} y={y / 360000:.2f}）")
