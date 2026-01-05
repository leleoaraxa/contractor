Start-Process powershell -ArgumentList "-NoExit","-Command","python -m uvicorn app.control_plane.api.main:app --host 0.0.0.0 --port 8001 --reload"
Start-Process powershell -ArgumentList "-NoExit","-Command","python -m uvicorn app.runtime.api.main:app --host 0.0.0.0 --port 8000 --reload"
