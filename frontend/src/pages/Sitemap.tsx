import { Link } from 'react-router-dom'

/* 시스템 사이트맵 — 전체 구성과 데이터 흐름 */

const MAP = [
  {
    group: '모니터링 (사이트 범위)', color: 'var(--ng)',
    items: [
      { to: '/', name: '대시보드', desc: 'KPI 4종 + 오늘의 조치 대상(알람→이슈→PM지연→발주) + 주간 BM·PM·알람 분포' },
      { to: '/fdc', name: 'FDC 트렌드/알람', desc: '센서 실시간 트렌드, 레벨/스파이크/드리프트 감지, 알람→BM 전환' },
      { to: '/issues', name: '이슈 관리', desc: '설비(기구/전장/제어/인터락)·시스템(CIM/MCS/RTD)·안전 분류, 도메인 통계' },
    ],
  },
  {
    group: '라이프사이클 (사이트 범위)', color: 'var(--accent)',
    items: [
      { to: '/lifecycle', name: '라이프사이클 맵', desc: '투자→제작→셋업→양산→폐기 플로우 — 단계/프로세스 편집 가능, 모듈 연결' },
      { to: '/projects', name: '프로젝트', desc: '투자/구축 프로젝트 CRUD (삭제는 관리자), 견적·예산 현황 요약' },
      { to: '/investment', name: '투자·견적 분석', desc: '견적 업로드→자동분류→원가구조/오류/이상단가/파레토→ERRC→업체 비교' },
      { to: '/equipment', name: '설비 마스터/이력', desc: 'DR~폐기 생애주기 타임라인, Install Parameter 버전 이력' },
      { to: '/workflows', name: '워크플로우', desc: 'DR/셋업안정화/알람/BM/PM/제어변경/시스템이슈 7종 절차 + DR 데이터팩' },
    ],
  },
  {
    group: '정비 운영 (사이트 범위)', color: 'var(--warn)',
    items: [
      { to: '/pm', name: 'PM 표준/오더', desc: '표준 점검항목(전사 공통)·주기 오더·측정값 자동판정' },
      { to: '/bm', name: 'BM 고장정비', desc: '고장 보고→원인→조치, 파츠 재고 자동 차감, L&L 연계' },
      { to: '/vision', name: '비전 측정', desc: '정기 상태감시(볼트/와이어/파손/레일 + 순회 동영상) + 수동 측정 4종' },
      { to: '/parts', name: '스페어 파츠', desc: '재고/입출고, BOM, MTBF 기반 권장재고(발주 우선순위)' },
    ],
  },
  {
    group: '전사 공통 표준', color: 'var(--ok)',
    items: [
      { to: '/engineering', name: '계산 툴 (PRO)', desc: '와이어로프/모터/컨베이어/체인/베어링/배터리/휠 + 산정 기준·표준 근거 탭' },
      { to: '/knowledge', name: '지식 DB·표준', desc: 'ISO/FEM/DIN/법규/논문 기반 17건+ — 출처 링크 포함' },
      { to: '/lessons', name: 'Lesson & Learn', desc: '전사 풀 — 등록 시 전 사이트 전파, 적용 매트릭스, PM 표준 반영' },
    ],
  },
  {
    group: '시스템', color: 'var(--text-3)',
    items: [
      { to: '/data-io', name: '데이터 관리 (엑셀)', desc: '9개 항목 양식 다운로드/가져오기(DB 반영)/내보내기' },
      { to: '/sitemap', name: '사이트맵', desc: '이 화면 — 시스템 전체 구성과 데이터 흐름' },
    ],
  },
]

export default function Sitemap() {
  return (
    <div>
      <p className="page-desc">
        시스템 전체 구성입니다. 사이트 범위 화면은 상단바 사이트 셀렉터로 필터되고,
        전사 공통 화면은 하나의 표준을 전 사이트가 공유합니다. 설정(⚙)에서 테마·밀도·역할을 변경합니다.
      </p>

      <div className="row">
        {MAP.map((g) => (
          <div className="panel" key={g.group} style={{ borderTop: `3px solid ${g.color}`, minWidth: 280 }}>
            <div className="panel-title">{g.group}</div>
            {g.items.map((i) => (
              <div key={i.to} style={{ padding: '7px 0', borderBottom: '1px solid var(--border)' }}>
                <Link to={i.to} style={{ fontWeight: 700, fontSize: 13 }}>{i.name}</Link>
                <div className="muted" style={{ marginTop: 2 }}>{i.desc}</div>
              </div>
            ))}
          </div>
        ))}
      </div>

      <div className="panel">
        <div className="panel-title">핵심 데이터 흐름</div>
        <div className="formula">{`[투자]  프로젝트 → 견적 자동분석/ERRC → 업체 선정
   ↓
[제작]  DR 워크플로우 ←── DR 데이터팩 (BM·PM NG·FDC·L&L 운영이력 자동 집계) ──┐
   ↓                                                                        │
[셋업]  설치 → Install Parameter(버전) → 알람/이슈/안전 → 안정화 판정         │
   ↓                                                                        │
[양산]  PM(표준점검·자동판정) · BM(고장→재발방지) · FDC(드리프트→CBM)          │
        비전 상태감시(정기촬영/순회영상 → 이상 자동감지 → 이슈)                │
   ↓                                                                        │
[L&L]   사이트 발생 → 전사 풀 → 전 사이트 전파/적용 → PM 표준 반영 ───────────┘`}</div>
        <p className="muted">상세 문서: docs/01 기획 · 02 데이터모델 · 03 비전측정 · 04 지식근거 · 05 워크플로우 · 06 블럭구조 · 07 엔지니어링기준 · 08 상태감시 · 09 사이트거버넌스 · 10 사이트맵</p>
      </div>
    </div>
  )
}
