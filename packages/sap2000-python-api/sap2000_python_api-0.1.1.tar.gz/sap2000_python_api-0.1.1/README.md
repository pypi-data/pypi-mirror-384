# SAP2000 MCP (Model Context Protocol)
## npm ��� (���� ��ġ)
- Node 18+�� ��ġ�Ǿ� �ִٸ�, ������Ʈ ��Ʈ���� ������ �����ϸ� CLI�� ��ġ�˴ϴ�.
`
npm i -g sap2000-python-api
`
- ����:
`
sap2000-python-api --host 127.0.0.1 --port 8000
`
- ù ���� �� .venv�� �����ϸ� �ش� Python�� ����ϰ�, ������ �ý��� python�� ����մϴ�. �ʿ��� ��� pip install -e .�� �������� �ڵ� ��ġ�ϰ�, DB�� ���� CHM_PATH/SAP2000_API_DLL�� �����Ǿ� ������ ���带 �ڵ����� �����մϴ�.

SAP2000 OAPI(CHM 문서) ??구조??카드(JSONL) ??DLL 리플?�션 보강 ??검???�산(FTS/3?�gram) ??SQLite ??MCP API(find_functions / to_python / render_hint)까�? 결정론적 ?�이?�라?�을 ?�공?�니?? Python ?�용?��? 복붙 ?��??�로 ?�전?�게 API�??�출?????�도�??�계?�습?�다.

## ?�구?�항
- Windows + Python 3.11
- SAP2000 OAPI DLL: `SAP2000v1.dll` (로컬 경로 지??
- CHM ?��?�??�일: `CSI_OAPI_Documentation.chm`(?�는 ?�등)

## ?�경 ?�정
```
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]

# ?�경변??(?�요 ???�용??경로�??�정)
setx CHM_PATH "%CD%\CSI_OAPI_Documentation.chm"
setx WORK_DIR "%CD%\build"
setx SAP2000_API_DLL "%CD%\SAP2000v1.dll"
```

## 빌드 ?�서(고정)
?�래 ?�서�?반드??지켜야 결정론적 ?�출물이 ?�성?�니??
```
# 1) CHM ??HTML ??카드(JSONL)
python scripts\build_cards.py

# 2) DLL 리플?�션 보강(?�탈???�그먼트 alias ?�함), ?�패 분류 ?�약 ?�성
python scripts\enrich_cards.py

# 3) 검???�산(FTS 문서/3?�gram) ?�성
python scripts\build_search_assets.py

# 4) SQLite 조립(fts/fts_gram ?�함, PRAGMA ?�드?? rowid==id 검�?
python scripts\build_database.py
```
?�출�??�치:
- 카드: `build/cards/functions_base.jsonl`, `build/cards/functions_enriched.jsonl`
- 검?? `build/search/functions_fts.jsonl`
- ?�이?�베?�스: `build/db/sap2000_mcp.db`
- 리플?�션 리포?? `build/reports/reflection_summary.json`

## ?�버 ?�행
```
.venv\Scripts\activate
uvicorn mcp.api:app --reload
```
- ?�스체크: `GET /health` ??`{ "status": "ok" }`

## ?�드?�인??- `POST /find_functions`
  - ?�력: `{ "q": "point coord cartesian", "top_k": 10, "verb_intent": "read", "expand_level": "expanded", "domain_hints": ["geometry"], "explain": true }`
  - 출력: ?�위 결과 리스???�수 id/?�름/section/qualified_c/qualified_py/?�수/?�니???�코??구성)
  - ?�작: FTS 매칭 ???�수?�진 ??3?�gram ?�백(?�요 ??. `reflection_status='missing'` ?�수??기본 ?�외.

- `POST /to_python`
  - ?�력: `{ "function_id": 116, "policy": "tuple_ret", "binding_mode": "direct|typed_wrapper" }`
  - 출력: ?�플 반환 ?�그?�처/?�출 ?�니???�트/?�라미터·반환 구조
  - 비정??`ret != 0`) ??`Sap2000CallError` 발생 ?�플�??�공, out/ref 배열?� `list(...)` 변??권고

- `POST /render_hint`
  - ?�력: `{ "function_id": 116 }`
  - 출력: import/?�류 처리/?�출 ?�식 간단 ?�트

## 결정론적 보장
- JSON 직렬?? NFC, LF, `sort_keys=True`, `separators=(',', ':')` 고정
- DB: `rowid == functions.id` 계약, fts/fts_gram 건수 ?�일 검�?
## ?�스??```
.venv\Scripts\activate
pytest -q
```
- DB 무결??검???�모???�그?�처 ?�모?��? 기본 ?�함?�니??

## ?�려�??�한/주의
- 문서?�는 존재?��?�?DLL???�는 API(브리지 고급/?�거???�계 코드 ????`reflection_status='missing'`?�로 분류?�어 기본 검?�에???�외?�니??
- 최신 DLL ?�보 ??`scripts\enrich_cards.py` ?�실?�으�??�동 ?�분류됩?�다.

## ?�영/배포 ?�약
- ?�빌?? `build_cards ??enrich_cards ??build_search_assets ??build_database`
- ?�버 교체: DB ?�일 ?�왑 ??`/health` ?�인
- 롤백: 직전 DB/검???�산 보�?본으�?교체

?�세???�영 ?�차??`RUNBOOK_KR.md`�?참고?�세??



