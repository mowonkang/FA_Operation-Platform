from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

CATEGORY_LABEL = {
    "COMMON": "공통 (로프·베어링·듀티·FDC)",
    "STK": "스태커크레인",
    "AGV_AMR": "AGV / AMR",
    "CNV": "컨베이어",
    "LIFT": "리프터",
    "PORT_OHT": "포트 / OHT",
    "ROBOT": "로봇",
}


@router.get("/categories")
def categories(db: Session = Depends(get_db)):
    counts = dict(
        db.query(models.KnowledgeArticle.category, func.count(models.KnowledgeArticle.id))
        .group_by(models.KnowledgeArticle.category)
        .all()
    )
    return [{"code": c, "label": l, "count": counts.get(c, 0)} for c, l in CATEGORY_LABEL.items()]


@router.get("", response_model=list[schemas.KnowledgeOut])
def list_articles(category: str | None = None, topic: str | None = None,
                  q: str | None = None, db: Session = Depends(get_db)):
    query = db.query(models.KnowledgeArticle)
    if category:
        query = query.filter(models.KnowledgeArticle.category == category)
    if topic:
        query = query.filter(models.KnowledgeArticle.topic == topic)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            models.KnowledgeArticle.title.like(like),
            models.KnowledgeArticle.summary.like(like),
            models.KnowledgeArticle.content.like(like),
            models.KnowledgeArticle.tags.like(like),
        ))
    return query.order_by(models.KnowledgeArticle.category, models.KnowledgeArticle.id).all()


@router.get("/{article_id}", response_model=schemas.KnowledgeOut)
def get_article(article_id: int, db: Session = Depends(get_db)):
    a = db.get(models.KnowledgeArticle, article_id)
    if not a:
        raise HTTPException(404, "article not found")
    return a


@router.post("", response_model=schemas.KnowledgeOut)
def create_article(body: schemas.KnowledgeIn, db: Session = Depends(get_db)):
    a = models.KnowledgeArticle(**body.model_dump())
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@router.post("/seed-defaults")
def seed_defaults(db: Session = Depends(get_db)):
    """기본 지식 DB 적재 (비어있을 때만)."""
    if db.query(models.KnowledgeArticle).first():
        return {"seeded": 0, "message": "이미 데이터가 있습니다"}
    from ..knowledge_seed import ARTICLES
    for a in ARTICLES:
        db.add(models.KnowledgeArticle(**a))
    db.commit()
    return {"seeded": len(ARTICLES)}
