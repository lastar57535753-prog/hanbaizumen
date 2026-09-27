"""21Cloud 画像登録モーダルへ写真を自動で入れる（Playwright・既存Chromeに接続）。

事前に Chrome を次のように起動して 21Cloud にログインし、対象物件の画像登録モーダルを開いておく:
  chrome.exe --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\\chrome-21cloud"

使い方:
  python upload_photos.py <21cloud入力.json> --discover   # 画面の構造を調べるだけ（何も変更しない）
  python upload_photos.py <21cloud入力.json>              # 写真・カテゴリ・コメントを入れる（「画像登録完了」は押さない）
  python upload_photos.py <21cloud入力.json> --save       # 最後に「画像登録完了」まで押す
  python upload_photos.py <21cloud入力.json> --include-pending  # 転載許可が取れた要許可写真も入れる
オプション: --start N  最初に使うスロット番号（既定: 空いている最初のスロット）
"""
import json, os, sys, time, argparse

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def find_modal_frame(page):
    for fr in page.frames:
        try:
            if fr.query_selector("textarea[id^=imageComment100_]"):
                return fr
        except Exception:
            pass
    return None


def slot_rows(fr):
    """スロット番号 -> 情報。imageComment100_N から親を遡ってスロット行を特定する。"""
    return fr.evaluate("""() => {
      const out = [];
      document.querySelectorAll('textarea[id^=imageComment100_]').forEach(ta => {
        const n = +ta.id.split('_').pop();
        let row = ta;
        for (let i = 0; i < 12 && row.parentElement; i++) {
          row = row.parentElement;
          if (row.querySelector('select') && row.querySelector('input[type=file], img.left-icon, button, a')) break;
        }
        row.setAttribute('data-claude-slot', n);
        const img = row.querySelector('img.left-icon');
        out.push({n, hasImage: !!(img && img.src && !/noimage|no_image|blank/i.test(img.src)),
                  fileInputs: row.querySelectorAll('input[type=file]').length,
                  selects: row.querySelectorAll('select').length});
      });
      return out;
    }""")


def fill_meta(fr, n, im):
    return fr.evaluate("""([n, cat, c20, c100]) => {
      const fire = (el, evs) => evs.forEach(ev => el.dispatchEvent(new Event(ev, {bubbles: true})));
      const row = document.querySelector('[data-claude-slot="' + n + '"]');
      const s = row && row.querySelectorAll('select')[0];
      if (s) { s.value = String(cat); fire(s, ['input','change','blur']); }
      const a = document.querySelector('#imageComment_' + n);
      if (a) { a.value = c20; fire(a, ['input','keyup','change','blur']); }
      const b = document.querySelector('#imageComment100_' + n);
      if (b) { b.value = c100; fire(b, ['input','keyup','change','blur']); }
      return {cat: s ? s.value : null, c20: a ? a.value.length : null, c100: b ? b.value.length : null};
    }""", [n, im["category"], im.get("comment20", ""), im.get("comment100", "")])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json")
    ap.add_argument("--discover", action="store_true")
    ap.add_argument("--save", action="store_true")
    ap.add_argument("--start", type=int, default=None)
    ap.add_argument("--include-pending", action="store_true", help="要許可の写真も入れる（元付の転載許可を取った後だけ使う）")
    ap.add_argument("--cdp", default="http://localhost:9222")
    a = ap.parse_args()
    d = json.load(open(a.json, encoding="utf-8"))
    images = d.get("images", []) + (d.get("images_pending_permission", []) if a.include_pending else [])

    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(a.cdp)
        pages = [pg for ctx in br.contexts for pg in ctx.pages if "century21" in pg.url]
        if not pages:
            sys.exit("21Cloud のタブが見つかりません（CDP接続先のChromeで開いてください）")
        page = pages[-1]
        fr = find_modal_frame(page)
        if not fr:
            sys.exit("画像登録モーダルが開いていません（imageComment100_ が見つからない）")
        rows = slot_rows(fr)
        print(f"スロット {len(rows)} 個 / 画像あり {sum(r['hasImage'] for r in rows)} / 入れる写真 {len(images)} 枚")
        if a.discover:
            for r in rows:
                print(r)
            print("file input 総数:", fr.evaluate("document.querySelectorAll('input[type=file]').length"), flush=True)
            return
        free = [r for r in rows if not r["hasImage"]]
        if a.start:
            free = [r for r in free if r["n"] >= a.start]
        if len(free) < len(images):
            print(f"注意: 空きスロット {len(free)} < 写真 {len(images)}。入る分だけ入れます")
        log = []
        for im, r in zip(images, free):
            n = r["n"]
            f = im.get("upload_file") or im["file"]
            path = f if os.path.isabs(f) else os.path.join(REPO, f)
            if not os.path.isfile(path):
                log.append((n, im["file"], "ファイルなし"))
                continue
            inp = fr.query_selector(f'[data-claude-slot="{n}"] input[type=file]')
            try:
                if inp:
                    inp.set_input_files(path)
                else:
                    # ボタン押下でファイル選択ダイアログが開く形式
                    btn = fr.query_selector(f'[data-claude-slot="{n}"] button, [data-claude-slot="{n}"] a')
                    with page.expect_file_chooser(timeout=8000) as fc:
                        btn.click()
                    fc.value.set_files(path)
                # サムネイルが出るまで待つ
                for _ in range(30):
                    if fr.evaluate(f"""() => {{const i=document.querySelector('[data-claude-slot="{n}"] img.left-icon');
                                        return !!(i && i.src && !/noimage|no_image|blank/i.test(i.src));}}"""):
                        break
                    time.sleep(0.5)
                res = fill_meta(fr, n, im)
                log.append((n, os.path.basename(path), f"OK {res}"))
            except Exception as e:
                log.append((n, os.path.basename(path), f"エラー {e}"))
        for x in log:
            print(*x)
        if a.save:
            clicked = False
            for f in [fr] + [x for x in page.frames if x is not fr]:
                try:
                    clicked = f.evaluate("""() => {
                      const el = [...document.querySelectorAll('a,button,input[type=button],input[type=submit]')]
                        .find(e => (e.innerText || e.value || '').trim() === '画像登録完了');
                      if (!el) return false; el.click(); return true; }""")
                except Exception:
                    clicked = False
                if clicked:
                    break
            time.sleep(2)
            print("画像登録完了を押しました。" if clicked else "「画像登録完了」ボタンが見つかりません。手動で押してください。")

if __name__ == "__main__":
    main()
