# -*- coding: utf-8 -*-
"""日本語の字幅計算と折り返し。全角=1em / 半角=0.5em で数える。

HGS明朝E も Noto Serif JP も全角は1emなので、折り返し位置の判定はこの近似で足りる。
（同梱フォントで実測しないのは、本番フォントが手元に無い環境でも同じ答えを出すため）
"""
import unicodedata

PT_CM = 0.0352778  # 1pt = 0.0352778cm
KINSOKU_HEAD = "、。，．）」』】〉》’”ー々〜！？ぁぃぅぇぉっゃゅょヵヶァィゥェォッャュョ"
KINSOKU_TAIL = "（「『【〈《‘“"


def em(s):
    """文字列の幅を em で返す。"""
    return sum(1.0 if unicodedata.east_asian_width(c) in "WFA" else 0.5 for c in s)


def cm(s, pt):
    """文字列を pt で組んだときの幅(cm)。"""
    return em(s) * pt * PT_CM


def capacity(width_cm, pt):
    """幅 width_cm に pt で入る字数(em)。"""
    return width_cm / (pt * PT_CM)


def wrap(text, cap_em):
    """cap_em(em) で折り返す。行頭・行末の禁則を簡易に処理する。"""
    if cap_em <= 0:
        return [text]
    out, cur, w = [], "", 0.0
    for ch in text:
        cw = 1.0 if unicodedata.east_asian_width(ch) in "WFA" else 0.5
        if w + cw > cap_em and cur:
            if ch in KINSOKU_HEAD:            # 行頭に来られない字はぶら下げる
                out.append(cur + ch)
                cur, w = "", 0.0
                continue
            if cur[-1] in KINSOKU_TAIL:       # 行末に来られない字は次行へ送る
                out.append(cur[:-1])
                cur, w = cur[-1] + ch, em(cur[-1]) + cw
                continue
            out.append(cur)
            cur, w = ch, cw
        else:
            cur += ch
            w += cw
    if cur:
        out.append(cur)
    return out or [""]


def lines_needed(text, width_cm, pt):
    return len(wrap(text, capacity(width_cm, pt)))
