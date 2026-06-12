import math

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/parts", tags=["parts"])


@router.get("", response_model=list[schemas.PartOut])
def list_parts(db: Session = Depends(get_db)):
    return db.query(models.Part).order_by(models.Part.part_no).all()


@router.post("", response_model=schemas.PartOut)
def create_part(body: schemas.PartIn, db: Session = Depends(get_db)):
    p = models.Part(**body.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("/bom", response_model=list[schemas.BomOut])
def list_bom(model_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.ModelPartBom)
    if model_id:
        q = q.filter(models.ModelPartBom.model_id == model_id)
    return q.all()


@router.post("/bom", response_model=schemas.BomOut)
def create_bom(body: schemas.BomIn, db: Session = Depends(get_db)):
    b = models.ModelPartBom(**body.model_dump())
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


@router.post("/transactions")
def add_transaction(body: schemas.PartTxIn, db: Session = Depends(get_db)):
    part = db.get(models.Part, body.part_id)
    if not part:
        raise HTTPException(404, "part not found")
    if body.tx_type == "IN":
        part.current_stock += body.qty
    elif body.tx_type == "OUT":
        if part.current_stock < body.qty:
            raise HTTPException(400, f"재고 부족 (현재 {part.current_stock})")
        part.current_stock -= body.qty
    else:
        raise HTTPException(400, "tx_type must be IN or OUT")
    db.add(models.PartTransaction(**body.model_dump()))
    db.commit()
    return {"part_id": part.id, "current_stock": part.current_stock}


@router.get("/recommendation")
def stock_recommendation(service_level_z: float = 1.65, db: Session = Depends(get_db)):
    """파츠 선정/권장재고 기초자료.

    연간 소요 = Σ(설비대수 × BOM수량 × 연간가동시간 / MTBF)
              (MTBF 없으면 교체주기 기반: 대수 × 수량 × 12/교체주기개월)
    권장재고 = 리드타임 소요 + z×√(리드타임 소요)  (포아송 가정 안전재고)
    """
    out = []
    for part in db.query(models.Part).all():
        boms = db.query(models.ModelPartBom).filter(models.ModelPartBom.part_id == part.id).all()
        annual_demand = 0.0
        used_on = []
        for bom in boms:
            eqs = (
                db.query(models.Equipment)
                .filter(models.Equipment.model_id == bom.model_id,
                        models.Equipment.status.notin_(["SCRAP"]))
                .all()
            )
            n = len(eqs)
            if n == 0:
                continue
            run_hours = sum(e.annual_run_hours for e in eqs)
            if part.mtbf_hours:
                annual_demand += bom.qty_per_unit * run_hours / part.mtbf_hours
            elif bom.replace_cycle_months:
                annual_demand += n * bom.qty_per_unit * 12.0 / bom.replace_cycle_months
            used_on.append({"model": bom.model.code, "equipment_count": n,
                            "qty_per_unit": bom.qty_per_unit, "critical": bom.critical})
        lead_demand = annual_demand * part.lead_time_days / 365.0
        recommended = math.ceil(lead_demand + service_level_z * math.sqrt(lead_demand)) if annual_demand > 0 else part.min_stock
        out.append({
            "part_id": part.id,
            "part_no": part.part_no,
            "name": part.name,
            "annual_demand": round(annual_demand, 2),
            "lead_time_days": part.lead_time_days,
            "recommended_stock": recommended,
            "current_stock": part.current_stock,
            "shortage": max(recommended - part.current_stock, 0),
            "mtbf_hours": part.mtbf_hours,
            "unit_price": part.unit_price,
            "used_on": used_on,
        })
    out.sort(key=lambda x: x["shortage"], reverse=True)
    return out
