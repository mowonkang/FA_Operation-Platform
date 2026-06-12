import json
import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services import vision as vision_svc

router = APIRouter(prefix="/vision", tags=["vision"])

UPLOAD_DIR = os.environ.get("FA_UPLOAD_DIR", "./uploads")


@router.post("/inspect", response_model=schemas.VisionInspectionOut)
async def inspect(
    file: UploadFile = File(...),
    kind: str = Form(...),
    equipment_id: int | None = Form(None),
    standard_item_id: int | None = Form(None),
    recipe: str | None = Form(None),  # JSON 문자열, 미지정 시 표준항목의 vision_recipe 사용
    db: Session = Depends(get_db),
):
    """PM/BM 점검 이미지 업로드 → 자동 측정/판정.

    standard_item_id 지정 시 해당 PM 표준항목의 레시피·한계값으로 자동 판정한다.
    """
    data = await file.read()
    recipe_dict: dict | None = json.loads(recipe) if recipe else None
    lower = upper = None
    if standard_item_id:
        std = db.get(models.PMStandardItem, standard_item_id)
        if not std:
            raise HTTPException(404, "standard item not found")
        recipe_dict = recipe_dict or std.vision_recipe
        lower, upper = std.lower_limit, std.upper_limit

    try:
        result = vision_svc.analyze(data, kind, recipe_dict)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception:
        raise HTTPException(400, "이미지 해석 실패 — 지원 포맷(JPG/PNG) 확인")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename or "img.jpg")[1] or ".jpg"
    path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
    with open(path, "wb") as f:
        f.write(data)

    judgment = vision_svc.judge(result["measured_value"], lower, upper)
    insp = models.VisionInspection(
        equipment_id=equipment_id, kind=kind.upper(), image_path=path,
        measured_value=result["measured_value"], unit=result["unit"],
        judgment=judgment, detail=result["detail"],
    )
    db.add(insp)
    db.commit()
    db.refresh(insp)
    return insp


@router.get("/inspections", response_model=list[schemas.VisionInspectionOut])
def list_inspections(equipment_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.VisionInspection)
    if equipment_id:
        q = q.filter(models.VisionInspection.equipment_id == equipment_id)
    return q.order_by(models.VisionInspection.created_at.desc()).limit(100).all()
