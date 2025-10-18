@echo off
REM QCC Windows Release Script
REM 用于自动化发布流程

setlocal enabledelayedexpansion

set VERSION=0.4.0
set BRANCH=feature/v0.4.0-development

echo ==================================
echo   QCC v%VERSION% 发布脚本 (Windows)
echo ==================================

REM 1. 检查工作目录
echo.
echo [1/8] 检查 Git 状态...
git status --porcelain > nul 2>&1
if errorlevel 1 (
    echo ❌ Git 检查失败
    exit /b 1
)
echo ✅ 工作目录检查完成

REM 2. 推送到远程
echo.
echo [2/8] 推送到远程仓库...
git push origin %BRANCH%
if errorlevel 1 (
    echo ❌ 推送失败，请检查网络连接
    echo.
    echo 你可以稍后手动执行：
    echo   git push origin %BRANCH%
    pause
    exit /b 1
)
echo ✅ 推送成功

REM 3. 合并到 main 分支
echo.
echo [3/8] 合并到 main 分支...
git checkout main
git pull origin main
git merge %BRANCH% --no-ff -m "Merge branch '%BRANCH%' - Release v%VERSION%"
git push origin main
if errorlevel 1 (
    echo ❌ 合并失败
    exit /b 1
)
echo ✅ 已合并到 main 并推送

REM 4. 创建 Git Tag
echo.
echo [4/8] 创建 Git Tag v%VERSION%...
git tag -a "v%VERSION%" -m "Release v%VERSION% - Anthropic Protocol Support"
git push origin "v%VERSION%"
if errorlevel 1 (
    echo ❌ Tag 创建失败
    exit /b 1
)
echo ✅ Tag 创建成功

REM 5. 提示创建 GitHub Release
echo.
echo [5/8] 创建 GitHub Release...
echo.
echo 请在 GitHub 上创建 Release:
echo   https://github.com/yxhpy/qcc/releases/new?tag=v%VERSION%
echo.
echo 或使用 gh cli (如果已安装):
echo   gh release create v%VERSION% --title "QCC v%VERSION%" --notes-file docs/releases/v%VERSION%.md
echo.
pause

REM 6. 清理旧构建
echo.
echo [6/8] 清理旧构建文件...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist *.egg-info rmdir /s /q *.egg-info
echo ✅ 清理完成

REM 7. 构建包
echo.
echo [7/8] 构建 Python 包...
python -m build
if errorlevel 1 (
    echo ❌ 构建失败
    echo.
    echo 请确保安装了 build 工具:
    echo   pip install build
    exit /b 1
)
echo ✅ 构建完成

REM 8. 检查并上传
echo.
echo [8/8] 检查包...
python -m twine check dist\*
if errorlevel 1 (
    echo ❌ 包检查失败
    echo.
    echo 请确保安装了 twine:
    echo   pip install twine
    exit /b 1
)
echo ✅ 包检查通过

echo.
echo ==================================
echo   准备上传到 PyPI
echo ==================================
echo.
echo 包文件:
dir /b dist
echo.
echo 版本: %VERSION%
echo.
set /p "confirm=是否上传到 PyPI? (y/N): "

if /i "%confirm%"=="y" (
    echo.
    echo 上传到 PyPI...
    python -m twine upload dist\*
    if errorlevel 1 (
        echo ❌ 上传失败
        echo.
        echo 请检查 PyPI 凭据是否正确
        exit /b 1
    )
    echo.
    echo ✅ 上传成功！
    echo.
    echo 🎉 发布完成！
    echo.
    echo 现在可以使用以下命令安装:
    echo   uvx qcc
    echo   pip install qcc
) else (
    echo.
    echo ℹ️  跳过 PyPI 上传
    echo.
    echo 手动上传命令:
    echo   python -m twine upload dist\*
)

echo.
echo ==================================
echo   发布流程完成
echo ==================================
pause
