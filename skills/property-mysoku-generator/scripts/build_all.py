# -*- coding: utf-8 -*-
"""販売図面を「1コマンド」で完成まで通す＝どの物件でも同一品質を再現する入口。

usage:
  python build_all.py <template.pptx> <data.json> <images.json> <out.pptx>
        [--no-pdf] [--pictograms point,note,life] [--qc-warn]
        [--agent キー] [--allow-missing]

処理:
  1) fill.py             … 文字（物件概要23項目・アクセス・POINT・備考・LIFE等）を流し込み
  2) place_images.py     … 写真スマート充填／間取り最大化／高級バッジ／統一キャプション／
                            スクリム／箇条書き／日本語ワードラップ 等を設定JSONで適用
  3) reflow_right.py     … 物件概要→備考→LIFE を実測高さで縦に自動整列
  4) place_pictograms.py … 行頭の「・」を物件の特徴に合ったピクトグラムに置換
                            （--pictograms で指定したときだけ。既定は入れない）
  5) preflight.py        … 出力前セルフQC。**違反があればここで止まる**（--qc-warn で警告のみ）
  6) export_pdf.py       … PDF書き出し（--no-pdf で省略）

写真は images.json の "path" にローカルパスでも共有URL（Dropbox / Google Drive）でも書ける。
取得できないときは止まる（--allow-missing で穴を許容）。
担当者は --agent キー（assets/agents.json）。既定は徳永。

data.json  = 文字値（sample: 設定サンプル_data.json）
images.json= 写真割当＋意匠設定（sample: 設定サンプル_images.json）
※ この2つを物件ごとに用意するだけで、あとは毎回同じクオリティで出る。
"""
import sys, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def run(script, *args):
    cmd = [PY, os.path.join(HERE, script), *args]
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    r = subprocess.run(cmd, env=env)
    if r.returncode != 0:
        if script == "preflight.py":
            print("\n!! セルフQCで問題が見つかったので中断しました。"
                  "\n   直すか、承知のうえで進めるなら --qc-warn を付けて再実行してください。")
        else:
            print(f"!! {script} が失敗しました")
        sys.exit(r.returncode)


def main():
    if len(sys.argv) < 5:
        print(__doc__); sys.exit(1)
    template, data, images, out = sys.argv[1:5]
    rest = sys.argv[5:]
    no_pdf = "--no-pdf" in rest
    qc_warn = "--qc-warn" in rest
    allow_missing = "--allow-missing" in rest
    agent = rest[rest.index("--agent") + 1] if "--agent" in rest else None
    zones = None
    if "--pictograms" in rest:
        i = rest.index("--pictograms")
        zones = rest[i + 1] if i + 1 < len(rest) and not rest[i + 1].startswith("--") else "point,note"
    base = os.path.splitext(out)[0]
    filled = base + "_1filled.pptx"
    imaged = base + "_2img.pptx"

    print("■ 文字流し込み")
    run("fill.py", template, data, filled, *(["--agent", agent] if agent else []))
    print("\n■ 画像・意匠")
    run("place_images.py", filled, images, imaged,
        *(["--allow-missing"] if allow_missing else []))
    print("\n■ 右カラム自動整列")
    run("reflow_right.py", imaged, out)

    if zones:
        print("\n■ ピクトグラム配置")
        run("place_pictograms.py", out, "--zones", zones, "-o", out)

    print("\n■ 出力前セルフQC（被り・はみ出し・整列・文字あふれ・書体）")
    run("preflight.py", out, *(["--warn-only"] if qc_warn else []))

    if not no_pdf:
        print("\n■ PDF書き出し")
        run("export_pdf.py", out, base + ".pdf")
    for tmp in (filled, imaged):
        try:
            os.remove(tmp)
        except OSError:
            pass
    print(f"\n✅ 完成: {out}" + ("" if no_pdf else f" / {base}.pdf"))


if __name__ == "__main__":
    main()
