import os
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "codebase_for_gemini.md")

TARGET_FILES = [
    "requirements.txt",
    ".github/workflows/daily_crawl.yml",
    "src/utils.py",
    "src/cleaner.py",
    "src/crawler.py",
    "app.py",
    "tests/test_pipeline.py",
    "README.md",
]

def generate_bundle():
    lines = []
    lines.append("# 📚 [프로젝트 전체 코드 분석 요청서] 한국어교원 채용 통합 대시보드\n")
    lines.append("> 이 문서는 Google Gemini에게 프로젝트 전체 구조 및 소스 코드를 심층 분석시키기 위해 자동 생성된 번들 파일입니다.\n")
    
    # 1. 제미나이 분석 지시 프롬프트
    lines.append("## 🤖 Gemini 분석 가이드 (System Prompt)\n")
    lines.append("```markdown")
    lines.append("당신은 시니어 풀스택 소프트웨어 엔지니어이자 파이썬/데이터 파이프라인 아키텍트입니다.")
    lines.append("아래에 첨부된 한국어교원 채용 대시보드 프로젝트의 전체 소스 코드를 면밀히 검토하고, 다음 항목에 대해 심층 분석 보고서를 작성해 주세요:")
    lines.append("")
    lines.append("1. **아키텍처 및 모듈 분리 평가**: 크롤러, 데이터 정제기, 유틸리티, Streamlit 웹 UI 간의 결합도 및 확장성 진단")
    lines.append("2. **크롤링 및 데이터 수집 안정성 분석**: 5대 포털(국립국어원, KLE Ocean, 세종학당재단, 다누리, 워크넷) 파싱 로직, 세션 처리, 네트워크 장애 대응력")
    lines.append("3. **데이터 정제(자가진단) 품질**: 비관련 직종, 결과 발표 공지, 만료일자 필터링 규칙의 빈틈 및 개선점")
    lines.append("4. **성능 및 보안 진단**: 메모리 누수, 불필요한 반복 연산, 외부 요청 예외 처리 및 잠재적 병목")
    lines.append("5. **프로덕션 고도화 로드맵 제안**: SQLite/PostgreSQL 등 DB 도입, 비동기(asyncio) 수집, 알림 기능(카카오톡/텔레그램) 등 추천 발전 방향")
    lines.append("```\n")

    # 2. 프로젝트 트리 구조
    lines.append("## 📂 프로젝트 구조 (Directory Tree)\n")
    lines.append("```text")
    lines.append("korean-teacher-jobs-search/")
    lines.append("├── .github/workflows/daily_crawl.yml  # GitHub Actions 매일 새벽 자동 수집 워크플로우")
    lines.append("├── data/jobs.json                     # 정제 완료된 채용 공고 데이터셋 (59건)")
    lines.append("├── src/")
    lines.append("│   ├── __init__.py")
    lines.append("│   ├── crawler.py                     # 5대 포털 모듈식 수집기 및 오케스트레이터")
    lines.append("│   ├── cleaner.py                     # 노이즈 필터링 및 데이터 품질 자가진단 모듈")
    lines.append("│   └── utils.py                       # 재시도 HTTP 요청, 날짜/D-Day/자격/지역 파싱")
    lines.append("├── tests/test_pipeline.py             # 5개 자동화 단위 테스트 스위트")
    lines.append("├── app.py                             # Streamlit 반응형 웹 대시보드")
    lines.append("├── requirements.txt                   # 의존성 패키지")
    lines.append("└── README.md                          # 프로젝트 종합 가이드")
    lines.append("```\n")

    # 3. 데이터 샘플
    jobs_json_path = os.path.join(PROJECT_ROOT, "data", "jobs.json")
    if os.path.exists(jobs_json_path):
        with open(jobs_json_path, "r", encoding="utf-8") as f:
            jobs_data = json.load(f)
        lines.append(f"## 📊 데이터셋 현황 (`data/jobs.json` - 총 {len(jobs_data)}건 중 상위 3건 샘플)\n")
        lines.append("```json")
        lines.append(json.dumps(jobs_data[:3], ensure_ascii=False, indent=2))
        lines.append("```\n")

    # 4. 파일별 소스 코드 전문
    lines.append("## 💻 전체 소스 코드 전문 (Full Source Code)\n")
    for rel_path in TARGET_FILES:
        abs_path = os.path.join(PROJECT_ROOT, rel_path.replace("/", os.sep))
        if not os.path.exists(abs_path):
            continue
        
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()

        ext = rel_path.split(".")[-1]
        lang = "python" if ext == "py" else ("yaml" if ext in ["yml", "yaml"] else ("json" if ext == "json" else ext))

        lines.append(f"### 📄 `{rel_path}`\n")
        lines.append(f"```{lang}")
        lines.append(content)
        lines.append("```\n")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"-> Successfully generated Gemini bundle at: {OUTPUT_FILE}")
    print(f"-> File size: {os.path.getsize(OUTPUT_FILE):,} bytes")

if __name__ == "__main__":
    generate_bundle()
