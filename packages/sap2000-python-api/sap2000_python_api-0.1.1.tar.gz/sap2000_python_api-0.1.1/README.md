# SAP2000 MCP (Model Context Protocol)
## npm »ç¿ë (·ÎÄÃ ¼³Ä¡)
- Node 18+°¡ ¼³Ä¡µÇ¾î ÀÖ´Ù¸é, ÇÁ·ÎÁ§Æ® ·çÆ®¿¡¼­ ´ÙÀ½À» ½ÇÇàÇÏ¸é CLI°¡ ¼³Ä¡µË´Ï´Ù.
`
npm i -g sap2000-python-api
`
- ½ÇÇà:
`
sap2000-python-api --host 127.0.0.1 --port 8000
`
- Ã¹ ½ÇÇà ½Ã .venv°¡ Á¸ÀçÇÏ¸é ÇØ´ç PythonÀ» »ç¿ëÇÏ°í, ¾øÀ¸¸é ½Ã½ºÅÛ pythonÀ» »ç¿ëÇÕ´Ï´Ù. ÇÊ¿äÇÑ °æ¿ì pip install -e .·Î ÀÇÁ¸¼ºÀ» ÀÚµ¿ ¼³Ä¡ÇÏ°í, DB°¡ ¾ø°í CHM_PATH/SAP2000_API_DLLÀÌ ¼³Á¤µÇ¾î ÀÖÀ¸¸é ºôµå¸¦ ÀÚµ¿À¸·Î ¼öÇàÇÕ´Ï´Ù.

SAP2000 OAPI(CHM ë¬¸ì„œ) ??êµ¬ì¡°??ì¹´ë“œ(JSONL) ??DLL ë¦¬í”Œ?‰ì…˜ ë³´ê°• ??ê²€???ì‚°(FTS/3?‘gram) ??SQLite ??MCP API(find_functions / to_python / render_hint)ê¹Œì? ê²°ì •ë¡ ì  ?Œì´?„ë¼?¸ì„ ?œê³µ?©ë‹ˆ?? Python ?¬ìš©?ê? ë³µë¶™ ?˜ì??¼ë¡œ ?ˆì „?˜ê²Œ APIë¥??¸ì¶œ?????ˆë„ë¡??¤ê³„?ˆìŠµ?ˆë‹¤.

## ?”êµ¬?¬í•­
- Windows + Python 3.11
- SAP2000 OAPI DLL: `SAP2000v1.dll` (ë¡œì»¬ ê²½ë¡œ ì§€??
- CHM ?„ì?ë§??Œì¼: `CSI_OAPI_Documentation.chm`(?ëŠ” ?™ë“±)

## ?˜ê²½ ?¤ì •
```
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]

# ?˜ê²½ë³€??(?„ìš” ???¬ìš©??ê²½ë¡œë¡??˜ì •)
setx CHM_PATH "%CD%\CSI_OAPI_Documentation.chm"
setx WORK_DIR "%CD%\build"
setx SAP2000_API_DLL "%CD%\SAP2000v1.dll"
```

## ë¹Œë“œ ?œì„œ(ê³ ì •)
?„ë˜ ?œì„œë¥?ë°˜ë“œ??ì§€ì¼œì•¼ ê²°ì •ë¡ ì  ?°ì¶œë¬¼ì´ ?ì„±?©ë‹ˆ??
```
# 1) CHM ??HTML ??ì¹´ë“œ(JSONL)
python scripts\build_cards.py

# 2) DLL ë¦¬í”Œ?‰ì…˜ ë³´ê°•(?¤íƒˆ???¸ê·¸ë¨¼íŠ¸ alias ?¬í•¨), ?¤íŒ¨ ë¶„ë¥˜ ?”ì•½ ?ì„±
python scripts\enrich_cards.py

# 3) ê²€???ì‚°(FTS ë¬¸ì„œ/3?‘gram) ?ì„±
python scripts\build_search_assets.py

# 4) SQLite ì¡°ë¦½(fts/fts_gram ?¬í•¨, PRAGMA ?˜ë“œ?? rowid==id ê²€ì¦?
python scripts\build_database.py
```
?°ì¶œë¬??„ì¹˜:
- ì¹´ë“œ: `build/cards/functions_base.jsonl`, `build/cards/functions_enriched.jsonl`
- ê²€?? `build/search/functions_fts.jsonl`
- ?°ì´?°ë² ?´ìŠ¤: `build/db/sap2000_mcp.db`
- ë¦¬í”Œ?‰ì…˜ ë¦¬í¬?? `build/reports/reflection_summary.json`

## ?œë²„ ?¤í–‰
```
.venv\Scripts\activate
uvicorn mcp.api:app --reload
```
- ?¬ìŠ¤ì²´í¬: `GET /health` ??`{ "status": "ok" }`

## ?”ë“œ?¬ì¸??- `POST /find_functions`
  - ?…ë ¥: `{ "q": "point coord cartesian", "top_k": 10, "verb_intent": "read", "expand_level": "expanded", "domain_hints": ["geometry"], "explain": true }`
  - ì¶œë ¥: ?ìœ„ ê²°ê³¼ ë¦¬ìŠ¤???¨ìˆ˜ id/?´ë¦„/section/qualified_c/qualified_py/?ìˆ˜/?¤ë‹ˆ???¤ì½”??êµ¬ì„±)
  - ?™ì‘: FTS ë§¤ì¹­ ???ìˆ˜?”ì§„ ??3?‘gram ?´ë°±(?„ìš” ??. `reflection_status='missing'` ?¨ìˆ˜??ê¸°ë³¸ ?œì™¸.

- `POST /to_python`
  - ?…ë ¥: `{ "function_id": 116, "policy": "tuple_ret", "binding_mode": "direct|typed_wrapper" }`
  - ì¶œë ¥: ?œí”Œ ë°˜í™˜ ?œê·¸?ˆì²˜/?¸ì¶œ ?¤ë‹ˆ???ŒíŠ¸/?Œë¼ë¯¸í„°Â·ë°˜í™˜ êµ¬ì¡°
  - ë¹„ì •??`ret != 0`) ??`Sap2000CallError` ë°œìƒ ?œí”Œë¦??œê³µ, out/ref ë°°ì—´?€ `list(...)` ë³€??ê¶Œê³ 

- `POST /render_hint`
  - ?…ë ¥: `{ "function_id": 116 }`
  - ì¶œë ¥: import/?¤ë¥˜ ì²˜ë¦¬/?¸ì¶œ ?•ì‹ ê°„ë‹¨ ?ŒíŠ¸

## ê²°ì •ë¡ ì  ë³´ì¥
- JSON ì§ë ¬?? NFC, LF, `sort_keys=True`, `separators=(',', ':')` ê³ ì •
- DB: `rowid == functions.id` ê³„ì•½, fts/fts_gram ê±´ìˆ˜ ?™ì¼ ê²€ì¦?
## ?ŒìŠ¤??```
.venv\Scripts\activate
pytest -q
```
- DB ë¬´ê²°??ê²€???¤ëª¨???œê·¸?ˆì²˜ ?¤ëª¨?¬ê? ê¸°ë³¸ ?¬í•¨?©ë‹ˆ??

## ?Œë ¤ì§??œí•œ/ì£¼ì˜
- ë¬¸ì„œ?ëŠ” ì¡´ì¬?˜ì?ë§?DLL???†ëŠ” API(ë¸Œë¦¬ì§€ ê³ ê¸‰/?ˆê±°???¤ê³„ ì½”ë“œ ????`reflection_status='missing'`?¼ë¡œ ë¶„ë¥˜?˜ì–´ ê¸°ë³¸ ê²€?‰ì—???œì™¸?©ë‹ˆ??
- ìµœì‹  DLL ?•ë³´ ??`scripts\enrich_cards.py` ?¬ì‹¤?‰ìœ¼ë¡??ë™ ?¬ë¶„ë¥˜ë©?ˆë‹¤.

## ?´ì˜/ë°°í¬ ?”ì•½
- ?¬ë¹Œ?? `build_cards ??enrich_cards ??build_search_assets ??build_database`
- ?œë²„ êµì²´: DB ?Œì¼ ?¤ì™‘ ??`/health` ?•ì¸
- ë¡¤ë°±: ì§ì „ DB/ê²€???ì‚° ë³´ê?ë³¸ìœ¼ë¡?êµì²´

?ì„¸???´ì˜ ?ˆì°¨??`RUNBOOK_KR.md`ë¥?ì°¸ê³ ?˜ì„¸??



