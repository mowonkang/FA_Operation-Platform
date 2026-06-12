"""상태감시 데모용 합성 이미지 — 볼트 합마크 회전 / 와이어 소선 돌출 / 레일 단차 / 표면 크랙.

실제 운영에서는 현장 촬영 이미지를 사용한다. 본 모듈은 알고리즘 시연·회귀 테스트용.
"""
import io
import math
import random

import numpy as np
from PIL import Image, ImageDraw

random.seed(7)
SIZE = (560, 420)


def _png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _noise(img: Image.Image, sigma: float = 3.0, shift: tuple[int, int] = (0, 0)) -> Image.Image:
    arr = np.asarray(img, dtype=np.float32)
    arr = np.roll(np.roll(arr, shift[0], axis=0), shift[1], axis=1)
    arr += np.random.normal(0, sigma, arr.shape)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def _bolt(mark_deg: float) -> Image.Image:
    img = Image.new("RGB", SIZE, (148, 152, 158))
    d = ImageDraw.Draw(img)
    cx, cy, r = 280, 210, 120
    # 플랜지 + 육각 볼트머리
    d.ellipse([cx - r - 40, cy - r - 40, cx + r + 40, cy + r + 40], fill=(120, 124, 130))
    pts = [(cx + r * math.cos(math.radians(a + 30)), cy + r * math.sin(math.radians(a + 30)))
           for a in range(0, 360, 60)]
    d.polygon(pts, fill=(188, 190, 194), outline=(80, 80, 84))
    d.ellipse([cx - 55, cy - 55, cx + 55, cy + 55], outline=(100, 100, 104), width=3)
    # 합마크(매칭 라인): 볼트머리→플랜지 연속 페인트 라인
    a = math.radians(mark_deg)
    d.line([cx + 30 * math.cos(a), cy + 30 * math.sin(a),
            cx + (r + 38) * math.cos(a), cy + (r + 38) * math.sin(a)],
           fill=(230, 60, 40), width=10)
    return img


def _wire(spurs: int) -> Image.Image:
    img = Image.new("RGB", SIZE, (210, 212, 215))
    d = ImageDraw.Draw(img)
    x0, x1 = 240, 320
    d.rectangle([x0, 0, x1, SIZE[1]], fill=(95, 98, 104))
    for y in range(-40, SIZE[1] + 40, 14):  # 스트랜드 꼬임 패턴
        d.line([x0, y, x1, y + 26], fill=(140, 144, 150), width=4)
    for i in range(spurs):  # 돌출 소선 (단선)
        y = 70 + i * 110 + random.randint(-15, 15)
        side = 1 if i % 2 == 0 else -1
        bx = x1 if side > 0 else x0
        d.line([bx, y, bx + side * 26, y - 14], fill=(70, 72, 76), width=3)
        d.line([bx + side * 26, y - 14, bx + side * 34, y - 26], fill=(70, 72, 76), width=2)
    return img


def _rail(step_px: int) -> Image.Image:
    img = Image.new("RGB", SIZE, (165, 168, 172))
    d = ImageDraw.Draw(img)
    y = 200
    d.rectangle([0, y, SIZE[0] // 2, y + 90], fill=(225, 227, 230))          # 좌측 레일 헤드
    d.rectangle([SIZE[0] // 2, y + step_px, SIZE[0], y + 90 + step_px],      # 우측 (단차)
                fill=(222, 224, 228))
    d.line([SIZE[0] // 2, y - 30, SIZE[0] // 2, y + 130], fill=(120, 122, 126), width=4)  # 조인트
    for x in range(40, SIZE[0], 90):
        d.ellipse([x, y + 110, x + 16, y + 126], fill=(110, 112, 116))       # 체결 볼트
    return img


def _surface(crack: bool) -> Image.Image:
    img = Image.new("RGB", SIZE, (172, 175, 179))
    d = ImageDraw.Draw(img)
    d.rectangle([40, 40, SIZE[0] - 40, SIZE[1] - 40], fill=(192, 194, 198), outline=(120, 120, 124), width=3)
    for x, y in [(80, 80), (SIZE[0] - 110, 80), (80, SIZE[1] - 110), (SIZE[0] - 110, SIZE[1] - 110)]:
        d.ellipse([x, y, x + 28, y + 28], fill=(130, 132, 136))
    if crack:
        pts = [(200, 120)]
        for _ in range(7):
            px, py = pts[-1]
            pts.append((px + random.randint(15, 45), py + random.randint(10, 35)))
        d.line(pts, fill=(60, 60, 64), width=4)
        d.line([(p[0] + 3, p[1] + 2) for p in pts[2:5]], fill=(80, 80, 84), width=2)
    return img


def build_demo_sets():
    """[(포인트 사양, 기준 PNG, [(일전, 촬영 PNG), ...]), ...]  — 마지막 회차가 이상."""
    sets = []
    # 1) 볼트 풀림: 합마크 0° 기준, 정상(1° 오차) → 이상(16° 회전)
    sets.append((
        {"name": "새들 고정 볼트 M20 #3 (합마크)", "type": "BOLT", "period": 7,
         "note": "촬영 지그 J-01, 정면 30cm, 조명 일정. 합마크 라인 전체가 프레임에 들어오게.",
         "params": {"rotation_limit_deg": 8}},
        _png(_bolt(20)),
        [(14, _png(_noise(_bolt(21), shift=(2, 1)))),
         (7, _png(_noise(_bolt(20.5), shift=(1, -2)))),
         (0, _png(_noise(_bolt(36), shift=(2, 2))))],   # 16° 회전 → NG
    ))
    # 2) 와이어 소선: 돌출 0 기준 → 이상(돌출 3개소)
    sets.append((
        {"name": "권상 와이어로프 드럼측 1m 구간", "type": "WIRE", "period": 7,
         "note": "로프 길이방향 정면, 배경판(밝은 회색) 사용.",
         "params": {"sensitivity": 3.0}},
        _png(_wire(0)),
        [(14, _png(_noise(_wire(0), shift=(1, 1)))),
         (7, _png(_noise(_wire(1), shift=(-1, 1)))),
         (0, _png(_noise(_wire(3), shift=(1, -1))))],   # 돌출 3개소 → NG
    ))
    # 3) 레일 단차: 0px 기준 → 이상(8px ≈ 0.8mm)
    sets.append((
        {"name": "주행레일 조인트 J-12", "type": "RAIL", "period": 14,
         "note": "조인트 중심, 레일 헤드 상면 에지가 수평으로 보이게.",
         "params": {"mm_per_px": 0.1, "step_limit_mm": 0.5}},
        _png(_rail(0)),
        [(28, _png(_noise(_rail(0), shift=(1, 0)))),
         (14, _png(_noise(_rail(2), shift=(0, 1)))),
         (0, _png(_noise(_rail(8), shift=(1, 1))))],    # 0.8mm 단차 → NG
    ))
    # 4) 표면 파손: 크랙 없음 기준 → 이상(크랙 발생)
    sets.append((
        {"name": "마스트 연결 플레이트 (용접부)", "type": "SURFACE", "period": 30,
         "note": "플레이트 전면, 4볼트가 모두 프레임에 들어오게.", "params": {}},
        _png(_surface(False)),
        [(30, _png(_noise(_surface(False), shift=(1, 1)))),
         (0, _png(_noise(_surface(True), shift=(2, 1))))],  # 크랙 → NG
    ))
    return sets
