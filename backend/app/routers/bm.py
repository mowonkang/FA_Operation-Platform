from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/bm", tags=["bm"])


@router.get("/reports", response_model=list[schemas.BMReportOut])
def list_reports(status: str | None = None, equipment_id: int | None = None,
                 site_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.BMReport)
    if site_id:
        q = q.join(models.Equipment).filter(models.Equipment.site_id == site_id)
    if status:
        q = q.filter(models.BMReport.status == status)
    if equipment_id:
        q = q.filter(models.BMReport.equipment_id == equipment_id)
    return q.order_by(models.BMReport.occurred_at.desc()).all()


@router.post("/reports", response_model=schemas.BMReportOut)
def create_report(body: schemas.BMReportIn, db: Session = Depends(get_db)):
    data = body.model_dump()
    if data.get("occurred_at") is None:
        data.pop("occurred_at")
    r = models.BMReport(**data)
    db.add(r)
    db.flush()
    db.add(models.LifecycleEvent(
        equipment_id=r.equipment_id, stage="BM",
        title=f"고장 발생: {r.symptom[:80]}", performed_by=r.reported_by,
        detail=f"BM 보고 #{r.id}",
    ))
    eq = db.get(models.Equipment, r.equipment_id)
    if eq and eq.status == "RUN":
        eq.status = "BM"
    db.commit()
    db.refresh(r)
    return r


@router.patch("/reports/{report_id}", response_model=schemas.BMReportOut)
def update_report(report_id: int, body: schemas.BMReportUpdate, db: Session = Depends(get_db)):
    r = db.get(models.BMReport, report_id)
    if not r:
        raise HTTPException(404, "report not found")
    was_closed = r.status in ("FIXED", "CLOSED")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(r, k, v)
    now_closed = r.status in ("FIXED", "CLOSED")
    # 종결 전이 시점에 1회만: 고장 파츠 재고 차감 + 설비 복귀 + 이력 기록 (중복 PATCH 에 안전)
    if not was_closed and now_closed:
        if r.failure_part_id:
            part = db.get(models.Part, r.failure_part_id)
            if part and part.current_stock > 0:
                part.current_stock -= 1
                db.add(models.PartTransaction(part_id=part.id, tx_type="OUT", qty=1,
                                              ref_type="BM", ref_id=r.id))
        eq = db.get(models.Equipment, r.equipment_id)
        if eq and eq.status == "BM":
            eq.status = "RUN"
        db.add(models.LifecycleEvent(
            equipment_id=r.equipment_id, stage="BM",
            title=f"수리 완료 (BM #{r.id})", detail=r.action or "",
        ))
    db.commit()
    db.refresh(r)
    return r
