@echo off
echo ===================================================
echo 🧠 NeuroHack Memory Console V2.0 - PRODUCTION MODE
echo ===================================================
echo.
echo [1/2] Starting Backend Server (FastAPI)...
start "NeuroHack Backend" cmd /k ".\venv\Scripts\uvicorn.exe server:app --host 0.0.0.0 --port 8000 --reload"

echo Waiting for backend to initialize (5s)...
timeout /t 5 > nul

echo [2/2] Starting Frontend UI (Streamlit)...
call .\venv\Scripts\streamlit.exe run app.py

echo.
echo System Running!
echo Backend: http://localhost:8000/docs
echo Frontend: http://localhost:8501
pause
