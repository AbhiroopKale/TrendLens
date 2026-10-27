@echo off
setlocal
cd /d "C:\Users\Abhiroop\Downloads\TrendLens_Full_Skeleton\TrendLens"
if not exist logs mkdir logs
echo ======================================================== >> logs\pipeline_runs.log
echo [%date% %time%] Starting TrendLens scheduled pipeline run >> logs\pipeline_runs.log
call .venv\Scripts\activate.bat
set PYTHONPATH=.
python -m orchestration.run_pipeline >> logs\pipeline_runs.log 2>&1
echo [%date% %time%] Pipeline run finished with code %ERRORLEVEL% >> logs\pipeline_runs.log
