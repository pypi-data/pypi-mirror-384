@echo off
setlocal enabledelayedexpansion
 
REM YData Profiling Multilingual - Windows Release Script
REM Fork of ydataai/ydata-profiling with multilingual support by Landon Zeng
 
echo.
echo [94m========================================================[0m
echo [94m YData Profiling Multilingual Release Script[0m
echo [94m========================================================[0m
echo [93m Fork of https://github.com/ydataai/ydata-profiling[0m
echo [93m Multilingual support added by Landon Zeng[0m
echo [93m Repository: https://github.com/landonzeng/ydata-profiling-multilingual[0m
echo.
 
REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [91m Python is not installed or not in PATH[0m
    pause
    exit /b 1
)
 
REM 检查pip是否可用
pip --version >nul 2>&1
if errorlevel 1 (
    echo [91m pip is not available[0m
    pause
    exit /b 1
)
 
echo [92m Python and pip are available[0m
 
REM 读取版本号
if exist VERSION (
    set /p VERSION=<VERSION
    echo [92m Version from VERSION file: !VERSION![0m
) else (
    echo [93m VERSION file not found[0m
    set /p VERSION="Enter version number (e.g., 1.0.0): "
)
 
echo.
echo [94m Starting release process for version !VERSION![0m
echo.
 
REM 步骤1: 清理之前的构建
echo [94m1 Cleaning previous builds...[0m
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
for /d %%i in (*.egg-info) do rmdir /s /q "%%i"
for /d %%i in (src\*.egg-info) do rmdir /s /q "%%i"
echo [92m Cleanup completed[0m
echo.
 
REM 步骤2: 安装构建依赖
echo [94m2 Installing build dependencies...[0m
pip install --upgrade build twine wheel setuptools
if errorlevel 1 (
    echo [91m Failed to install build dependencies[0m
    pause
    exit /b 1
)
echo [92m Build dependencies installed[0m
echo.
 
REM 步骤3: 运行测试（可选）
if exist tests (
    echo [94m3 Tests directory found[0m
    set /p RUN_TESTS="Run tests before building (Y/n): "
    if /i "!RUN_TESTS!"=="n" (
        echo [93m Skipping tests[0m
    ) else (
        echo [94m Running tests...[0m
        if exist requirements-dev.txt (
            pip install -r requirements-dev.txt
        )
        python -m pytest tests/ -v
        if errorlevel 1 (
            echo [91m Tests failed[0m
            set /p CONTINUE="Continue anyway (y/N): "
            if /i not "!CONTINUE!"=="y" (
                echo [91m Aborting release due to test failures[0m
                pause
                exit /b 1
            )
        ) else (
            echo [92m All tests passed[0m
        )
    )
) else (
    echo [93m No tests directory found[0m
)
echo.
 
REM 步骤4: 构建包
echo [94m4 Building package...[0m
python -m build
if errorlevel 1 (
    echo [91m Build failed[0m
    pause
    exit /b 1
)
echo [92m Package built successfully[0m
echo.
 
REM 步骤5: 检查构建结果
echo [94m5 Checking built package...[0m
python -m twine check dist/*
if errorlevel 1 (
    echo [91m Package check failed[0m
    pause
    exit /b 1
)
echo [92m Package check passed[0m
echo.
 
echo [94m Built files:[0m
dir dist /b
echo.
 
REM 步骤6: 显示包信息
echo [94m6 Package Information:[0m
echo    Package Name: ydata-profiling-multilingual
echo    Version: !VERSION!
echo    Author: Landon Zeng
echo    Description: Fork of ydata-profiling with international multilingual functionality
echo    Repository: https://github.com/landonzeng/ydata-profiling-multilingual
echo    Original Project: https://github.com/ydataai/ydata-profiling
echo.
 
REM 步骤7: 选择上传目标
echo [94m7 Upload Options:[0m
echo   1) Test PyPI (recommended for testing)
echo   2) Production PyPI
echo   3) Skip upload
echo.
 
set /p UPLOAD_CHOICE="Choose upload target (1/2/3): "
 
if "!UPLOAD_CHOICE!"=="1" (
    echo [93m Uploading to Test PyPI...[0m
    echo [94m You'll need your TestPyPI API token[0m
    echo [94m Create one at: https://test.pypi.org/manage/account/token/[0m
    echo.
    
    python -m twine upload --repository testpypi dist/*
    if errorlevel 1 (
        echo [91m Upload to Test PyPI failed[0m
        pause
        exit /b 1
    )
    
    echo.
    echo [92m Successfully uploaded to Test PyPI![0m
    echo.
    echo [94m Test installation with:[0m
    echo pip install --index-url https://test.pypi.org/simple/ ydata-profiling-multilingual
    echo.
    echo [94m View on Test PyPI:[0m
    echo https://test.pypi.org/project/ydata-profiling-multilingual/
    
) else if "!UPLOAD_CHOICE!"=="2" (
    echo [91m WARNING: This will upload to production PyPI![0m
    echo [93mThis version will be publicly available and cannot be deleted.[0m
    echo.
    set /p CONFIRMATION="Are you absolutely sure Type 'YES' to confirm: "
    
    if "!CONFIRMATION!"=="YES" (
        echo [93m Uploading to Production PyPI...[0m
        echo [94m You'll need your PyPI API token[0m
        echo [94m Create one at: https://pypi.org/manage/account/token/[0m
        echo.
        
        python -m twine upload dist/*
        if errorlevel 1 (
            echo [91m Upload to PyPI failed[0m
            pause
            exit /b 1
        )
        
        echo.
        echo [92m Successfully uploaded to PyPI![0m
        echo.
        echo [94m Install with:[0m
        echo pip install ydata-profiling-multilingual
        echo.
        echo [94m View on PyPI:[0m
        echo https://pypi.org/project/ydata-profiling-multilingual/
        echo.
        echo [92m Consider starring both repositories:[0m
        echo    Original: https://github.com/ydataai/ydata-profiling
        echo    This fork: https://github.com/landonzeng/ydata-profiling-multilingual
    ) else (
        echo [93m Upload cancelled[0m
    )
    
) else if "!UPLOAD_CHOICE!"=="3" (
    echo [93m Skipping upload[0m
    echo [94m Package is ready in dist\ directory[0m
    echo.
    echo [94mManual upload commands:[0m
    echo   Test PyPI: python -m twine upload --repository testpypi dist/*
    echo   Production: python -m twine upload dist/*
    
) else (
    echo [91m Invalid option[0m
    pause
    exit /b 1
)
 
echo.
echo [92m Release process completed![0m
echo.
echo [94m Summary:[0m
echo    Package: ydata-profiling-multilingual v!VERSION!
echo    Fork by: Landon Zeng
echo    Added: Multilingual i18n support
echo    Based on: https://github.com/ydataai/ydata-profiling
 
pause