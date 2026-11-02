@echo off
chcp 65001 >nul
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title sy-style-new20 install

rem ============================================================
rem  新风格 20 种（sy-style-new20）一键安装 · 作者 肖雄 / XIAOXIONG
rem  双击运行。可以反复运行：已经装好的会跳过。
rem  测试用：把 AI 说明书装到别的文件夹
rem    set SY_SKILL_DIR=D:\test\skills\sy-style-new20  再运行
rem    或  安装-Windows.bat --skill-dir D:\test\skills\sy-style-new20
rem  --no-pause：结束时不等按键
rem ============================================================

set "SKILL_DIR=%SY_SKILL_DIR%"
:parseargs
if "%~1"=="" goto argsdone
if /i "%~1"=="--skill-dir" goto argskill
if /i "%~1"=="--no-pause" set "SY_NOPAUSE=1"
shift
goto parseargs
:argskill
set "SKILL_DIR=%~2"
shift
shift
goto parseargs
:argsdone

if exist "make.js" goto pkgok
echo.
echo 这个文件要和整个包放在一起才能用。
echo 请先把下载的压缩包“全部解压”，再到解压出来的文件夹里双击「安装-Windows.bat」。
echo.
if "%SY_NOPAUSE%"=="1" goto skippause1
echo 按任意键关闭这个窗口……
pause >nul
:skippause1
exit /b 1
:pkgok

echo.
echo ==================================================
echo    新风格 20 种 · 一键安装
echo    作者：肖雄 / XIAOXIONG
echo ==================================================
echo.
echo 包的位置：
echo    "%CD%"
echo.
echo 要装的东西：Node.js、Python、ffmpeg、渲染用的浏览器。
echo 已经装好的会自动跳过。第一次大约要 5 到 20 分钟，看网速。
echo.

set "HAVE_WINGET=0"
where winget >nul 2>nul && set "HAVE_WINGET=1"
set "FAILED="

rem ------------------------------------------------------------ 1. Node.js
echo [1/6] 检查 Node.js ……
call :findnode
if defined NODE_OK goto nodeok
if "%HAVE_WINGET%"=="0" goto nonode
echo       没找到，正在用 winget 安装 Node.js（长期支持版）。
echo       如果弹出“是否允许此应用更改设备”，请点“是”。
winget install -e --id OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements --silent
call :refreshpath
call :findnode
if defined NODE_OK goto nodeok
:nonode
echo.
echo   × 没能自动装上 Node.js。请手动下载安装（选 LTS 长期支持版）：
echo       https://nodejs.org/zh-cn/download
echo     装好后关掉这个窗口，再双击一次「安装-Windows.bat」。
goto fail
:nodeok
for /f "delims=" %%v in ('node -v') do echo       √ Node.js %%v

rem ------------------------------------------------------------ 2. Python
echo [2/6] 检查 Python ……
call :findpy
if defined PY goto pyok
if "%HAVE_WINGET%"=="0" goto nopy
echo       没找到，正在用 winget 安装 Python 3.12（只装给当前用户，不用管理员）。
winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements --silent
call :refreshpath
call :findpy
if defined PY goto pyok
:nopy
echo.
echo   × 没能自动装上 Python。请手动下载安装：
echo       https://www.python.org/downloads/
echo     安装第一页一定要勾选 “Add python.exe to PATH”。
echo     装好后关掉这个窗口，再双击一次「安装-Windows.bat」。
goto fail
:pyok
echo       √ Python 已就绪：
%PY% --version

rem ------------------------------------------------------------ 3. ffmpeg
echo [3/6] 检查 ffmpeg ……
call :findff
if defined FF_OK goto ffok
if "%HAVE_WINGET%"=="0" goto noff
echo       没找到，正在用 winget 安装 ffmpeg（只装给当前用户）。
winget install -e --id Gyan.FFmpeg --accept-package-agreements --accept-source-agreements --silent
call :refreshpath
call :findff
if defined FF_OK goto ffok
:noff
echo.
echo   × 没能自动装上 ffmpeg。请手动安装：
echo       https://www.gyan.dev/ffmpeg/builds/  下载 ffmpeg-release-essentials.zip，
echo       解压到 C:\ffmpeg（让 C:\ffmpeg\bin\ffmpeg.exe 存在）。
echo     装好后再双击一次「安装-Windows.bat」。
goto fail
:ffok
echo       √ ffmpeg 已就绪

rem ------------------------------------------------------------ 4. 渲染组件 + 浏览器
echo [4/6] 安装渲染组件（playwright）和它用的浏览器 ……
call npm install --no-audit --no-fund --loglevel=error
if not errorlevel 1 goto npmok
echo       下载失败，换国内镜像再试一次 ……
call npm install --no-audit --no-fund --loglevel=error --registry=https://registry.npmmirror.com
if errorlevel 1 goto npmfail
:npmok
node node_modules\playwright\cli.js install chromium
if not errorlevel 1 goto pwok
echo       浏览器下载失败，换国内镜像再试一次 ……
set "PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/playwright"
node node_modules\playwright\cli.js install chromium
if errorlevel 1 goto pwfail
set "PLAYWRIGHT_DOWNLOAD_HOST="
:pwok
echo       √ 渲染组件和浏览器已就绪
goto step5
:npmfail
echo.
echo   × 渲染组件下载失败（网络问题）。换个网络或稍后再双击一次「安装-Windows.bat」。
goto fail
:pwfail
echo.
echo   × 浏览器下载失败（网络问题）。换个网络或稍后再双击一次「安装-Windows.bat」。
goto fail

rem ------------------------------------------------------------ 5. Python 依赖（numpy / scipy）
:step5
echo [5/6] 检查合成声音要用的 numpy、scipy ……
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import numpy, scipy" >nul 2>nul && goto depok
)
%PY% -c "import numpy, scipy" >nul 2>nul && goto depok
echo       没有，正在装到这个文件夹的 .venv 里（不影响电脑上别的 Python）……
if not exist ".venv\Scripts\python.exe" %PY% -m venv .venv
if not exist ".venv\Scripts\python.exe" goto depfail
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt
if not errorlevel 1 goto depcheck
echo       下载失败，换国内镜像再试一次 ……
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
:depcheck
".venv\Scripts\python.exe" -c "import numpy, scipy" >nul 2>nul && goto depok
:depfail
echo.
echo   × numpy / scipy 没装上（网络问题）。换个网络或稍后再双击一次「安装-Windows.bat」。
goto fail
:depok
echo       √ numpy、scipy 已就绪

rem ------------------------------------------------------------ 6. AI 说明书（SKILL）+ 总检查
echo [6/6] 安装 AI 说明书（SKILL），让 Claude Code 在任何文件夹都能找到这个包 ……
if defined SKILL_DIR goto skillcustom
node make.js install-skill
goto skilldone
:skillcustom
node make.js install-skill --to "%SKILL_DIR%"
:skilldone
if errorlevel 1 set "FAILED=1"
echo.
echo ---------------------------------- 总检查 ----------------------------------
node make.js check --installer
if errorlevel 1 set "FAILED=1"
echo ----------------------------------------------------------------------------
echo.
if defined FAILED goto fail
echo 安装完成！
echo.
echo 下一步：打开 Claude Code，直接说一句话，比如：
echo     帮我把字符画那条做出来
echo     20 种全部渲染
echo     把彩色玻璃窗改成偏蓝的晨光
echo 做好的片子会放在这个文件夹里的 out 文件夹。
echo.
echo 注意：如果 Claude Code 已经开着，请关掉再打开一次，它才能看到新装的说明。
echo.
if "%SY_NOPAUSE%"=="1" goto skippause2
echo 按任意键关闭这个窗口……
pause >nul
:skippause2
exit /b 0

:fail
echo.
echo 安装没有完成。按上面的提示处理后，再双击一次「安装-Windows.bat」就行（已装好的会跳过）。
echo.
if "%SY_NOPAUSE%"=="1" goto skippause3
echo 按任意键关闭这个窗口……
pause >nul
:skippause3
exit /b 1

rem ============================================================ 子程序
:findnode
set "NODE_OK="
node -v >nul 2>nul || exit /b 0
for /f "tokens=1 delims=v." %%m in ('node -v') do if %%m GEQ 18 set "NODE_OK=1"
if not defined NODE_OK echo       现有的 Node.js 版本太旧（要 18 以上）。
exit /b 0

:findpy
set "PY="
python -c "import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)" >nul 2>nul && set "PY=python" && exit /b 0
py -3 -c "import sys" >nul 2>nul && set "PY=py -3" && exit /b 0
python3 -c "import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)" >nul 2>nul && set "PY=python3" && exit /b 0
for /d %%d in ("%LOCALAPPDATA%\Programs\Python\Python3*") do if exist "%%d\python.exe" set "PY="%%d\python.exe""
exit /b 0

:findff
set "FF_OK="
ffmpeg -hide_banner -version >nul 2>nul && set "FF_OK=1" && exit /b 0
if exist "%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe" set "FF_OK=1"
if exist "C:\ffmpeg\bin\ffmpeg.exe" set "FF_OK=1"
exit /b 0

:refreshpath
rem winget 装完后，这个窗口的 PATH 还是旧的：从注册表重新读一遍
for /f "usebackq delims=" %%P in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "[Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')"`) do set "PATH=%%P;%PATH%"
if exist "%ProgramFiles%\nodejs\node.exe" set "PATH=%ProgramFiles%\nodejs;%PATH%"
if exist "%LOCALAPPDATA%\Microsoft\WinGet\Links" set "PATH=%LOCALAPPDATA%\Microsoft\WinGet\Links;%PATH%"
exit /b 0
