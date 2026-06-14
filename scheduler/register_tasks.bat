@echo off
REM CPDS-AI Task Scheduler Registration
REM Run this as Administrator once to register all scheduled tasks
REM After running, tasks appear in Windows Task Scheduler

echo Registering CPDS-AI scheduled tasks...

REM Source runner — Saturday 9pm
schtasks /Create /TN "CPDS-AI\SourceRunner" /XML "%~dp0source_runner_task.xml" /F
if %ERRORLEVEL% EQU 0 (echo   [OK] SourceRunner registered) else (echo   [FAIL] SourceRunner failed)

REM Curate — Sunday 6am
schtasks /Create /TN "CPDS-AI\Curate" /XML "%~dp0curate_task.xml" /F
if %ERRORLEVEL% EQU 0 (echo   [OK] Curate registered) else (echo   [FAIL] Curate failed)

REM Analytics — Monday 8am
schtasks /Create /TN "CPDS-AI\Analytics" /XML "%~dp0analytics_task.xml" /F
if %ERRORLEVEL% EQU 0 (echo   [OK] Analytics registered) else (echo   [FAIL] Analytics failed)

echo.
echo Done. To verify: schtasks /Query /TN "CPDS-AI" /FO LIST
echo.
echo Tasks registered:
echo   CPDS-AI\SourceRunner  — Saturday 9:00 PM
echo   CPDS-AI\Curate        — Sunday 6:00 AM
echo   CPDS-AI\Analytics     — Monday 8:00 AM
