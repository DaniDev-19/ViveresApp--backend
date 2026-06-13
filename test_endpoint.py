import sys
import asyncio
sys.path.insert(0, r"d:\Escritorio\ViveresApp\backend")
from app.api.v1.routes.reports import export_returns_report
from app.db.session import SessionLocal

async def main():
    async with SessionLocal() as db:
        try:
            res = await export_returns_report(start_date=None, end_date=None, format="pdf", db=db, current_user=None)
            print("Status Code:", res.status_code)
            if hasattr(res, "body"):
                print(res.body[:200])
        except Exception as e:
            print(f"Exception: {e}")

asyncio.run(main())
