"""21Cloud 操作ヘルパー（Playwright・デバッグポート付きで起動したChromeに接続）。
Claude Code が画面を見ながら全自動で入力するための道具。

  python c21.py shot [name]              画面（全フレーム含む）をPNG保存 → Readで見る
  python c21.py fields [filter]          入力欄の一覧（frame番号・id・name・type・ラベル・現在値・maxlength）
  python c21.py set <json>               {"#id": "値", "name=xxx": "値", ...} をまとめて入力（イベント発火付き）
  python c21.py click <テキスト|#id>     ボタン・リンクを押す（全フレームを探す）
  python c21.py goto <url>               ページ移動
  python c21.py read <#id> [#id...]      値を読み出す（保存後の照合用）
  python c21.py comments <21cloud入力.json>  キャッチコピー登録モーダルに17コメントを入れて文字数を返す
  python c21.py dialogs on               以後の確認ダイアログを自動で「OK」にする（このプロセス内のみ）
環境変数 C21_CDP（既定 http://localhost:9222）
"""
import json, os, sys, time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
CDP = os.environ.get("C21_CDP", "http://localhost:9222")
HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "..", "..", "c21_shots")

FIELDS_JS = r"""(filter) => {
  const lab = el => {
    if (el.id) { const l = document.querySelector('label[for="' + el.id + '"]'); if (l) return l.innerText.trim(); }
    const td = el.closest('td'); const tr = el.closest('tr');
    if (tr) { const th = tr.querySelector('th'); if (th) return th.innerText.trim().slice(0, 30); }
    if (td && td.previousElementSibling) return td.previousElementSibling.innerText.trim().slice(0, 30);
    return (el.placeholder || el.title || '').slice(0, 30);
  };
  return [...document.querySelectorAll('input,select,textarea')]
    .filter(el => el.type !== 'hidden' && el.offsetParent !== null)
    .map(el => ({id: el.id, name: el.name, type: el.type || el.tagName.toLowerCase(), label: lab(el),
                 value: el.type === 'checkbox' || el.type === 'radio' ? (el.checked ? 'ON' : 'off') + ':' + el.value
                        : el.tagName === 'SELECT' ? el.value + '=' + (el.selectedOptions[0] ? el.selectedOptions[0].text : '')
                        : (el.value || '').slice(0, 40),
                 max: el.maxLength > 0 ? el.maxLength : null}))
    .filter(f => !filter || JSON.stringify(f).includes(filter));
}"""

SET_JS = r"""([sel, val]) => {
  let el = sel.startsWith('name=') ? document.querySelector('[name="' + sel.slice(5) + '"]') : document.querySelector(sel);
  if (!el) return null;
  const fire = evs => evs.forEach(ev => el.dispatchEvent(new Event(ev, {bubbles: true})));
  if (el.type === 'checkbox' || el.type === 'radio') {
    const want = val === true || val === 'ON' || val === '1' || val === 'true';
    if (el.type === 'radio' && typeof val === 'string' && !['ON','true','1'].includes(val)) {
      const r = document.querySelector('[name="' + el.name + '"][value="' + val + '"]'); if (r) el = r;
      el.checked = true;
    } else { el.checked = want; }
    fire(['click', 'change']);
  } else if (el.tagName === 'SELECT') {
    const opt = [...el.options].find(o => o.value === String(val)) || [...el.options].find(o => o.text.trim() === String(val));
    if (!opt) return 'NO OPTION:' + [...el.options].map(o => o.value + '=' + o.text.trim()).join(',').slice(0, 300);
    el.value = opt.value; fire(['input', 'change', 'blur']);
  } else {
    el.value = val; fire(['input', 'keyup', 'change', 'blur']);
  }
  return el.type === 'checkbox' || el.type === 'radio' ? String(el.checked) : String(el.value).length + (el.maxLength > 0 ? '/' + el.maxLength : '');
}"""

CLICK_JS = r"""(t) => {
  const el = t.startsWith('#') ? document.querySelector(t)
    : [...document.querySelectorAll('a,button,input[type=button],input[type=submit],span[onclick],div[onclick],li')]
        .filter(e => e.offsetParent !== null)
        .find(e => (e.innerText || e.value || '').trim() === t)
      || [...document.querySelectorAll('a,button,input[type=button],input[type=submit]')]
        .filter(e => e.offsetParent !== null)
        .find(e => (e.innerText || e.value || '').includes(t));
  if (!el) return false; el.scrollIntoView({block: 'center'}); el.click(); return true;
}"""


def page_of(p):
    br = p.chromium.connect_over_cdp(CDP)
    pages = [pg for ctx in br.contexts for pg in ctx.pages if "century21" in pg.url or "21cloud" in pg.url]
    if not pages:
        pages = [pg for ctx in br.contexts for pg in ctx.pages]
    return pages[-1]


def frames(pg):
    return [f for f in pg.frames if not f.is_detached()]


def main():
    cmd, args = sys.argv[1], sys.argv[2:]
    with sync_playwright() as p:
        pg = page_of(p)
        if cmd == "dialogs":
            pg.on("dialog", lambda d: (print("DIALOG:", d.message), d.accept()))
            print("このプロセス内のみ有効。長い処理は Python から c21 を import して使うこと")
        elif cmd == "shot":
            os.makedirs(SHOTS, exist_ok=True)
            fn = os.path.abspath(os.path.join(SHOTS, (args[0] if args else time.strftime("%H%M%S")) + ".png"))
            pg.screenshot(path=fn, full_page=True)
            print(fn, pg.url)
        elif cmd == "fields":
            for i, f in enumerate(frames(pg)):
                try:
                    res = f.evaluate(FIELDS_JS, args[0] if args else "")
                except Exception:
                    continue
                for r in res:
                    print(i, json.dumps(r, ensure_ascii=False))
        elif cmd == "set":
            data = json.loads(args[0]) if not os.path.isfile(args[0]) else json.load(open(args[0], encoding="utf-8"))
            for sel, val in data.items():
                out = None
                for f in frames(pg):
                    try:
                        out = f.evaluate(SET_JS, [sel, val])
                    except Exception:
                        out = None
                    if out is not None:
                        break
                print(sel, "→", out if out is not None else "NOT FOUND")
        elif cmd == "click":
            ok = False
            pg.on("dialog", lambda d: (print("DIALOG:", d.message), d.accept()))
            for f in frames(pg):
                try:
                    ok = f.evaluate(CLICK_JS, args[0])
                except Exception:
                    ok = False
                if ok:
                    break
            time.sleep(2)
            print("clicked" if ok else "NOT FOUND", pg.url)
        elif cmd == "goto":
            pg.goto(args[0])
            print(pg.url, pg.title())
        elif cmd == "read":
            for sel in args:
                v = None
                for f in frames(pg):
                    try:
                        v = f.evaluate("s => { const e = document.querySelector(s); return e ? (e.tagName==='SELECT' ? e.value + '=' + (e.selectedOptions[0]||{}).text : e.value ?? e.innerText) : null; }", sel)
                    except Exception:
                        v = None
                    if v is not None:
                        break
                print(sel, "=", v)
        elif cmd == "comments":
            d = json.load(open(args[0], encoding="utf-8"))
            for sel, val in d["comments"].items():
                out = None
                for f in frames(pg):
                    try:
                        out = f.evaluate(SET_JS, ["#" + sel, val])
                    except Exception:
                        out = None
                    if out is not None:
                        break
                print(sel, "→", out if out is not None else "NOT FOUND")
        else:
            print(__doc__)


if __name__ == "__main__":
    main()
