from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/bm", tags=["bm"])


@router.get("/reports", response_model=list[schemas.BMReportOut])
def list_reports(status: str | None = None, equipment_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.BMReport)
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
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(r, k, v)
    # 고장 파츠 사용 시 재고 차감
    if body.failure_part_id and body.status in ("FIXED", "CLOSED"):
        part = db.get(models.Part, body.failure_part_id)
        if part and part.current_stock > 0:
            part.current_stock -= 1
            db.add(models.PartTransaction(part_id=part.id, tx_type="OUT", qty=1,
                                          ref_type="BM", ref_id=r.id))
    if body.status in ("FIXED", "CLOSED"):
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
