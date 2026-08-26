@echo off
rem launch_selector.cmd - locate a Python >= 3.6 interpreter and run launch_selector.py
setlocal EnableExtensions
set "SCRIPT=%~dp0launch_selector.py"
set "ARGS=%*"
set "TRIED=py -3; python3; python; %USERPROFILE%\anaconda3\python.exe; %USERPROFILE%\miniconda3\python.exe; %LOCALAPPDATA%\Programs\Python\Python39\python.exe; %LOCALAPPDATA%\Programs\Python\Python310\python.exe; %LOCALAPPDATA%\Programs\Python\Python311\python.exe; %LOCALAPPDATA%\Programs\Python\Python312\python.exe; %LOCALAPPDATA%\Programs\Python\Python313\python.exe"

rem --- command candidates on PATH ---
py -3 -c "import sys;sys.exit(0 if sys.version_info>=(3,6) else 1)" >nul 2>nul
if not errorlevel 1 (
    py -3 "%SCRIPT%" %ARGS%
    exit /b %ERRORLEVEL%
)

python3 -c "import sys;sys.exit(0 if sys.version_info>=(3,6) else 1)" >nul 2>nul
if not errorlevel 1 (
    python3 "%SCRIPT%" %ARGS%
    exit /b %ERRORLEVEL%
)

python -c "import sys;sys.exit(0 if sys.version_info>=(3,6) else 1)" >nul 2>nul
if not errorlevel 1 (
    python "%SCRIPT%" %ARGS%
    exit /b %ERRORLEVEL%
)

rem --- absolute-path candidates ---
call :tryexe "%USERPROFILE%\anaconda3\python.exe"
if not errorlevel 100 exit /b %ERRORLEVEL%
call :tryexe "%USERPROFILE%\miniconda3\python.exe"
if not errorlevel 100 exit /b %ERRORLEVEL%
call :tryexe "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
if not errorlevel 100 exit /b %ERRORLEVEL%
call :tryexe "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
if not errorlevel 100 exit /b %ERRORLEVEL%
call :tryexe "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if not errorlevel 100 exit /b %ERRORLEVEL%
call :tryexe "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not errorlevel 100 exit /b %ERRORLEVEL%
call :tryexe "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
if not errorlevel 100 exit /b %ERRORLEVEL%

echo [launch_selector] ERROR: no Python interpreter with version 3.6 or newer was found. 1>&2
echo [launch_selector] Tried:%TRIED% 1>&2
echo [launch_selector] Install Python 3.6+ or add it to PATH, then retry. 1>&2
exit /b 4

:tryexe
rem returns 100 when the candidate is unusable; otherwise runs the script and returns its exit code
if not exist "%~1" exit /b 100
"%~1" -c "import sys;sys.exit(0 if sys.version_info>=(3,6) else 1)" >nul 2>nul
if errorlevel 1 exit /b 100
"%~1" "%SCRIPT%" %ARGS%
exit /b %ERRORLEVEL%
