// 连续运动轨道：镜头、灯光、任何随时间变化的一组数值都可以用。
// 问题：每段各自 ease-in-out，镜头每到一个关键帧就减速到零，看起来“走走停停”。
// 做法：关键帧之间用三次 Hermite 曲线，经过关键帧时速度连续不归零；只有首尾（或标了 stop 的关键帧）才停。
//   const cam = Track([
//     { t: 0,   v: [0, 1.2, 8] },
//     { t: 2,   v: [1, 1.0, 6] },
//     { t: 4,   v: [0, 0.4, 3], stop: true },   // stop: 这一帧真的要停住（撞击、定格）
//     { t: 5.5, v: [0, 2.0, 9] },
//   ], { easeIn: true, easeOut: true });        // 默认首尾缓入缓出；false = 首尾也带速度进出
//   const [x, y, z] = cam(t);                    // t 超出范围时停在首 / 尾
//   cam.vel(t) → 每秒速度（用来做跟随、晃动强度、运动模糊参考）
// 角度（如 yaw）跨 ±π 时请先展开成连续数值再放进来。
(function (g) {
  function Track(keys, o = {}) {
    const n = keys.length, dim = keys[0].v.length, zero = () => new Array(dim).fill(0);
    const sl = (i, j) => keys[i].v.map((x, d) => (keys[j].v[d] - x) / (keys[j].t - keys[i].t));
    const m = keys.map((k, i) => {
      if (n === 1) return zero();
      if (i === 0) return o.easeIn === false ? sl(0, 1) : zero();
      if (i === n - 1) return o.easeOut === false ? sl(n - 2, n - 1) : zero();
      if (k.stop) return zero();
      const a = sl(i - 1, i), b = sl(i, i + 1), d0 = k.t - keys[i - 1].t, d1 = keys[i + 1].t - k.t;
      // 两侧斜率按时长加权；方向相反（来回运动的拐点）时取 0，避免冲过头
      return a.map((_, d) => (a[d] * b[d] <= 0 ? 0 : (a[d] * d1 + b[d] * d0) / (d0 + d1)));
    });
    function seg(t) {
      if (t <= keys[0].t) return [0, 0];
      if (t >= keys[n - 1].t) return [n - 2, 1];
      let i = 0; while (keys[i + 1].t < t) i++;
      return [i, (t - keys[i].t) / (keys[i + 1].t - keys[i].t)];
    }
    function at(t) {
      if (n === 1) return keys[0].v.slice();
      const [i, u] = seg(t), h = keys[i + 1].t - keys[i].t, u2 = u * u, u3 = u2 * u;
      const h00 = 2 * u3 - 3 * u2 + 1, h10 = u3 - 2 * u2 + u, h01 = -2 * u3 + 3 * u2, h11 = u3 - u2;
      return keys[i].v.map((p0, d) => h00 * p0 + h10 * h * m[i][d] + h01 * keys[i + 1].v[d] + h11 * h * m[i + 1][d]);
    }
    at.vel = (t) => { const e = 1 / 240, a = at(t - e), b = at(t + e); return a.map((x, d) => (b[d] - x) / (2 * e)); };
    at.keys = keys;
    return at;
  }
  // 整段只做一次缓动的写法：路径匀速，时间整体 ease（适合一条完整的推拉 / 环绕）
  Track.ease = (u) => (u <= 0 ? 0 : u >= 1 ? 1 : u * u * (3 - 2 * u));
  Track.easeRange = (t, t0, t1) => Track.ease((t - t0) / (t1 - t0));
  g.Track = Track;
  if (typeof module !== 'undefined') module.exports = Track;
})(typeof window !== 'undefined' ? window : globalThis);
