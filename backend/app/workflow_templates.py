"""표준 워크플로우 템플릿 정의.

각 템플릿은 설비 생애주기의 핵심 업무 절차를 단계화한다.
step.link 는 플랫폼 내 도구/지식/페이지로 연결된다:
  {"kind": "tool",      "ref": "wire-rope-pro", "label": "..."}  → 엔지니어링 툴
  {"kind": "knowledge", "ref": "WIRE_ROPE",     "label": "..."}  → 지식 DB topic
  {"kind": "page",      "ref": "/pm",           "label": "..."}  → 플랫폼 화면
"""

TEMPLATES: dict[str, dict] = {
    "DR": {
        "label": "Design Review (설계 검토)",
        "description": "신규/개조 설비 설계 검토. 과거 BM·L&L·FDC 이력 데이터팩을 근거로 수행한다.",
        "steps": [
            {"name": "사양·듀티 검토", "guide": "가반하중, 속도, 가감속, 일일 사이클 → ISO 4301/FEM 듀티등급(M1~M8) 선정 적정성. 요구 가동률과 설계 수명(FEM 9.755: 10년/250일 기준) 정합 확인.",
             "link": {"kind": "knowledge", "ref": "DUTY_CLASS", "label": "듀티등급 지식"}},
            {"name": "과거 이력 데이터팩 검토", "guide": "동일/유사 모델의 BM 원인 Top, PM NG 항목, FDC 알람 통계, L&L 미반영 항목을 설계에 반영했는지 확인. (DR 데이터팩 자동 생성 사용)",
             "link": {"kind": "page", "ref": "drpack", "label": "DR 데이터팩 열기"}},
            {"name": "권상계 안전율 계산서", "guide": "와이어로프/체인 안전율 — 산업안전보건규칙 제163조: 화물 직접지지 5 이상, 사람 탑승 10 이상. 로프 수명예측 툴로 D/d·체결방식 민감도 검토.",
             "link": {"kind": "tool", "ref": "wire-rope-pro", "label": "와이어로프 수명예측 툴"}},
            {"name": "구동계 수명 계산서", "guide": "베어링 L10(ISO 281) ≥ 설계수명, 감속기(하모닉드라이브 L10 = Ln×(Tr/Ta)³×(nr/na)), 휠 마모 여유 확인.",
             "link": {"kind": "tool", "ref": "bearing", "label": "베어링 L10 계산기"}},
            {"name": "제어 안전 설계 검토", "guide": "비상정지 카테고리, 인터록 매트릭스, 안전 PLC PL(ISO 13849-1) — AGV/AMR 은 ISO 3691-4 인적감지·제동 요구 확인.",
             "link": {"kind": "knowledge", "ref": "SAFETY_STD", "label": "안전 표준 지식"}},
            {"name": "유지보수성 검토", "guide": "소모품 접근성(교체 시간), 파츠 표준화(기존 BOM 공용화율), 점검 포인트 비전 측정 가능성, FDC 센서 사양·설치 위치 확정."},
            {"name": "스페어파츠 초기 리스트", "guide": "Critical 파츠 선정(단종 리스크, 리드타임), MTBF 기반 초기 권장재고 산출.",
             "link": {"kind": "page", "ref": "/parts", "label": "권장재고 화면"}},
            {"name": "DR 승인·액션아이템 등록", "guide": "지적사항을 액션아이템화하고 설비 생애주기 이력(DR 단계)에 기록. 미결 액션은 제작 착수 전 클로즈."},
        ],
    },
    "SETUP_STAB": {
        "label": "셋업 후 안정화",
        "description": "설치~시운전~안정화 모니터링 기간 운영 절차 (통상 2~4주).",
        "steps": [
            {"name": "설치 정밀도 측정", "guide": "레일 직진도/수평도, 마스트 수직도 등 측정 후 기록. 비전 ALIGNMENT 측정 병행 가능.",
             "link": {"kind": "page", "ref": "/vision", "label": "비전 측정"}},
            {"name": "Install Parameter 확정", "guide": "속도/가감속/위치 게인 등 파라미터를 확정하고 플랫폼에 버전 등록 (이후 변경은 CONTROL_CHANGE 워크플로우 사용).",
             "link": {"kind": "page", "ref": "/equipment", "label": "파라미터 등록"}},
            {"name": "무부하 시운전", "guide": "전 구간 주행/권상 사이클, 이상소음·진동 확인. FDC 센서 베이스라인 수집 시작."},
            {"name": "정격부하 시운전", "guide": "정격 하중으로 반복 사이클, 모터 전류·온도 트렌드가 설계 범위 내인지 FDC 로 확인.",
             "link": {"kind": "page", "ref": "/fdc", "label": "FDC 트렌드"}},
            {"name": "안전장치 검증", "guide": "비상정지, 리미트, 과부하 검출, (AGV/AMR) 인적감지 센서 — 전 항목 작동 시험 기록."},
            {"name": "안정화 모니터링 (2주)", "guide": "초기 고장(initial failure) 구간 집중 감시 — 알람/BM 발생 시 즉시 원인 분석. 무고장 기준 충족 시 종료."},
            {"name": "인수인계·표준 등록", "guide": "PM 표준 점검항목 적용 확인, 운전·정비 교육, 셋업 완료를 생애주기 이력에 기록 후 설비 상태 RUN 전환."},
        ],
    },
    "ALARM_ACTION": {
        "label": "알람 조치",
        "description": "FDC/설비 알람 발생 시 표준 대응 절차.",
        "steps": [
            {"name": "알람 분류·심각도 판정", "guide": "FDC 분류(LEVEL/SPIKE/DRIFT) 확인. ALARM 레벨 또는 반복 WARN 은 즉시 현장 확인.",
             "link": {"kind": "page", "ref": "/fdc", "label": "FDC 알람"}},
            {"name": "1차 현장 확인", "guide": "센서 오류 여부(센서 자체 점검) → 실제 이상이면 운전 지속 가능성 판단(감속 운전/정지)."},
            {"name": "원인 분석", "guide": "트렌드 이력·최근 PM/BM·파라미터 변경 이력 대조. DRIFT 는 마모·열화 진행 신호 — 비전 측정으로 정량 확인."},
            {"name": "조치 실행", "guide": "조정/청소/급유로 해소되면 기록 후 종료. 부품 열화면 PM 앞당김 또는 BM 전환(FDC 알람→BM 버튼)."},
            {"name": "임계값 재검토", "guide": "오탐/미탐이면 워닝·알람 임계 보정. 변경 근거를 note 에 기록."},
            {"name": "재발 모니터링", "guide": "조치 후 동일 센서 1주 집중 감시, 재발 시 SYS_ISSUE 또는 BM_FLOW 로 격상."},
        ],
    },
    "BM_FLOW": {
        "label": "BM 처리 (고장 정비)",
        "description": "고장 발생 → 복구 → 재발방지까지의 표준 절차.",
        "steps": [
            {"name": "고장 보고·안전 확보", "guide": "BM 보고 등록(설비 상태 자동 BM 전환), 전원 차단·LOTO, 협착·낙하 위험 통제.",
             "link": {"kind": "page", "ref": "/bm", "label": "BM 등록"}},
            {"name": "응급 복구 판단", "guide": "생산 영향도에 따라 응급조치(우회 운전) vs 완전 수리 결정. 다운타임 기록 시작."},
            {"name": "근본원인 분석 (5Why)", "guide": "현상→직접원인→근본원인. FDC 사전 징후 여부 확인(있었다면 임계 재검토 연계)."},
            {"name": "부품 교체·재고 처리", "guide": "고장 파츠 지정 시 재고 자동 차감. 재고 부족 시 권장재고 재산정 및 긴급 발주.",
             "link": {"kind": "page", "ref": "/parts", "label": "파츠 재고"}},
            {"name": "수리 후 검증 운전", "guide": "단독 → 연동 운전 확인, FDC 트렌드 정상 복귀 확인 후 설비 RUN 전환."},
            {"name": "재발방지·L&L 등록", "guide": "동일 모델 타호기/타법인 수평전개 필요 시 L&L 등록(자동 전 법인 전파). PM 표준 개정 필요 시 반영.",
             "link": {"kind": "page", "ref": "/lessons", "label": "L&L 등록"}},
        ],
    },
    "PM_FLOW": {
        "label": "PM 수행",
        "description": "예방정비 오더 발행부터 완료 보고까지.",
        "steps": [
            {"name": "오더 발행·일정 협의", "guide": "주기 기반 자동 생성 또는 수동 발행. 생산과 정지 시간 협의.",
             "link": {"kind": "page", "ref": "/pm", "label": "PM 오더"}},
            {"name": "안전조치 (LOTO)", "guide": "전원 차단·잠금·표지, 고소작업 시 추락 방지. 작업허가 필요 여부 확인."},
            {"name": "표준 점검 수행", "guide": "모델별 표준 점검항목 순서대로. VISION 항목은 이미지 업로드로 정량 측정.",
             "link": {"kind": "page", "ref": "/vision", "label": "비전 측정"}},
            {"name": "측정값 판정·NG 처리", "guide": "자동판정 결과 확인. NG 는 즉시 교체 또는 BM 전환, CHECK 는 차기 PM 주기 단축 검토."},
            {"name": "소모품 교체·급유", "guide": "교체 파츠 출고 처리(재고 차감), 급유·청소 항목 수행 기록."},
            {"name": "완료 보고", "guide": "오더 완료 처리(생애주기 이력 자동 기록), 차기 오더 자동 생성 확인."},
        ],
    },
    "CONTROL_CHANGE": {
        "label": "제어 변경 관리",
        "description": "PLC 로직·파라미터·SW 변경의 변경관리(MOC) 절차.",
        "steps": [
            {"name": "변경 요청·사유 등록", "guide": "변경 대상(로직/파라미터/버전), 사유(개선/버그/안전), 요청자 기록."},
            {"name": "영향 분석", "guide": "안전 기능 영향(인터록·속도·토크 제한), 상위 시스템(MES/MCS) 인터페이스 영향, 타호기 동일 적용 필요성."},
            {"name": "백업·롤백 계획", "guide": "변경 전 프로그램/파라미터 백업, 실패 시 복구 절차와 판단 기준 명시."},
            {"name": "변경 적용", "guide": "정지 상태에서 적용 원칙. 적용자·일시 기록."},
            {"name": "검증 운전", "guide": "변경 기능 + 회귀 확인(기존 기능 영향 없음). FDC 트렌드 변화 모니터링."},
            {"name": "파라미터 이력 갱신", "guide": "Install Parameter 새 버전 등록(이전 버전 보존) — 플랫폼이 변경 이력을 생애주기에 자동 기록.",
             "link": {"kind": "page", "ref": "/equipment", "label": "파라미터 이력"}},
        ],
    },
    "SYS_ISSUE": {
        "label": "시스템 이슈",
        "description": "제어/SW/통신 등 시스템성 이슈 처리(벤더 협업 포함).",
        "steps": [
            {"name": "이슈 등록·재현 조건", "guide": "발생 조건, 빈도, 영향 범위(단일 호기/전체) 기록. 로그·화면 캡처 확보."},
            {"name": "로그 수집·분석", "guide": "설비 로그, 상위 통신 로그, FDC 데이터 시간 동기화하여 원인 구간 특정."},
            {"name": "임시조치 (Workaround)", "guide": "운영 지속을 위한 우회 방안 적용 및 리스크 명시."},
            {"name": "벤더 에스컬레이션", "guide": "재현 절차·로그 패키지 전달, 패치 일정 합의. 진행 상황 추적."},
            {"name": "패치 적용·검증", "guide": "CONTROL_CHANGE 워크플로우 절차에 따라 적용·검증."},
            {"name": "수평전개·L&L", "guide": "동일 버전 사용 타호기/타법인 적용 계획 수립, L&L 등록.",
             "link": {"kind": "page", "ref": "/lessons", "label": "L&L 등록"}},
        ],
    },
}
