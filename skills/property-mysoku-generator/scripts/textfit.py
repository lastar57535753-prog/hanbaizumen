# -*- coding: utf-8 -*-
"""日本語の字幅計算と折り返し。全角=1em / 半角=0.5em で数える。

HGS明朝E も Noto Serif JP も全角は1emなので、折り返し位置の判定はこの近似で足りる。
（同梱フォントで実測しないのは、本番フォントが手元に無い環境でも同じ答えを出すため）
"""
import re
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


JP_OPEN = "「（【(『［｛《〈"
JP_CLOSE = "」）】)』］｝》〉"
CLAUSE_END = "、。・／，"                 # ここで改行すると意味が切れない
NO_START = "、。，．・）」』】）,.:：;；!！?？ー〜%"     # 行頭に置けない（前行へ）
_ASCII = re.compile(r"[0-9A-Za-z%．.,／/－ー~〜:：＋+#&']+")
_KATA = re.compile(r"[ァ-ヶー・]{2,}")   # カタカナ語（ワイドサッシ/コンシェルジュ等）は分割しない


def _tokenize(t):
    """語中で切らないための最小トークン化。英数字連続・カタカナ語・『「…」』等の括弧内は分割不可。"""
    toks, i, n = [], 0, len(t)
    while i < n:
        c = t[i]
        if c in JP_OPEN:
            close = JP_CLOSE[JP_OPEN.index(c)]
            j = t.find(close, i + 1)
            j = j if j != -1 else i
            toks.append(t[i:j + 1]); i = j + 1; continue
        m = _ASCII.match(t, i)
        if m and m.end() > i:
            toks.append(t[i:m.end()]); i = m.end(); continue
        m = _KATA.match(t, i)
        if m and m.end() > i:
            toks.append(t[i:m.end()]); i = m.end(); continue
        toks.append(c); i += 1
    return toks


def _clauses(text):
    """「、。・／，」の直後で区切った節のリスト。改行位置の第一候補になる。"""
    out, cur, depth = [], "", 0
    for ch in text:
        cur += ch
        if ch in JP_OPEN:
            depth += 1
        elif ch in JP_CLOSE:
            depth = max(0, depth - 1)
        elif ch in CLAUSE_END and depth == 0:   # 括弧の中では切らない
            out.append(cur); cur = ""
    if cur:
        out.append(cur)
    return out


def jp_wrap(text, max_cm, pt):
    """日本語を語中で切らずに折り返す。禁則（行頭約物）も簡易対応。

    幅は「全角1em・半角0.5em」で数える。実フォントで計測しないのは、本番の
    HGS明朝E が mac/Linux に無く、環境ごとに折返し位置が変わってしまうため。
    和文は全角1emなので、この数え方なら Windows でも mac でも同じ結果になる。

    まず「、。・／」で区切った節を単位に詰め、節が1行に収まらないときだけ
    語単位に落とす。こうすると改行が意味の切れ目に来て、語の途中で切れない。"""
    def pack_tokens(seg, lines, cur):
        for tok in _tokenize(seg):
            if cur and cm(cur + tok, pt) > max_cm:
                lines.append(cur); cur = tok
            else:
                cur += tok
        return cur

    lines, cur = [], ""
    for cl in _clauses(text):
        if not cur:
            cur = cl if cm(cl, pt) <= max_cm else pack_tokens(cl, lines, "")
        elif cm(cur + cl, pt) <= max_cm:
            cur += cl
        elif cm(cl, pt) <= max_cm:          # 節ごと次の行へ（意味の切れ目で改行）
            lines.append(cur); cur = cl
        else:                                # 1節が1行に入らないときだけ語単位で詰める
            lines.append(cur); cur = pack_tokens(cl, lines, "")
    if cur:
        lines.append(cur)
    fixed = []
    for ln in lines:
        while ln and fixed and ln[0] in NO_START:
            fixed[-1] += ln[0]; ln = ln[1:]
        fixed.append(ln)
    return [l for l in fixed if l] or [text]
