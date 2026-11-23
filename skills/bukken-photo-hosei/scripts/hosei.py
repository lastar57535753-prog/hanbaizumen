#!/usr/bin/env python3
"""物件の広告写真を「構造を変えずに」補正する。

やること（すべて画素ごとの色・明るさ調整か、画像全体の回転だけ）:
  1. 向きの正規化（EXIF）
  2. 傾き補正（縦線から求めた回転角。±0.3°〜±5°のときだけ。回転＋内側トリミング）
  3. ホワイトバランス（グレーワールド。補正量に上限あり）
  4. 明るさ・コントラスト（明度だけを伸張＋ガンマ＋弱い局所コントラスト）
  5. 空の差し替え（任意）: 空のマスク内だけを青空に置き換える。マスク外の画素は1画素も変えない
  6. 書き出し（presets.json のサイズ・画質・容量上限）

やらないこと: 物を足す・消す・形を変える（壁・柱・窓・設備・電線・眺望・傷汚れ）。
生成AI（Codex の $imagegen 等）で物件写真そのものを描き直すことはしない。

使い方:
  python hosei.py 入力(ファイル or フォルダ) 出力フォルダ [--sky auto|off|マスク.png] [--sky-image 空.jpg]
                  [--preset web] [--interior] [--no-straighten]
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sky import detect_sky_mask, make_sky, composite_sky, sky_is_already_blue, sun_in_frame  # noqa: E402

EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".heic"}
SKY_NOTE = "※空は画像処理により青空に差し替えています。"


# ---------------------------------------------------------------- 読み書き
def load_rgb(path: Path) -> tuple[np.ndarray, bytes | None]:
    im = Image.open(path)
    icc = im.info.get("icc_profile")
    im = ImageOps.exif_transpose(im).convert("RGB")
    return np.asarray(im).copy(), icc


def save_with_preset(rgb: np.ndarray, out: Path, preset: dict, icc: bytes | None) -> dict:
    im = Image.fromarray(rgb)
    long_side = preset.get("long_side")
    if long_side and max(im.size) > long_side:
        s = long_side / max(im.size)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    fmt = preset.get("format", "jpeg").lower()
    q = int(preset.get("quality", 88))
    max_bytes = int(preset.get("max_kb", 0)) * 1024
    kw = {"icc_profile": icc} if icc else {}
    if fmt == "png":
        out = out.with_suffix(".png")
        im.save(out, **kw)
        return {"file": out.name, "size": im.size, "quality": None, "bytes": out.stat().st_size}
    out = out.with_suffix(".jpg")
    while True:
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=q, optimize=True, progressive=True, subsampling=0 if q >= 90 else 2, **kw)
        if not max_bytes or buf.tell() <= max_bytes or q <= 60:
            break
        q -= 4
    out.write_bytes(buf.getvalue())
    return {"file": out.name, "size": im.size, "quality": q, "bytes": out.stat().st_size}


# ---------------------------------------------------------------- 傾き
def estimate_roll(rgb: np.ndarray) -> float:
    """縦に近い直線の傾きの長さ加重中央値（度）。正=反時計回りに傾いている。"""
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    s = 1200 / max(g.shape)
    g = cv2.resize(g, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else g
    edges = cv2.Canny(cv2.GaussianBlur(g, (3, 3), 0), 60, 160)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 720, threshold=80,
                            minLineLength=max(g.shape) // 8, maxLineGap=6)
    if lines is None:
        return 0.0
    angs, wts = [], []
    for x1, y1, x2, y2 in np.asarray(lines).reshape(-1, 4):
        dx, dy = x2 - x1, y2 - y1
        if dy == 0:
            continue
        a = math.degrees(math.atan2(dx, dy))  # 縦線からのずれ
        if a > 90:
            a -= 180
        if a < -90:
            a += 180
        if abs(a) <= 8:
            angs.append(a)
            wts.append(math.hypot(dx, dy))
    if len(angs) < 4:
        return 0.0
    o = np.argsort(angs)
    a, w = np.array(angs)[o], np.array(wts)[o]
    c = np.cumsum(w)
    return float(a[np.searchsorted(c, c[-1] / 2)])


def rotate_crop(rgb: np.ndarray, deg: float) -> np.ndarray:
    h, w = rgb.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), -deg, 1.0)
    rot = cv2.warpAffine(rgb, M, (w, h), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)
    # 回転で生じた余白が入らない最大の同比率矩形
    t = math.radians(abs(deg))
    sc = 1 / (math.cos(t) + max(w / h, h / w) * math.sin(t))
    cw, ch = int(w * sc), int(h * sc)
    x0, y0 = (w - cw) // 2, (h - ch) // 2
    return rot[y0:y0 + ch, x0:x0 + cw].copy()


# ---------------------------------------------------------------- 色・明るさ
def white_balance(rgb: np.ndarray, strength: float = 0.6, cap: float = 0.12) -> tuple[np.ndarray, list]:
    f = rgb.astype(np.float32)
    lum = f.mean(axis=2)
    sel = (lum > 40) & (lum < 220)
    if sel.sum() < 1000:
        return rgb, [1, 1, 1]
    means = np.array([f[..., c][sel].mean() for c in range(3)])
    gains = means.mean() / means
    gains = 1 + (gains - 1) * strength
    gains = np.clip(gains, 1 - cap, 1 + cap)
    out = np.clip(f * gains, 0, 255).astype(np.uint8)
    return out, [round(float(x), 3) for x in gains]


def tone(rgb: np.ndarray, interior: bool) -> tuple[np.ndarray, dict]:
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    L = lab[..., 0].astype(np.float32) / 255.0
    lo, hi = np.percentile(L, [0.5, 99.6])
    lo = min(lo, 0.08)            # 黒は締めすぎない
    hi = max(hi, 0.85)            # 白は飛ばさない
    Ln = np.clip((L - lo) / (hi - lo), 0, 1)
    target = 0.60 if interior else 0.55
    m = float(np.clip(np.median(Ln), 0.05, 0.95))
    gamma = float(np.clip(math.log(target) / math.log(m), 0.62, 1.05))
    Ln = Ln ** gamma
    # 局所コントラスト（CLAHE を4割だけ混ぜる。影の中のディテールを起こす）
    L8 = (Ln * 255).astype(np.uint8)
    cl = cv2.createCLAHE(clipLimit=1.6, tileGridSize=(8, 8)).apply(L8)
    Lf = cv2.addWeighted(L8, 0.6, cl, 0.4, 0)
    lab[..., 0] = Lf
    out = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    # 彩度を少しだけ（くすみ取り）
    hsv = cv2.cvtColor(out, cv2.COLOR_RGB2HSV).astype(np.float32)
    s = hsv[..., 1] / 255.0
    hsv[..., 1] = np.clip(s + 0.10 * s * (1 - s) * 2, 0, 1) * 255
    out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    return out, {"black": round(float(lo), 3), "white": round(float(hi), 3), "gamma": round(gamma, 3)}


def sharpen(rgb: np.ndarray, amount: float = 0.35) -> np.ndarray:
    blur = cv2.GaussianBlur(rgb, (0, 0), 1.2)
    return cv2.addWeighted(rgb, 1 + amount, blur, -amount, 0)


# ---------------------------------------------------------------- 本体
def process(path: Path, outdir: Path, args, presets: dict) -> dict:
    rgb, icc = load_rgb(path)
    log = {"src": path.name, "ops": []}

    if not args.no_straighten:
        a = estimate_roll(rgb)
        if 0.3 <= abs(a) <= 5:
            rgb = rotate_crop(rgb, a)
            log["ops"].append(f"傾き補正 {a:+.2f}°")
        log["roll_deg"] = round(a, 2)

    rgb, gains = white_balance(rgb)
    log["ops"].append(f"WB {gains}")
    rgb, t = tone(rgb, args.interior)
    log["ops"].append(f"明るさ black={t['black']} white={t['white']} gamma={t['gamma']}")

    log["sky"] = "なし"
    if args.sky != "off":
        if args.sky == "auto":
            mask = detect_sky_mask(rgb)
        else:
            m = Image.open(args.sky).convert("L").resize((rgb.shape[1], rgb.shape[0]), Image.BILINEAR)
            mask = np.asarray(m).astype(np.float32) / 255.0
        cover = float((mask > 0.5).mean())
        if cover < 0.01:
            log["sky"] = "空が見つからない→差し替えなし"
        elif sun_in_frame(rgb, mask):
            log["sky"] = "太陽の写り込みあり（晴天）→空はそのまま"
        elif sky_is_already_blue(rgb, mask) and not args.force_sky:
            log["sky"] = f"既に青空（{cover:.0%}）→差し替えなし"
        else:
            before = rgb.copy()
            sky_rgb = (np.asarray(Image.open(args.sky_image).convert("RGB")) if args.sky_image
                       else make_sky(rgb.shape[1], rgb.shape[0], mask, seed=hash(path.name) & 0xFFFF, clouds=args.clouds))
            rgb, alpha = composite_sky(rgb, sky_rgb, mask)
            # 構造保全チェック: 空マスクの外は1画素も変わっていないこと
            outside = alpha <= 0
            changed = int(np.any(before[outside] != rgb[outside], axis=-1).sum())
            if changed:
                raise SystemExit(f"[NG] {path.name}: 空マスクの外で {changed} 画素が変化。出力を中止")
            log["sky"] = f"差し替え（空 {cover:.0%}・マスク外の変化 0画素）"
            log["note"] = SKY_NOTE
            Image.fromarray((alpha * 255).astype(np.uint8)).save(outdir / f"{path.stem}_skymask.png")

    rgb = sharpen(rgb)
    outs = []
    for name in args.preset:
        p = presets[name]
        info = save_with_preset(rgb, outdir / f"{path.stem}{p.get('suffix', '_' + name)}", p, icc)
        outs.append({"preset": name, **info})
    log["outputs"] = outs
    return log


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("outdir")
    ap.add_argument("--sky", default="off", help="off（既定）/ auto / 空マスクPNG（白=空）")
    ap.add_argument("--sky-image", help="差し替えに使う空の画像（未指定なら自動生成のグラデーション空）")
    ap.add_argument("--clouds", action="store_true", help="自動生成の空に薄い雲を入れる")
    ap.add_argument("--force-sky", action="store_true", help="既に青空でも差し替える（太陽が写り込んだ晴天の写真は差し替えない）")
    ap.add_argument("--preset", default="web", help="presets.json のキーをカンマ区切り（例 web,print）")
    ap.add_argument("--interior", action="store_true", help="室内写真（明るめに仕上げる）")
    ap.add_argument("--no-straighten", action="store_true")
    args = ap.parse_args()
    args.preset = [s.strip() for s in args.preset.split(",") if s.strip()]

    presets = json.loads((HERE.parent / "assets" / "presets.json").read_text(encoding="utf-8"))
    for n in args.preset:
        if n not in presets:
            raise SystemExit(f"プリセット {n} がありません: {list(presets)}")

    src = Path(args.src)
    files = sorted(p for p in src.iterdir() if p.suffix.lower() in EXTS) if src.is_dir() else [src]
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    logs = []
    for f in files:
        lg = process(f, outdir, args, presets)
        logs.append(lg)
        print(f"{f.name}: {' / '.join(lg['ops'])} / 空: {lg['sky']}")

    with open(outdir / "hosei_log.csv", "w", newline="", encoding="utf-8-sig") as fp:
        w = csv.writer(fp)
        w.writerow(["元ファイル", "出力", "実施した補正", "空", "注記"])
        for lg in logs:
            w.writerow([lg["src"], " ".join(o["file"] for o in lg["outputs"]),
                        " / ".join(lg["ops"]), lg["sky"], lg.get("note", "")])
    if any(lg.get("note") for lg in logs):
        print(f"\n空を差し替えた写真があります。掲載時は注記を添えてください: {SKY_NOTE}")
    print(f"台帳: {outdir / 'hosei_log.csv'}")


if __name__ == "__main__":
    main()
