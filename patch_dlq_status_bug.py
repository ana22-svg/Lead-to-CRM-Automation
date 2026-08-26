import ast
import pathlib

REPO = pathlib.Path("/workspaces/Lead-to-CRM-Automation/lead_to_crm/app")
DB_PATH = REPO / "db.py"
MAIN_PATH = REPO / "main.py"

db_src = DB_PATH.read_text()

old_fn = '''def mark_processed(row_id: int):
    conn = get_conn()
    conn.execute("UPDATE inbox SET processed = 1, status = 'success' WHERE id = ?", (row_id,))
    conn.commit()
    conn.close()'''

assert old_fn in db_src, "mark_processed() body not found verbatim -- aborting, check for prior edits"

new_fn = '''def mark_processed(row_id: int, status: str = "success"):
    conn = get_conn()
    conn.execute("UPDATE inbox SET processed = 1, status = ? WHERE id = ?", (status, row_id))
    conn.commit()
    conn.close()'''

db_src = db_src.replace(old_fn, new_fn)
ast.parse(db_src)
DB_PATH.write_text(db_src)
print(f"Patched {DB_PATH}")

main_src = MAIN_PATH.read_text()

old_call_site = '''                domain=domain,
                confidence=extraction.extraction_confidence,
            )
            result = {
                "inbox_id": row_id,
                "source": source,
                "extraction_method": method,
                "extracted": extraction.model_dump(),
                "enrichment_source": enrichment_source,
                "enrichment": enrichment.model_dump() if enrichment else None,
                "icp_score": icp.model_dump(),
                "routing": routing.model_dump(),
                "status": "queued_for_review",
                "review_id": review_id,
            }
            mark_processed(row_id)
            return result'''

assert old_call_site in main_src, "process_lead() review branch not found verbatim -- aborting"

new_call_site = old_call_site.replace(
    "            mark_processed(row_id)\n            return result",
    '            mark_processed(row_id, status="queued_for_review")\n            return result'
)

main_src = main_src.replace(old_call_site, new_call_site)
ast.parse(main_src)
MAIN_PATH.write_text(main_src)
print(f"Patched {MAIN_PATH}")

print("\nDone. Restart uvicorn (--reload should pick it up) and re-run the DLQ test.")
