"""정기 촬영 기반 설비 상태 감시 API.

운영 흐름:
  1) POST /points                  촬영 포인트 등록 (타입·주기·판정 파라미터)
  2) POST /points/{id}/baseline    기준 이미지(골든 샘플) 업로드
  3) POST /points/{id}/shots       정기 촬영본 업로드(사진/동영상) → 자동 분석·판정
     - NG/CHECK 시 이슈 자동 생성 → 대시보드 '오늘의 조치 대상' 노출
  4) GET  /points/due              촬영 주기 도래/지연 포인트 목록
"""
import os
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services import vision_monitor as vm

router = APIRouter(prefix="/vision-monitor", tags=["vision-monitor"])

UPLOAD_DIR = os.environ.get("FA_UPLOAD_DIR", "./uploads")
VIDEO_EXTS = (".mp4", ".avi", ".mov", ".mkv", ".webm")
DOMAIN_BY_TYPE = {"BOLT": "MECH", "WIRE": "MECH", "SURFACE": "MECH", "RAIL": "MECH", "GENERIC": "MECH"}


def _save(data: bytes, ext: str = ".png") -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
    with open(path, "wb") as f:
        f.write(data)
    return path


def _url(path: str) -> str:
    return "/uploads/" + os.path.basename(path) if path else ""


def _point_status(p: models.InspectionPoint) -> dict:
    last = p.shots[-1] if p.shots else None
    next_due = (last.captured_at if last else p.created_at) + timedelta(days=p.period_days)
    overdue = datetime.utcnow() > next_due
    return {
        "last_shot_at": last.captured_at.isoformat() if last else None,
        "last_judgment": last.judgment if last else None,
        "last_score": last.score if last else None,
        "next_due": next_due.isoformat(),
        "overdue": overdue,
        "shot_count": len(p.shots),
        "has_baseline": bool(p.baseline_path),
    }


@router.get("/types")
def types():
    return [{"code": k, "label": v} for k, v in vm.TYPE_LABEL.items()]


@router.get("/points")
def list_points(equipment_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.InspectionPoint).filter(models.InspectionPoint.active.is_(True))
    if equipment_id:
        q = q.filter(models.InspectionPoint.equipment_id == equipment_id)
    out = []
    for p in q.all():
        d = schemas.InspectionPointOut.model_validate(p).model_dump()
        d["baseline_url"] = _url(p.baseline_path)
        d.update(_point_status(p))
        out.append(d)
    return out


@router.get("/points/due")
def due_points(db: Session = Depends(get_db)):
    """촬영 지연 포인트 — 정기 촬영 누락 감시."""
    out = []
    for p in db.query(models.InspectionPoint).filter(models.InspectionPoint.active.is_(True)).all():
        st = _point_status(p)
        if st["overdue"]:
            out.append({"id": p.id, "name": p.name, "equipment": p.equipment.asset_code,
                        "target_type": p.target_type, **st})
    return out


@router.post("/points", response_model=schemas.InspectionPointOut)
def create_point(body: schemas.InspectionPointIn, db: Session = Depends(get_db)):
    if body.target_type.upper() not in vm.TYPE_LABEL:
        raise HTTPException(400, f"target_type 은 {list(vm.TYPE_LABEL)} 중 하나여야 합니다")
    p = models.InspectionPoint(**body.model_dump())
    p.target_type = p.target_type.upper()
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.post("/points/{point_id}/baseline")
async def upload_baseline(point_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """기준 이미지(골든 샘플) 등록 — 정상 상태에서 촬영 표준 구도로 찍은 사진."""
    p = db.get(models.InspectionPoint, point_id)
    if not p:
        raise HTTPException(404, "point not found")
    data = await file.read()
    try:
        vm.load_gray(data)
    except Exception:
        raise HTTPException(400, "이미지 해석 실패 — JPG/PNG 확인")
    p.baseline_path = _save(data, os.path.splitext(file.filename or "b.png")[1] or ".png")
    db.commit()
    return {"point_id": p.id, "baseline_url": _url(p.baseline_path)}


@router.post("/points/{point_id}/shots", response_model=schemas.InspectionShotOut)
async def upload_shot(
    point_id: int,
    file: UploadFile = File(...),
    captured_at: str | None = Form(None),
    db: Session = Depends(get_db),
):
    """정기 촬영본 업로드 → 기준 대비 자동 분석.

    동영상(mp4 등)은 프레임을 균등 추출해 각각 분석하고 최악(점수 최대) 프레임으로 판정한다.
    NG/CHECK 판정 시 이슈가 자동 생성되어 대시보드 조치 대상에 표출된다.
    """
    p = db.get(models.InspectionPoint, point_id)
    if not p:
        raise HTTPException(404, "point not found")
    if not p.baseline_path or not os.path.exists(p.baseline_path):
        raise HTTPException(400, "기준 이미지를 먼저 등록하세요 (POST /baseline)")
    baseline = open(p.baseline_path, "rb").read()
    data = await file.read()
    ext = os.path.splitext(file.filename or "")[1].lower()

    source = "IMAGE"
    if ext in VIDEO_EXTS:
        source = "VIDEO"
        try:
            frames = vm.extract_video_frames(data)
        except RuntimeError as e:
            raise HTTPException(400, str(e))
        if not frames:
            raise HTTPException(400, "동영상에서 프레임을 추출하지 못했습니다")
        results = [vm.analyze_shot(baseline, f, p.target_type, p.params) for f in frames]
        worst_i = max(range(len(results)), key=lambda i: results[i]["score"])
        result = results[worst_i]
        result["detail"]["video_frames_analyzed"] = len(frames)
        result["detail"]["worst_frame_index"] = worst_i
        shot_bytes = frames[worst_i]
    else:
        try:
            result = vm.analyze_shot(baseline, data, p.target_type, p.params)
        except Exception:
            raise HTTPException(400, "이미지 해석 실패 — JPG/PNG/MP4 확인")
        shot_bytes = data

    # 추세 기반 보강: 점수가 이력 평균+3σ 초과면 최소 CHECK
    history = [s.score for s in p.shots]
    if len(history) >= 5 and result["judgment"] == "OK":
        mean = sum(history) / len(history)
        std = (sum((x - mean) ** 2 for x in history) / len(history)) ** 0.5
        if result["score"] > mean + 3 * max(std, 1.0):
            result["judgment"] = "CHECK"
            result["findings"].append(
                f"이상점수 {result['score']} — 이력 평균 {mean:.1f}+3σ 초과 (추세 이상)")

    shot = models.InspectionShot(
        point_id=p.id, source=source,
        captured_at=datetime.fromisoformat(captured_at) if captured_at else datetime.utcnow(),
        image_path=_save(shot_bytes), overlay_path=_save(result["overlay_png"]),
        score=result["score"], judgment=result["judgment"],
        findings=result["findings"], detail=result["detail"],
    )
    db.add(shot)
    db.flush()

    if result["judgment"] in ("NG", "CHECK"):
        issue = models.Issue(
            equipment_id=p.equipment_id, phase="PRODUCTION",
            domain=DOMAIN_BY_TYPE.get(p.target_type, "MECH"),
            severity="HIGH" if result["judgment"] == "NG" else "MID",
            title=f"[비전감시 {result['judgment']}] {p.name} — "
                  f"{result['findings'][0] if result['findings'] else '변화 감지'}",
            description=f"촬영 포인트 #{p.id} ({vm.TYPE_LABEL.get(p.target_type)}), "
                        f"이상점수 {result['score']}, 회차 #{shot.id}",
            owner="", status="OPEN",
        )
        db.add(issue)
        db.flush()
        shot.issue_id = issue.id
        db.add(models.LifecycleEvent(
            equipment_id=p.equipment_id, stage="BM" if result["judgment"] == "NG" else "PM",
            title=f"비전감시 {result['judgment']}: {p.name}",
            detail="; ".join(result["findings"]), performed_by="VISION",
        ))
    db.commit()
    db.refresh(shot)
    return shot


@router.get("/points/{point_id}/shots", response_model=list[schemas.InspectionShotOut])
def list_shots(point_id: int, db: Session = Depends(get_db)):
    return (db.query(models.InspectionShot)
            .filter(models.InspectionShot.point_id == point_id)
            .order_by(models.InspectionShot.captured_at).all())


@router.delete("/points/{point_id}")
def deactivate_point(point_id: int, db: Session = Depends(get_db)):
    p = db.get(models.InspectionPoint, point_id)
    if not p:
        raise HTTPException(404, "point not found")
    p.active = False
    db.commit()
    return {"ok": True}


# ───────────────────────── 데모 ─────────────────────────

@router.post("/seed-demo")
def seed_demo(db: Session = Depends(get_db)):
    """합성 이미지로 4종 포인트(볼트/와이어/레일/표면) + 정상/이상 촬영 회차 생성."""
    if db.query(models.InspectionPoint).first():
        return {"seeded": 0, "message": "이미 포인트가 있습니다"}
    from ..services.vision_demo import build_demo_sets
    eqs = db.query(models.Equipment).limit(4).all()
    if not eqs:
        raise HTTPException(400, "설비가 없습니다 — 먼저 시드를 실행하세요")
    created = 0
    for spec, baseline_png, shots in build_demo_sets():
        eq = eqs[created % len(eqs)]
        p = models.InspectionPoint(
            equipment_id=eq.id, name=spec["name"], target_type=spec["type"],
            location_note=spec["note"], period_days=spec["period"], params=spec.get("params"),
            created_at=datetime.utcnow() - timedelta(days=30),
        )
        p.baseline_path = _save(baseline_png)
        db.add(p)
        db.flush()
        for days_ago, shot_png in shots:
            result = vm.analyze_shot(baseline_png, shot_png, p.target_type, p.params)
            shot = models.InspectionShot(
                point_id=p.id, captured_at=datetime.utcnow() - timedelta(days=days_ago),
                image_path=_save(shot_png), overlay_path=_save(result["overlay_png"]),
                score=result["score"], judgment=result["judgment"],
                findings=result["findings"], detail=result["detail"],
            )
            db.add(shot)
            db.flush()
            if result["judgment"] in ("NG", "CHECK") and days_ago <= 1:
                issue = models.Issue(
                    equipment_id=p.equipment_id, phase="PRODUCTION", domain="MECH",
                    severity="HIGH" if result["judgment"] == "NG" else "MID",
                    title=f"[비전감시 {result['judgment']}] {p.name} — "
                          f"{result['findings'][0] if result['findings'] else '변화 감지'}",
                    description=f"이상점수 {result['score']}", status="OPEN")
                db.add(issue)
                db.flush()
                shot.issue_id = issue.id
        created += 1
    db.commit()
    return {"seeded": created}
