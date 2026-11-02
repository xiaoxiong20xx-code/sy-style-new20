#!/usr/bin/env node
// sy-style-new20 唯一入口（作者：肖雄 XIAOXIONG · MIT）
//
//   node make.js check              检查电脑上东西装齐没有
//   node make.js list               20 种风格的编号和名字
//   node make.js still 35 5         出一张图：35 号第 5 秒 → out/35-字符画_5s.jpg（可以给多个时间）
//   node make.js still 28 5 --compare  改过场景后：原版（index.原版.html）和现在左右对比 → out/28-彩色玻璃窗_5s_对比.jpg
//   node make.js style 35           出 10 秒成片 → out/35-字符画.mp4（编号 / 中文名 / 英文名都行，all = 全部 20 种）
//   node make.js sheet 35           从成片里抽 9 帧拼一张联系表 → out/35-字符画_联系表.jpg
//   node make.js status             看正在出的片子进行到哪了
//   node make.js clean              删掉临时帧（frames 文件夹），腾硬盘
//
// 可加的选项：--gpu 强制用显卡  --cpu 强制软件渲染  --force 已经做好的也重做  --draft 草稿（半分辨率、无运动模糊，快很多）
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const { spawn, spawnSync } = require('child_process');

const ROOT = __dirname;
const OUT = path.join(ROOT, 'out');
const FRAMES = path.join(ROOT, 'frames');
const IS_WIN = process.platform === 'win32';
const IS_TTY = !!process.stdout.isTTY;
const REINSTALL = IS_WIN ? '重新双击「安装-Windows.bat」' : '重新双击「安装-Mac.command」';

const argv = process.argv.slice(2);
const FLAGS = new Set(argv.filter((a) => a.startsWith('--')));
const ARGS = argv.filter((a, i) => !a.startsWith('--') && !(argv[i - 1] === '--to'));
const cmd = (ARGS.shift() || 'help').toLowerCase();

const STYLES = JSON.parse(fs.readFileSync(path.join(ROOT, 'styles', 'styles.json'), 'utf8')).styles;
const CPU_SLOW = '比显卡慢几倍到两三百倍，正式片一条要半小时到一天多';   // 软件渲染比显卡慢多少（12 线程 CPU 实测估算）

// ---------------------------------------------------------------- 小工具
const say = (...a) => console.log(...a);
const fmtDur = (ms) => {
  const s = Math.max(0, Math.round(ms / 1000));
  if (s < 60) return s + ' 秒';
  const m = Math.floor(s / 60), r = s % 60;
  if (m < 60) return m + ' 分' + (r ? ' ' + r + ' 秒' : '');
  return Math.floor(m / 60) + ' 小时 ' + (m % 60) + ' 分';
};
const fmtMin = (min) => (min < 1 ? '不到 1 分钟' : min < 90 ? '约 ' + Math.round(min) + ' 分钟' : '约 ' + (min / 60).toFixed(1) + ' 小时');
const outName = (s, suffix = '') => path.join(OUT, `${s.id}-${s.zh}${suffix}`);
const rel = (p) => path.relative(ROOT, p) || '.';
function hashFiles(files, extra = '') {
  const h = crypto.createHash('sha1');
  // 用相对路径：整个文件夹挪了位置也认得出做过的
  for (const f of files) { h.update(path.relative(ROOT, f)); try { h.update(fs.readFileSync(f)); } catch (e) { h.update('missing'); } }
  h.update(extra);
  return h.digest('hex').slice(0, 16);
}
function run(exe, args, opts = {}) {
  return spawnSync(exe, args, { encoding: 'utf8', windowsHide: true, maxBuffer: 64 * 1024 * 1024, ...opts });
}
function freeGB(p) {
  try { const st = fs.statfsSync(p); return (st.bavail * st.bsize) / 1e9; } catch (e) { return null; }
}

// ---------------------------------------------------------------- 找工具（刚装完、终端还没刷新 PATH 时也能找到）
function globDirs(dir, re) {
  try { return fs.readdirSync(dir).filter((n) => re.test(n)).map((n) => path.join(dir, n)); } catch (e) { return []; }
}
let _ff;
function findFfmpeg() {
  if (_ff !== undefined) return _ff;
  const c = [];
  if (process.env.SY_FFMPEG) c.push(process.env.SY_FFMPEG);
  c.push('ffmpeg');
  if (IS_WIN) {
    const la = process.env.LOCALAPPDATA || '';
    c.push(path.join(la, 'Microsoft', 'WinGet', 'Links', 'ffmpeg.exe'));
    for (const d of globDirs(path.join(la, 'Microsoft', 'WinGet', 'Packages'), /^Gyan\.FFmpeg/i)) for (const e of globDirs(d, /^ffmpeg-/i)) c.push(path.join(e, 'bin', 'ffmpeg.exe'));
    c.push('C:\\ffmpeg\\bin\\ffmpeg.exe', path.join(process.env.ProgramData || 'C:\\ProgramData', 'chocolatey', 'bin', 'ffmpeg.exe'));
  } else c.push('/opt/homebrew/bin/ffmpeg', '/usr/local/bin/ffmpeg', '/usr/bin/ffmpeg');
  for (const e of c) { const r = run(e, ['-hide_banner', '-version']); if (r.status === 0 && /ffmpeg version/.test(r.stdout)) return (_ff = { exe: e, ver: r.stdout.split('\n')[0].replace('ffmpeg version ', '').split(' ')[0] }); }
  return (_ff = null);
}
let _py;
function findPython() {
  if (_py !== undefined) return _py;
  const c = [];
  if (process.env.SY_PYTHON) c.push([process.env.SY_PYTHON]);
  if (IS_WIN) {
    c.push([path.join(ROOT, '.venv', 'Scripts', 'python.exe')], ['python'], ['py', '-3'], ['python3']);
    for (const d of globDirs(path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Python'), /^Python3/i).reverse()) c.push([path.join(d, 'python.exe')]);
  } else c.push([path.join(ROOT, '.venv', 'bin', 'python')], ['python3'], ['/opt/homebrew/bin/python3'], ['/usr/local/bin/python3'], ['python']);
  let bare = null;
  for (const [exe, ...pre] of c) {
    const r = run(exe, [...pre, '-c', 'import sys; print(sys.version.split()[0])'], { timeout: 30000 });
    if (r.status !== 0 || !/^3\./.test((r.stdout || '').trim())) continue;
    const ver = r.stdout.trim();
    const m = run(exe, [...pre, '-c', 'import numpy, scipy; print("ok")'], { timeout: 60000 });
    if (m.status === 0 && /ok/.test(m.stdout)) return (_py = { exe, pre, ver, ok: true });
    if (!bare) bare = { exe, pre, ver, ok: false };
  }
  return (_py = bare);
}
function playwright() {
  try { return require('playwright'); } catch (e) { return null; }
}

// ---------------------------------------------------------------- 显卡检测
const PROBE_JS = () => {
  const c = document.createElement('canvas'); c.width = 64; c.height = 64;
  const gl = c.getContext('webgl2');
  if (!gl) return { ok: false, why: 'no webgl2' };
  const e = gl.getExtension('WEBGL_debug_renderer_info');
  const name = e ? gl.getParameter(e.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
  const sh = (t, s) => { const o = gl.createShader(t); gl.shaderSource(o, s); gl.compileShader(o); return o; };
  const p = gl.createProgram();
  gl.attachShader(p, sh(gl.VERTEX_SHADER, '#version 300 es\nin vec2 a; void main(){ gl_Position = vec4(a, 0., 1.); }'));
  gl.attachShader(p, sh(gl.FRAGMENT_SHADER, '#version 300 es\nprecision highp float; out vec4 o; void main(){ float s = 0.; for (int i = 0; i < 64; i++) s += sin(float(i)); o = vec4(1., .5, .25, 1.) + s * 0.; }'));
  gl.linkProgram(p);
  if (!gl.getProgramParameter(p, gl.LINK_STATUS)) return { ok: false, name, why: 'shader' };
  gl.useProgram(p);
  const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
  gl.drawArrays(gl.TRIANGLES, 0, 3);
  const px = new Uint8Array(4); gl.readPixels(32, 32, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
  const fb = gl.createFramebuffer(); const tx = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tx);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA16F, 4, 4, 0, gl.RGBA, gl.HALF_FLOAT, null);
  gl.bindFramebuffer(gl.FRAMEBUFFER, fb); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tx, 0);
  const half = !!gl.getExtension('EXT_color_buffer_float') && gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE;
  return { ok: px[0] > 240 && px[1] > 110 && px[1] < 145, name: String(name), half };
};
async function probeBrowser(gpu) {
  const pw = playwright();
  if (!pw) return { ok: false, why: 'noplaywright' };
  const args = gpu ? ['--ignore-gpu-blocklist', '--enable-gpu-rasterization'] : ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
  if (gpu) { const a = process.env.SY_ANGLE || (IS_WIN ? 'gl' : ''); if (a && a !== 'default') args.push('--use-angle=' + a); }
  let browser;
  try {
    browser = await pw.chromium.launch({ args, timeout: 120000 });
    const page = await browser.newPage();
    let timer;
    const r = await Promise.race([page.evaluate(PROBE_JS), new Promise((res) => { timer = setTimeout(() => res({ ok: false, why: 'timeout' }), 60000); })]);
    clearTimeout(timer);   // 不清掉的话，命令做完还要白等一分钟才退出
    return r;
  } catch (e) {
    const m = String(e.message || e);
    return { ok: false, why: /Executable doesn't exist|executable.*not.*found|install/i.test(m) ? 'nochromium' : 'launch', msg: m.split('\n')[0] };
  } finally { try { if (browser) await browser.close(); } catch (e) { /* ignore */ } }
}
function noChromium() {
  say(`还不能出片：渲染用的浏览器（Chromium）还没下载。\n\n解决办法：${REINSTALL}，装完后关掉这个窗口重新打开再试。`);
  process.exit(1);
}
const isNoChromium = (lines) => /Executable doesn't exist|playwright install/i.test(lines.join('\n'));
let _gpu;
async function gpuMode(quiet) {
  if (FLAGS.has('--cpu')) return 'cpu';
  if (FLAGS.has('--gpu') || FLAGS.has('--hwgpu')) return 'gpu';
  if (_gpu) return _gpu;
  const r = await probeBrowser(true);
  if (r.why === 'nochromium') noChromium();
  const hw = r.ok && !/swiftshader|llvmpipe|software|basic render/i.test(r.name || '');
  _gpu = hw ? 'gpu' : 'cpu';
  if (!quiet) say(hw ? `显卡：${shortGpu(r.name)}（用显卡渲染）` : '没检测到能用的显卡，用软件渲染（CPU）');
  return _gpu;
}
const shortGpu = (n) => {
  // "ANGLE (NVIDIA Corporation, NVIDIA GeForce RTX 4060 Ti/PCIe/SSE2, OpenGL 4.5.0)" → "NVIDIA GeForce RTX 4060 Ti"
  const s = String(n || '').replace(/^ANGLE \(/, '').replace(/\)$/, '');
  const p = s.split(/,\s*/).filter(Boolean);
  const name = p.length >= 2 ? p[1] : p[0] || s;
  return name.replace(/\/PCIe.*|\/SSE2.*| Direct3D.*| OpenGL.*|\(0x[0-9A-F]+\)/gi, '').replace(/ANGLE Metal Renderer:\s*/i, '').trim() || s;
};

// ---------------------------------------------------------------- 风格名字
function norm(s) { return String(s).toLowerCase().replace(/[\s\-_·&]+/g, ''); }
function resolve(tokens) {
  const all = tokens.join(' ').trim();
  if (!all) return { err: '要告诉我做哪一种：编号（21-40）、中文名或英文名，比如 node make.js style 35' };
  if (/^(all|全部|全部风格|20)$/i.test(all)) return { list: STYLES.slice() };
  const one = findStyle(all);
  if (one.s) return { list: [one.s] };
  const list = [];
  for (const t of tokens.flatMap((x) => x.split(/[,，、]/)).filter(Boolean)) {
    if (/^(all|全部)$/i.test(t)) return { list: STYLES.slice() };
    const r = findStyle(t);
    if (!r.s) return { err: r.err };
    if (!list.includes(r.s)) list.push(r.s);
  }
  return { list };
}
function findStyle(tok) {
  const t = norm(tok);
  const num = t.match(/^(\d{1,2})(?:-.*)?$/);
  if (num) { const s = STYLES.find((x) => x.id === num[1].padStart(2, '0')); if (s) return { s }; }
  let hit = STYLES.filter((s) => [s.id, s.dir, s.zh, s.en, s.dir.slice(3), ...(s.alias || [])].some((n) => norm(n) === t));
  if (hit.length === 1) return { s: hit[0] };
  hit = STYLES.filter((s) => [s.zh, s.en, ...(s.alias || [])].some((n) => norm(n).includes(t) || (t.length >= 2 && t.includes(norm(n)))));
  if (hit.length === 1) return { s: hit[0] };
  if (hit.length > 1) return { err: `「${tok}」能对上好几种：${hit.map((s) => s.id + ' ' + s.zh).join('、')}。请说具体是哪一种。` };
  // 只在至少有两个字对得上时才猜（避免“不存在的名字”因为一个“字”猜成字符画）
  const score = (s) => new Set([...tok].filter((ch) => /[一-鿿]/.test(ch) && (s.zh + (s.alias || []).join('')).includes(ch))).size;
  const near = STYLES.map((s) => [s, score(s)]).filter(([, n]) => n >= 2).sort((a, b) => b[1] - a[1]).map(([s]) => s).slice(0, 4);
  return { err: `没找到「${tok}」这种风格。` + (near.length ? `你是不是想要：${near.map((s) => s.id + ' ' + s.zh).join('、')}？` : '') + '\n可以用编号（21-40）、中文名或英文名，比如：35、字符画、ascii。全部 20 种看这里：node make.js list' };
}

// ---------------------------------------------------------------- 进度文件（给 AI 和 status 命令看）
const PROG = path.join(OUT, '进度.txt');
function writeProgress(text) { try { fs.mkdirSync(OUT, { recursive: true }); fs.writeFileSync(PROG, new Date().toLocaleString() + '\n' + text + '\n'); } catch (e) { /* ignore */ } }

// ---------------------------------------------------------------- 调用渲染器
function renderJs(scene, args, onLine) {
  return new Promise((resolveP) => {
    const ff = findFfmpeg();
    const child = spawn(process.execPath, [path.join(ROOT, 'render.js'), scene, ...args], { cwd: ROOT, env: { ...process.env, SY_FFMPEG: ff ? ff.exe : 'ffmpeg' }, windowsHide: true });
    const errLines = [];
    let buf = '';
    child.stdout.on('data', (d) => { buf += d; let i; while ((i = buf.indexOf('\n')) >= 0) { const l = buf.slice(0, i).replace(/\r/g, ''); buf = buf.slice(i + 1); if (onLine) onLine(l); } });
    child.stderr.on('data', (d) => { for (const l of String(d).split(/\r?\n/)) if (l.trim()) { errLines.push(l); if (errLines.length > 40) errLines.shift(); } });
    const killer = () => { try { child.kill(); } catch (e) { /* ignore */ } };
    process.on('exit', killer);   // make.js 被关掉时顺手关掉渲染进程
    child.on('close', (code) => { process.removeListener('exit', killer); resolveP({ code, errLines }); });
  });
}
function renderArgs(s, draft) {
  const ra = path.join(ROOT, 'styles', s.dir, 'render.args');
  let a = fs.existsSync(ra) ? fs.readFileSync(ra, 'utf8').split(/\s+/).filter(Boolean) : [];
  if (draft) { const b = []; for (let i = 0; i < a.length; i++) { if (a[i] === '--mb' || a[i] === '--shutter') { i++; continue; } b.push(a[i]); } a = b; }
  return a;
}
const mbOf = (s) => { const a = renderArgs(s, false); const i = a.indexOf('--mb'); return i >= 0 ? parseInt(a[i + 1]) : 1; };
function sceneFiles(s) {
  const d = path.join(ROOT, 'styles', s.dir);
  return [path.join(d, 'index.html'), path.join(d, 'render.args'), ...['core.js', 'gl.js', 'rm.js', 'track.js', 'strokegl.js'].map((f) => path.join(ROOT, 'lib', f)), path.join(ROOT, 'fonts', 'fonts.json'), path.join(ROOT, 'render.js')];
}
function audioFiles(s) { return [path.join(ROOT, 'styles', s.dir, 'music.py'), path.join(ROOT, 'audio', 'synth.py'), path.join(ROOT, 'audio', 'make_audio.py')]; }

const MY_LOCKS = new Set();
process.on('exit', () => { for (const l of MY_LOCKS) { try { if (fs.readFileSync(l, 'utf8') === String(process.pid)) fs.rmSync(l, { force: true }); } catch (e) { /* ignore */ } } });
async function renderFrames(s, mode, draft, label) {
  const fd = path.join(FRAMES, s.id + (draft ? '_draft' : ''));
  const stamp = hashFiles(sceneFiles(s), mode + (process.env.SY_ANGLE || '') + (draft ? 'draft' : 'final'));   // 换了渲染方式就从头渲，不混用
  const sf = path.join(fd, '.stamp');
  // 同一条已经在另一个窗口里做着：不抢
  const lock = path.join(FRAMES, (s.id + (draft ? '_draft' : '')) + '.lock');
  try {
    const pid = parseInt(fs.readFileSync(lock, 'utf8'));
    if (pid && pid !== process.pid) { process.kill(pid, 0); return { code: 9, errLines: [], fd, ms: 0, busy: true }; }
  } catch (e) { /* 没有锁，或者那个进程已经不在了 */ }
  fs.mkdirSync(FRAMES, { recursive: true });
  fs.writeFileSync(lock, String(process.pid));
  MY_LOCKS.add(lock);
  let resumed = false;
  if (fs.existsSync(fd)) {
    const old = fs.existsSync(sf) ? fs.readFileSync(sf, 'utf8').trim() : '';
    if (old !== stamp) fs.rmSync(fd, { recursive: true, force: true });
    else resumed = fs.readdirSync(fd).length > 1;
  }
  fs.mkdirSync(fd, { recursive: true });
  fs.writeFileSync(sf, stamp);
  if (resumed) say('  接着上次没做完的地方继续……');
  say(mode === 'gpu' ? '  正在准备场景（第一次要编译着色器，几秒到一分钟）……' : '  正在准备场景（软件渲染第一次准备要久一点，可能几分钟）……');
  const t0 = Date.now();
  let last = 0, lastPct = -1;
  const args = ['--frames', fd, '--rs', draft ? '0.5' : '1', '--q', 'nolabel', mode === 'gpu' ? '--gpu' : '--cpu', '--progress', ...renderArgs(s, draft)];
  const r = await renderJs(path.join('styles', s.dir, 'index.html'), args, (l) => {
    const m = l.match(/^@@P (\d+) (\d+) (\d+) (\d+)/);
    if (!m) return;
    const [done, N, rendered, ms] = m.slice(1).map(Number);
    // 剩余时间：开头几帧往往比后面的轻，只按已渲帧速度估会偏乐观。
    // 前半段和实测的整条耗时（styles.json）加权，渲到一半以后才完全按实际速度；再留 10% 余量，加上配声音和合成的时间。
    const prior = (draft ? null : mode === 'gpu' ? s.gpu_frames_min : s.cpu_frames_min);
    const byRate = rendered > 0 ? (ms / rendered) * (N - done) : null;
    const byPrior = prior ? prior * 60000 * (N - done) / N : null;
    const w = Math.min(1, done / N / 0.5);
    const mixLeft = byRate === null ? byPrior : byPrior === null ? byRate : w * byRate + (1 - w) * byPrior;
    const left = mixLeft === null ? null : mixLeft * 1.1 + (mode === 'gpu' ? 40000 : 70000);
    const pct = Math.floor((done / N) * 100);
    const line = `${label} 画面 ${done}/${N} 帧（${pct}%）· 已用 ${fmtDur(Date.now() - t0)}` + (left !== null && done < N ? ` · 预计还要 ${fmtDur(left)}（含配声音）` : '');
    const now = Date.now();
    if (IS_TTY) { if (now - last > 500 || done === N) { process.stdout.write('\r' + line.padEnd(78)); last = now; } }
    else if (pct >= lastPct + 10 || now - last > 120000 || done === N) { say(line); lastPct = pct - (pct % 10); last = now; }
    if (now - (renderFrames._w || 0) > 3000 || done === N) { renderFrames._w = now; writeProgress(`正在做 ${s.id} ${s.zh}：${line}`); }
  });
  if (IS_TTY) process.stdout.write('\n');
  return { ...r, fd, ms: Date.now() - t0 };
}

// ---------------------------------------------------------------- 声音 + 合成
function ff(args, what, opts = {}) {
  const f = findFfmpeg();
  const r = run(f.exe, args, opts);
  if (r.status !== 0) throw new Error(`ffmpeg ${what}失败：` + String(r.stderr || '').trim().split('\n').slice(-3).join(' '));
  return r;
}
function makeAudio(s, fd, mode) {
  return (async () => {
    const cues = path.join(ROOT, 'styles', s.dir, 'cues.json');
    const rc = await renderJs(path.join('styles', s.dir, 'index.html'), ['--cues', cues, '--rs', '0.25', mode === 'gpu' ? '--gpu' : '--cpu']);
    if (rc.code !== 0) throw new Error('导出音效时间点失败：' + rc.errLines.slice(-3).join(' | '));
    const py = findPython();
    const raw = path.join(fd, 'audio_raw.wav'), wav = path.join(fd, 'audio.wav');
    const r = run(py.exe, [...py.pre, path.join(ROOT, 'audio', 'make_audio.py'), path.join(ROOT, 'styles', s.dir), s.id, cues, raw], { env: { ...process.env, PYTHONIOENCODING: 'utf-8' } });
    if (r.status !== 0) throw new Error('合成声音失败：' + String(r.stderr || r.stdout).trim().split('\n').slice(-4).join(' | '));
    // 两遍 loudnorm：-15 LUFS，真峰值 ≤ -1.5 dBTP（AAC 编码后仍 ≤ -1）
    const m = ff(['-hide_banner', '-i', raw, '-af', 'loudnorm=I=-15:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], '测响度');
    const e = m.stderr; const j = JSON.parse(e.slice(e.lastIndexOf('{'), e.lastIndexOf('}') + 1));
    const af = `loudnorm=I=-15:TP=-1.5:LRA=11:measured_I=${j.input_i}:measured_TP=${j.input_tp}:measured_LRA=${j.input_lra}` +
      `:measured_thresh=${j.input_thresh}:offset=${j.target_offset}:linear=true,aresample=48000`;
    ff(['-y', '-v', 'error', '-i', raw, '-af', af, '-ar', '48000', wav], '调响度');
    return wav;
  })();
}
function mux(fd, wav, out, scale) {
  fs.mkdirSync(path.dirname(out), { recursive: true });
  // jpg 帧是全范围（pc），转成普通视频的 tv 范围；5 毫秒音频淡入，避免第 0 个采样满音量起跳
  const vf = (scale ? 'scale=1920:1080:flags=lanczos:' : 'scale=') + 'in_range=pc:out_range=tv';
  ff(['-y', '-v', 'error', '-framerate', '30', '-i', path.join(fd, 'f%05d.jpg'), '-i', wav, '-vf', vf,
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-color_range', 'tv',
    '-af', 'afade=t=in:d=0.005', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', out], '合成视频');
}
function loudness(f) {
  const r = run(findFfmpeg().exe, ['-hide_banner', '-nostats', '-i', f, '-af', 'ebur128=peak=true', '-f', 'null', '-']);
  const i = [...String(r.stderr).matchAll(/I:\s+(-?[\d.]+) LUFS/g)].pop(), p = [...String(r.stderr).matchAll(/Peak:\s+(-?[\d.]+) dBFS/g)].pop();
  return { I: i ? parseFloat(i[1]) : NaN, TP: p ? parseFloat(p[1]) : NaN };
}

// ---------------------------------------------------------------- 预检（出片前）
function preflight(needPython) {
  const bad = [];
  if (!playwright()) bad.push('渲染组件（playwright）还没装');
  if (!findFfmpeg()) bad.push('ffmpeg 还没装（或装了但找不到）');
  if (needPython) { const p = findPython(); if (!p) bad.push('Python 还没装'); else if (!p.ok) bad.push('Python 缺 numpy / scipy'); }
  const g = freeGB(ROOT);
  if (g !== null && g < 2) bad.push(`硬盘剩余空间只有 ${g.toFixed(1)} GB，至少要留 2 GB（可以先运行 node make.js clean 删掉临时帧）`);
  if (bad.length) {
    say('还不能出片：\n' + bad.map((b) => '  × ' + b).join('\n'));
    say(`\n解决办法：${REINSTALL}，装完后关掉这个窗口重新打开再试。想看详细情况：node make.js check`);
    process.exit(1);
  }
}

// ---------------------------------------------------------------- 显卡出问题时
const altAngles = () => (IS_WIN && !process.env.SY_ANGLE ? ['d3d11', 'vulkan'] : []);
const why = (fr) => (fr.errLines.find((l) => /加载失败|出错|超时|帧不完整/.test(l)) || fr.errLines.slice(-1)[0] || '原因不明').slice(0, 120);
function cpuGuard(list, reason) {
  const ids = list.map((s) => s.id).join(' ');
  const cpu = list.reduce((a, s) => a + (s.cpu_min || 600), 0), dr = list.reduce((a, s) => a + (s.cpu_draft_min || 30), 0);
  say(`\n${reason}。不用显卡、用软件渲染（CPU）出正式片非常慢：${list.length > 1 ? `这 ${list.length} 条` : list[0].zh + '这一条'}${fmtMin(cpu)}（有显卡的电脑${fmtMin(list.reduce((a, s) => a + (s.gpu_min || 5), 0))}）。`);
  say('可以这样：');
  say('  1. 直接下载做好的 20 条成片：GitHub 页面右边 Releases → new-styles-20.zip（README 第一屏有说明）');
  say(`  2. 先出草稿看动起来的效果（半分辨率、无运动模糊）：node make.js style ${ids} --draft，${fmtMin(dr)}`);
  say(`  3. 确定要用软件渲染出正式片（可以过夜跑，中断了能接着做）：node make.js style ${ids} --cpu`);
  writeProgress(`${reason}，没有开始。见 make.js 的提示（下载成片 / --draft 草稿 / --cpu 软件渲染）`);
  process.exit(3);
}

// ---------------------------------------------------------------- 命令：style
async function cmdStyle() {
  const r = resolve(ARGS);
  if (r.err) { say(r.err); process.exit(2); }
  preflight(true);
  const draft = FLAGS.has('--draft');
  let mode = await gpuMode();
  // 没有显卡时正式片要几个小时：不悄悄开始，先说清楚（明确加了 --cpu 才做）
  if (mode === 'cpu' && !draft && !FLAGS.has('--cpu')) cpuGuard(r.list, '没检测到能用的显卡');
  const total = r.list.length, results = [];
  const estOf = (s) => (draft ? (mode === 'gpu' ? 1 : s.cpu_draft_min) : mode === 'gpu' ? s.gpu_min : s.cpu_min) || 10;
  if (total > 1) say(`一共 ${total} 条，全部做完${fmtMin(r.list.reduce((a, s) => a + estOf(s), 0))}。中途关掉也没关系，再运行同一条命令会接着做。\n`);
  for (const [k, s] of r.list.entries()) {
    const label = total > 1 ? `[${k + 1}/${total}] ${s.id} ${s.zh}` : `${s.id} ${s.zh}`;
    const out = outName(s, draft ? '_草稿.mp4' : '.mp4');
    const doneStamp = path.join(OUT, '.done', s.id + (draft ? '_draft' : '') + '.txt');
    const want = hashFiles([...sceneFiles(s), ...audioFiles(s)], draft ? 'draft' : 'final');
    if (!FLAGS.has('--force') && fs.existsSync(out) && fs.existsSync(doneStamp) && fs.readFileSync(doneStamp, 'utf8').trim() === want) {
      say(`${label}：已经做好了（画面没改过），在 ${out}。要重做加 --force`);
      results.push({ s, out, skipped: true }); continue;
    }
    say(`\n→ ${label}（${s.en}）开始` + (draft ? '：草稿（半分辨率、无运动模糊）' : '') + `，${mode === 'gpu' ? '用显卡' : '软件渲染'}${fmtMin(estOf(s))}` + (mode === 'cpu' && !draft && s.gpu_min ? `（有显卡的电脑${fmtMin(s.gpu_min)}）` : ''));
    const t0 = Date.now();
    try {
      let fr = await renderFrames(s, mode, draft, label);
      if (fr.busy) {
        say(`  ${label} 正在另一个窗口里做，这里先跳过（node make.js status 看进度；如果确定没有在做，运行 node make.js clean 后再来）`);
        results.push({ s, err: '正在另一个窗口里做' }); continue;
      }
      if (fr.code !== 0 && isNoChromium(fr.errLines)) noChromium();
      if (fr.code !== 0 && mode === 'gpu') {
        // 显卡出问题：先换别的显卡接口（Windows：d3d11、vulkan）再试，都不行才考虑软件渲染
        for (const alt of altAngles()) {
          say(`  显卡渲染没成功（${why(fr)}），换一种显卡接口（${alt}）再试……`);
          process.env.SY_ANGLE = alt;
          fr = await renderFrames(s, mode, draft, label);
          if (fr.code === 0) break;
        }
        if (fr.code !== 0 && !FLAGS.has('--gpu')) {
          say(`  显卡渲染还是没成功（${why(fr)}）。`);
          if (!draft) cpuGuard(r.list.slice(k), '显卡渲染出错');
          say('  草稿改用软件渲染重来……');
          mode = 'cpu'; _gpu = 'cpu';
          fr = await renderFrames(s, mode, draft, label);
        }
      }
      if (fr.code !== 0) throw new Error('渲染画面失败：\n    ' + fr.errLines.slice(-8).join('\n    '));
      say('  画面做完，正在配声音……');
      const wav = await makeAudio(s, fr.fd, mode);
      say('  正在合成视频……');
      mux(fr.fd, wav, out, draft);
      const L = loudness(out);
      const ok = Math.abs(L.I + 15) <= 0.5 && L.TP <= -1;
      fs.mkdirSync(path.dirname(doneStamp), { recursive: true }); fs.writeFileSync(doneStamp, want);
      fs.rmSync(fr.fd, { recursive: true, force: true });   // 临时帧删掉，不占硬盘
      say(`√ ${label} 做好了：${out}`);
      say(`  10 秒 · 1920×1080 · 响度 ${L.I.toFixed(1)} LUFS（目标 -15）· 真峰值 ${L.TP.toFixed(1)} dBTP（要求 ≤ -1）${ok ? ' √' : ' ! 响度不在范围内'} · 用时 ${fmtDur(Date.now() - t0)}`);
      results.push({ s, out, ok, L });
      writeProgress(`${label} 做好了：${out}` + (k + 1 < total ? `\n接下来还有 ${total - k - 1} 条` : ''));
    } catch (e) {
      say(`× ${label} 没做成：${e.message}`);
      say(`  已经渲好的帧留在 ${rel(path.join(FRAMES, s.id + (draft ? '_draft' : '')))}，再运行同一条命令会接着做。`);
      results.push({ s, err: e.message });
      writeProgress(`${label} 没做成：${e.message.split('\n')[0]}`);
    }
  }
  const bad = results.filter((x) => x.err);
  if (total > 1) {
    say(`\n完成 ${total - bad.length}/${total} 条，片子都在 ${OUT}`);
    if (bad.length) say('没做成的：' + bad.map((x) => x.s.id + ' ' + x.s.zh).join('、') + '（再运行一次同样的命令会接着做）');
  }
  writeProgress(bad.length ? `结束：${bad.length} 条没做成，见上面的提示` : `全部完成，片子在 ${OUT}`);
  process.exit(bad.length ? 1 : 0);
}

// ---------------------------------------------------------------- 命令：still
async function cmdStill() {
  const times = [];
  while (ARGS.length > 1 && /^\d+(\.\d+)?s?$/.test(ARGS[ARGS.length - 1])) times.unshift(parseFloat(ARGS.pop()));
  const r = resolve(ARGS);
  if (r.err) { say(r.err); process.exit(2); }
  preflight(false);
  if (!times.length) times.push(5);
  if (times.some((t) => t < 0 || t > 10)) { say('时间要在 0 到 10 秒之间（每条片子 10 秒）'); process.exit(2); }
  let mode = await gpuMode();
  for (const s of r.list) {
    const files = times.map((t) => outName(s, `_${t}s.jpg`));
    const args = ['--rs', '1', '--q', 'nolabel', mode === 'gpu' ? '--gpu' : '--cpu', ...times.flatMap((t, i) => ['--still', `${t}:${files[i]}`])];
    const t0 = Date.now();
    say(`${s.id} ${s.zh}：正在出图（${mode === 'gpu' ? '显卡' : '软件渲染，第一次准备可能要几分钟'}）……`);
    let rr = await renderJs(path.join('styles', s.dir, 'index.html'), args);
    if (rr.code !== 0 && isNoChromium(rr.errLines)) noChromium();
    if (rr.code !== 0 && mode === 'gpu') {
      for (const alt of altAngles()) {
        say(`  显卡出图没成功，换一种显卡接口（${alt}）再试……`);
        process.env.SY_ANGLE = alt;
        rr = await renderJs(path.join('styles', s.dir, 'index.html'), args);
        if (rr.code === 0) break;
      }
      if (rr.code !== 0 && !FLAGS.has('--gpu')) { say('  显卡出图还是没成功，改用软件渲染重试（一张图一般几秒到几分钟）……'); mode = 'cpu'; _gpu = 'cpu'; rr = await renderJs(path.join('styles', s.dir, 'index.html'), args.map((a) => (a === '--gpu' ? '--cpu' : a))); }
    }
    if (rr.code !== 0) { say('× 出图失败：\n    ' + rr.errLines.slice(-8).join('\n    ')); process.exit(1); }
    files.forEach((f) => say('√ ' + f));
    if (FLAGS.has('--compare')) await compareStills(s, times, files, mode);
    say(`  用时 ${fmtDur(Date.now() - t0)}`);
  }
}

// 原版（index.原版.html）和现在的版本同一时刻左右拼一张对比图 → out/NN-名_Ts_对比.jpg
async function compareStills(s, times, files, mode) {
  const origRel = path.join('styles', s.dir, 'index.原版.html');
  if (!fs.existsSync(path.join(ROOT, origRel))) {
    say(`  没找到原版备份（${origRel}），没法对比。改之前先把 index.html 复制一份，名字叫 index.原版.html。`);
    return;
  }
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'cmp-'));
  const of = times.map((t, i) => path.join(tmp, `o${i}.jpg`));
  say('  正在出原版的图做对比……');
  const rr = await renderJs(origRel, ['--rs', '1', '--q', 'nolabel', mode === 'gpu' ? '--gpu' : '--cpu', ...times.flatMap((t, i) => ['--still', `${t}:${of[i]}`])]);
  if (rr.code !== 0) { say('  原版出图失败，对比图没做成：' + rr.errLines.slice(-3).join(' | ')); fs.rmSync(tmp, { recursive: true, force: true }); return; }
  const tag = (lab) => `scale=1280:720:flags=lanczos,drawbox=x=0:y=0:w=${lab.length * 40 + 48}:h=66:color=black@0.6:t=fill,` +
    `drawtext=fontfile=NotoSansCJKsc-Bold.otf:text=${lab}:x=24:y=12:fontsize=40:fontcolor=white`;
  times.forEach((t, i) => {
    const out = outName(s, `_${t}s_对比.jpg`);
    // 在 fonts 文件夹里运行，字体用相对路径（Windows 盘符的冒号在滤镜里要转义，这样最省事）
    ff(['-y', '-v', 'error', '-i', of[i], '-i', files[i], '-filter_complex',
      `[0:v]${tag('原版')}[a];[1:v]${tag('修改后')}[b];[a][b]hstack=inputs=2`, '-q:v', '3', out], '拼对比图', { cwd: path.join(ROOT, 'fonts') });
    say('√ ' + out + '（左：原版，右：修改后）');
  });
  fs.rmSync(tmp, { recursive: true, force: true });
}

// ---------------------------------------------------------------- 命令：sheet（联系表）
function cmdSheet() {
  const r = resolve(ARGS);
  if (r.err) { say(r.err); process.exit(2); }
  if (!findFfmpeg()) { say('找不到 ffmpeg，' + REINSTALL); process.exit(1); }
  for (const s of r.list) {
    const src = [outName(s, '.mp4'), outName(s, '_草稿.mp4')].find((f) => fs.existsSync(f));
    if (!src) { say(`${s.id} ${s.zh} 还没出片，先运行 node make.js style ${s.id}`); continue; }
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'sheet-'));
    const ts = Array.from({ length: 9 }, (_, k) => 0.3 + k * 1.15);
    ts.forEach((t, k) => ff(['-y', '-v', 'error', '-ss', String(t), '-i', src, '-frames:v', '1', '-vf', 'scale=640:360', '-q:v', '3', path.join(tmp, `${k}.jpg`)], '抽帧'));
    const out = outName(s, '_联系表.jpg');
    ff(['-y', '-v', 'error', '-i', path.join(tmp, '%d.jpg'), '-frames:v', '1', '-vf', 'tile=3x3:padding=6:color=white', '-q:v', '3', out], '拼图');
    fs.rmSync(tmp, { recursive: true, force: true });
    say(`√ ${out}（9 帧：${ts.map((t) => t.toFixed(1) + 's').join(' ')}）`);
  }
}

// ---------------------------------------------------------------- 命令：list
function cmdList() {
  say('编号  中文名        英文名               一句话');
  for (const s of STYLES) say(`${s.id}    ${s.zh.padEnd(6, '　')}  ${s.en.padEnd(19)}  ${s.desc}`);
  say('\n用法：node make.js style 35（或 字符画 / ascii）；all = 全部 20 种。先看一张图：node make.js still 35 5');
}

// ---------------------------------------------------------------- 命令：check
async function cmdCheck() {
  say('检查出片需要的东西……\n');
  let bad = 0;
  const line = (ok, name, msg, fix) => { say(`  ${ok ? '√' : '×'} ${name}：${msg}`); if (!ok) { bad++; if (fix) say(`      怎么办：${fix}`); } };
  const nv = parseInt(process.versions.node);
  line(nv >= 18, 'Node.js', 'v' + process.versions.node + (nv >= 18 ? '' : '（太旧，要 18 以上）'), REINSTALL);
  const py = findPython();
  if (!py) line(false, 'Python', '没找到', REINSTALL + '（装完关掉窗口重开）');
  else line(py.ok, 'Python', `${py.ver}` + (py.ok ? '，numpy / scipy 都在' : '，但缺 numpy / scipy'), REINSTALL);
  const f = findFfmpeg();
  if (!f) line(false, 'ffmpeg', '没找到', REINSTALL + '（装完关掉窗口重开）');
  else {
    const x = run(f.exe, ['-hide_banner', '-h', 'encoder=libx264']);
    line(/libx264/.test(x.stdout || ''), 'ffmpeg', f.ver + (/libx264/.test(x.stdout || '') ? '' : '（这个版本不带 libx264 编码器，换一个完整版）'), REINSTALL);
  }
  const pw = playwright();
  if (!pw) line(false, '渲染组件', 'playwright 没装', REINSTALL);
  else {
    const c = await probeBrowser(false);
    if (c.ok) line(true, 'Chromium', `能用（playwright ${require('playwright/package.json').version}，软件渲染正常）`);
    else line(false, 'Chromium', c.why === 'nochromium' ? '浏览器还没下载' : '打不开：' + (c.msg || c.why), REINSTALL);
  }
  let fonts = [];
  try { fonts = JSON.parse(fs.readFileSync(path.join(ROOT, 'fonts', 'fonts.json'), 'utf8')).faces; } catch (e) { /* */ }
  const miss = fonts.filter((x) => !fs.existsSync(path.join(ROOT, 'fonts', x.file)));
  line(fonts.length > 0 && !miss.length, '字体', miss.length ? '缺 ' + miss.map((x) => x.file).join('、') : `${fonts.length} 个字体文件都在（渲染时自动加载，不用装进系统）`, '重新下载完整的包（fonts 文件夹不能少）');
  if (pw) {
    const g = await probeBrowser(true);
    const hw = g.ok && !/swiftshader|llvmpipe|software|basic render/i.test(g.name || '');
    if (g.why === 'nochromium') say('  · 显卡：等浏览器装好后才能检测');
    else say(`  ${hw ? '√' : '·'} 显卡：${hw ? shortGpu(g.name) + '，出片会用它' : '没检测到能用的显卡' + (g.name ? `（${shortGpu(g.name)}）` : '') + `。也能出片，用软件渲染，${CPU_SLOW}（详见 README 的耗时表）`}`);
  }
  const gb = freeGB(ROOT);
  if (gb !== null) line(gb >= 2, '硬盘', `这个盘还剩 ${gb.toFixed(1)} GB` + (gb >= 2 ? '' : '（至少要留 2 GB）'), '清理一下硬盘，或者把整个文件夹挪到空间大的盘');
  say(`\n包的位置：${ROOT}`);
  if (bad) { say(`\n有 ${bad} 项没准备好。按上面「怎么办」处理，然后再运行 node make.js check`); process.exit(1); }
  say('\n全部就绪，可以出片了。');
  if (FLAGS.has('--installer')) return;   // 安装程序自己会印“下一步”，这里不重复
  say('下一步：打开 Claude Code（或别的 AI 编程助手），说一句「帮我把字符画那条做出来」或「20 种全部渲染」。');
  say('自己动手也行：node make.js list 看名字，node make.js style 35 出片。');
}

// ---------------------------------------------------------------- 命令：install-skill（安装程序调用）
function cmdInstallSkill() {
  const i = argv.indexOf('--to');
  let to = path.resolve(i >= 0 && argv[i + 1] ? argv[i + 1] : process.env.SY_SKILL_DIR || path.join(os.homedir(), '.claude', 'skills', 'sy-style-new20'));
  // Claude Code 按文件夹名认技能：给的文件夹不叫 sy-style-new20（比如只给了 …\skills），就在下面补一层
  if (path.basename(to).toLowerCase() !== 'sy-style-new20') to = path.join(to, 'sy-style-new20');
  const src = path.join(ROOT, 'skills', 'sy-style-new20', 'SKILL.md');
  const txt = fs.readFileSync(src, 'utf8').split('{{PACKAGE_DIR}}').join(ROOT);
  fs.mkdirSync(to, { recursive: true });
  fs.writeFileSync(path.join(to, 'SKILL.md'), txt);
  say(`√ AI 说明书（SKILL）已装到：${to}`);
  say(`  里面写好了包的位置：${ROOT}`);
}

// ---------------------------------------------------------------- 命令：status / clean / help
function cmdStatus() {
  if (fs.existsSync(PROG)) say(fs.readFileSync(PROG, 'utf8').trim()); else say('现在没有正在出的片子。');
  const done = STYLES.filter((s) => fs.existsSync(outName(s, '.mp4')));
  say(`\nout 文件夹里已有 ${done.length}/20 条成片` + (done.length ? '：' + done.map((s) => s.id + ' ' + s.zh).join('、') : ''));
}
function cmdClean() {
  if (!fs.existsSync(FRAMES)) { say('没有临时帧，不用清理。'); return; }
  for (const f of fs.readdirSync(FRAMES).filter((n) => n.endsWith('.lock'))) {
    try { const pid = parseInt(fs.readFileSync(path.join(FRAMES, f), 'utf8')); if (pid && pid !== process.pid) { process.kill(pid, 0); say(`有片子正在做（${f.replace('.lock', '')} 号），先等它做完或关掉那个窗口，再清理。`); return; } } catch (e) { /* 进程不在了 */ }
  }
  let n = 0; const walk = (d) => { for (const e of fs.readdirSync(d, { withFileTypes: true })) { const p = path.join(d, e.name); if (e.isDirectory()) walk(p); else n += fs.statSync(p).size; } }; walk(FRAMES);
  fs.rmSync(FRAMES, { recursive: true, force: true });
  say(`√ 删掉了临时帧 ${(n / 1e9).toFixed(2)} GB（没做完的片子下次要从头渲）。成片在 out 文件夹，没动。`);
}
function cmdHelp() {
  say(`sy-style-new20 · 新风格 20 种（作者 肖雄 XIAOXIONG）

  node make.js check            检查电脑上东西装齐没有
  node make.js list             20 种风格的编号和名字
  node make.js still 35 5       出一张图（35 号第 5 秒）→ out/35-字符画_5s.jpg
  node make.js still 28 5 --compare   原版和修改后左右对比 → out/28-彩色玻璃窗_5s_对比.jpg
  node make.js style 35         出 10 秒成片 → out/35-字符画.mp4
  node make.js style all        20 种全部出片（中断后再运行会接着做）
  node make.js sheet 35         从成片抽 9 帧拼联系表
  node make.js status           看进行到哪了
  node make.js clean            删临时帧腾硬盘

风格可以写编号、中文名或英文名：35 / 字符画 / ascii。
选项：--gpu 强制显卡  --cpu 强制软件渲染  --force 已做好的也重做  --draft 快速草稿`);
}

// ---------------------------------------------------------------- 入口
process.on('SIGINT', () => { say('\n已停下。再运行同一条命令会从停下的地方接着做。'); process.exit(130); });
(async () => {
  try {
    if (cmd === 'style' || cmd === 'render') await cmdStyle();
    else if (cmd === 'still') await cmdStill();
    else if (cmd === 'list') cmdList();
    else if (cmd === 'check') await cmdCheck();
    else if (cmd === 'sheet') cmdSheet();
    else if (cmd === 'status') cmdStatus();
    else if (cmd === 'clean') cmdClean();
    else if (cmd === 'install-skill') cmdInstallSkill();
    else if (cmd === 'help' || cmd === '-h' || cmd === '--help') cmdHelp();
    else { say(`不认识「${cmd}」这个命令。\n`); cmdHelp(); process.exit(2); }
    process.exit(0);
  } catch (e) { say('出错了：' + (e && e.message || e)); process.exit(1); }
})();
