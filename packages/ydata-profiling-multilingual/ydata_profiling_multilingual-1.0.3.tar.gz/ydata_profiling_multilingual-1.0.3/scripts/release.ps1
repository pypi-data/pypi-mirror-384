# YData Profiling Multilingual - Windows PowerShell Release Script
# Fork of ydataai/ydata-profiling with multilingual support by Landon Zeng

param(
    [string]$Version = "",
    [switch]$SkipTests = $false,
    [string]$Target = "ask"
)

# 确保在项目根目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

# 检查是否在正确目录
if (!(Test-Path "pyproject.toml")) {
    Write-Host "❌ pyproject.toml not found. Please run this script from the project root directory." -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

if (!(Test-Path "setup.py")) {
    Write-Host "❌ setup.py not found. Please run this script from the project root directory." -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ Found project configuration files in: $(Get-Location)" -ForegroundColor Green

# 配置
$PackageName = "ydata-profiling-multilingual"
$RepoUrl = "https://github.com/landonzeng/ydata-profiling-multilingual"
$OriginalRepo = "https://github.com/ydataai/ydata-profiling"

# 颜色输出函数
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    else {
        $input | Write-Output
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Info($Message) { Write-ColorOutput Blue "ℹ️ $Message" }
function Write-Success($Message) { Write-ColorOutput Green "✅ $Message" }
function Write-Warning($Message) { Write-ColorOutput Yellow "⚠️ $Message" }
function Write-Error($Message) { Write-ColorOutput Red "❌ $Message" }

# 主标题
Write-Host ""
Write-ColorOutput Blue "========================================================"
Write-ColorOutput Blue "🌍 YData Profiling Multilingual Release Script"
Write-ColorOutput Blue "========================================================"
Write-ColorOutput Yellow "📍 Fork of $OriginalRepo"
Write-ColorOutput Yellow "👨‍💻 Multilingual support added by Landon Zeng"
Write-ColorOutput Yellow "🔗 Repository: $RepoUrl"
Write-Host ""

try {
    # 检查必要工具
    Write-Info "Checking required tools..."

    if (!(Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Error "Python is not installed or not in PATH"
        exit 1
    }

    if (!(Get-Command pip -ErrorAction SilentlyContinue)) {
        Write-Error "pip is not available"
        exit 1
    }

    $pythonVersion = python --version
    Write-Success "Python found: $pythonVersion"

    # 获取版本号
    if (!$Version) {
        if (Test-Path "VERSION") {
            $Version = Get-Content "VERSION" -Raw | ForEach-Object { $_.Trim() }
            Write-Success "Version from VERSION file: $Version"
        } else {
            Write-Warning "VERSION file not found"
            $Version = Read-Host "Enter version number (e.g., 1.0.0)"
        }
    }

    Write-Host ""
    Write-Info "Starting release process for version $Version"
    Write-Host ""

    # 步骤1: 清理构建
    Write-Info "1️⃣ Cleaning previous builds..."
    $cleanDirs = @("build", "dist")
    foreach ($dir in $cleanDirs) {
        if (Test-Path $dir) {
            Remove-Item $dir -Recurse -Force
            Write-Host "🗑️ Removed: $dir"
        }
    }

    # 清理 .egg-info 目录
    Get-ChildItem -Path . -Filter "*.egg-info" -Directory | Remove-Item -Recurse -Force
    Get-ChildItem -Path "src" -Filter "*.egg-info" -Directory | Remove-Item -Recurse -Force

    Write-Success "Cleanup completed"
    Write-Host ""

    # 步骤2: 安装构建依赖
    Write-Info "2️⃣ Installing build dependencies..."
    & python -m pip install --upgrade build twine wheel setuptools
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install build dependencies"
        exit 1
    }
    Write-Success "Build dependencies installed"
    Write-Host ""

    # 步骤3: 运行测试
    if ((Test-Path "tests") -and !$SkipTests) {
        Write-Info "3️⃣ Tests directory found"
        $runTests = Read-Host "Run tests before building? (Y/n)"

        if ($runTests -ne "n" -and $runTests -ne "N") {
            Write-Info "🧪 Running tests..."

            if (Test-Path "requirements-dev.txt") {
                & python -m pip install -r requirements-dev.txt
            }

            & python -m pytest tests/ -v
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Tests failed"
                $continue = Read-Host "Continue anyway? (y/N)"
                if ($continue -ne "y" -and $continue -ne "Y") {
                    Write-Error "Aborting release due to test failures"
                    exit 1
                }
            } else {
                Write-Success "All tests passed"
            }
        } else {
            Write-Warning "⏭️ Skipping tests"
        }
    } else {
        Write-Warning "⏭️ No tests directory found or tests skipped"
    }
    Write-Host ""

    # 步骤4: 构建包
    Write-Info "4️⃣ Building package..."
    & python -m build
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Build failed"
        exit 1
    }
    Write-Success "Package built successfully"
    Write-Host ""

    # 步骤5: 检查包
    Write-Info "5️⃣ Checking built package..."
    & python -m twine check dist/*
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Package check failed"
        exit 1
    }
    Write-Success "Package check passed"
    Write-Host ""

    Write-Info "📦 Built files:"
    Get-ChildItem -Path "dist" | ForEach-Object { Write-Host "  📄 $($_.Name)" }
    Write-Host ""

    # 步骤6: 显示包信息
    Write-Info "6️⃣ Package Information:"
    Write-Host "  📦 Package Name: $PackageName"
    Write-Host "  🏷️ Version: $Version"
    Write-Host "  👨‍💻 Author: Landon Zeng"
    Write-Host "  📝 Description: Fork of ydata-profiling with international multilingual functionality"
    Write-Host "  🔗 Repository: $RepoUrl"
    Write-Host "  📊 Original Project: $OriginalRepo"
    Write-Host ""

    # 步骤7: 上传选择
    if ($Target -eq "ask") {
        Write-Info "7️⃣ Upload Options:"
        Write-Host "  1) Test PyPI (recommended for testing)"
        Write-Host "  2) Production PyPI"
        Write-Host "  3) Skip upload"
        Write-Host ""

        $choice = Read-Host "Choose upload target (1/2/3)"
    } else {
        $choice = switch ($Target) {
            "test" { "1" }
            "prod" { "2" }
            "skip" { "3" }
            default { "3" }
        }
    }

    switch ($choice) {
        "1" {
            Write-Warning "📤 Uploading to Test PyPI..."
            Write-Info "ℹ️ You'll need your TestPyPI API token"
            Write-Info "ℹ️ Create one at: https://test.pypi.org/manage/account/token/"
            Write-Host ""

            & python -m twine upload --repository testpypi dist/*
            if ($LASTEXITCODE -eq 0) {
                Write-Host ""
                Write-Success "🎉 Successfully uploaded to Test PyPI!"
                Write-Host ""
                Write-Info "📥 Test installation with:"
                Write-Host "pip install --index-url https://test.pypi.org/simple/ $PackageName"
                Write-Host ""
                Write-Info "🔗 View on Test PyPI:"
                Write-Host "https://test.pypi.org/project/$PackageName/"
            } else {
                Write-Error "Upload to Test PyPI failed"
                exit 1
            }
        }

        "2" {
            Write-Error "⚠️ WARNING: This will upload to production PyPI!"
            Write-Warning "This version will be publicly available and cannot be deleted."
            Write-Host ""
            $confirmation = Read-Host "Are you absolutely sure? Type 'YES' to confirm"

            if ($confirmation -eq "YES") {
                Write-Warning "📤 Uploading to Production PyPI..."
                Write-Info "ℹ️ You'll need your PyPI API token"
                Write-Info "ℹ️ Create one at: https://pypi.org/manage/account/token/"
                Write-Host ""

                & python -m twine upload dist/*
                if ($LASTEXITCODE -eq 0) {
                    Write-Host ""
                    Write-Success "🎉 Successfully uploaded to PyPI!"
                    Write-Host ""
                    Write-Info "📥 Install with:"
                    Write-Host "pip install $PackageName"
                    Write-Host ""
                    Write-Info "🔗 View on PyPI:"
                    Write-Host "https://pypi.org/project/$PackageName/"
                    Write-Host ""
                    Write-Success "🌟 Consider starring both repositories:"
                    Write-Host "  ⭐ Original: $OriginalRepo"
                    Write-Host "  ⭐ This fork: $RepoUrl"
                } else {
                    Write-Error "Upload to PyPI failed"
                    exit 1
                }
            } else {
                Write-Warning "❌ Upload cancelled"
            }
        }

        "3" {
            Write-Warning "⏭️ Skipping upload"
            Write-Info "📦 Package is ready in dist\ directory"
            Write-Host ""
            Write-Info "Manual upload commands:"
            Write-Host "  Test PyPI: python -m twine upload --repository testpypi dist/*"
            Write-Host "  Production: python -m twine upload dist/*"
        }

        default {
            Write-Error "Invalid option"
            exit 1
        }
    }

    Write-Host ""
    Write-Success "✅ Release process completed!"
    Write-Host ""
    Write-Info "📋 Summary:"
    Write-Host "  📦 Package: $PackageName v$Version"
    Write-Host "  👨‍💻 Fork by: Landon Zeng"
    Write-Host "  🌍 Added: Multilingual i18n support"
    Write-Host "  📊 Based on: $OriginalRepo"

} catch {
    Write-Error "Release failed: $($_.Exception.Message)"
    exit 1
}

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")