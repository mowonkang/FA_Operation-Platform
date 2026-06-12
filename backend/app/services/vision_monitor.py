"""정기 촬영 기반 설비 상태 감시 (Vision Condition Monitoring).

기준 이미지(골든 샘플)와 정기 촬영본을 비교하여 이상을 감지한다.

파이프라인:
  1) 그레이 변환·리사이즈 → 2) 위상상관(phase correlation) 위치 정합(카메라 미세 흔들림 보정)
  → 3) 국부 차이맵 + 변화 블록 클러스터링 → 4) 타입별 전용 검출
  → 5) 이상점수(0~100)·판정 → 6) 변화영역 오버레이 이미지 생성

타입별 검출기:
  BOLT    볼트 풀림 — 합마크(매칭 라인) 회전각: 그래디언트 방향 히스토그램의 원형 시프트
  WIRE    와이어 소선 불량 — 로프 윤곽 주변 신규 돌출(에지 증가·국부 변화 블롭)
  SURFACE 파손/크랙 — 신규 변화 영역 면적·블롭 수
  RAIL    레일 단차 — 조인트 좌/우 수평 에지 y-위치 차 → mm 환산
  GENERIC 범용 — 변화율 기반
"""
import io
import math

import numpy as np
from PIL import Image, ImageDraw

MAX_SIDE = 768
BLOCK = 16  # 변화 블록 크기(px)


# ───────────────────────── 기본 유틸 ─────────────────────────

def load_gray(data: bytes) -> tuple[np.ndarray, Image.Image]:
    img = Image.open(io.BytesIO(data)).convert("RGB")
    if max(img.size) > MAX_SIDE:
        img.thumbnail((MAX_SIDE, MAX_SIDE))
    arr = np.asarray(img, dtype=np.float32)
    gray = arr @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    return gray, img


def _box_blur(a: np.ndarray, r: int = 2) -> np.ndarray:
    """누적합 기반 박스 블러 (의존성 없이 가우시안 근사 — 2회 적용)."""
    for _ in range(2):
        c = np.cumsum(np.cumsum(a, axis=0), axis=1)
        c = np.pad(c, ((1, 0), (1, 0)))
        h, w = a.shape
        y0 = np.clip(np.arange(h) - r, 0, h)
        y1 = np.clip(np.arange(h) + r + 1, 0, h)
        x0 = np.clip(np.arange(w) - r, 0, w)
        x1 = np.clip(np.arange(w) + r + 1, 0, w)
        area = (y1 - y0)[:, None] * (x1 - x0)[None, :]
        a = (c[y1][:, x1] - c[y1][:, x0] - c[y0][:, x1] + c[y0][:, x0]) / area
    return a


def register(base: np.ndarray, cur: np.ndarray) -> tuple[np.ndarray, tuple[int, int]]:
    """위상상관으로 평행이동량 추정 후 정합. (카메라 위치 미세 변화 보정, ±64px)"""
    h = min(base.shape[0], cur.shape[0])
    w = min(base.shape[1], cur.shape[1])
    b, c = base[:h, :w], cur[:h, :w]
    win = np.outer(np.hanning(h), np.hanning(w))
    fb = np.fft.rfft2(b * win)
    fc = np.fft.rfft2(c * win)
    cross = fb * np.conj(fc)
    cross /= np.abs(cross) + 1e-9
    corr = np.fft.irfft2(cross, s=(h, w))
    peak = np.unravel_index(np.argmax(corr), corr.shape)
    dy = peak[0] if peak[0] <= h // 2 else peak[0] - h
    dx = peak[1] if peak[1] <= w // 2 else peak[1] - w
    dy, dx = int(np.clip(dy, -64, 64)), int(np.clip(dx, -64, 64))
    shifted = np.roll(np.roll(c, dy, axis=0), dx, axis=1)
    return shifted[:h, :w], (dy, dx)


def diff_blocks(base: np.ndarray, cur: np.ndarray, sensitivity: float = 3.0):
    """국부 차이맵 → BLOCK 단위 변화 플래그 → 변화율·블롭 클러스터."""
    h, w = base.shape
    b = _box_blur(base.copy())
    c = _box_blur(cur.copy())
    diff = np.abs(b - c)
    noise = max(float(np.median(diff)) * 2.5, 4.0)
    mask = diff > noise * sensitivity / 3.0

    gh, gw = h // BLOCK, w // BLOCK
    grid = np.zeros((gh, gw), dtype=bool)
    for gy in range(gh):
        for gx in range(gw):
            blk = mask[gy * BLOCK:(gy + 1) * BLOCK, gx * BLOCK:(gx + 1) * BLOCK]
            grid[gy, gx] = blk.mean() > 0.25
    changed_ratio = float(grid.mean() * 100)

    # 블록 그리드 BFS 클러스터링
    visited = np.zeros_like(grid)
    blobs = []
    for gy in range(gh):
        for gx in range(gw):
            if grid[gy, gx] and not visited[gy, gx]:
                stack, cells = [(gy, gx)], []
                visited[gy, gx] = True
                while stack:
                    y, x = stack.pop()
                    cells.append((y, x))
                    for ny, nx in ((y+1, x), (y-1, x), (y, x+1), (y, x-1)):
                        if 0 <= ny < gh and 0 <= nx < gw and grid[ny, nx] and not visited[ny, nx]:
                            visited[ny, nx] = True
                            stack.append((ny, nx))
                ys = [c_[0] for c_ in cells]
                xs = [c_[1] for c_ in cells]
                blobs.append({
                    "cells": len(cells),
                    "box": [min(xs) * BLOCK, min(ys) * BLOCK,
                            (max(xs) + 1) * BLOCK, (max(ys) + 1) * BLOCK],
                })
    blobs.sort(key=lambda x: -x["cells"])
    return changed_ratio, blobs


# ───────────────────────── 타입별 검출기 ─────────────────────────

def _orientation_hist(gray: np.ndarray, bins: int = 36,
                      mask: np.ndarray | None = None) -> np.ndarray:
    gx = np.zeros_like(gray)
    gy = np.zeros_like(gray)
    gx[:, 1:-1] = gray[:, 2:] - gray[:, :-2]
    gy[1:-1, :] = gray[2:, :] - gray[:-2, :]
    mag = np.hypot(gx, gy)
    ang = (np.degrees(np.arctan2(gy, gx)) + 360) % 180  # 0~180 (선분 방향)
    sel = mag > np.percentile(mag, 90)
    if mask is not None:
        sel &= mask
    if sel.sum() < 20:
        return np.zeros(bins)
    hist, _ = np.histogram(ang[sel], bins=bins, range=(0, 180), weights=mag[sel])
    return hist / (hist.sum() + 1e-9)


def bolt_rotation_deg(base: np.ndarray, cur: np.ndarray) -> float:
    """합마크 회전각 추정.

    마크가 회전하면 '변화 영역'(옛 위치+새 위치)이 생긴다. 변화 영역에 한정해
    기준 이미지의 지배 선분각(옛 마크)과 현재 이미지의 지배 선분각(새 마크)을
    구하고, 두 각의 원형 거리(0~90°)를 회전각으로 본다. 고정 에지(육각 머리·배경)는
    변화 영역 밖이므로 영향이 배제된다.
    """
    b = _box_blur(base.copy())
    c = _box_blur(cur.copy())
    diff = np.abs(b - c)
    thr = max(float(np.median(diff)) * 4.0, 8.0)
    mask = diff > thr
    if mask.mean() < 0.002:  # 변화 자체가 없음 → 회전 없음
        return 0.0
    hb = _orientation_hist(base, mask=mask)
    hc = _orientation_hist(cur, mask=mask)
    if hb.sum() < 0.5 or hc.sum() < 0.5:
        return 0.0
    n = len(hb)
    delta = abs(int(np.argmax(hb)) - int(np.argmax(hc))) * (180 / n)
    if delta > 90:
        delta = 180 - delta
    return delta


def edge_density(gray: np.ndarray) -> float:
    gx = np.abs(np.diff(gray, axis=1))
    gy = np.abs(np.diff(gray, axis=0))
    thr = float(gx.mean() + 2 * gx.std())
    return float((gx > thr).mean() + (gy[:, :gx.shape[1]] > thr).mean()) * 100


def rail_step_mm(gray: np.ndarray, mm_per_px: float | None) -> dict:
    """레일 단차: 각 열의 최강 수평에지 y위치 → 좌/우 절반 중앙값 차이."""
    gy = np.abs(np.diff(gray, axis=0))
    h, w = gy.shape
    band = gy[h // 6: h * 5 // 6]  # 상하단 노이즈 제외
    ys = band.argmax(axis=0)
    strength = band.max(axis=0)
    valid = strength > strength.mean()
    left = ys[: w // 2][valid[: w // 2]]
    right = ys[w // 2:][valid[w // 2:]]
    if len(left) < 10 or len(right) < 10:
        return {"step_px": None, "step_mm": None, "note": "레일 에지 미검출"}
    step_px = float(abs(np.median(left) - np.median(right)))
    return {
        "step_px": round(step_px, 1),
        "step_mm": round(step_px * mm_per_px, 2) if mm_per_px else None,
    }


# ───────────────────────── 종합 분석 ─────────────────────────

TYPE_LABEL = {"BOLT": "볼트 풀림", "WIRE": "와이어 소선", "SURFACE": "표면 파손/크랙",
              "RAIL": "레일 단차", "GENERIC": "범용 변화감지"}


def analyze_shot(baseline: bytes, shot: bytes, target_type: str,
                 params: dict | None = None) -> dict:
    """기준 대비 촬영본 분석 → 이상점수·판정·검출 상세·변화 박스 목록."""
    params = params or {}
    base_g, _ = load_gray(baseline)
    cur_g, cur_img = load_gray(shot)
    cur_reg, (dy, dx) = register(base_g, cur_g)
    base_c = base_g[: cur_reg.shape[0], : cur_reg.shape[1]]

    sensitivity = float(params.get("sensitivity", 3.0))
    changed_ratio, blobs = diff_blocks(base_c, cur_reg, sensitivity)

    detail: dict = {
        "registration_shift_px": [dy, dx],
        "changed_area_pct": round(changed_ratio, 2),
        "change_blobs": len(blobs),
        "largest_blob_cells": blobs[0]["cells"] if blobs else 0,
    }
    findings: list[str] = []
    score = min(changed_ratio * 8, 60.0)  # 변화율 기본 점수 (7.5%≈60점)

    t = target_type.upper()
    if t == "BOLT":
        deg = bolt_rotation_deg(base_c, cur_reg)
        detail["marking_rotation_deg"] = round(deg, 1)
        limit = float(params.get("rotation_limit_deg", 8.0))
        if deg >= limit:
            score = max(score, 75.0)
            findings.append(f"합마크 회전 {deg:.1f}° (한계 {limit}°) — 볼트 풀림 의심")
        elif deg >= limit * 0.5:
            score = max(score, 40.0)
            findings.append(f"합마크 미세 회전 {deg:.1f}° — 추세 감시")
    elif t == "WIRE":
        ed_b, ed_c = edge_density(base_c), edge_density(cur_reg)
        detail["edge_density_base"] = round(ed_b, 2)
        detail["edge_density_cur"] = round(ed_c, 2)
        spur = max(ed_c - ed_b, 0)
        detail["edge_increase"] = round(spur, 2)
        small_blobs = sum(1 for b in blobs if b["cells"] <= 4)
        detail["small_blobs"] = small_blobs
        if spur > 1.2 or small_blobs >= 3:
            score = max(score, 70.0)
            findings.append(f"로프 윤곽 신규 돌출 {small_blobs}개소·에지 증가 {spur:.1f}%p — 소선 단선 의심")
        elif spur > 0.5 or small_blobs >= 1:
            score = max(score, 35.0)
            findings.append("미세 윤곽 변화 — 차기 촬영 주기 단축 권장")
    elif t == "RAIL":
        r = rail_step_mm(cur_reg, params.get("mm_per_px"))
        detail.update({"rail_" + k: v for k, v in r.items()})
        limit_mm = float(params.get("step_limit_mm", 0.5))
        step = r.get("step_mm")
        if step is not None:
            if step >= limit_mm:
                score = max(score, 80.0)
                findings.append(f"레일 이음부 단차 {step}mm (관리기준 {limit_mm}mm) — 보정 필요")
            elif step >= limit_mm * 0.6:
                score = max(score, 45.0)
                findings.append(f"단차 {step}mm — 기준 접근, 감시 강화")
        elif r.get("step_px") and not params.get("mm_per_px"):
            findings.append(f"단차 {r['step_px']}px 검출 — mm 환산하려면 포인트에 mm_per_px 설정")
    elif t == "SURFACE":
        big = [b for b in blobs if b["cells"] >= 6]
        detail["large_damage_blobs"] = len(big)
        if big:
            score = max(score, 70.0)
            findings.append(f"신규 손상 의심 영역 {len(big)}개소 (최대 {big[0]['cells']}블록) — 파손/크랙 확인 필요")

    warn = float(params.get("warn_score", 30))
    ng = float(params.get("ng_score", 60))
    judgment = "NG" if score >= ng else ("CHECK" if score >= warn else "OK")
    if not findings and judgment != "OK":
        findings.append(f"기준 대비 변화 영역 {changed_ratio:.1f}% — 현장 확인 권장")

    overlay = make_overlay(cur_img, blobs, judgment)
    return {
        "score": round(score, 1),
        "judgment": judgment,
        "findings": findings,
        "detail": detail,
        "boxes": [b["box"] for b in blobs[:12]],
        "overlay_png": overlay,
    }


def make_overlay(img: Image.Image, blobs: list[dict], judgment: str) -> bytes:
    """변화 블롭에 박스를 그린 오버레이 PNG."""
    out = img.copy()
    d = ImageDraw.Draw(out)
    color = {"NG": (220, 38, 38), "CHECK": (217, 119, 6), "OK": (21, 128, 61)}[judgment]
    for b in blobs[:12]:
        d.rectangle(b["box"], outline=color, width=3)
    d.rectangle([0, 0, out.width - 1, out.height - 1], outline=color, width=4)
    buf = io.BytesIO()
    out.save(buf, format="PNG")
    return buf.getvalue()


def extract_video_frames(data: bytes, max_frames: int = 6) -> list[bytes]:
    """동영상에서 균등 간격 프레임 추출 (opencv 필요 — 미설치 시 예외)."""
    try:
        import cv2
    except ImportError:
        raise RuntimeError("동영상 분석에는 opencv-python-headless 설치가 필요합니다")
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(data)
        path = f.name
    try:
        cap = cv2.VideoCapture(path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        idxs = sorted({int(i) for i in np.linspace(0, total - 1, max_frames)})
        frames = []
        for i in idxs:
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ok, frame = cap.read()
            if not ok:
                continue
            ok2, png = cv2.imencode(".png", frame)
            if ok2:
                frames.append(png.tobytes())
        cap.release()
        return frames
    finally:
        os.unlink(path)
