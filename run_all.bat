@echo off
chcp 65001 >nul
echo =====================================================================
echo  KHOI CHAY HE THONG QUAN LY BAO HIEM TICH HOP AI (INSURTECH SMART)
echo =====================================================================
echo [1/2] Dang kiem tra va khoi tao co so du lieu...
set PYTHONIOENCODING=utf-8
python backend/seed_data.py

echo.
echo [2/2] Dang khoi chay Backend FastAPI Server tai cong 8000...
echo  - Swagger API Documentation: http://127.0.0.1:8000/docs
echo  - Web Application Portal:    http://127.0.0.1:8000/
echo.

start cmd /k "set PYTHONIOENCODING=utf-8 && set PYTHONPATH=backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 3 >nul
start http://127.0.0.1:8000/docs
start http://127.0.0.1:8000/

echo He thong da duoc khoi chay thanh cong!
pause
