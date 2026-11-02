#!/bin/bash
# ============================================================
#  新风格 20 种（sy-style-new20）一键安装 · macOS · 作者 肖雄 / XIAOXIONG
#  双击运行。第一次如果提示“无法打开 / 来自身份不明的开发者”：
#    在访达里按住 control 点它 → 打开 → 再点“打开”；
#    或者打开“终端”，输入 bash 加一个空格，把这个文件拖进去，回车。
#  可以反复运行：已经装好的会跳过。
#  测试用：SY_SKILL_DIR=/某个/文件夹 bash 安装-Mac.command   或   --skill-dir /某个/文件夹
#  （这个脚本作者没在 Mac 上实测过，遇到问题欢迎反馈）
# ============================================================
cd "$(dirname "$0")" || exit 1
SKILL_DIR="${SY_SKILL_DIR:-}"
while [ $# -gt 0 ]; do
  case "$1" in
    --skill-dir) SKILL_DIR="$2"; shift 2 ;;
    --no-pause) SY_NOPAUSE=1; shift ;;
    *) shift ;;
  esac
done

pause_exit() {
  echo
  [ "$SY_NOPAUSE" = "1" ] || read -r -p "按回车键关闭这个窗口……" _
  exit "$1"
}
fail() {
  echo
  echo "  × $1"
  echo
  echo "安装没有完成。按上面的提示处理后，再双击一次「安装-Mac.command」就行（已装好的会跳过）。"
  pause_exit 1
}
have() { command -v "$1" >/dev/null 2>&1; }

if [ ! -f make.js ]; then
  echo "这个文件要和整个包放在一起才能用。请先把下载的压缩包全部解压，再到解压出来的文件夹里双击「安装-Mac.command」。"
  pause_exit 1
fi

echo
echo "=================================================="
echo "   新风格 20 种 · 一键安装（Mac）"
echo "   作者：肖雄 / XIAOXIONG"
echo "=================================================="
echo
echo "包的位置："
echo "   $(pwd)"
echo
echo "要装的东西：Homebrew 里的 Node.js、Python、ffmpeg，以及渲染用的浏览器。"
echo "已经装好的会自动跳过。第一次大约要 10 到 30 分钟，看网速。"
echo

# Homebrew 装在哪：Apple 芯片在 /opt/homebrew，Intel 在 /usr/local
for b in /opt/homebrew/bin/brew /usr/local/bin/brew; do
  if [ -x "$b" ]; then eval "$("$b" shellenv)"; break; fi
done
need_brew() {
  if ! have brew; then
    echo
    echo "  需要先装 Homebrew（Mac 上装软件的工具），这一步要你自己来："
    echo "  打开“终端”，粘贴下面这一整行，回车（中途会让你输入开机密码，输入时屏幕不显示，是正常的）："
    echo
    echo '    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    echo
    echo "  装好后再双击一次「安装-Mac.command」。"
    pause_exit 1
  fi
}

# ------------------------------------------------------------ 1. Node.js
echo "[1/6] 检查 Node.js ……"
node_ok() { have node && [ "$(node -p 'parseInt(process.versions.node)' 2>/dev/null || echo 0)" -ge 18 ]; }
if ! node_ok; then
  need_brew
  echo "      没找到（或版本太旧），正在用 Homebrew 安装 Node.js ……"
  brew install node || fail "Node.js 没装上。可以到 https://nodejs.org/zh-cn/download 手动下载 LTS 版安装。"
fi
node_ok || fail "Node.js 没装上。可以到 https://nodejs.org/zh-cn/download 手动下载 LTS 版安装。"
echo "      √ Node.js $(node -v)"

# ------------------------------------------------------------ 2. Python
echo "[2/6] 检查 Python ……"
PY=""
for c in /opt/homebrew/bin/python3 /usr/local/bin/python3; do
  if [ -x "$c" ] && "$c" -c 'import sys' >/dev/null 2>&1; then PY="$c"; break; fi
done
# 系统自带的 /usr/bin/python3 要先装“命令行开发工具”才能用，没装时直接调用会弹窗，所以先问一下
if [ -z "$PY" ] && xcode-select -p >/dev/null 2>&1 && /usr/bin/python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then PY=/usr/bin/python3; fi
if [ -z "$PY" ]; then
  need_brew
  echo "      没找到，正在用 Homebrew 安装 Python ……"
  brew install python@3.12 || fail "Python 没装上。"
  for c in /opt/homebrew/bin/python3 /usr/local/bin/python3 "$(brew --prefix)/opt/python@3.12/bin/python3.12"; do
    if [ -x "$c" ] && "$c" -c 'import sys' >/dev/null 2>&1; then PY="$c"; break; fi
  done
fi
[ -n "$PY" ] || fail "Python 没装上。"
echo "      √ $("$PY" --version)"

# ------------------------------------------------------------ 3. ffmpeg
echo "[3/6] 检查 ffmpeg ……"
if ! have ffmpeg; then
  need_brew
  echo "      没找到，正在用 Homebrew 安装 ffmpeg（东西比较多，要等一会儿）……"
  brew install ffmpeg || fail "ffmpeg 没装上。"
fi
have ffmpeg || fail "ffmpeg 没装上。"
echo "      √ ffmpeg 已就绪"

# ------------------------------------------------------------ 4. 渲染组件 + 浏览器
echo "[4/6] 安装渲染组件（playwright）和它用的浏览器 ……"
if ! npm install --no-audit --no-fund --loglevel=error; then
  echo "      下载失败，换国内镜像再试一次 ……"
  npm install --no-audit --no-fund --loglevel=error --registry=https://registry.npmmirror.com || fail "渲染组件下载失败（网络问题）。换个网络或稍后再试。"
fi
if ! node node_modules/playwright/cli.js install chromium; then
  echo "      浏览器下载失败，换国内镜像再试一次 ……"
  PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/playwright node node_modules/playwright/cli.js install chromium || fail "浏览器下载失败（网络问题）。换个网络或稍后再试。"
fi
echo "      √ 渲染组件和浏览器已就绪"

# ------------------------------------------------------------ 5. numpy / scipy（装进这个文件夹的 .venv，不影响系统）
echo "[5/6] 检查合成声音要用的 numpy、scipy ……"
if [ -x .venv/bin/python ] && .venv/bin/python -c 'import numpy, scipy' >/dev/null 2>&1; then
  :
elif "$PY" -c 'import numpy, scipy' >/dev/null 2>&1; then
  :
else
  echo "      没有，正在装到这个文件夹的 .venv 里 ……"
  [ -x .venv/bin/python ] || "$PY" -m venv .venv || fail "建 .venv 失败。"
  if ! .venv/bin/python -m pip install --disable-pip-version-check -q -r requirements.txt; then
    echo "      下载失败，换国内镜像再试一次 ……"
    .venv/bin/python -m pip install --disable-pip-version-check -q -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
  fi
  .venv/bin/python -c 'import numpy, scipy' >/dev/null 2>&1 || fail "numpy / scipy 没装上（网络问题）。换个网络或稍后再试。"
fi
echo "      √ numpy、scipy 已就绪"

# ------------------------------------------------------------ 6. AI 说明书 + 总检查
echo "[6/6] 安装 AI 说明书（SKILL），让 Claude Code 在任何文件夹都能找到这个包 ……"
if [ -n "$SKILL_DIR" ]; then node make.js install-skill --to "$SKILL_DIR"; else node make.js install-skill; fi || fail "SKILL 没装上。"
echo
echo "---------------------------------- 总检查 ----------------------------------"
node make.js check --installer || fail "总检查没通过，看上面打 × 的那几项。"
echo "----------------------------------------------------------------------------"
echo
echo "安装完成！"
echo
echo "下一步：打开 Claude Code，直接说一句话，比如："
echo "    帮我把字符画那条做出来"
echo "    20 种全部渲染"
echo "    把彩色玻璃窗改成偏蓝的晨光"
echo "做好的片子会放在这个文件夹里的 out 文件夹。"
echo
echo "注意：如果 Claude Code 已经开着，请关掉再打开一次，它才能看到新装的说明。"
pause_exit 0
