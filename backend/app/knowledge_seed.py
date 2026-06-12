"""물류설비 엔지니어링 지식 DB 초기 데이터.

웹·표준·문헌 조사 기반 (2026-06 조사). 각 항목에 출처(sources)를 포함한다.
실행: python -m app.knowledge_seed  (이미 데이터가 있으면 건너뜀)
"""
from .database import Base, SessionLocal, engine
from .models import KnowledgeArticle

ARTICLES: list[dict] = [
    # ── COMMON: 와이어로프 ──
    dict(
        category="COMMON", topic="WIRE_ROPE",
        title="와이어로프 안전계수 법규 기준 (산업안전보건규칙 제163조)",
        summary="양중기 와이어로프 안전계수: 사람 탑승 지지 10 이상, 화물 직접 지지 5 이상, 훅·샤클 3 이상, 그 밖 4 이상.",
        content=(
            "안전계수 = 절단하중(파단하중) / 최대 사용하중.\n\n"
            "산업안전보건기준에 관한 규칙 제163조(와이어로프 등 달기구의 안전계수):\n"
            "- 근로자가 탑승하는 운반구를 지지하는 달기와이어로프·달기체인: 10 이상\n"
            "- 화물의 하중을 직접 지지하는 달기와이어로프·달기체인: 5 이상\n"
            "- 훅, 샤클, 클램프, 리프팅 빔: 3 이상\n"
            "- 그 밖의 경우: 4 이상\n\n"
            "제166조(사용금지 기준): 이음매가 있는 것, 한 꼬임(스트랜드)에서 소선 수의 10% 이상 단선,\n"
            "공칭지름 대비 7% 초과 직경 감소, 꼬인 것·심하게 변형되거나 부식된 것, 열과 전기충격에 의해 손상된 것.\n\n"
            "DR 단계에서 권상 로프 선정 시 정격하중 + 운반구 자중 + 동적계수를 포함한 최대 장력 기준으로\n"
            "안전계수를 산출하고, 본 플랫폼의 와이어로프 수명예측 툴로 D/d·체결방식 민감도를 검토할 것."
        ),
        sources=[
            {"title": "산업안전보건기준에 관한 규칙 제163조 (국가법령정보센터)", "url": "https://www.law.go.kr/법령/산업안전보건기준에관한규칙/제163조(와이어로프)"},
            {"title": "법령 본문 — 국가법령정보센터", "url": "https://law.go.kr/LSW/lsInfoP.do?lsiSeq=272927"},
        ],
        tags="와이어로프,안전계수,법규,KOSHA,권상",
    ),
    dict(
        category="COMMON", topic="WIRE_ROPE",
        title="ISO 4309 와이어로프 점검·폐기 기준",
        summary="가시 단선 수(6d/30d 구간), 직경 감소, 부식·변형의 정량 폐기 기준. 단선의 국부 집중은 분산 단선보다 위험.",
        content=(
            "ISO 4309:2017 (Cranes — Wire ropes — Care and maintenance, inspection and discard) 핵심:\n\n"
            "1) 가시 단선 수 기준: 로프 구성(RCN: Rope Category Number)과 크레인 등급(M1~M8),\n"
            "   드럼 형식(단층/다층권)에 따라 6d 또는 30d 길이 구간 내 허용 단선 수가 표로 규정됨.\n"
            "   ※ 같은 수의 단선이라도 한 곳에 몰려 있으면(클러스터) 분산된 경우보다 훨씬 위험 → 즉시 폐기 검토.\n"
            "2) 직경 감소: 공칭지름 대비 균일 마모·심 압괴에 의한 감소율 기준 (한국 법규는 7% 초과 시 사용금지).\n"
            "3) 부식, 변형(킹크·바스켓·압괴), 열 손상도 폐기 사유.\n"
            "4) 다층권 드럼은 크로스오버 구간 손상이 가속됨 → 점검 주기 강화.\n\n"
            "PM 표준화 적용: 단선 수·직경을 정기 측정(본 플랫폼 비전 DIMENSION 측정 활용 가능)하고\n"
            "측정 이력의 추세로 교체 시점을 예측한다."
        ),
        sources=[
            {"title": "ISO 4309:2017", "url": "https://www.iso.org/standard/66759.html"},
            {"title": "verope — Discard Criteria", "url": "https://verope.com/rope-tech/discard-criteria/"},
            {"title": "CASAR Wire Rope Guidelines (2018)", "url": "https://www.casar.de/Portals/0/Guidelines_32112022_EN_UK.pdf"},
        ],
        tags="와이어로프,폐기기준,ISO4309,점검",
    ),
    dict(
        category="COMMON", topic="WIRE_ROPE",
        title="와이어로프 굽힘피로 수명 — Feyrer 모델",
        summary="수명(굽힘 횟수)은 장력(S/d²)과 시브비(D/d)에 지배됨. 장력 증가·시브 소경화 시 수명 급감.",
        content=(
            "Feyrer(슈투트가르트대) 굽힘피로 시험 기반 수명식은 와이어로프 수명 예측의 사실상 표준이다.\n\n"
            "핵심 변수: 시브/로프 직경비(D/d), 비장력(S/d², 단위 단면적당 장력), 로프 직경(d),\n"
            "굽힘 길이(l), 소선 인장강도(R0).\n\n"
            "정성적 결론(문헌 일치):\n"
            "- 장력 S 증가 → 폐기 도달 수명 급감 (대략 S^-3 차수의 민감도)\n"
            "- D/d 증가 → 수명 급증 (소경 시브는 굽힘응력 증가로 수명 단축)\n"
            "- 회전저항 로프는 일반 로프 대비 같은 조건에서 굽힘피로 수명이 짧은 경향\n\n"
            "1 권상 사이클당 굽힘 횟수 = 로프가 통과하는 시브 수 × 2(상승+하강) + 드럼 감김.\n"
            "본 플랫폼의 와이어로프 수명예측 툴은 Feyrer 형태의 간이식(보정계수 포함)을 사용하며,\n"
            "실측 단선 추세 데이터가 축적되면 계수를 보정(RUL 업데이트)한다.\n\n"
            "참고 서적: K. Feyrer, 'Wire Ropes: Tension, Endurance, Reliability' (Springer)."
        ),
        sources=[
            {"title": "Discard fatigue life of stranded steel wire rope subjected to bending over sheave fatigue (Mechanics & Industry, 2017)", "url": "https://www.mechanics-industry.org/articles/meca/pdf/2017/02/mi160060.pdf"},
            {"title": "Discarding lifetime investigation of a rotation resistant rope (ScienceDirect)", "url": "https://www.sciencedirect.com/science/article/abs/pii/S026322411930404X"},
            {"title": "Prediction of rope bending fatigue life based on wire breaking rate (ResearchGate)", "url": "https://www.researchgate.net/publication/369161999_Prediction_of_rope_bending_fatigue_life_based_on_wire_breaking_rate"},
        ],
        tags="와이어로프,수명예측,Feyrer,굽힘피로,D/d",
    ),
    # ── COMMON: 베어링/듀티 ──
    dict(
        category="COMMON", topic="BEARING",
        title="베어링 L10 수명 (ISO 281) 설계 적용",
        summary="L10h = 10⁶/(60N) × (C/P)^p, 볼 p=3·롤러 p=10/3. 90% 신뢰도 기준이므로 상태감시 병행 필수.",
        content=(
            "기본 정격수명 L10 은 동일 조건 베어링 군의 90% 가 피로 박리 없이 도달하는 회전수.\n"
            "L10h[시간] = 10⁶/(60·N[rpm]) × (C/P)^p  (볼베어링 p=3, 롤러베어링 p=10/3)\n\n"
            "설계 체크포인트:\n"
            "- P(등가 동하중)는 레디얼+액시얼 합성으로 산출, 충격계수 반영\n"
            "- 윤활 불량·오염·고온은 수명계수(aISO)로 추가 감소 — 그리스 주입주기 관리가 실수명을 지배\n"
            "- L10 은 통계 수명: 10% 는 그 전에 고장 → FDC 진동·온도 감시 병행으로 조기 검출\n\n"
            "정비 적용: 진동 속도(mm/s RMS, ISO 10816 존 기준)와 온도 트렌드의 DRIFT 가\n"
            "박리 진행의 선행 지표. 본 플랫폼 FDC 의 DRIFT 분류와 연계할 것."
        ),
        sources=[
            {"title": "ISO 281 (Rolling bearings — Dynamic load ratings and rating life)", "ref": "ISO 281:2007"},
            {"title": "CEMA — Conveyor Idlers Rating and Bearing Life", "url": "https://www.ckit.co.za/secure/tech-focus/idlers/idlers.htm"},
        ],
        tags="베어링,L10,ISO281,수명",
    ),
    dict(
        category="COMMON", topic="DUTY_CLASS",
        title="권상장치 듀티 등급 (ISO 4301 M1~M8, FEM) 과 SWP",
        summary="FEM 9.755: 호이스트 설계수명 10년(연 250일) 기준의 SWP(안전사용기간) 관리. 듀티 초과 사용은 수명 단축.",
        content=(
            "ISO 4301 은 기구(메커니즘)를 가동시간 등급과 하중 스펙트럼으로 M1~M8 로 분류한다.\n"
            "FEM 등급(1Dm~5m)과 상호 대응 (1Dm=M1, 1Cm=M2, 1Bm=M3 ...).\n\n"
            "FEM 9.755 (Safe Working Period): 전동 호이스트의 안전사용기간 개념 —\n"
            "설계 수명 10년(연 250일 가동 기준)을 하중스펙트럼·가동시간 실적으로 소비량을 계산해 관리.\n"
            "SWP 소진 시 제너럴 오버홀(GO) 수행 후 연장.\n\n"
            "운영 적용:\n"
            "- DR 단계에서 실제 듀티(사이클/일, 평균하중비)로 등급 선정의 적정성 검증\n"
            "- 운영 단계에서 실적 가동 데이터(FDC)로 SWP 소비율을 추적 → 오버홀 시점 예측\n"
            "- 설계 듀티보다 높게 운영 중이면 PM 주기 단축 필요"
        ),
        sources=[
            {"title": "Hoist UK — FEM Hoist Duty Classifications Explained", "url": "https://www.hoistuk.com/fem-hoist-duty-classifications-explained/"},
            {"title": "ISO 4301-1:2016 (Cranes — Classification)", "url": "https://www.dgcrane.com/wp-content/uploads/2023/09/ISO-04301-1-2016.pdf"},
            {"title": "Verlinde — Hoist Classification EN 14492 / ISO 4301", "url": "https://www.verlinde.com/wp-content/uploads/2023/02/EN-14492-ISO-4301-GB-F.pdf"},
        ],
        tags="듀티,M등급,FEM9.755,SWP,ISO4301",
    ),
    # ── STK ──
    dict(
        category="STK", topic="WHEEL",
        title="스태커크레인 주행휠·레일 — 경도와 마모 관리 (DIN 15070)",
        summary="휠 최소 경도 300HB(고내마모 350~400HB). 답면 폭은 레일 헤드보다 20~30mm 넓게. 구동휠 직경차 관리 필수.",
        content=(
            "DIN 15070 (크레인 휠 치수 표준) 기반 설계·정비 포인트:\n\n"
            "- 휠 경도: 최소 300HB 권장, 고듀티는 350~400HB 표면경화. 경도 부족 + 과하중 → 피팅·치핑 가속\n"
            "- 답면 폭: 레일 헤드폭 + 20~30mm (편심 주행 여유)\n"
            "- 플랜지 높이: 통상 휠 직경의 20~30%\n"
            "- 구동휠 직경 매칭: CMAA 기준 직경차 허용 0.001in/in(최대 0.01in) — 직경차 과대 시\n"
            "  속도차에 의한 사행(skew)·플랜지 편마모·레일 헤드 변형 유발\n"
            "- 레일 신축에 의한 횡추력이 양쪽 플랜지 동시 접촉을 만들면 플랜지 마모 급가속\n\n"
            "PM 표준화: 답면 직경(비전 DIMENSION), 플랜지 두께, 편마모 여부를 정기 측정하고\n"
            "좌우 구동휠 직경차를 관리치로 운영. 마모율 실측 → 휠 안전연수 계산기로 잔여수명 산출."
        ),
        sources=[
            {"title": "Extending Crane Wheel and Rail Life (LinkedIn 전문 기고)", "url": "https://www.linkedin.com/pulse/extending-crane-wheel-rail-life-aleksandar-miljevic"},
            {"title": "Crane Wheels: Selection, Maintenance, Replacement (Yuantai)", "url": "https://www.yuantaicrane.com/news/crane-wheels.html"},
            {"title": "SIBRE Crane Wheel Systems (DIN 15070/15071)", "url": "https://www.sibre.de/wp-content/uploads/2022/05/sibre-data-sheet-couplings-crane-wheel-systems.pdf"},
        ],
        tags="STK,휠,레일,DIN15070,마모",
    ),
    dict(
        category="STK", topic="WIRE_ROPE",
        title="스태커크레인 권상부 점검 표준 (와이어로프·브레이크·시브)",
        summary="로프 단선·직경, 시브 홈 마모, 브레이크 라이닝, 드럼 크로스오버 구간을 주기 점검. M등급별 단선 허용치 적용.",
        content=(
            "AS/RS 스태커크레인 권상부의 핵심 점검 항목:\n\n"
            "1) 와이어로프: ISO 4309 단선 수(6d/30d), 직경 7% 감소(법규), 다층권 드럼 크로스오버 구간 집중 점검\n"
            "2) 시브: 홈 반경 마모(로프 직경 게이지), 홈 바닥 직경 감소 → D/d 실질 감소로 로프 수명 단축\n"
            "3) 브레이크: 라이닝 두께 한계, 토크 시험(정격 1.5배 유지), 에어갭\n"
            "4) 드럼: 홈 마모, 로프 고정단(클램프) 토크\n"
            "5) 권상 모터: 절연저항(1MΩ 이상), 전류 트렌드(FDC) — 기계 저항 증가의 선행지표\n\n"
            "포크(셔틀)부: 체인 신율(2~3% 한계 — LIFT 지식 참조), 가이드롤러 마모.\n"
            "거더·마스트: 용접부 균열(연 1회 육안+필요시 MT), 수직도."
        ),
        sources=[
            {"title": "ISO 4309:2017", "url": "https://www.iso.org/standard/66759.html"},
            {"title": "FEM 9.755 (Safe Working Periods)", "ref": "FEM 9.755"},
        ],
        tags="STK,권상,PM표준,점검",
    ),
    # ── AGV / AMR ──
    dict(
        category="AGV_AMR", topic="BATTERY",
        title="AGV/AMR 리튬배터리(LiFePO4) 수명 — DOD와 사이클의 관계",
        summary="80% DOD 기준 3,000~5,000 사이클. DOD 50%로 낮추면 5,000~7,000+, 100% DOD는 2,000~3,000으로 급감.",
        content=(
            "LiFePO4(LFP) 사이클 수명 데이터 (제조사 공통 경향):\n"
            "- 100% DOD: 2,000~3,000 사이클\n"
            "- 80% DOD: 3,000~5,000 사이클 (정격 표기 기준점, EOL=용량 80%)\n"
            "- 50% DOD: 5,000~7,000 사이클\n"
            "- 10% DOD: ~14,000 사이클\n\n"
            "운영 권고:\n"
            "- 운용 SOC 윈도우 20~80%(=DOD 60% 수준) 설정이 수명·가용량 균형점\n"
            "- 기회충전(opportunity charging)으로 DOD 를 낮추면 교체주기 연장 — 단, 충전 포인트 배치 필요\n"
            "- 고온(>45°C) 운용·보관은 캘린더 열화 가속 — FDC 배터리 온도 감시 임계 45/55°C 권장\n"
            "- SOH 80% 도달을 교체 기준으로 운영, BMS SOH 를 PM 항목으로 정기 기록\n\n"
            "본 플랫폼 배터리 수명 계산기는 DOD 보정 사이클 수명과 캘린더 수명 중 짧은 쪽을 적용한다."
        ),
        sources=[
            {"title": "EcoTree Lithium — LiFePO4 Battery Cycle Life & Durability", "url": "https://ecotreelithium.co.uk/news/lifepo4-battery-cycle-life-and-durability/"},
            {"title": "Grepow — What is DOD for LiFePO4 batteries", "url": "https://www.grepow.com/blog/what-is-dod-for-lifepo4-batteries.html"},
            {"title": "Ufine — LiFePO4 Cycle Life and DoD", "url": "https://www.ufinebattery.com/blog/lifepo4-cycle-life/"},
        ],
        tags="AGV,AMR,배터리,LiFePO4,DOD,SOH",
    ),
    dict(
        category="AGV_AMR", topic="WHEEL",
        title="AGV/AMR 폴리우레탄 휠 — 경도 선정과 고장 메커니즘",
        summary="표준 90A~95A. 과하중·고속 발열(>65°C)이 수명 지배 — 트레드 변형·코어 박리(delamination)가 주 고장모드.",
        content=(
            "폴리우레탄 휠 듀로미터(경도) 선정:\n"
            "- 75A~85A(소프트): 그립·정숙성 우수, 구름저항 큼 — 슬립 민감 구간\n"
            "- 90A~95A(표준): 내마모·구름저항 균형 — 일반 창고/제조 권장\n"
            "- 95A+(하드): 구름저항 최소, 거친 바닥에서 채터링\n\n"
            "고장 메커니즘:\n"
            "- PU 는 변형 시 발열 — 과하중+고속에서 방열량 초과 → 트레드 영구변형·용융\n"
            "  (정격은 21°C 기준이며 65°C 이상 지속 시 허용하중 30~50% 저하)\n"
            "- 하중·토크 과소평가 → 코어-트레드 박리(delamination)\n"
            "- 오일류는 PU 를 팽윤시켜 마모 가속, 바닥 이물은 국부 손상\n\n"
            "수명: 평활 콘크리트·정격하중에서 통상 5~10년. 단, 듀티가 높은 AGV 구동휠은 주행거리 기준 관리 필요.\n"
            "PM 표준화: 휠 직경(비전 DIMENSION)·트레드 표면(비전 WEAR)·편마모를 주기 측정,\n"
            "구동 전류 트렌드(FDC) 상승은 휠 변형/베어링 열화의 선행지표."
        ),
        sources=[
            {"title": "Caster Concepts — Specifying Polyurethane Caster Wheels For AGV", "url": "https://www.casterconcepts.com/blog/beyond-standard-blog/caster-wheels/4-tips-to-specifying-polyurethane-caster-wheels-for-agv-applications/"},
            {"title": "AGV Wheels — Polyurethane Drive Wheel", "url": "https://www.agv-wheels.com/agv-drive-wheel"},
        ],
        tags="AGV,AMR,휠,폴리우레탄,마모",
    ),
    dict(
        category="AGV_AMR", topic="SAFETY_STD",
        title="AGV/AMR 안전 표준 — ISO 3691-4",
        summary="무인운반차 안전요구: 경로 전폭 인적감지, 접촉 검출(범퍼), 제동, 안전기능 PL 검증(ISO 13849).",
        content=(
            "ISO 3691-4:2023 (Driverless industrial trucks) 핵심 요구:\n\n"
            "- 인적감지: 차체+적재물 전폭에 대해 진행 경로상의 사람을 감지(통상 안전 LiDAR),\n"
            "  감지 불가 영역은 접촉 검출 장치(압력 범퍼)로 보완\n"
            "- 제동: 감지 거리 내 정지 가능한 제동 성능, 동력 상실 시 자동 제동\n"
            "- 운전 모드: 자동/수동/정비 모드별 안전 요구 구분\n"
            "- 안전 관련 제어부(SRP/CS)는 ISO 13849-1 성능레벨(PL) 요구, 검증은 ISO 13849-2\n\n"
            "DR 체크: 안전 LiDAR 보호필드 설계(속도 연동 필드 전환), 비상정지 회로 카테고리,\n"
            "경사·바닥 조건에서의 제동거리 검증 계획.\n"
            "PM 체크: 보호필드 작동시험, 범퍼 스위치, 비상정지, 경고등·음향 — 주기 작동시험 항목화."
        ),
        sources=[
            {"title": "ISO 3691-4:2023", "url": "https://www.iso.org/standard/83545.html"},
            {"title": "TÜV Rheinland — AGV Whitepaper (ISO 3691-4:2020)", "url": "https://www.tuv.com/content-media-files/master-content/services/industrial-services/pdf/tuv-rheinland-automatic-guided-vehicles-whitepaper-en_neu.pdf"},
            {"title": "agvnetwork — What is ISO 3691-4", "url": "https://www.agvnetwork.com/automated-guided-vehicles-technology/standard-3691-4"},
        ],
        tags="AGV,AMR,안전,ISO3691-4,LiDAR",
    ),
    # ── CNV ──
    dict(
        category="CNV", topic="BEARING",
        title="컨베이어 아이들러/롤러 수명 — CEMA L10 기준",
        summary="CEMA 등급(B/C/D/E)별 하중·속도 한계. L10 정격은 500rpm 기준 — 벨트속도 상승 시 수명 비례 단축.",
        content=(
            "CEMA(컨베이어 제조자 협회)는 아이들러 정격을 베어링 L10 수명으로 정의한다.\n"
            "- 모든 CEMA L10 정격은 500rpm 기준 → 실제 회전수가 높으면(벨트 고속·소경 롤러) 시간수명 비례 단축\n"
            "- 테이퍼 롤러: L10 = 1.5×10⁶ × y/N × (C90/P)^(10/3) 형태의 산업식 사용\n"
            "- CEMA 등급 B/C/D/E 가 듀티(하중·속도 한계)를 규정\n\n"
            "정비 포인트:\n"
            "- 롤러 회전 불량(고착)은 벨트 마모·사행·동력 증가의 원인 — 열화상/소음 점검 유효\n"
            "- 벨트: 트레드 마모(비전 WEAR), 엣지 손상, 이음부(클립/가황) 상태\n"
            "- 풀리 래깅 마모, 텐션 장치 스트로크 잔량\n"
            "- 사행(벨트 트래킹)은 구조 정렬 문제 — 비전 ALIGNMENT 측정 적용 가능"
        ),
        sources=[
            {"title": "CKIT — Conveyor Idlers: Rating and Bearing Life", "url": "https://www.ckit.co.za/secure/tech-focus/idlers/idlers.htm"},
            {"title": "CEMA Belt Book 7th Edition (errata)", "url": "https://www.cemanet.org/wp-content/uploads/2015/04/BBK-7th-Edition-Errata-Summary-Pages-as-of-Feb1-2015-SEC.pdf"},
            {"title": "Calculating Idler L10 Life", "url": "https://www.scribd.com/document/99803038/Calculating-Idler-L10-Life"},
        ],
        tags="컨베이어,아이들러,롤러,CEMA,L10,벨트",
    ),
    # ── LIFT ──
    dict(
        category="LIFT", topic="CHAIN",
        title="리프터/마스트 체인(리프 체인) 신율 관리 기준",
        summary="신율 2% 도달 시 교체 계획(3개월 내), 3% 이상은 즉시 교체. 3% 신율 체인은 강도 15% 손실 상태.",
        content=(
            "리프 체인(BL 체인) 마모 신율 관리 (포크리프트·리프터 마스트 공통):\n\n"
            "- 신율 2% 미만: 정상 사용\n"
            "- 신율 2~3%: 동적 수명 한계 도달 신호 — 즉시 교체 또는 3개월 내 교체 계획 수립\n"
            "  (영국·네덜란드 등 일부 규정은 2% 를 교체 한계로 적용 — 보수적 운영 권장)\n"
            "- 신율 3% 이상: 위험 — 즉시 교체, 교체 전 설비 사용 금지\n"
            "- 신율 3% 체인은 파단강도가 약 15% 저하된 상태\n\n"
            "측정 방법: 하중을 건 상태에서 핀 중심간 표점거리(예: 12피치)를 체인 게이지/버니어로 측정,\n"
            "신율% = (실측-공칭)/공칭×100. 마모는 풀리 통과 구간에 집중되므로 여러 구간 측정.\n\n"
            "병행 점검: 핀 회전 흔적(윤활 부족), 플레이트 균열·부식, 앵커 볼트, 체인 정렬.\n"
            "윤활: 침투성 체인 오일을 정기 도포 — 무윤활은 신율 진행 3~5배 가속."
        ),
        sources=[
            {"title": "leafchain.com — Replacement indicators", "url": "https://www.leafchain.com/knowledge-hub/how-can-i-tell-when-its-time-to-replace-my-leaf-chain"},
            {"title": "FLTA Technical Bulletin — Inspection of Leaf Chains", "url": "https://www.cdforktrucksltd.co.uk/siteDocuments/flta-lift-chain-technical-bulletin.pdf"},
            {"title": "SAFed — Leaf Chain Elongation Rejection Criteria", "url": "https://www.safed.co.uk/publications-home/tc2-machinery-lift-crane/policy-statements-for-download/41-fork-lift-truck-order-picker-leaf-chain-elongation-rejection-criteria/file"},
        ],
        tags="리프터,체인,신율,교체기준",
    ),
    # ── PORT / OHT ──
    dict(
        category="PORT_OHT", topic="VIBRATION",
        title="OHT(천장반송) 진동 관리 — 휠 진원도와 레일 상태가 수율을 좌우",
        summary="OHT는 일 평균 ~20km 주행. 휠 편심(out-of-round)·레일 이음 단차가 미세진동 원인 — 웨이퍼 수율과 직결.",
        content=(
            "반도체 FAB AMHS(OHT) 의 진동 관리 핵심:\n\n"
            "- OHT 는 FAB 내 수백 대가 일 평균 ~20km 주행 — 구동휠·가이드휠과 레일 접촉면이 주 진동원\n"
            "- 휠이 미세하게라도 진원이 깨지면(out-of-round) 캠처럼 작용해 회전마다 차체를 들었다 놓음\n"
            "  → 반송 중 FOUP 미세진동 → 공정 미세화에 따라 수율 리스크 증가\n"
            "- 과도 진동은 내부 레이저 센서(위치인식) 간섭 → 위치오차·비상정지 유발\n"
            "- 진동은 호이스트 기구 마모도 가속 → 정비비 증가\n"
            "- 레일: 이음부 단차·마모·오염이 국부 가진원 — 주행 대차 기반 레일 모니터링(가속도 측정) 연구·적용 사례 존재\n"
            "- AMHS 신뢰성 목표는 통상 99.999% 수준 — 개별 레일 구간 고장이 네트워크 전체 정체로 파급\n\n"
            "PM 표준화: 구동휠 직경·진원도(편마모) 주기 측정(비전), 레일 이음 단차 점검,\n"
            "차체 가속도(FDC 진동 센서) 트렌드의 DRIFT 감시로 휠 교체 시점 예측."
        ),
        sources=[
            {"title": "Hickwall — How OHT Precision Affects Semiconductor Yield: The Vibration Challenge", "url": "https://www.hit1994.com/en-US/blogc54-how-overhead-hoist-transfer-oht-precision-affects-semiconductor-yield-the-vibration-challenge"},
            {"title": "Trailer based rail monitoring in OHT systems (논문)", "url": "https://www.researchgate.net/publication/331589555_Trailer_based_rail_monitoring_in_overhead_hoist_transport_systems"},
            {"title": "MFSG — AMHS in Semiconductor Manufacturing: A Practical Guide", "url": "https://www.mfsg-tech.com/industry/amhs-in-semiconductor-manufacturing-a-practical-guide/"},
            {"title": "OHT 네트워크 취약 링크 시각화 (PMC 논문)", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC11244790/"},
        ],
        tags="OHT,AMHS,진동,레일,수율,반도체",
    ),
    # ── ROBOT ──
    dict(
        category="ROBOT", topic="REDUCER",
        title="로봇 감속기(하모닉드라이브) L10 수명 계산",
        summary="L10 = Ln × (Tr/Tav)³ × (nr/nav). 평균 부하토크의 3제곱으로 수명 감소 — 페이로드 여유 설계가 핵심.",
        content=(
            "하모닉드라이브(스트레인 웨이브 기어) 수명은 웨이브 제너레이터 베어링이 지배:\n\n"
            "L10 = Ln × (Tr / Tav)³ × (nr / nav)\n"
            "  Ln: 정격수명(모델별, 통상 7,000~10,000h @ 정격토크·정격회전수)\n"
            "  Tr: 정격 출력토크, Tav: 평균 부하토크(가감속 토크 포함 RMS 등가)\n"
            "  nr: 정격 입력회전수, nav: 평균 입력회전수\n\n"
            "설계·운영 포인트:\n"
            "- 평균토크가 정격의 1.3배면 수명은 1/2.2, 2배면 1/8 — 페이로드·가감속 여유가 수명을 지배\n"
            "- 기동·정지 빈도가 높은 핸들링 로봇은 가감속 토크가 평균토크를 끌어올림 → 모션 프로파일 최적화로 수명 연장\n"
            "- 열화 징후: 백래시 증가, 위치 반복정밀도 저하, 구동 전류 상승(FDC), 그리스 철분 증가\n"
            "- 그리스 교환주기 준수(통상 1만 시간 또는 3년) — 윤활 열화 시 수명식 자체가 무효\n\n"
            "PM 항목화: 반복정밀도 측정, 백래시, 구동축 전류 트렌드, 그리스 샘플링(철분 농도)."
        ),
        sources=[
            {"title": "Harmonic Drive — Reducer Catalog Engineering Data", "url": "https://www.harmonicdrive.net/_hd/content/documents/reducer_catalog.pdf"},
            {"title": "howtomechatronics — What is Strain Wave Gear", "url": "https://howtomechatronics.com/how-it-works/what-is-strain-wave-gear-harmonic-drive-a-perfect-gear-set-for-robotics-applications/"},
        ],
        tags="로봇,감속기,하모닉드라이브,L10",
    ),
    dict(
        category="ROBOT", topic="CABLE",
        title="로봇 가동 케이블 굴곡 수명 관리",
        summary="굴곡 반경 비(R/d)와 굴곡 횟수가 수명 지배. 케이블베어 적용 시 정격 굴곡수명·최소 굴곡반경 준수.",
        content=(
            "다관절 로봇·주행축의 가동 케이블 고장은 단선·절연 열화로 나타나며 간헐 통신 이상(SYS_ISSUE 로 위장)이 흔하다.\n\n"
            "관리 기준:\n"
            "- 최소 굴곡반경: 가동용 케이블은 통상 외경의 7.5~10배 이상 (제조사 정격 준수)\n"
            "- 케이블베어 내 점유율 60% 이하, 케이블 간 간섭 방지\n"
            "- 굴곡 수명: 제조사 정격(예: 수백만 회) 대비 실제 사이클 카운트 추적 → 예방 교체\n"
            "- 토크(비틀림) 동반 구간은 전용 로봇케이블 사용\n\n"
            "징후·진단: 간헐 인코더/통신 에러(특정 자세에서 재현), 절연저항 저하.\n"
            "재현 조건이 자세 의존적이면 케이블 굴곡 단선을 1순위로 의심 — SYS_ISSUE 워크플로우의\n"
            "'재현 조건' 단계에서 자세·위치 기록을 필수화한 이유."
        ),
        sources=[
            {"title": "igus/제조사 가동 케이블 설계 일반 기준", "ref": "Chainflex 등 가동케이블 카탈로그 통칙"},
        ],
        tags="로봇,케이블,굴곡수명",
    ),
    # ── COMMON: FDC/상태감시 ──
    dict(
        category="COMMON", topic="FDC",
        title="상태기반정비(CBM)를 위한 FDC 임계 설계 가이드",
        summary="레벨(워닝/알람) + 스파이크(4σ) + 드리프트의 3계층 룰. 베이스라인은 셋업 안정화 기간에 수집.",
        content=(
            "본 플랫폼 FDC 룰 엔진의 설계 근거와 운영 가이드:\n\n"
            "1) 레벨 룰: 물리 한계 기반 — 예) 베어링 진동 ISO 10816 존 경계, 배터리 온도 45/55°C,\n"
            "   모터 전류 정격의 110%(워닝)/125%(알람)\n"
            "2) 스파이크 룰: 최근 표본 평균 ±4σ 이탈 — 충격성 이상(이물 통과, 충돌) 검출\n"
            "3) 드리프트 룰: 이동평균이 워닝 한계의 70% 에 접근 — 마모·열화의 점진 진행 검출,\n"
            "   PM 앞당김(CBM) 트리거로 활용\n\n"
            "운영 원칙:\n"
            "- 베이스라인(평균·분산)은 셋업 안정화 기간(SETUP_STAB 워크플로우)에 수집\n"
            "- 알람 임계 변경은 ALARM_ACTION 워크플로우의 '임계값 재검토' 단계로만 — 변경 근거 기록\n"
            "- 오탐율이 높으면 임계 완화보다 센서 위치·필터링 재검토를 우선\n"
            "- Phase 2 고도화: EWMA, Isolation Forest 등 통계/ML 모델로 다변량 이상 감지"
        ),
        sources=[
            {"title": "ISO 10816/20816 (기계 진동 평가)", "ref": "ISO 20816 시리즈"},
        ],
        tags="FDC,CBM,임계,이상감지",
    ),
    # ── PORT(항만) ──
    dict(
        category="PORT_OHT", topic="WIRE_ROPE",
        title="포트(항만 크레인)·대형 호이스트 로프 운영 특이사항",
        summary="다층권 드럼·대수심 권상은 로프 회전·크로스오버 마모 관리가 핵심. 회전저항 로프는 굽힘피로 수명이 짧음.",
        content=(
            "대양정(高양정) 권상 설비(항만 크레인, 대형 리프터)의 와이어로프 관리:\n\n"
            "- 다층권 드럼: 크로스오버 구간에서 로프 간 압괴·마모 집중 — ISO 4309 도 다층권에 강화 기준 적용\n"
            "- 회전저항(rotation resistant) 로프: 후크 회전 방지에 필수지만 일반 로프 대비\n"
            "  굽힘피로 수명이 짧다는 시험 결과(문헌) — 폐기기준 도달 전 내부 단선 진행 주의\n"
            "- 대수심/대양정은 로프 자중이 장력에 가산 — 안전율 계산 시 로프 자중 포함\n"
            "- 염분 환경(항만)은 부식 가속 — 아연도금/내식 로프 + 방청 그리스, 부식률 비전(CORROSION) 측정 유효\n\n"
            "교체 전략: 동일 듀티 로프의 실측 수명 데이터를 축적해 교체주기를 통계적으로 설정하고\n"
            "(평균수명의 70~80% 시점 계획 교체), 단선 추세가 비정상이면 조기 교체."
        ),
        sources=[
            {"title": "Discarding lifetime investigation of a rotation resistant rope (ScienceDirect)", "url": "https://www.sciencedirect.com/science/article/abs/pii/S026322411930404X"},
            {"title": "CASAR Wire Rope Guidelines", "url": "https://www.casar.de/Portals/0/Guidelines_32112022_EN_UK.pdf"},
        ],
        tags="포트,크레인,와이어로프,다층권,부식",
    ),
]


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(KnowledgeArticle).first():
            print("지식 DB 이미 시드됨 — 건너뜀")
            return
        for a in ARTICLES:
            db.add(KnowledgeArticle(**a))
        db.commit()
        print(f"지식 DB 시드 완료: {len(ARTICLES)}건")
    finally:
        db.close()


if __name__ == "__main__":
    run()
