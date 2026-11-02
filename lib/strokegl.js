/* strokegl.js — 肖雄 XIAOXIONG 新风格 21 油画 / 22 粉笔 / 38 蜡笔 共用的小工具（只给这几个场景用）
   - SG.prog(gl, vs, fs)            编译着色器（报错时打印带行号源码）
   - SG.tex(gl, w, h, o)            建纹理；SG.fbo(gl, [tex...]) 建多目标帧缓冲（MRT）
   - SG.Strokes                     折线笔触 → 三角形条带顶点（每顶点 20 个 float），一次 draw 画完全部笔触
       顶点布局 a0=(x, y, s, v)  a1=(L, w, t0, t1)  a2=(rA, gA, bA, thick)  a3=(rB, gB, bB, kind)  a4=(seed, p1, p2, p3)
       s = 沿笔触的像素距离（两端各延伸 w/2 做圆头），v = 横向 -1..1（含 pad 余量），L = 笔触总长
   - SG.quad(gl)                    全屏三角形（attribute 0 = p） */
(function () {
  const SG = {};
  SG.prog = function (gl, vs, fs) {
    const sh = (type, src) => {
      const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) { const e = gl.getShaderInfoLog(s); console.error(e + '\n' + src.split('\n').map((l, i) => i + 1 + ': ' + l).join('\n')); throw new Error(e); }
      return s;
    };
    const pr = gl.createProgram();
    gl.attachShader(pr, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, fs));
    ['p', 'a0', 'a1', 'a2', 'a3', 'a4'].forEach((n, i) => gl.bindAttribLocation(pr, i, n));
    gl.linkProgram(pr);
    if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) { const e = gl.getProgramInfoLog(pr); console.error(e); throw new Error(e); }
    const locs = {};
    const P = {
      pr,
      use() { gl.useProgram(pr); P._unit = 0; return P; },
      loc(n) { if (!(n in locs)) locs[n] = gl.getUniformLocation(pr, n); return locs[n]; },
      f(n, ...v) { const l = P.loc(n); if (l === null) return P; [gl.uniform1f, gl.uniform2f, gl.uniform3f, gl.uniform4f][v.length - 1].call(gl, l, ...v); return P; },
      v(n, arr) { const l = P.loc(n); if (l === null) return P; const k = arr.length; (k === 2 ? gl.uniform2fv : k === 3 ? gl.uniform3fv : gl.uniform4fv).call(gl, l, arr); return P; },
      arr4(n, arr) { const l = P.loc(n); if (l !== null) gl.uniform4fv(l, arr); return P; },
      t(n, tex) { const l = P.loc(n); const u = P._unit++; gl.activeTexture(gl.TEXTURE0 + u); gl.bindTexture(gl.TEXTURE_2D, tex.tex || tex); if (l !== null) gl.uniform1i(l, u); return P; },
    };
    return P;
  };
  SG.tex = function (gl, w, h, o = {}) {
    const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
    const ifmt = o.ifmt || gl.RGBA8, fmt = o.fmt || gl.RGBA, type = o.type || gl.UNSIGNED_BYTE;
    if (o.mips) {
      const lv = Math.floor(Math.log2(Math.max(w, h))) + 1;
      gl.texStorage2D(gl.TEXTURE_2D, lv, ifmt, w, h);
    } else gl.texImage2D(gl.TEXTURE_2D, 0, ifmt, w, h, 0, fmt, type, null);
    const f = o.filter || gl.LINEAR;
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, o.mips ? gl.LINEAR_MIPMAP_LINEAR : f);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, f);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, o.wrap || gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, o.wrap || gl.CLAMP_TO_EDGE);
    if (o.aniso) { const ext = gl.getExtension('EXT_texture_filter_anisotropic'); if (ext) gl.texParameterf(gl.TEXTURE_2D, ext.TEXTURE_MAX_ANISOTROPY_EXT, o.aniso); }
    return { tex: t, w, h, mips: !!o.mips };
  };
  SG.fbo = function (gl, texs) {
    const fb = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
    texs.forEach((t, i) => gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0 + i, gl.TEXTURE_2D, t.tex, 0));
    gl.drawBuffers(texs.map((_, i) => gl.COLOR_ATTACHMENT0 + i));
    const st = gl.checkFramebufferStatus(gl.FRAMEBUFFER);
    if (st !== gl.FRAMEBUFFER_COMPLETE) console.error('FBO incomplete', st.toString(16));
    return { fb, w: texs[0].w, h: texs[0].h, texs };
  };
  SG.bind = function (gl, f) { gl.bindFramebuffer(gl.FRAMEBUFFER, f ? f.fb : null); if (f) gl.viewport(0, 0, f.w, f.h); };
  // immutable (mipmapped) textures must be filled with texSubImage2D
  SG.upload = function (gl, t, src) { gl.bindTexture(gl.TEXTURE_2D, t.tex); if (t.mips) { gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, gl.RGBA, gl.UNSIGNED_BYTE, src); gl.generateMipmap(gl.TEXTURE_2D); } else gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, src); };
  SG.quad = function (gl) {
    const vao = gl.createVertexArray(); gl.bindVertexArray(vao);
    const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    gl.bindVertexArray(null);
    return { draw() { gl.bindVertexArray(vao); gl.drawArrays(gl.TRIANGLES, 0, 3); gl.bindVertexArray(null); } };
  };
  SG.VS_QUAD = `#version 300 es
in vec2 p; out vec2 uv; void main(){ uv = p*.5+.5; gl_Position = vec4(p,0.,1.); }`;

  // ---------- Catmull-Rom resample of a control polyline ----------
  function crSample(P, ds) {
    if (P.length === 1) P = [P[0], [P[0][0] + 0.01, P[0][1]]];
    const pts = [];
    const n = P.length;
    const g = (i) => P[Math.max(0, Math.min(n - 1, i))];
    for (let i = 0; i < n - 1; i++) {
      const p0 = g(i - 1), p1 = g(i), p2 = g(i + 1), p3 = g(i + 2);
      const segL = Math.hypot(p2[0] - p1[0], p2[1] - p1[1]);
      const k = Math.max(2, Math.ceil(segL / ds));
      for (let j = 0; j < k; j++) {
        const t = j / k, t2 = t * t, t3 = t2 * t;
        const c = (a, b, c_, d) => 0.5 * (2 * b + (-a + c_) * t + (2 * a - 5 * b + 4 * c_ - d) * t2 + (-a + 3 * b - 3 * c_ + d) * t3);
        pts.push([c(p0[0], p1[0], p2[0], p3[0]), c(p0[1], p1[1], p2[1], p3[1])]);
      }
    }
    pts.push(P[n - 1].slice());
    return pts;
  }
  SG.crSample = crSample;
  function linSample(P, ds) {
    if (P.length === 1) P = [P[0], [P[0][0] + 0.01, P[0][1]]];
    const pts = [];
    for (let i = 0; i < P.length - 1; i++) {
      const a = P[i], b = P[i + 1], k = Math.max(1, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / ds));
      for (let j = 0; j < k; j++) pts.push([a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k]);
    }
    pts.push(P[P.length - 1].slice());
    return pts;
  }
  SG.linSample = linSample;

  class Strokes {
    constructor() { this.d = []; this.nv = 0; this.list = []; }
    /* pts: control points [[x,y],...] (design/paint px); o: { w, t0, t1, colA:[r,g,b] 0..1, colB, thick, kind, seed, p1, p2, p3, pad, wf(u)->width factor, ds } */
    add(pts, o) {
      const ds = o.ds || Math.max(2, Math.min(10, (o.w || 10) * 0.25));
      const S = o.lin ? linSample(pts, ds) : crSample(pts, ds);
      // cumulative length
      const cl = [0];
      for (let i = 1; i < S.length; i++) cl.push(cl[i - 1] + Math.hypot(S[i][0] - S[i - 1][0], S[i][1] - S[i - 1][1]));
      const L = Math.max(cl[cl.length - 1], 0.01);
      const w = o.w || 10, pad = o.pad ?? 0.25;
      // tangents
      const T = S.map((p, i) => {
        const a = S[Math.max(0, i - 1)], b = S[Math.min(S.length - 1, i + 1)];
        const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1; return [dx / l, dy / l];
      });
      // extend both ends by w/2 for round caps
      const ext = w * 0.5 * (o.cap ?? 1);
      const rows = [];
      const t0 = T[0], tn = T[T.length - 1];
      rows.push([S[0][0] - t0[0] * ext, S[0][1] - t0[1] * ext, -ext, t0]);
      for (let i = 0; i < S.length; i++) rows.push([S[i][0], S[i][1], cl[i], T[i]]);
      rows.push([S[S.length - 1][0] + tn[0] * ext, S[S.length - 1][1] + tn[1] * ext, L + ext, tn]);
      const cA = o.colA || [1, 1, 1], cB = o.colB || cA;
      const per = [L, w, o.t0 ?? 0, o.t1 ?? 0.001, cA[0], cA[1], cA[2], o.thick ?? 1, cB[0], cB[1], cB[2], o.kind ?? 0, o.seed ?? ((this.list.length * 7.31 + 1.7) % 97), o.p1 ?? 0, o.p2 ?? 0, o.p3 ?? 0];
      const vmax = 1 + pad;
      const vert = (r, side) => {
        const u = Math.max(0, Math.min(1, r[2] / L));
        const wf = o.wf ? o.wf(u) : 1;
        const hw = w * 0.5 * wf * vmax;
        const nx = -r[3][1], ny = r[3][0];
        this.d.push(r[0] + nx * hw * side, r[1] + ny * hw * side, r[2], side * vmax, ...per);
        this.nv++;
      };
      for (let i = 0; i < rows.length - 1; i++) {
        const a = rows[i], b = rows[i + 1];
        vert(a, -1); vert(a, 1); vert(b, 1);
        vert(a, -1); vert(b, 1); vert(b, -1);
      }
      this.list.push({ pts, o, L });
      return L;
    }
    upload(gl) {
      const arr = new Float32Array(this.d);
      this.vao = gl.createVertexArray(); gl.bindVertexArray(this.vao);
      const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b); gl.bufferData(gl.ARRAY_BUFFER, arr, gl.STATIC_DRAW);
      for (let k = 0; k < 5; k++) { gl.enableVertexAttribArray(k + 1); gl.vertexAttribPointer(k + 1, 4, gl.FLOAT, false, 80, k * 16); }
      gl.bindVertexArray(null);
      this.gl = gl; this.count = this.nv;
      return this;
    }
    reset() { this.d = []; this.nv = 0; this.list = []; return this; }
    // re-upload every frame (geometry that changes, e.g. a stop-motion redraw)
    uploadDynamic(gl) {
      if (!this.vao) {
        this.vao = gl.createVertexArray(); gl.bindVertexArray(this.vao);
        this.buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, this.buf);
        for (let k = 0; k < 5; k++) { gl.enableVertexAttribArray(k + 1); gl.vertexAttribPointer(k + 1, 4, gl.FLOAT, false, 80, k * 16); }
        gl.bindVertexArray(null);
      }
      gl.bindBuffer(gl.ARRAY_BUFFER, this.buf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(this.d), gl.DYNAMIC_DRAW);
      this.gl = gl; this.count = this.nv;
      return this;
    }
    draw(first = 0, count = this.count) { const gl = this.gl; gl.bindVertexArray(this.vao); gl.drawArrays(gl.TRIANGLES, first, count); gl.bindVertexArray(null); }
  }
  SG.Strokes = Strokes;

  // vertex shader for strokes: paint-space px -> clip; PS = paint size, VIEW = (ox, oy, scale) optional
  SG.VS_STROKE = `#version 300 es
in vec4 a0; in vec4 a1; in vec4 a2; in vec4 a3; in vec4 a4;
uniform vec2 PS; uniform vec3 VIEW;
out vec4 v0; flat out vec4 v1; flat out vec4 v2; flat out vec4 v3; flat out vec4 v4;
void main(){
  v0 = a0; v1 = a1; v2 = a2; v3 = a3; v4 = a4;
  vec2 q = (a0.xy - VIEW.xy) * VIEW.z;
  gl_Position = vec4(q.x/PS.x*2.-1., 1.-q.y/PS.y*2., 0., 1.);
}`;
  // GLSL noise helpers shared by the scenes
  SG.GLSL_NOISE = `
float hash11(float p){ p=fract(p*.1031); p*=p+33.33; p*=p+p; return fract(p); }
float hash12(vec2 p){ vec3 p3=fract(vec3(p.xyx)*.1031); p3+=dot(p3,p3.yzx+33.33); return fract((p3.x+p3.y)*p3.z); }
vec2 hash22(vec2 p){ vec3 p3=fract(vec3(p.xyx)*vec3(.1031,.1030,.0973)); p3+=dot(p3,p3.yzx+33.33); return fract((p3.xx+p3.yz)*p3.zy); }
float vn(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.-2.*f);
  return mix(mix(hash12(i),hash12(i+vec2(1,0)),f.x), mix(hash12(i+vec2(0,1)),hash12(i+vec2(1,1)),f.x), f.y); }
float vn1(float x){ float i=floor(x), f=fract(x); f=f*f*(3.-2.*f); return mix(hash11(i), hash11(i+1.), f); }
float fbm(vec2 p){ float a=.5, s=0.; for(int i=0;i<5;i++){ s+=a*vn(p); p=mat2(1.6,1.2,-1.2,1.6)*p+3.1; a*=.5; } return s; }
float fbm3(vec2 p){ float a=.5, s=0.; for(int i=0;i<3;i++){ s+=a*vn(p); p=mat2(1.6,1.2,-1.2,1.6)*p+3.1; a*=.5; } return s; }
`;
  window.SG = SG;
})();
