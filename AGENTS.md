# 给 AI 编程助手的说明（Codex / Cursor / Claude Code 等通用）

这个仓库是「新风格 20 种」（sy-style-new20，作者 肖雄 / XIAOXIONG，MIT 协议）：20 条 10 秒纯画面短片，每一帧都由代码在无头浏览器里算出来，`make.js` 一条命令出片（画面 + 程序合成的配乐音效 + 响度标准化）。

**完整做法写在 [`skills/sy-style-new20/SKILL.md`](skills/sy-style-new20/SKILL.md)，开工前先读它，照着做。** 下面是最要紧的几条，方便你快速上手。

## 用户通常会说

- “帮我把字符画那条做出来” → `node make.js style 35`
- “20 种全部渲染” → `node make.js style all`
- “把彩色玻璃窗改成偏蓝的晨光” → 备份后改 `styles/28-stained/index.html` 里的 `SUN_COL`，`still 28 1 5 9.5 --compare` 出对比图给用户看，满意再出片

## 命令（都在仓库根目录运行）

```
node make.js check            # 先跑：检查 Node / Python / ffmpeg / 浏览器 / 字体 / 显卡
node make.js list             # 20 种：编号 21-40、中文名、英文名
node make.js still 35 5       # 出一张图 → out/35-字符画_5s.jpg
node make.js still 28 5 --compare   # 原版（index.原版.html）和修改后左右对比 → out/28-彩色玻璃窗_5s_对比.jpg
node make.js style 35         # 出成片 → out/35-字符画.mp4（编号 / 中文名 / 英文名；all = 全部）
node make.js sheet 35         # 成片抽 9 帧拼联系表
node make.js status           # 进度（也写在 out/进度.txt）
```

- 出片有显卡要几分钟到十几分钟，**放后台运行**，不要用短超时干等；中断后再跑同一条命令会接着做。
- 没有显卡时正式片要几个小时，`style` 会停下（退出码 3）并列出办法：下载 Releases 里的成片 / `--draft` 草稿 / `--cpu` 过夜跑。把这几个办法告诉用户，让他选。
- `check` 有 × 时，请用户双击 `安装-Windows.bat`（Mac：`安装-Mac.command`）重新安装，不要自己改系统设置。
- 选项：`--gpu` / `--cpu` 强制显卡或软件渲染，`--force` 重做已完成的，`--draft` 快速草稿。

## 场景的规矩

- 每个风格：`styles/NN-name/index.html`（画面）、`music.py`（配乐和专属音效）、`render.args`（`--mb N` 运动模糊子帧数）。公共库在 `lib/`，渲染器 `render.js`，声音合成 `audio/synth.py`。
- `render(t)` 必须确定性：同一个 t 永远同一张图；不用 `Math.random()` / `Date.now()` 驱动画面，用 `Reel.rng(seed)`。
- 10 秒、30fps、1920×1080 不变；节拍 120 BPM（每拍 0.5 秒）。改了动作时间就同步改 `cues` 里的 `t`。
- 字体只认 `fonts/fonts.json` 里登记的（Noto Sans CJK SC 400/500/700、Inter 500/600/700、DejaVu Sans Mono、TeX Gyre Heros Cn），渲染器自动加载，不要装进系统。
- 改之前先把 `index.html` 备份成 `index.原版.html`；改完用 `node make.js still 编号 1 5 9.5 --compare` 出“原版 / 修改后”左右对比图，亲眼看过、给用户看过，再出片。
- **改光色和改配色是两回事**：光色要乘在光进入着色的每一个地方（受光面、高光、光柱、光斑、溢光），只改一处色值，最显眼的光柱、光斑往往不变。每个风格从哪下手、哪些变量看着像其实不是，见 SKILL.md 第 7 节的对照表。26、28（`SUN_COL`）、29、30、31、34、38、40 已经有光色旋钮 `LIGHT_COL`，默认 `vec3(1.)` = 和成片一致。
- 出完片跑 `node make.js sheet 编号`，自己看一眼联系表再告诉用户。

## 和用户说话

用户多半是不懂编程的小白：简短、说人话、少提问、不贴日志。开工说要多久，做完说片子的完整路径。
