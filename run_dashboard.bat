@echo off
setlocal enabledelayedexpansion
title Oil India Limited - Baghewala Field AI Digital Twin
color 0B

echo ==============================================================================
echo    OIL INDIA LIMITED - BAGHEWALA HEAVY OIL FIELD DIGITAL TWIN
echo    AI-Enabled Well-to-Surface Cyber-Physical Simulation Platform
echo ==============================================================================
echo.

:: 1. Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Python is not found in system PATH!
    echo Please install Python 3.10+ from https://www.python.org/ and ensure
    echo "Add Python to PATH" is checked during installation.
    echo.
    pause
    exit /b 1
)

:: 2. Check and automatically install dependencies from requirements.txt
echo [1/3] Verifying Python environment & dependencies...
python -c "import streamlit, numpy, pandas, plotly, scipy, sklearn, pptx" >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] Missing Python packages detected.
    echo [*] Automatically installing all required dependencies from requirements.txt...
    echo.
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        color 0C
        echo.
        echo [ERROR] Failed to install required packages!
        echo Please check your internet connection or run: pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
    echo.
    echo [OK] All dependencies successfully installed!
) else (
    echo [OK] All required packages are already present in the environment.
)

:: 3. Verify / Generate Jury Evaluation Datasets
if not exist "jury_dataset_1_reservoir_geology.csv" (
    echo [2/3] Generating jury evaluation CSV datasets...
    python export_jury_datasets.py >nul 2>nul
    echo [OK] Jury datasets ready.
) else (
    echo [2/3] Jury datasets verified.
)

:: 4. Launch Streamlit Dashboard
echo.
echo [3/3] Starting Streamlit Server at http://localhost:8501 ...
echo.
echo ==============================================================================
echo    Dashboard URL : http://localhost:8501
echo    Press Ctrl+C in this terminal window to stop the server.
echo ==============================================================================
echo.

python -m streamlit run app.py --server.port 8501
if %errorlevel% neq 0 (
    echo.
    echo [INFO] Dashboard session stopped.
)
pause
