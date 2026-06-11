"""비전 기반 설비 상태 측정.

Pillow + numpy 고전 영상처리로 PM/BM 점검 이미지를 정량화한다.
레시피(recipe) 로 임계값·캘리브레이션을 항목별로 표준화한다.

kind:
  WEAR       마모 영역 비율(%)  — 어두운(또는 밝은) 픽셀 비율
  CORROSION  부식 영역 비율(%)  — 적갈색(HSV) 픽셀 비율
  DIMENSION  치수(mm)          — 행별 엣지 간 폭의 중앙값 × mm_per_px
  ALIGNMENT  정렬 편차(deg)    — 주 엣지 직선 피팅 기울기
"""
import io

import numpy as np
from PIL import Image

MAX_SIDE = 1024


def _load(data: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(data)).convert("RGB")
    if max(img.size) > MAX_SIDE:
        img.thumbnail((MAX_SIDE, MAX_SIDE))
    return np.asarray(img, dtype=np.float32)


def _gray(rgb: np.ndarray) -> np.ndarray:
    return rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)


def analyze(data: bytes, kind: str, recipe: dict | None = None) -> dict:
    recipe = recipe or {}
    rgb = _load(data)
    kind = kind.upper()
    if kind == "WEAR":
        return _wear(rgb, recipe)
    if kind == "CORROSION":
        return _corrosion(rgb, recipe)
    if kind == "DIMENSION":
        return _dimension(rgb, recipe)
    if kind == "ALIGNMENT":
        return _alignment(rgb, recipe)
    raise ValueError(f"unsupported kind: {kind}")


def _wear(rgb: np.ndarray, recipe: dict) -> dict:
    """마모부(정상면 대비 어둡거나 밝은 영역) 비율."""
    g = _gray(rgb)
    thr = recipe.get("threshold")  # 0~255, 미지정 시 Otsu 간이(평균-표준편차)
    mode = recipe.get("mode", "dark")  # dark: 어두운 영역이 마모
    if thr is None:
        thr = float(g.mean() - 0.8 * g.std()) if mode == "dark" else float(g.mean() + 0.8 * g.std())
    mask = g < thr if mode == "dark" else g > thr
    ratio = float(mask.mean() * 100)
    return {
        "measured_value": round(ratio, 2),
        "unit": "%",
        "detail": {"threshold": round(float(thr), 1), "mode": mode,
                   "image_size": list(g.shape[::-1])},
    }


def _corrosion(rgb: np.ndarray, recipe: dict) -> dict:
    """녹(적갈색) 픽셀 비율: R 채널 우세 + 저채도 갈색 톤."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    rust = (r > g * recipe.get("rg_ratio", 1.15)) & (r > b * recipe.get("rb_ratio", 1.25)) & (r > 60)
    ratio = float(rust.mean() * 100)
    return {
        "measured_value": round(ratio, 2),
        "unit": "%",
        "detail": {"rule": "R>1.15G & R>1.25B & R>60", "image_size": list(r.shape[::-1])},
    }


def _dimension(rgb: np.ndarray, recipe: dict) -> dict:
    """수평 방향 폭 측정: 행마다 좌/우 첫 엣지 사이 픽셀 수의 중앙값 × mm_per_px.

    mm_per_px 는 레시피 직접 지정 또는 ref_length_mm/ref_length_px 로 환산.
    """
    mm_per_px = recipe.get("mm_per_px")
    if mm_per_px is None and recipe.get("ref_length_mm") and recipe.get("ref_length_px"):
        mm_per_px = recipe["ref_length_mm"] / recipe["ref_length_px"]
    g = _gray(rgb)
    # 수평 그래디언트 → 행별로 강한 엣지의 좌/우 끝 위치
    gx = np.abs(np.diff(g, axis=1))
    thr = float(gx.mean() + 2 * gx.std())
    widths = []
    for row in gx:
        idx = np.where(row > thr)[0]
        if len(idx) >= 2:
            widths.append(idx[-1] - idx[0])
    if not widths:
        return {"measured_value": None, "unit": "mm",
                "detail": {"error": "엣지 미검출 — 조명/배경 대비 확인 필요"}}
    width_px = float(np.median(widths))
    value = round(width_px * mm_per_px, 2) if mm_per_px else round(width_px, 1)
    return {
        "measured_value": value,
        "unit": "mm" if mm_per_px else "px",
        "detail": {"width_px": round(width_px, 1), "mm_per_px": mm_per_px,
                   "rows_used": len(widths), "edge_threshold": round(thr, 1)},
    }


def _alignment(rgb: np.ndarray, recipe: dict) -> dict:
    """주 엣지(행별 최대 그래디언트 위치)를 직선 피팅하여 기울기(도) 산출."""
    g = _gray(rgb)
    gx = np.abs(np.diff(g, axis=1))
    ys, xs = [], []
    row_max = gx.max(axis=1)
    thr = float(row_max.mean())
    for y, row in enumerate(gx):
        if row.max() > thr:
            ys.append(y)
            xs.append(int(row.argmax()))
    if len(xs) < 10:
        return {"measured_value": None, "unit": "deg",
                "detail": {"error": "엣지 미검출"}}
    slope, _ = np.polyfit(ys, xs, 1)
    angle = float(np.degrees(np.arctan(slope)))
    residual = float(np.std(np.array(xs) - np.polyval(np.polyfit(ys, xs, 1), ys)))
    return {
        "measured_value": round(abs(angle), 3),
        "unit": "deg",
        "detail": {"angle_deg": round(angle, 3), "straightness_residual_px": round(residual, 2),
                   "points": len(xs)},
    }


def judge(value: float | None, lower: float | None, upper: float | None) -> str:
    """한계값 대비 자동 판정. 한계 ±10% 밴드 접근 시 CHECK."""
    if value is None:
        return "CHECK"
    if lower is not None and value < lower:
        return "NG"
    if upper is not None and value > upper:
        return "NG"
    span = None
    if lower is not None and upper is not None:
        span = upper - lower
    if upper is not None and span and value > upper - 0.1 * span:
        return "CHECK"
    if lower is not None and span and value < lower + 0.1 * span:
        return "CHECK"
    return "OK"
