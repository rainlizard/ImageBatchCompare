@echo off
echo Setting up build environment...

REM Check if virtual environment exists, create if it doesn't
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt pyinstaller==6.4.0

REM Create executable
echo Building executable...
pyinstaller --noconfirm --onefile ^
    --windowed ^
    --icon="icon.png" ^
    --add-data "icon.png;." ^
    --distpath "." ^
    --name "ImageBatchCompare" ^
    --collect-all tkinterdnd2 ^
    --hidden-import tkinter ^
    --hidden-import tkinterdnd2 ^
    image-batch-compare.py

REM Clean up
echo Cleaning up...
rmdir /s /q build
del "ImageBatchCompare.spec"

echo.
if exist "ImageBatchCompare.exe" (
    echo Build successful! The executable has been created.
) else (
    echo Build failed! Please check the error messages above.
)

pause 