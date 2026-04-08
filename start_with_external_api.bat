@echo off
echo ============================================================
echo Starting Pi Agent Boss with External NVIDIA Model
echo ============================================================
echo.
echo Setting environment variables...
set NVIDIA_API_KEY=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
echo API Key set: %NVIDIA_API_KEY:~0,20%...
echo.
echo Starting Pi Agent Boss...
echo - Mode: BOSS
echo - External Config: config\external_apis.yaml
echo - Discovery Interval: 600 seconds
echo.
python scripts\pi_agent.py start --mode boss --external-api-config config\external_apis.yaml --discovery-interval 600
echo.
echo Pi Agent Boss stopped.
pause
