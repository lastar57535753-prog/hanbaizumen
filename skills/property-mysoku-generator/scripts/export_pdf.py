# -*- coding: utf-8 -*-
"""pptx を PDF に書き出す（クロスプラットフォーム）。

  usage: python export_pdf.py 入力.pptx [出力.pdf] [--outline]

--outline を付けると、書き出したPDFの文字を **すべてアウトライン化**（図形化）する。
配布先に HGS明朝E が無くても字形が置き換わらない＝**中国語の字形（中華文字）に化けない**。
Ghostscript が要る（apt install ghostscript / brew install ghostscript）。

方式（自動選択）:
  - Windows            → PowerPoint COM (pywin32)
  - macOS / Linux      → LibreOffice (soffice --headless --convert-to pdf)
  - macOS で soffice 無し → PowerPoint for Mac を AppleScript で駆動（フォールバック）

環境変数 SOFFICE_BIN で soffice の絶対パスを明示指定できる。
"""
import sys, io, os, subprocess, shutil, platform, glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def _via_powerpoint_com(src, dst):
    import win32com.client  # Windows のみ
    PP_PDF = 32  # ppSaveAsPDF
    app = win32com.client.Dispatch("PowerPoint.Application")
    pres = None
    try:
        pres = app.Presentations.Open(src, WithWindow=False)
        pres.SaveAs(dst, PP_PDF)
    finally:
        if pres is not None:
            pres.Close()
        app.Quit()


def _find_soffice():
    if os.environ.get("SOFFICE_BIN") and os.path.exists(os.environ["SOFFICE_BIN"]):
        return os.environ["SOFFICE_BIN"]
    for name in ("soffice", "libreoffice"):
        p = shutil.which(name)
        if p:
            return p
    # macOS / Windows の代表的なインストール先
    for cand in (
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/opt/homebrew/bin/soffice",
        "/usr/local/bin/soffice",
        r"C:\Program Files\LibreOffice\program\soffice.exe",
    ):
        if os.path.exists(cand):
            return cand
    return None


def _via_soffice(src, dst):
    soffice = _find_soffice()
    if not soffice:
        return False
    outdir = os.path.dirname(dst) or "."
    subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir", outdir, src],
        check=True,
    )
    # soffice は <元名>.pdf を outdir に作る。dst 名が違えばリネーム。
    produced = os.path.join(outdir, os.path.splitext(os.path.basename(src))[0] + ".pdf")
    if os.path.abspath(produced) != os.path.abspath(dst) and os.path.exists(produced):
        shutil.move(produced, dst)
    return os.path.exists(dst)


def _via_powerpoint_mac(src, dst):
    """PowerPoint for Mac を AppleScript で駆動（LibreOffice が無い場合）。"""
    script = f'''
    tell application "Microsoft PowerPoint"
        set p to open POSIX file "{src}"
        save p in POSIX file "{dst}" as save as PDF
        close p saving no
    end tell
    '''
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return r.returncode == 0 and os.path.exists(dst)


def check_glyph_order(pdf):
    """書き出したPDFで、文字が前に戻って重なって描かれていないかを見る。

    LibreOffice は書体と文字の組み合わせによっては、直前の文字の送り幅を
    取りこぼして次の文字を前に戻して描くことがある（例:「土地面積」が
    「地面積」に見える）。字は正しく入っているので見落としやすい。
    出たら、その文言を言い換えるか、代替書体を変えて回避する。"""
    try:
        import pymupdf
    except ImportError:
        return True
    bad = []
    doc = pymupdf.open(pdf)
    for page in doc:
        for blk in page.get_text("rawdict")["blocks"]:
            for ln in blk.get("lines", []):
                for sp in ln["spans"]:
                    xs = [c["origin"][0] for c in sp["chars"]]
                    if len(xs) > 1 and xs != sorted(xs):
                        bad.append("".join(c["c"] for c in sp["chars"]))
    doc.close()
    if bad:
        print("⚠ 文字が重なって描かれています（LibreOffice の字送りの取りこぼし）:")
        for t in bad:
            print(f"   「{t}」")
        print("   → その文言を言い換えるか、別の書体で書き出してください。")
        return False
    return True


def outline_text(pdf):
    """PDFの文字を図形に変換する。フォントが無い環境での字形置換（中華文字化け）を断つ。"""
    gs = shutil.which("gs") or shutil.which("gswin64c")
    if gs is None:
        print("ℹ Ghostscript が無いのでアウトライン化を飛ばしました"
              "（apt install ghostscript / brew install ghostscript）")
        return False
    tmp = pdf + ".outlined.pdf"
    r = subprocess.run([gs, "-dNoOutputFonts", "-sDEVICE=pdfwrite", "-dNOPAUSE", "-dBATCH",
                        "-dQUIET", "-r600", f"-sOutputFile={tmp}", pdf], capture_output=True)
    if r.returncode != 0 or not os.path.exists(tmp):
        print("⚠ アウトライン化に失敗:", r.stderr.decode("utf-8", "ignore")[:200])
        return False
    shutil.move(tmp, pdf)
    print("アウトライン化: 文字を図形に変換しました（書体が無い環境でも化けません）")
    return True


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    outline = "--outline" in sys.argv
    src = os.path.abspath(args[0])
    dst = os.path.abspath(args[1]) if len(args) > 1 else os.path.splitext(src)[0] + ".pdf"
    system = platform.system()

    if system == "Windows":
        _via_powerpoint_com(src, dst)
        print(f"saved: {dst}  (PowerPoint COM)")
        if outline:
            outline_text(dst)
        return

    # macOS / Linux
    if _via_soffice(src, dst):
        print(f"saved: {dst}  (LibreOffice)")
        check_glyph_order(dst)       # アウトライン化する前に、文字の重なりを見る
        if outline:
            outline_text(dst)
        return
    if system == "Darwin" and _via_powerpoint_mac(src, dst):
        print(f"saved: {dst}  (PowerPoint for Mac)")
        if outline:
            outline_text(dst)
        return

    sys.stderr.write(
        "!! PDF書き出しに失敗。macOS/Linux では LibreOffice が必要です。\n"
        "   brew install --cask libreoffice  (mac)  /  環境変数 SOFFICE_BIN でパス指定も可。\n"
        "   pptx は出力済みなので、手動で PDF 書き出ししてください。\n"
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
