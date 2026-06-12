from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services import quotation as qsvc

router = APIRouter(prefix="/quotations", tags=["quotations"])


def _quote_payload(q: models.Quotation) -> dict:
    return {"vendor": q.vendor, "total": q.total_amount,
            "items": [{"name": i.name, "category": i.category, "qty": i.qty,
                       "unit_price": i.unit_price, "amount": i.amount} for i in q.items]}


@router.get("", response_model=list[schemas.QuotationOut])
def list_quotations(project: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Quotation)
    if project:
        q = q.filter(models.Quotation.project == project)
    return q.order_by(models.Quotation.created_at.desc()).all()


@router.get("/projects")
def projects(db: Session = Depends(get_db)):
    rows = db.query(models.Quotation.project).distinct().all()
    return [r[0] for r in rows]


@router.post("/upload", response_model=schemas.QuotationDetailOut)
async def upload(
    file: UploadFile = File(...),
    project: str = Form(...),
    vendor: str = Form(...),
    currency: str = Form("KRW"),
    db: Session = Depends(get_db),
):
    """견적서 업로드(CSV/XLSX) → 자동 파싱·분류·적재. 컬럼(품명/수량/단가/금액) 자동 인식."""
    data = await file.read()
    try:
        items = qsvc.parse_file(data, file.filename or "quote.csv")
    except ValueError as e:
        raise HTTPException(400, str(e))
    quote = models.Quotation(
        project=project, vendor=vendor, currency=currency,
        file_name=file.filename or "", status="ANALYZED",
        total_amount=sum(i["amount"] for i in items),
    )
    db.add(quote)
    db.flush()
    for it in items:
        db.add(models.QuotationItem(quotation_id=quote.id, **it))
    db.commit()
    db.refresh(quote)
    return quote


@router.get("/compare")
def compare(project: str, db: Session = Depends(get_db)):
    quotes = db.query(models.Quotation).filter(models.Quotation.project == project).all()
    if len(quotes) < 2:
        raise HTTPException(400, "비교에는 같은 프로젝트의 견적이 2개 이상 필요합니다")
    return qsvc.compare([_quote_payload(q) for q in quotes])


@router.get("/{quote_id}", response_model=schemas.QuotationDetailOut)
def get_quotation(quote_id: int, db: Session = Depends(get_db)):
    q = db.get(models.Quotation, quote_id)
    if not q:
        raise HTTPException(404, "quotation not found")
    return q


@router.get("/{quote_id}/analysis")
def analysis(quote_id: int, db: Session = Depends(get_db)):
    """자동 데이터 분석: 원가구조·계산오류·이상단가·중복·파레토 + ERRC 절감 요약."""
    q = db.get(models.Quotation, quote_id)
    if not q:
        raise HTTPException(404, "quotation not found")
    items = [{"line_no": i.line_no, "name": i.name, "category": i.category,
              "qty": i.qty, "unit_price": i.unit_price, "amount": i.amount} for i in q.items]
    result = qsvc.analyze(items)

    # ERRC 태깅 절감 요약 (Eliminate 전액, Reduce 30% 추정)
    elim = sum(i.amount for i in q.items if i.errc == "ELIMINATE")
    reduce_ = sum(i.amount for i in q.items if i.errc == "REDUCE")
    result["errc_summary"] = {
        "eliminate_amount": elim,
        "reduce_amount": reduce_,
        "estimated_saving": round(elim + reduce_ * 0.3),
        "tagged_count": sum(1 for i in q.items if i.errc),
        "note": "절감 추정 = Eliminate 전액 + Reduce 30% (협상 목표선)",
    }
    return result


@router.patch("/items/{item_id}", response_model=schemas.QuotationItemOut)
def tag_item(item_id: int, body: schemas.QuotationItemUpdate, db: Session = Depends(get_db)):
    it = db.get(models.QuotationItem, item_id)
    if not it:
        raise HTTPException(404, "item not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(it, k, v)
    db.commit()
    db.refresh(it)
    return it


@router.patch("/{quote_id}/status")
def set_status(quote_id: int, status: str, db: Session = Depends(get_db)):
    q = db.get(models.Quotation, quote_id)
    if not q:
        raise HTTPException(404, "quotation not found")
    q.status = status
    if status == "SELECTED":  # 동일 프로젝트 나머지는 REJECTED
        db.query(models.Quotation).filter(
            models.Quotation.project == q.project, models.Quotation.id != q.id
        ).update({"status": "REJECTED"})
    db.commit()
    return {"id": q.id, "status": q.status}


@router.post("/seed-demo")
def seed_demo(db: Session = Depends(get_db)):
    """데모 견적 2건(업체A/B) 생성 — 분석/비교 기능 시연용."""
    if db.query(models.Quotation).filter(models.Quotation.project == "STK-3000 신규라인").first():
        return {"seeded": 0, "message": "데모 견적이 이미 있습니다"}
    demo = {
        "FA중공업": [
            ("스태커크레인 프레임/마스트 제작", "MECH", 1, 185000000, 185000000),
            ("주행 모터 7.5kW", "DRIVE", 2, 4200000, 8400000),
            ("권상 모터 15kW", "DRIVE", 1, 9800000, 9800000),
            ("감속기 (권상용)", "DRIVE", 1, 6500000, 6500000),
            ("와이어로프 Φ12 6x36", "DRIVE", 4, 480000, 1920000),
            ("서보 드라이브", "CONTROL", 3, 3800000, 11400000),
            ("PLC 시스템 (CPU+IO)", "CONTROL", 1, 14500000, 14500000),
            ("레이저 거리센서", "ELEC", 2, 2900000, 5800000),
            ("제어 판넬 제작/배선", "ELEC", 1, 28000000, 28000000),
            ("안전 라이트커튼", "ELEC", 4, 1850000, 7400000),
            ("운영 소프트웨어 라이선스", "SW", 1, 35000000, 35000000),
            ("설치/시운전 (4주)", "INSTALL", 1, 48000000, 48000000),
            ("운송/포장", "INSTALL", 1, 12000000, 12000000),
            ("예비품 패키지", "ETC", 1, 18000000, 18500000),  # 계산오류 데모
            ("교육 (운전/정비)", "INSTALL", 1, 5000000, 5000000),
        ],
        "대한물류기계": [
            ("크레인 본체 구조물 제작", "MECH", 1, 172000000, 172000000),
            ("주행 모터 7.5kW", "DRIVE", 2, 4900000, 9800000),
            ("권상 모터 15kW", "DRIVE", 1, 8900000, 8900000),
            ("감속기 (권상용)", "DRIVE", 1, 7200000, 7200000),
            ("와이어로프 Φ12 6x36", "DRIVE", 4, 520000, 2080000),
            ("서보 드라이브", "CONTROL", 3, 3500000, 10500000),
            ("PLC 시스템 (CPU+IO)", "CONTROL", 1, 16800000, 16800000),
            ("레이저 거리센서", "ELEC", 2, 3400000, 6800000),
            ("제어 판넬 제작/배선", "ELEC", 1, 24500000, 24500000),
            ("안전 라이트커튼", "ELEC", 4, 1700000, 6800000),
            ("안전 라이트커튼 (예비)", "ELEC", 2, 1700000, 3400000),  # 중복 데모
            ("운영 소프트웨어 라이선스", "SW", 1, 52000000, 52000000),  # 고가 데모
            ("설치/시운전 (5주)", "INSTALL", 1, 56000000, 56000000),
            ("운송/포장", "INSTALL", 1, 9500000, 9500000),
            ("교육 (운전/정비)", "INSTALL", 1, 4500000, 4500000),
        ],
    }
    created = 0
    for vendor, items in demo.items():
        q = models.Quotation(project="STK-3000 신규라인", vendor=vendor, status="ANALYZED",
                             total_amount=sum(x[4] for x in items), file_name="demo")
        db.add(q)
        db.flush()
        for ln, (name, cat, qty, up, amt) in enumerate(items, start=1):
            db.add(models.QuotationItem(quotation_id=q.id, line_no=ln, name=name,
                                        category=cat, qty=qty, unit_price=up, amount=amt))
        created += 1
    db.commit()
    return {"seeded": created}
