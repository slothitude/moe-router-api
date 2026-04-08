@echo off
REM Start Pi Agent Boss with External API Integration

echo Starting Pi Agent Boss with External API Models...
echo.

REM Set environment variables from .env file
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if not "%%a"=="" if not "%%a:~0,1%"=="#" (
        set %%a=%%b
    )
)

echo NVIDIA API Key: %NVIDIA_API_KEY:~0,20%...
echo External Config: %EXTERNAL_API_CONFIG%
echo.

REM Start Pi Agent Boss
python scripts\pi_agent.py start --external-api-config config\external_apis.yaml

pause
