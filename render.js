// 逐帧渲染器：用无头 Chromium 打开一个场景（styles/NN-name/index.html），按时间一帧一帧截图。
// 平时不用直接运行它，用 make.js（node make.js style 35）。给 AI / 想深入的人看的用法：
//
//   node render.js styles/35-ascii/index.html --frames frames/35 --mb 12 --gpu   逐帧渲染到文件夹（f00000.jpg …）
//   node render.js styles/35-ascii/index.html --still 5:out/a.jpg --still 9:out/b.jpg   出单帧
//   node render.js styles/35-ascii/index.html --cues styles/35-ascii/cues.json    导出场景里的音效时间点
//
// 参数：
//   --gpu / --cpu     用显卡（快）或软件渲染 SwiftShader（哪里都能跑，慢）；默认 --cpu。旧名 --hwgpu 也认。
//   --mb N            每帧 N 个子帧叠出运动模糊（场景的 render.args 里写好了）；--shutter 快门（默认 0.5）
//   --rs 0.5          渲染缩放（0.5 = 960×540 草稿）
//   --from / --to     只渲染一段（秒）
//   --progress        每帧打印一行机器可读的进度（make.js 用）
//
// 内置两件事（不需要设任何环境变量）：
//   1) 字体：fonts/fonts.json 里登记的字体文件，每个页面打开时自动加载（不装进系统）。
//   2) 显卡：Windows 上 --gpu 走 ANGLE 的 OpenGL 后端（d3d11 后端遇到部分着色器会卡死）。想换：设 SY_ANGLE=d3d11 / vulkan。
//
// 中断续跑：已经写好的帧（完整的 JPEG）会保留，再跑同一条命令会接着往下渲。
// 运动模糊：子帧每凑够一小批就用 ffmpeg 平均成正式帧并删掉，硬盘上不会堆几千张子帧。
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const { pathToFileURL } = require('url');

const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const has = (k) => argv.includes('--' + k);
const html = path.resolve(argv[0] || '');
const q = opt('q', 'nolabel');
const stills = argv.filter((a, i) => argv[i - 1] === '--still');
const rs = parseFloat(opt('rs', '1'));
const framesDir = opt('frames', '');
const cuesOut = opt('cues', '');
const PROGRESS = has('progress');
const FFMPEG = process.env.SY_FFMPEG || 'ffmpeg';
const VW = Math.round(1920 * rs), VH = Math.round(1080 * rs);
const USE_GPU = has('gpu') || has('hwgpu');

function die(code, msg) { console.error(msg); process.exit(code); }
if (!argv[0] || !fs.existsSync(html)) die(2, '找不到场景文件：' + (argv[0] || '（没给）'));

// ---------- fonts (fonts/fonts.json) ----------
function fontFaces() {
  const dir = path.join(__dirname, 'fonts');
  let list = [];
  try { list = JSON.parse(fs.readFileSync(path.join(dir, 'fonts.json'), 'utf8')).faces || []; } catch (e) { console.error('[字体] 读不到 fonts/fonts.json：' + e.message); }
  const out = [];
  for (const f of list) {
    const p = path.join(dir, f.file);
    if (!fs.existsSync(p)) { console.error('[字体] 缺文件 fonts/' + f.file + '（这个字体会被系统字体代替，画面可能不一样）'); continue; }
    out.push({ fam: f.family, url: pathToFileURL(p).href, weight: String(f.weight || 400), style: f.style || 'normal' });
  }
  return out;
}
const initFonts = (list) => {
  for (const f of list) {
    try { document.fonts.add(new FontFace(f.fam, `url("${f.url}")`, { weight: f.weight, style: f.style })); } catch (e) { /* ignore */ }
  }
};

// ---------- browser ----------
function launchArgs() {
  const gpu = USE_GPU
    ? ['--ignore-gpu-blocklist', '--enable-gpu-rasterization']
    : ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
  const extra = ['--font-render-hinting=none', '--disable-lcd-text', '--force-color-profile=srgb', '--hide-scrollbars', '--allow-file-access-from-files'];
  if (USE_GPU) {
    const angle = process.env.SY_ANGLE || (process.platform === 'win32' ? 'gl' : '');
    if (angle && angle !== 'default') extra.push('--use-angle=' + angle);
  }
  return [...gpu, ...extra];
}

const flushOut = () => new Promise((r) => process.stdout.write('', () => r()));
// 超时保护（计时器用完要清掉，不然进程会一直挂着等它）
function withTimeout(p, ms, what) {
  if (!(ms > 0)) return p;
  let timer;
  return Promise.race([p, new Promise((_, rej) => { timer = setTimeout(() => rej(new Error('超时：' + what)), ms); })]).finally(() => clearTimeout(timer));
}

(async () => {
  const browser = await chromium.launch({ args: launchArgs() });
  const ctx = await browser.newContext({ viewport: { width: VW, height: VH }, deviceScaleFactor: 1 });
  await ctx.addInitScript(initFonts, fontFaces());
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', (m) => { if (m.type() === 'error') { errs.push(m.text()); console.error('[page]', m.text()); } });
  page.on('pageerror', (e) => { errs.push(e.message); console.error('[pageerror]', e.message); });
  // 显卡模式下着色器编译卡死时要能退出，让 make.js 换软件渲染重来；软件渲染只是慢，给足时间
  const LOAD_MS = parseInt(process.env.SY_LOAD_TIMEOUT || (USE_GPU ? '240000' : '1800000'));
  page.setDefaultTimeout(LOAD_MS);
  const fail = async (code, msg) => {
    console.error(msg);
    try { await Promise.race([browser.close(), new Promise((r) => setTimeout(r, 15000))]); } catch (e) { /* 卡死的浏览器关不掉也照样退出 */ }
    process.exit(code);
  };

  try {
    await page.goto(pathToFileURL(html).href + '?render=1&rs=' + rs + (q ? '&' + q : ''), { timeout: LOAD_MS });
    if (cuesOut) {
      await page.waitForFunction(() => Array.isArray(window.__cues), null, { timeout: LOAD_MS });
      const cues = await page.evaluate(() => window.__cues.map((c) => Object.assign({}, c)));
      fs.mkdirSync(path.dirname(path.resolve(cuesOut)), { recursive: true });
      fs.writeFileSync(cuesOut, JSON.stringify(cues));
      console.log('cues', cues.length, cuesOut);
      await browser.close(); await flushOut(); process.exit(0);
    }
    await page.waitForFunction(() => typeof window.__seek === 'function', null, { timeout: LOAD_MS });
    // 第一次 seek 会等 setup（生成纹理、编译着色器）做完
    await withTimeout(page.evaluate(() => window.__seek(0)), LOAD_MS, '场景准备（setup）');
  } catch (e) {
    return fail(3, '[加载失败] ' + e.message.split('\n')[0] + (errs.length ? '\n  页面报错：' + errs.slice(-3).join(' | ') : ''));
  }

  const dur = await page.evaluate(() => window.__duration);
  const fps = await page.evaluate(() => window.__fps);
  const hasKey = await page.evaluate(() => typeof window.__frameKey === 'function');

  if (stills.length) {
    for (const s of stills) {
      const k = s.indexOf(':'); const t = s.slice(0, k), f = s.slice(k + 1);   // 只按第一个冒号切（Windows 路径里还有冒号）
      fs.mkdirSync(path.dirname(path.resolve(f)), { recursive: true });
      await page.evaluate((tt) => window.__seek(tt), parseFloat(t));
      await page.screenshot({ path: f, type: 'jpeg', quality: 95, animations: 'disabled', caret: 'hide', timeout: 0 });
      console.log('still', t, f);
    }
    await browser.close(); await flushOut(); process.exit(0);
  }
  if (!framesDir) return fail(2, '要给 --frames 文件夹、--still 时间:文件 或 --cues 文件');

  const from = parseFloat(opt('from', 0)), to = parseFloat(opt('to', dur));
  const n0 = Math.round(from * fps), n1 = Math.round(to * fps), N = n1 - n0;
  fs.mkdirSync(framesDir, { recursive: true });
  // --mb N：每帧在 180° 快门（--shutter）内取 N 个子帧，每个带一点亚像素抖动（Halton 2,3），平均后 = 运动模糊 + 抗锯齿
  const MB = Math.max(1, parseInt(opt('mb', '1'))), SH = parseFloat(opt('shutter', '0.5'));
  const halton = (i, b) => { let f = 1, r = 0; while (i > 0) { f /= b; r += f * (i % b); i = Math.floor(i / b); } return r; };
  const subDir = path.join(framesDir, '_sub');
  if (MB > 1) fs.mkdirSync(subDir, { recursive: true });
  const fname = (n) => path.join(framesDir, `f${String(n).padStart(5, '0')}.jpg`);
  const sname = (n, k) => path.join(subDir, `s${String((n - n0) * MB + k).padStart(6, '0')}.jpg`);
  const okJpg = (f) => { try { const st = fs.statSync(f); if (st.size < 1000) return false; const fd = fs.openSync(f, 'r'); const b = Buffer.alloc(2); fs.readSync(fd, b, 0, 2, st.size - 2); fs.closeSync(fd); return b[0] === 0xff && b[1] === 0xd9; } catch (e) { return false; } };
  const keyAt = (n) => (hasKey ? page.evaluate((tt) => window.__frameKey(tt), n / fps) : null);

  // 子帧分批合成：一批 CH 帧，平均结果和整段一次合成完全一样（每帧只平均自己的 N 个子帧）
  const CH = Math.max(1, Math.round(parseInt(process.env.SY_MB_BATCH || '240') / MB));
  let pend = null;              // { a: 第一帧, c: 帧数 }
  let lastKey = null, lastFile = null, lastSubs = null;
  const flush = () => {
    if (MB === 1 || !pend || !pend.c) { pend = null; return; }
    const { a, c } = pend; pend = null;
    const w = Array(MB).fill(1).join(' ');
    execFileSync(FFMPEG, ['-y', '-v', 'error', '-framerate', String(fps * MB), '-start_number', String((a - n0) * MB), '-i', path.join(subDir, 's%06d.jpg'),
      '-vf', `tmix=frames=${MB}:weights='${w}',select='eq(mod(n\\,${MB})\\,${MB - 1})'`, '-fps_mode', 'passthrough',
      '-frames:v', String(c), '-q:v', '2', '-start_number', String(a), path.join(framesDir, 'f%05d.jpg')]);
    const keep = new Set(lastSubs || []);   // 定格动画（frameKey）重复的帧还要复制上一张画的子帧
    for (let n = a; n < a + c; n++) for (let k = 0; k < MB; k++) { const s = sname(n, k); if (!keep.has(s)) fs.rmSync(s, { force: true }); }
  };

  const t0 = Date.now();
  let done = 0, rendered = 0, lastPrint = 0;
  const report = (n) => {
    done++;
    if (PROGRESS) { process.stdout.write(`@@P ${done} ${N} ${rendered} ${Date.now() - t0}\n`); return; }
    if (Date.now() - lastPrint > 2000 || done === N) { lastPrint = Date.now(); process.stdout.write(`\r${path.basename(path.dirname(html))} ${done}/${N} ${rendered ? ((Date.now() - t0) / rendered).toFixed(0) : '-'}ms/f   `); }
  };

  for (let n = n0; n < n1; n++) {
    // 续跑：这一帧已经有完整的成品 → 跳过
    if (okJpg(fname(n))) {
      flush();   // 先把前面没合成的一批合成掉（它正好到 n-1 为止）
      lastKey = await keyAt(n); lastFile = fname(n); lastSubs = null;
      report(n); continue;
    }
    const key = await keyAt(n);
    if (MB === 1) {
      if (key !== null && key === lastKey && lastFile) { fs.copyFileSync(lastFile, fname(n)); lastFile = fname(n); report(n); continue; }
      await page.evaluate((tt) => window.__seek(tt), n / fps);
      await page.screenshot({ path: fname(n), type: 'jpeg', quality: 93, animations: 'disabled', caret: 'hide', timeout: 0 });
      lastKey = key; lastFile = fname(n); rendered++;
    } else {
      if (!pend) pend = { a: n, c: 0 };
      const subs = Array.from({ length: MB }, (_, k) => sname(n, k));
      if (subs.every(okJpg)) {
        // 续跑：上次已经把这一帧的子帧全渲完了
      } else if (key !== null && key === lastKey && lastSubs) {
        lastSubs.forEach((f, k) => fs.copyFileSync(f, subs[k]));
      } else {
        for (let k = 0; k < MB; k++) {
          const tt = (n + SH * ((k + 0.5) / MB - 0.5)) / fps;
          const jx = halton(k + 1, 2) - 0.5, jy = halton(k + 1, 3) - 0.5;
          await page.evaluate(([a, x, y]) => { if (window.__setJitter) window.__setJitter(x, y); return window.__seek(a); }, [tt, jx, jy]);
          await page.screenshot({ path: subs[k], type: 'jpeg', quality: 97, animations: 'disabled', caret: 'hide', timeout: 0 });
        }
        rendered++;
      }
      if (hasKey) lastSubs = subs;
      lastKey = key;
      pend.c++;
      if (pend.c >= CH) flush();
    }
    report(n);
  }
  flush();
  if (MB > 1) fs.rmSync(subDir, { recursive: true, force: true });
  const bad = [];
  for (let n = n0; n < n1; n++) if (!okJpg(fname(n))) bad.push(n);
  if (bad.length) return fail(4, `\n[帧不完整] 有 ${bad.length} 帧没写好（例如第 ${bad[0]} 帧），再跑一次会补上`);
  if (!PROGRESS) console.log(`\ndone ${framesDir} in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  await browser.close();
  await flushOut();
  process.exit(0);
})().catch((e) => { console.error('[渲染出错] ' + (e && e.stack || e)); process.exit(1); });
