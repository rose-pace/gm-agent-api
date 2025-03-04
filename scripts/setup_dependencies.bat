@echo off
echo Installing dependencies for GM Assistant API...

REM Set project root directory to the parent directory of the batch file location
set PROJECT_ROOT=%~dp0..
REM Define list of dependencies
set DEPENDENCIES=fastapi uvicorn pydantic chromadb langchain langchain-community langchain-openai langchain-hugginface langchain-text-splitters openai python-dotenv tiktoken numpy sentence-transformers httpx pytest pytest-asyncio tqdm pypdf unstructured "unstructured[pdf]" markdown pandas tabulate pillow python-docx openpyxl

REM Install each dependency
for %%d in (%DEPENDENCIES%) do (
    echo Installing %%d...
    %PROJECT_ROOT%\venv\Scripts\python.exe -m pip install %%d
    if errorlevel 1 (
        echo Error installing %%d
        pause
        exit /b 1
    )
)

set REQUIREMENTS_PATH=%PROJECT_ROOT%\requirements.txt

REM Generate requirements.txt
echo Freezing dependencies to %REQUIREMENTS_PATH%...
python -m pip freeze > "%REQUIREMENTS_PATH%"

echo Dependencies installed successfully!
echo Requirements file created at: %REQUIREMENTS_PATH%

pause
