# -*- coding: utf-8 -*-
"""pptx を PDF に書き出す（クロスプラットフォーム）。

  usage: python export_pdf.py 入力.pptx [出力.pdf]

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


def main():
    src = os.path.abspath(sys.argv[1])
    dst = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.splitext(src)[0] + ".pdf"
    system = platform.system()

    if system == "Windows":
        _via_powerpoint_com(src, dst)
        print(f"saved: {dst}  (PowerPoint COM)")
        return

    # macOS / Linux
    if _via_soffice(src, dst):
        print(f"saved: {dst}  (LibreOffice)")
        return
    if system == "Darwin" and _via_powerpoint_mac(src, dst):
        print(f"saved: {dst}  (PowerPoint for Mac)")
        return

    sys.stderr.write(
        "!! PDF書き出しに失敗。macOS/Linux では LibreOffice が必要です。\n"
        "   brew install --cask libreoffice  (mac)  /  環境変数 SOFFICE_BIN でパス指定も可。\n"
        "   pptx は出力済みなので、手動で PDF 書き出ししてください。\n"
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
