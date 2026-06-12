"""설비 전체 라이프사이클 기본 구성 (투자 → 제작 → 셋업 → 양산 → 폐기/이설).

시스템에서 추가·이름변경·수정·순서변경이 가능한 시작점(기본값)이다.
실행: python -m app.lifecycle_seed
"""
from .database import Base, SessionLocal, engine
from .models import LifecyclePhase, LifecycleProcess

DEFAULTS: list[dict] = [
    {
        "code": "INVEST", "name": "투자", "seq": 1,
        "description": "투자 기획부터 업체 선정까지 — 견적 자동분석·ERRC 로 원가 최적화",
        "processes": [
            {"code": "BASIC_APPROVAL", "name": "기본품의", "module_key": "",
             "description": "투자 목적·CAPA·예산 개략 품의. 유사 설비 운영 실적(DR 데이터팩)을 근거자료로 첨부."},
            {"code": "SPEC_WRITE", "name": "사양서 작성", "module_key": "knowledge",
             "description": "요구 사양(가반하중·속도·듀티·안전 표준) 작성 — 지식 DB 의 표준·L&L 미반영 항목 반영."},
            {"code": "RFQ", "name": "견적 입수", "module_key": "quotation",
             "description": "업체별 견적 접수 → 견적서 자동분석(원가구조·이상단가·계산오류·중복 검출)."},
            {"code": "ERRC", "name": "ERRC 검토", "module_key": "quotation",
             "description": "견적 항목별 Eliminate/Raise/Reduce/Create 태깅으로 사양 최적화·절감액 산출."},
            {"code": "NEGO", "name": "구매 Nego", "module_key": "quotation",
             "description": "업체간 비교분석(공통 항목 단가차·카테고리별 차이) 데이터 기반 협상."},
            {"code": "VENDOR_SELECT", "name": "업체 선정", "module_key": "quotation",
             "description": "최종 업체 선정(견적 상태 SELECTED 처리), 계약 조건·일정 확정."},
        ],
    },
    {
        "code": "FABRICATION", "name": "제작", "seq": 2,
        "description": "설계 검토부터 출하까지",
        "processes": [
            {"code": "DR", "name": "Design Review", "module_key": "workflow:DR",
             "description": "DR 워크플로우(8단계) — DR 데이터팩·안전율 계산서·유지보수성 검토."},
            {"code": "MACHINING", "name": "가공", "module_key": "",
             "description": "주요 가공품 검사 성적서(치수·경도), 장납기 품목 일정 추적."},
            {"code": "ASSEMBLY", "name": "조립", "module_key": "",
             "description": "조립 공정 체크시트, 중간 검사(정렬·토크), 사진 기록."},
            {"code": "ELEC_WIRING", "name": "전장", "module_key": "",
             "description": "판넬 제작·배선 검사, 절연·내전압 시험 성적서."},
            {"code": "CONTROL_SW", "name": "제어", "module_key": "workflow:CONTROL_CHANGE",
             "description": "PLC/모션 SW 버전 관리, 시뮬레이션 검증, 인터락 매트릭스 확인."},
            {"code": "FAT", "name": "FAT (공장 입회시험)", "module_key": "",
             "description": "성능(속도·정밀도·사이클타임)·안전 항목 입회 시험, 지적사항 클로즈 후 출하 승인."},
            {"code": "FOB", "name": "FOB (출하)", "module_key": "",
             "description": "포장·운송 사양, 출하 서류(성적서·매뉴얼·예비품 리스트) 확인."},
        ],
    },
    {
        "code": "SETUP", "name": "셋업", "seq": 3,
        "description": "반입·설치·안정화 — 알람/파라미터/이슈/안전 통합 관리",
        "processes": [
            {"code": "INSTALL", "name": "반입/설치", "module_key": "workflow:SETUP_STAB",
             "description": "셋업 안정화 워크플로우(7단계)와 연계 — 설치 정밀도 측정(비전 ALIGNMENT 활용)."},
            {"code": "INSTALL_PARAM", "name": "Install Parameter", "module_key": "params",
             "description": "파라미터 확정·버전 등록. 이후 변경은 제어 변경 워크플로우로만."},
            {"code": "ALARM_MGMT", "name": "알람 관리", "module_key": "workflow:ALARM_ACTION",
             "description": "초기 알람 다발 구간 — 알람 조치 워크플로우로 분류·임계 보정, FDC 베이스라인 수집."},
            {"code": "ISSUE_EQUIP", "name": "설비 이슈 (기구/전장/제어/인터락)", "module_key": "issues",
             "description": "도메인별 이슈 등록·추적. 미결 HIGH 이슈는 안정화 판정 보류."},
            {"code": "ISSUE_SYSTEM", "name": "시스템 이슈 (CIM/MCS/RTD)", "module_key": "issues",
             "description": "상위 시스템 연동 이슈 — 재현조건·로그 기반, 시스템 이슈 워크플로우 연계."},
            {"code": "SAFETY_CHECK", "name": "안전 점검", "module_key": "issues",
             "description": "비상정지·인터락·인적감지(ISO 3691-4) 작동 시험, 안전 이슈는 severity HIGH 고정."},
            {"code": "STABILIZE", "name": "안정화 판정", "module_key": "workflow:SETUP_STAB",
             "description": "무고장 기준(예: 2주 MTBF)·미결 이슈 0건 충족 시 양산 이관, 설비 상태 RUN 전환."},
        ],
    },
    {
        "code": "PRODUCTION", "name": "양산", "seq": 4,
        "description": "운영 단계 — 데이터가 차기 투자/DR 로 환류",
        "processes": [
            {"code": "PM", "name": "PM (예방정비)", "module_key": "pm",
             "description": "표준 점검항목·주기 기반 오더, 측정값 자동판정."},
            {"code": "BM", "name": "BM (사후정비)", "module_key": "bm",
             "description": "고장 보고→5Why→재발방지, 파츠 재고 자동 연동."},
            {"code": "AUTO_SCAN", "name": "자동 스캐닝 (비전)", "module_key": "vision",
             "description": "마모·부식·치수·정렬 자동 측정, PM 판정 연계. 고정 카메라 무인화 로드맵."},
            {"code": "FDC", "name": "FDC", "module_key": "fdc",
             "description": "센서 트렌드 실시간 감시, 레벨/스파이크/드리프트 감지 → CBM."},
            {"code": "SPARE_PARTS", "name": "스페어파츠", "module_key": "parts",
             "description": "MTBF 기반 권장재고, BM 연동 자동 차감."},
            {"code": "LESSON", "name": "Lesson & Learn", "module_key": "lessons",
             "description": "전 법인 전파·PM 표준 반영 — 차기 DR 데이터팩의 핵심 입력."},
        ],
    },
    {
        "code": "DISPOSAL", "name": "폐기/이설 (제안)", "seq": 5,
        "description": "놓치기 쉬운 마지막 단계 — 오버홀 연장 vs 교체 의사결정 포함",
        "processes": [
            {"code": "OVERHAUL_REVIEW", "name": "오버홀/수명연장 검토", "module_key": "engineering",
             "description": "FEM 9.755 SWP 소진율·잔존수명 계산으로 오버홀 vs 신규 투자 경제성 비교."},
            {"code": "RELOCATE", "name": "이설", "module_key": "workflow:SETUP_STAB",
             "description": "타법인 이설 시 셋업 워크플로우 재수행, 이력은 설비에 연속 유지."},
            {"code": "SCRAP_SELL", "name": "매각/폐기", "module_key": "",
             "description": "자산 처리, 잔존 파츠 회수(공용 파츠는 재고 편입), 이력 보존."},
        ],
    },
]


def seed_defaults(db) -> int:
    """기본 라이프사이클 적재 (비어있을 때만). 라우터/CLI 공용. 적재한 단계 수 반환."""
    if db.query(LifecyclePhase).first():
        return 0
    for ph in DEFAULTS:
        phase = LifecyclePhase(code=ph["code"], name=ph["name"], seq=ph["seq"],
                               description=ph["description"])
        db.add(phase)
        db.flush()
        for i, pr in enumerate(ph["processes"], start=1):
            db.add(LifecycleProcess(phase_id=phase.id, seq=i, **pr))
    db.commit()
    return len(DEFAULTS)


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        n = seed_defaults(db)
        print(f"라이프사이클 시드 완료: {n}단계" if n else "라이프사이클 이미 시드됨 — 건너뜀")
    finally:
        db.close()


if __name__ == "__main__":
    run()
