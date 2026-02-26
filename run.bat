@echo off
start "MindWay Main Server" cmd /k ".venv\Scripts\activate && uvicorn main:app --reload --port 8000"
start "MindWay Face Server" cmd /k ".venv\Scripts\activate && uvicorn deepface_main:app --reload --port 8001"
