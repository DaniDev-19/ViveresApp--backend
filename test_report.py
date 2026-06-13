import sys
import os
sys.path.insert(0, r"d:\Escritorio\ViveresApp\backend")
from app.services.report_service import ReportService
import datetime

service = ReportService()
mock_data = [
    {
        "id": 1,
        "type": "Devolución",
        "date": "10/10/2023",
        "sale_id": 123,
        "amount": 50.0,
        "reason": "Test",
        "status": "completed"
    }
]

try:
    print("Testing PDF...")
    service.generate_returns_pdf(mock_data)
    print("PDF OK!")
except Exception as e:
    import traceback
    traceback.print_exc()

try:
    print("Testing Excel...")
    service.generate_returns_excel(mock_data)
    print("Excel OK!")
except Exception as e:
    import traceback
    traceback.print_exc()

