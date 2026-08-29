# -*- coding: utf-8 -*-
"""PPTXの図形と「文字が実際に占める範囲」をcmで測る。

PowerPoint が無い環境（mac/Linux）でもQCできるようにするための、python-pptx だけの計測。
文字幅は textfit（全角1em・半角0.5em）で数えるので、どの環境でも同じ答えになる。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textfit

CM = 360000.0
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
LINE_EM = 1.2      # PowerPoint の1行 ≒ 文字サイズの1.2倍


def cm_of(v):
    return (v or 0) / CM


def box(shape):
    """図形の枠 (左, 上, 右, 下) cm。"""
    l, t = cm_of(shape.left), cm_of(shape.top)
    return (l, t, l + cm_of(shape.width), t + cm_of(shape.height))


def insets(tf):
    out = {}
    bp = tf._txBody.bodyPr
    for k, dflt in (("lIns", 0.254), ("rIns", 0.254), ("tIns", 0.127), ("bIns", 0.127)):
        v = bp.get(k)
        out[k] = (int(v) / 914400 * 2.54) if v is not None else dflt
    return out


def para_pt(p, dflt=10.0):
    sizes = [r.font.size.pt for r in p.runs if r.font.size]
    return max(sizes) if sizes else dflt


def para_width(p, dflt=10.0):
    """段落を1行に組んだときの幅(cm)。ランごとに文字サイズが違う行に対応する。

    「54,800万円（非課税）」のように 36pt と 10pt が混在する行を、段落の最大サイズで
    まとめて数えると幅を大きく見誤り、ありもしない被りを報告してしまう。"""
    last = next((r.font.size.pt for r in p.runs if r.font.size), dflt)
    total = 0.0
    for r in p.runs:
        if r.font.size:
            last = r.font.size.pt
        total += textfit.cm(r.text, last)
    return total


def para_linespace(p):
    if p._pPr is None:
        return 1.0
    ls = p._pPr.find(A + "lnSpc")
    if ls is None or not len(ls) or not ls[0].get("val"):
        return 1.0
    return int(ls[0].get("val")) / 100000.0


def lines(shape):
    """(行テキスト, pt, 行の高さcm) のリスト。折返し済み。"""
    tf = shape.text_frame
    ins = insets(tf)
    w = cm_of(shape.width) - ins["lIns"] - ins["rIns"]
    no_wrap = tf._txBody.bodyPr.get("wrap") == "none"
    out = []
    for p in tf.paragraphs:
        pt = para_pt(p)
        lh = pt * para_linespace(p) * LINE_EM * textfit.PT_CM
        if not p.text.strip():
            out.append(("", pt, lh))
            continue
        segs = [p.text] if no_wrap else textfit.wrap(p.text, textfit.capacity(w, pt))
        for seg in segs:
            out.append((seg, pt, lh))
    return out


def text_rect(shape):
    """文字が実際に occupying している範囲 (左,上,右,下) cm。文字が無ければ枠。

    横長のボックスでも文字が右端まで届いていなければ、そこは空きとして扱う。"""
    if not shape.has_text_frame or not shape.text_frame.text.strip():
        return box(shape)
    l, t, r, b = box(shape)
    tf = shape.text_frame
    ins = insets(tf)
    ls = lines(shape)
    total = sum(lh for _, _, lh in ls)
    anchor = tf._txBody.bodyPr.get("anchor") or "t"
    if anchor == "ctr":
        top = t + (cm_of(shape.height) - total) / 2
    elif anchor == "b":
        top = b - ins["bIns"] - total
    else:
        top = t + ins["tIns"]
    no_wrap = tf._txBody.bodyPr.get("wrap") == "none"
    if no_wrap:
        # 折り返さない行はランごとに数える（サイズ混在に対応）
        width = max((para_width(p) for p in tf.paragraphs if p.text.strip()), default=0.0)
    else:
        width = max((textfit.cm(seg, pt) for seg, pt, _ in ls), default=0.0)
    left = l + ins["lIns"]
    # 中央揃えの段落があるときは、いちばん広い行を中央に置いたときの範囲にする
    if any(p.alignment is not None and int(p.alignment) == 2 for p in tf.paragraphs):
        left = l + (cm_of(shape.width) - width) / 2
    return (left, top, left + width, top + total)


def text_height(shape):
    return sum(lh for _, _, lh in lines(shape)) if shape.has_text_frame else 0.0


def fonts(shape):
    """図形で使われている書体名の集合。"""
    names = set()
    if not shape.has_text_frame:
        return names
    for p in shape.text_frame.paragraphs:
        for r in p.runs:
            rPr = r._r.find(A + "rPr")
            if rPr is None:
                continue
            for tag in ("latin", "ea", "cs"):
                el = rPr.find(A + tag)
                if el is not None and el.get("typeface"):
                    names.add(el.get("typeface"))
    return names
