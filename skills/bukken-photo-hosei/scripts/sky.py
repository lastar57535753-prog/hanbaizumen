"""空の検出・生成・合成。

方針: 空のマスクの中だけを置き換える。電線・木の枝・アンテナなど空に重なる細い物は
「空らしさ（明るさ・色・平坦さ）」で自動的にマスクから外れるので消えない。
マスクの外の画素は合成前とまったく同じ値のまま残す（hosei.py で検査する）。
"""
from __future__ import annotations

import cv2
import numpy as np


def _skyness(rgb: np.ndarray, flat_thr: float = 40) -> np.ndarray:
    """画素ごとの空らしさ 0/1（明るい灰白〜青で、なだらか）。"""
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV).astype(np.float32)
    h, s, v = hsv[..., 0], hsv[..., 1] / 255, hsv[..., 2] / 255
    overcast = (v > 0.55) & (s < 0.22)                      # 曇天・白飛び
    blue = (h >= 88) & (h <= 132) & (s > 0.10) & (v > 0.30)  # 青空
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    grad = cv2.magnitude(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
    flat = cv2.GaussianBlur(grad, (0, 0), 2) < flat_thr
    return ((overcast | blue) & flat).astype(np.float32)


def detect_sky_mask(rgb: np.ndarray) -> np.ndarray:
    """空の領域（0..1, float32）。

    1) 縮小画像で空らしい画素を拾い、上端（または上半分の左右端）につながる塊だけ残す
    2) 塊を一度まとめて（電線ごと）面にする
    3) フル解像度で「周りの空の色」との差を見て、電線・枝・アンテナ等の
       空と違う色の物をマスクから外す（＝それらは元写真のまま残る）
    """
    H, W = rgb.shape[:2]
    s = 1000 / max(H, W)
    small = cv2.resize(rgb, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else rgb
    h, w = small.shape[:2]
    cand = _skyness(small)
    cand = cv2.morphologyEx(cand, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    link = cv2.dilate((cand > 0).astype(np.uint8), np.ones((7, 7), np.uint8))
    n, lab = cv2.connectedComponents(link, connectivity=4)
    seeds = set(np.unique(lab[0, :])) | set(np.unique(lab[: int(h * 0.6), 0])) | set(np.unique(lab[: int(h * 0.6), -1]))
    seeds.discard(0)
    region = (np.isin(lab, list(seeds)) & (link > 0)).astype(np.uint8)
    # 面にする（電線のすき間を埋める）。下方向に建物へはみ出さないよう cand と重なる範囲に限定
    region = cv2.morphologyEx(region, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    region = (region & cv2.dilate((cand > 0).astype(np.uint8), np.ones((9, 9), np.uint8))).astype(np.float32)
    # 周りの空の色（空の画素だけで平均した色）
    wsum = cv2.blur(region * (cand > 0), (31, 31)) + 1e-4
    ref = np.dstack([cv2.blur(small[..., c].astype(np.float32) * region * (cand > 0), (31, 31)) / wsum for c in range(3)])
    region = cv2.resize(region, (W, H), interpolation=cv2.INTER_LINEAR)
    ref = cv2.resize(ref, (W, H), interpolation=cv2.INTER_LINEAR)
    lab_img = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    lab_ref = cv2.cvtColor(np.clip(ref, 0, 255).astype(np.uint8), cv2.COLOR_RGB2LAB).astype(np.float32)
    dist = np.sqrt(((lab_img - lab_ref) ** 2).sum(axis=2))
    # 差が小さい=空（ノイズ程度は空のまま）、差が大きい=空に重なった物（残す）
    soft = np.clip((34 - dist) / 14, 0, 1)
    dark = lab_img[..., 0] < 0.33 * 255
    soft[dark] = 0
    return np.clip(region * soft, 0, 1).astype(np.float32)


def sky_is_already_blue(rgb: np.ndarray, mask: np.ndarray) -> bool:
    sel = mask > 0.5
    if sel.sum() < 100:
        return False
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    h, s = hsv[..., 0][sel], hsv[..., 1][sel] / 255
    return bool(((h >= 90) & (h <= 130) & (s > 0.25)).mean() > 0.6)


def sun_in_frame(rgb: np.ndarray, mask: np.ndarray) -> bool:
    """太陽が写り込んだ晴天か。白飛びした小さな塊が上側にあり、周りの空が青いとき True。
    曇天の白い空（空全体が白飛び）は塊が大きすぎるので False。"""
    H, W = rgb.shape[:2]
    s = 800 / max(H, W)
    small = cv2.resize(rgb, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else rgb
    m = cv2.resize(mask, (small.shape[1], small.shape[0]), interpolation=cv2.INTER_LINEAR)
    hsv = cv2.cvtColor(small, cv2.COLOR_RGB2HSV)
    h, sat, v = hsv[..., 0], hsv[..., 1] / 255, hsv[..., 2]
    sky = m > 0.3
    if sky.sum() < 100:
        return False
    blue_ratio = ((h >= 88) & (h <= 132) & (sat > 0.25))[sky].mean()
    if blue_ratio < 0.3:
        return False
    hot = ((v >= 250) & (sat < 0.12)).astype(np.uint8)
    hot[int(small.shape[0] * 0.7):] = 0
    n, lab, st, _ = cv2.connectedComponentsWithStats(hot, connectivity=8)
    total = small.shape[0] * small.shape[1]
    for i in range(1, n):
        x, y, w, hh, area = st[i]
        if not (0.0003 * total <= area <= 0.05 * total and area / max(w * hh, 1) > 0.35):
            continue
        # 太陽は周りが空と光のにじみで囲まれる（白い看板や壁は周りが建物）
        blob = (lab == i).astype(np.uint8)
        ring = (cv2.dilate(blob, np.ones((13, 13), np.uint8)) - blob) > 0
        if sky[ring].mean() >= 0.35 and (v[ring] > 200).mean() >= 0.7:
            return True
    return False


def make_sky(W: int, H: int, mask: np.ndarray, seed: int = 0, clouds: bool = False) -> np.ndarray:
    """自然な青空（上が濃く地平線側が淡い）。clouds=True で薄い雲を足す。"""
    ys = np.where(mask.max(axis=1) > 0.5)[0]
    bottom = (ys.max() + 1) if len(ys) else H
    y = np.clip(np.arange(H, dtype=np.float32) / max(bottom, 1), 0, 1)[:, None]
    top_c = np.array([38, 110, 205], np.float32)
    hor_c = np.array([168, 205, 238], np.float32)
    t = y ** 0.8
    sky = top_c * (1 - t[..., None]) + hor_c * t[..., None]
    sky = np.broadcast_to(sky, (H, W, 3)).copy()
    if not clouds:
        return np.clip(sky, 0, 255).astype(np.uint8)
    # 雲: ぼかしたノイズを重ねる（大きく柔らかく）
    rng = np.random.default_rng(seed)
    cloud = np.zeros((H, W), np.float32)
    for k, amp in ((220, 1.0), (90, 0.45), (36, 0.15)):
        n = rng.random((max(H // k, 2), max(W // k, 2))).astype(np.float32)
        cloud += amp * cv2.resize(n, (W, H), interpolation=cv2.INTER_CUBIC)
    cloud = (cloud - cloud.min()) / (np.ptp(cloud) + 1e-6)
    cloud = np.clip((cloud - 0.62) / 0.3, 0, 1) ** 1.5 * 0.55
    cloud *= np.clip(1 - y * 0.3, 0, 1)
    sky = sky * (1 - cloud[..., None]) + 250 * cloud[..., None]
    return np.clip(sky, 0, 255).astype(np.uint8)


def composite_sky(rgb: np.ndarray, sky: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    H, W = rgb.shape[:2]
    if sky.shape[:2] != (H, W):
        # 比率を保って覆うように拡大し、上寄せでトリミング
        sh, sw = sky.shape[:2]
        sc = max(W / sw, H / sh)
        sky = cv2.resize(sky, (int(sw * sc + 1), int(sh * sc + 1)), interpolation=cv2.INTER_CUBIC)
        x0 = (sky.shape[1] - W) // 2
        sky = sky[:H, x0:x0 + W]
    # 境界だけ内側に柔らかく（外側へは広げない＝マスク外は不変）
    hard = (mask > 0.5).astype(np.uint8)
    dist = cv2.distanceTransform(hard, cv2.DIST_L2, 3)
    alpha = np.clip(dist / 3.0, 0, 1) * mask
    alpha[hard == 0] = 0
    # 空の明るさを元写真の空に合わせる（浮かないように）
    sel = hard > 0
    if sel.any():
        src_l = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)[..., 0][sel].mean()
        sky_lab = cv2.cvtColor(sky, cv2.COLOR_RGB2LAB).astype(np.float32)
        d = np.clip((src_l - sky_lab[..., 0][sel].mean()) * 0.35, -25, 25)
        sky_lab[..., 0] = np.clip(sky_lab[..., 0] + d, 0, 255)
        sky = cv2.cvtColor(sky_lab.astype(np.uint8), cv2.COLOR_LAB2RGB)
    a = alpha[..., None]
    out = rgb.astype(np.float32) * (1 - a) + sky.astype(np.float32) * a
    out = np.where(a > 0, np.clip(np.round(out), 0, 255), rgb).astype(np.uint8)
    return out, alpha
