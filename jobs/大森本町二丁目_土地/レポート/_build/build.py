# -*- coding: utf-8 -*-
"""テキストのレポートを、ヒラギノ角ゴシック＋C21ロゴのPDFに組む。"""
import html, re, sys, os

SRC = "/home/user/hanbaizumen/jobs/大森本町二丁目_土地/レポート/大森本町二丁目_土地_調査レポート.txt"
B   = os.path.dirname(os.path.abspath(__file__))

lines = open(SRC, encoding="utf-8").read().split("\n")

MARK = {"◎": ("m-a", "確"), "○": ("m-b", "複"), "△": ("m-c", "推"), "✕": ("m-d", "要修正")}
URL  = re.compile(r"(https?://[^\s　]+)")

def esc(s):
    s = html.escape(s)
    return URL.sub(lambda m: f'<a href="{m.group(1)}">{m.group(1)}</a>', s)

out, i, n = [], 0, len(lines)
first_h2 = True

# ── 表紙ブロック（先頭の ═ に挟まれた部分）
while i < n and not lines[i].startswith("═"): i += 1
i += 1
cover = []
while i < n and not lines[i].startswith("═"):
    cover.append(lines[i].strip()); i += 1
i += 1
title = cover[0] if cover else ""
out.append('<div class="cover">')
out.append(f'<div class="ctitle">{esc(title)}</div>')
for c in cover[1:]:
    if c: out.append(f'<div class="csub">{esc(c)}</div>')
out.append('</div>')

while i < n:
    ln = lines[i]; i += 1
    s  = ln.strip()

    if not s:
        out.append('<div class="sp"></div>'); continue
    if set(s) <= {"─"}:
        out.append('<hr>'); continue
    if set(s) <= {"═"}:
        continue

    m = re.match(r"^■■\s*(.+?)\s*■■$", s)
    if m:
        cls = "h2" + ("" if first_h2 else " brk"); first_h2 = False
        out.append(f'<h2 class="{cls}">{esc(m.group(1))}</h2>'); continue

    # 先頭の印（◎○△✕）
    m = re.match(r"^([◎○△✕])\s*(.*)$", s)
    if m and m.group(1) in MARK:
        cls, lab = MARK[m.group(1)]
        indent = len(ln) - len(ln.lstrip("　 "))
        out.append(f'<div class="mk {cls}" style="margin-left:{indent*0.45:.1f}em">'
                   f'<span class="badge">{lab}</span><span class="mtx">{esc(m.group(2))}</span></div>')
        continue

    # 【見出し】だけの行／【見出し】＋本文
    m = re.match(r"^【(.+?)】\s*(.*)$", s)
    if m:
        h = f'<h3>{esc("【"+m.group(1)+"】")}</h3>'
        out.append(h)
        if m.group(2): out.append(f'<div class="ln">{esc("　"+m.group(2))}</div>')
        continue

    out.append(f'<div class="ln">{esc(ln)}</div>')

body = "\n".join(out)

CSS = """
@font-face{font-family:"Hiragino";src:url("fonts/hiragino-w3.ttf");font-weight:normal;}
@font-face{font-family:"Hiragino";src:url("fonts/hiragino-w6.ttf");font-weight:bold;}
@page{
  size:A4; margin:20mm 16mm 12mm 16mm;
  @top-right{ content:url("hdr_c21.png"); }
  @top-left{ content:"大森本町二丁目 売地　調査レポート"; font-family:"Hiragino"; font-size:7.5pt; color:#8A7A5C; }
  @bottom-left-corner{ background:#1A2C56; outline:0.5mm solid #1A2C56; content:""; }
  @bottom-right-corner{ background:#1A2C56; outline:0.5mm solid #1A2C56; content:""; }
  @bottom-left{ width:40mm; background:#1A2C56; outline:0.5mm solid #1A2C56; vertical-align:middle;
                padding-left:3mm; content:url("ft_seal.png"); }
  @bottom-center{ width:98mm; background:#1A2C56; outline:0.5mm solid #1A2C56; color:#fff; vertical-align:middle;
                  text-align:center; font-family:"Hiragino"; font-size:7pt; letter-spacing:.02em;
                  content:"CENTURY 21 ラスターハウス　売買営業部　担当：徳永 新太郎"; }
  @bottom-right{ width:40mm; background:#1A2C56; outline:0.5mm solid #1A2C56; color:#fff; vertical-align:middle;
                 text-align:right; padding-right:3mm; font-family:"Hiragino"; font-size:7pt;
                 content:counter(page) " / " counter(pages) "　" url("ft_portal.png"); }
}
html{ font-family:"Hiragino",sans-serif; font-size:9pt; color:#1B1B1B; line-height:1.62; }
body{ margin:0; }
a{ color:#2B4C86; text-decoration:none; word-break:break-all; }
.cover{ border-top:3px solid #B99C6B; border-bottom:1px solid #D8CDB6;
        padding:7mm 0 5mm; margin-bottom:6mm; }
.ctitle{ font-weight:bold; font-size:17pt; color:#1A2C56; letter-spacing:.02em; line-height:1.35; }
.csub{ font-size:9pt; color:#4A4A4A; margin-top:1.6mm; }
h2{ font-weight:bold; font-size:12.5pt; color:#fff; background:#1A2C56;
    padding:2.2mm 4mm; margin:7mm 0 3.5mm; border-left:4mm solid #B99C6B; line-height:1.4; }
h2.brk{ break-before:page; margin-top:0; }
h3{ font-weight:bold; font-size:9.8pt; color:#1A2C56; margin:4mm 0 1.2mm;
    padding-bottom:.8mm; border-bottom:1px solid #DCD3C0; }
hr{ border:0; border-top:1px solid #E2DBCC; margin:4mm 0; }
.sp{ height:1.7mm; }
.ln{ white-space:pre-wrap; word-break:break-word; }
.mk{ display:flex; gap:2mm; align-items:baseline; margin:.7mm 0; }
.mk .mtx{ white-space:pre-wrap; word-break:break-word; flex:1; }
.badge{ flex:none; display:inline-block; min-width:5.2mm; text-align:center;
        font-size:6.8pt; font-weight:bold; color:#fff; border-radius:1mm;
        padding:.3mm 1.1mm; line-height:1.5; position:relative; top:-.3mm; }
.m-a .badge{ background:#1A2C56; }
.m-b .badge{ background:#6E8AB5; }
.m-c .badge{ background:#B99C6B; }
.m-d .badge{ background:#A32B2B; }
.m-d .mtx{ font-weight:bold; color:#8E1F1F; }
"""
CSS = CSS.replace("#8A7photo", "#8A7A5C")

open(f"{B}/index.html","w",encoding="utf-8").write(
  f'<!doctype html><html lang="ja"><head><meta charset="utf-8">'
  f'<title>大森本町二丁目 売地 調査レポート</title><style>{CSS}</style></head>'
  f'<body>{body}</body></html>')
print("html ok")
