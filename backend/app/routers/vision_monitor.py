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
def list_points(equipment_id: int | None = None, site_id: int | None = None,
                db: Session = Depends(get_db)):
    q = db.query(models.InspectionPoint).filter(models.InspectionPoint.active.is_(True))
    if site_id:
        q = q.join(models.Equipment).filter(models.Equipment.site_id == site_id)
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


# ───────────────────────── 순회(패트롤) 동영상 ─────────────────────────

def _persist_patrol(db: Session, report: dict, points_by_id: dict,
                    site_id: int | None, file_name: str, performed_by: str) -> models.PatrolRun:
    """순회 분석 결과를 회차·이슈로 적재."""
    run = models.PatrolRun(
        site_id=site_id, file_name=file_name, performed_by=performed_by,
        frames_total=report["frames_total"], frames_unmatched=report["frames_unmatched"],
        points_covered=len(report["results"]),
        ng_count=sum(1 for r in report["results"] if r["analysis"]["judgment"] == "NG"),
        check_count=sum(1 for r in report["results"] if r["analysis"]["judgment"] == "CHECK"),
        missed_points=report["missed_points"],
    )
    db.add(run)
    db.flush()
    for r in report["results"]:
        p = points_by_id[r["point_id"]]
        a = r["analysis"]
        shot = models.InspectionShot(
            point_id=p.id, patrol_run_id=run.id, source="VIDEO",
            image_path=_save(r["shot_bytes"]), overlay_path=_save(a["overlay_png"]),
            score=a["score"], judgment=a["judgment"], findings=a["findings"],
            detail={**a["detail"], "match_confidence": r["match_confidence"],
                    "frame_index": r["frame_index"]},
        )
        db.add(shot)
        db.flush()
        if a["judgment"] in ("NG", "CHECK"):
            issue = models.Issue(
                equipment_id=p.equipment_id, phase="PRODUCTION",
                domain=DOMAIN_BY_TYPE.get(p.target_type, "MECH"),
                severity="HIGH" if a["judgment"] == "NG" else "MID",
                title=f"[순회감시 {a['judgment']}] {p.name} — "
                      f"{a['findings'][0] if a['findings'] else '변화 감지'}",
                description=f"순회 #{run.id} (프레임 {r['frame_index']}, "
                            f"매칭 신뢰도 {r['match_confidence']}), 이상점수 {a['score']}",
                status="OPEN")
            db.add(issue)
            db.flush()
            shot.issue_id = issue.id
            db.add(models.LifecycleEvent(
                equipment_id=p.equipment_id,
                stage="BM" if a["judgment"] == "NG" else "PM",
                title=f"순회감시 {a['judgment']}: {p.name}",
                detail="; ".join(a["findings"]), performed_by="PATROL"))
    db.commit()
    db.refresh(run)
    return run


@router.post("/patrol")
async def patrol(
    file: UploadFile = File(...),
    site_id: int | None = Form(None),
    performed_by: str = Form(""),
    db: Session = Depends(get_db),
):
    """순회 동영상 분석 — 영상 하나로 여러 포인트를 자동 매칭·판정.

    이동하며 촬영한 영상의 프레임을 등록 포인트의 기준 이미지와 자동 매칭하고
    (정합 NCC ≥ 0.55), 포인트별 최적 프레임으로 이상 분석을 수행한다.
    커버되지 않은 포인트는 '미촬영'으로 리포트한다.
    """
    q = db.query(models.InspectionPoint).filter(
        models.InspectionPoint.active.is_(True),
        models.InspectionPoint.baseline_path != "")
    if site_id:
        q = q.join(models.Equipment).filter(models.Equipment.site_id == site_id)
    pts = q.all()
    if not pts:
        raise HTTPException(400, "기준 이미지가 등록된 촬영 포인트가 없습니다")
    points_payload = []
    points_by_id = {}
    for p in pts:
        if not os.path.exists(p.baseline_path):
            continue
        points_payload.append({"id": p.id, "name": p.name, "target_type": p.target_type,
                               "params": p.params,
                               "baseline": open(p.baseline_path, "rb").read()})
        points_by_id[p.id] = p
    data = await file.read()
    try:
        report = vm.analyze_patrol(data, points_payload)
    except (RuntimeError, ValueError) as e:
        raise HTTPException(400, str(e))
    run = _persist_patrol(db, report, points_by_id, site_id,
                          file.filename or "patrol.mp4", performed_by)
    return _patrol_report(db, run)


@router.get("/patrols", response_model=list[schemas.PatrolRunOut])
def list_patrols(site_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.PatrolRun)
    if site_id:
        q = q.filter(models.PatrolRun.site_id == site_id)
    return q.order_by(models.PatrolRun.started_at.desc()).all()


def _patrol_report(db: Session, run: models.PatrolRun) -> dict:
    shots = (db.query(models.InspectionShot)
             .filter(models.InspectionShot.patrol_run_id == run.id).all())
    return {
        "run": schemas.PatrolRunOut.model_validate(run).model_dump(),
        "shots": [{
            **schemas.InspectionShotOut.model_validate(s).model_dump(),
            "point_name": s.point.name, "target_type": s.point.target_type,
            "overlay_url": _url(s.overlay_path),
        } for s in shots],
    }


@router.get("/patrols/{run_id}")
def get_patrol(run_id: int, db: Session = Depends(get_db)):
    run = db.get(models.PatrolRun, run_id)
    if not run:
        raise HTTPException(404, "patrol run not found")
    return _patrol_report(db, run)


@router.post("/patrol-demo")
def patrol_demo(db: Session = Depends(get_db)):
    """데모: 합성 순회 영상(포인트 3곳 + 이동 장면) 생성 후 분석 — 1곳은 의도적으로 미촬영."""
    pts = db.query(models.InspectionPoint).filter(models.InspectionPoint.active.is_(True)).all()
    if len(pts) < 4:
        raise HTTPException(400, "데모 포인트가 필요합니다 — 먼저 seed-demo 를 실행하세요")
    try:
        import cv2
    except ImportError:
        raise HTTPException(400, "opencv-python-headless 설치가 필요합니다")
    import numpy as np
    from PIL import Image as PImage, ImageDraw
    from ..services.vision_demo import _bolt, _wire, _rail, _noise, _png

    def walk_frame(i):
        img = PImage.new("RGB", (560, 420), (118 + i * 2, 122, 128))
        d = ImageDraw.Draw(img)
        for k in range(9):
            d.rectangle([k * 60 + i * 7, 0, k * 60 + 24 + i * 7, 420], fill=(95, 99, 105))
        return img

    # 순회 시나리오: 이동 → 볼트(이상) → 이동 → 와이어(정상) → 이동 → 레일(이상) → 이동
    seq = [walk_frame(0), walk_frame(1),
           _noise(_bolt(36), shift=(3, 2)), _noise(_bolt(36), shift=(2, 3)),
           walk_frame(2), walk_frame(3),
           _noise(_wire(0), shift=(1, -2)), _noise(_wire(0), shift=(-1, 1)),
           walk_frame(4),
           _noise(_rail(8), shift=(2, 1)), _noise(_rail(8), shift=(1, 2)),
           walk_frame(5)]
    out_path = "/tmp/patrol_demo.mp4"
    vw = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), 2, (560, 420))
    for f in seq:
        vw.write(cv2.cvtColor(np.asarray(f), cv2.COLOR_RGB2BGR))
    vw.release()

    points_payload, points_by_id = [], {}
    for p in pts:
        if p.baseline_path and os.path.exists(p.baseline_path):
            points_payload.append({"id": p.id, "name": p.name, "target_type": p.target_type,
                                   "params": p.params,
                                   "baseline": open(p.baseline_path, "rb").read()})
            points_by_id[p.id] = p
    report = vm.analyze_patrol(open(out_path, "rb").read(), points_payload, max_frames=24)
    run = _persist_patrol(db, report, points_by_id, None, "patrol_demo.mp4", "데모")
    return _patrol_report(db, run)


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
