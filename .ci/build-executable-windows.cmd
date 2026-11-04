@echo off
setlocal

for %%I in ("%~dp0..") do set "REPO_ROOT=%%~fI"
set "VENV_DIR=%~dp0.venv"

where python >nul 2>nul
if errorlevel 1 (
    echo build-executable-windows.cmd: Python 3.10 or newer is required on PATH. 1>&2
    exit /b 1
)

python -m venv "%VENV_DIR%"
if errorlevel 1 exit /b %errorlevel%

set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
"%VENV_PYTHON%" -m pip install --upgrade pip PyInstaller "%REPO_ROOT%"
if errorlevel 1 exit /b %errorlevel%

if not exist "%REPO_ROOT%\dist" mkdir "%REPO_ROOT%\dist"
if errorlevel 1 exit /b %errorlevel%
if not exist "%REPO_ROOT%\build\pyinstaller-spec" mkdir "%REPO_ROOT%\build\pyinstaller-spec"
if errorlevel 1 exit /b %errorlevel%
if not exist "%REPO_ROOT%\build\pyinstaller-work" mkdir "%REPO_ROOT%\build\pyinstaller-work"
if errorlevel 1 exit /b %errorlevel%

pushd "%REPO_ROOT%"
"%VENV_PYTHON%" -m PyInstaller --noconfirm --clean --onefile --name keysec --distpath "%REPO_ROOT%\dist" --workpath "%REPO_ROOT%\build\pyinstaller-work" --specpath "%REPO_ROOT%\build\pyinstaller-spec" "%REPO_ROOT%\src\keysec\cli.py"
set "BUILD_EXIT=%ERRORLEVEL%"
popd
exit /b %BUILD_EXIT%
