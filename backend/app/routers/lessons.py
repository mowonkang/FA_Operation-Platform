from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/lessons", tags=["lessons"])


def create_lesson_with_deployments(db: Session, **fields) -> models.Lesson:
    """L&L 생성 + 발생 법인 외 전 법인 자동 전파(NOTIFIED). 모든 생성 경로의 공용 헬퍼."""
    lesson = models.Lesson(**fields)
    db.add(lesson)
    db.flush()
    for site in db.query(models.Site).filter(models.Site.id != lesson.origin_site_id).all():
        db.add(models.LessonDeployment(lesson_id=lesson.id, site_id=site.id))
    return lesson


@router.get("", response_model=list[schemas.LessonOut])
def list_lessons(db: Session = Depends(get_db)):
    return db.query(models.Lesson).order_by(models.Lesson.created_at.desc()).all()


@router.post("", response_model=schemas.LessonOut)
def create_lesson(body: schemas.LessonIn, db: Session = Depends(get_db)):
    lesson = create_lesson_with_deployments(db, **body.model_dump())
    db.commit()
    db.refresh(lesson)
    return lesson


@router.get("/{lesson_id}", response_model=schemas.LessonOut)
def get_lesson(lesson_id: int, db: Session = Depends(get_db)):
    lesson = db.get(models.Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "lesson not found")
    return lesson


@router.patch("/deployments/{dep_id}", response_model=schemas.LessonDeploymentOut)
def update_deployment(dep_id: int, body: schemas.DeploymentUpdate, db: Session = Depends(get_db)):
    dep = db.get(models.LessonDeployment, dep_id)
    if not dep:
        raise HTTPException(404, "deployment not found")
    dep.status = body.status
    dep.note = body.note
    dep.applied_date = body.applied_date or (date.today() if body.status == "APPLIED" else None)
    db.commit()
    db.refresh(dep)
    return dep


@router.post("/{lesson_id}/reflect-standard", response_model=schemas.PMStandardItemOut)
def reflect_to_standard(lesson_id: int, body: schemas.PMStandardItemIn, db: Session = Depends(get_db)):
    """L&L 을 PM 표준 점검항목으로 반영 — 전 법인 표준 확산의 핵심 경로."""
    lesson = db.get(models.Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "lesson not found")
    item = models.PMStandardItem(**body.model_dump())
    item.origin_lesson_id = lesson_id
    lesson.std_reflected = True
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
