# 27 拼插积木 · 配乐：明亮的「塑料放克」——切分的电子琴（clavinet 质感的脉冲波）+ 弹跳的八度贝斯 + 用积木咔哒声做的打击乐，
# 灯塔亮起时钟琴（glockenspiel）旋律进入；和其他几首的扬琴/板胡/合成器氛围完全不同。
# 音效：积木扣上（brick_click / brick_snap）、一串快速搭建（brick_rain）、低掠（swoosh_low）、灯亮（lamp_on）、印字砖扣上（tile_click）
# audio/make_audio.py 把 synth.py 的全部函数注入本模块：np, SR, BEAT, BAR, t2n, mtof, nm, sine, noise, lp, hp, bp, expenv, adsr, polyblep_saw ...
import numpy as np


def abs_click(pitch=1.0, amp=1.0, seed=0):
    """ABS plastic: a hard tick, a short hollow body resonance, a tiny rattle"""
    r = np.random.default_rng(seed)
    n = t2n(0.14); t = np.arange(n) / SR
    y = hp(noise(n), 3500) * np.exp(-t / 0.0018) * 0.9
    for f, a, d in [(1250 * pitch, 0.5, 0.018), (2650 * pitch, 0.35, 0.010), (4300 * pitch, 0.2, 0.006)]:
        y += np.sin(2 * np.pi * f * t + r.random() * 6) * np.exp(-t / d) * a
    k = t2n(0.009 + r.random() * 0.006)
    y[k:] += (hp(noise(n - k), 3000) * np.exp(-np.arange(n - k) / SR / 0.003) * 0.35)
    return y * amp * 0.6


def clav(m, dur=0.22, bright=1.0):
    n = t2n(dur); f = mtof(m); t = np.arange(n) / SR
    ph = np.cumsum(np.full(n, f)) / SR % 1.0
    y = np.where(ph < 0.28, 1.0, -0.4)
    y = y - lp(y, 120)
    fc = 600 + 4200 * bright * np.exp(-t / 0.045)
    y = svf_lp(y, fc, 0.25)
    return y * adsr(n, 0.001, 0.06, 0.45, 0.03) * 0.22


def fbass(m, dur):
    n = t2n(dur); f = mtof(m); t = np.arange(n) / SR
    y = polyblep_saw(f, n) * 0.5 + sine(f, n) * 0.8
    y = svf_lp(y, 200 + 1600 * np.exp(-t / 0.05), 0.4)
    return y * adsr(n, 0.002, 0.08, 0.6, 0.03) * 0.5


def glock(m, dur=1.2):
    n = t2n(dur); f = mtof(m); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.7) + 0.35 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / 0.18) + 0.15 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t / 0.06)
    return y * (1 - np.exp(-t / 0.0006)) * 0.22


GL_MEL = {2: ['E6', None, 'G6', 'A6', None, 'G6', 'E6', None], 3: ['C6', None, 'E6', 'G6', None, 'C7', 'B6', None], 4: ['A6', None, None, None, None, None, None, None]}


def mus(M, tb, name, root, tones, bi):
    swing = BEAT / 2 * 0.1
    # drums: kick on 1 / the "and" of 2 / 3, clap-snap backbeat, hats from bar 1, brick clicks as ghost percussion
    kicks = [0] if bi == 4 else ([0, 1.5, 2] if bi > 0 else [0, 2])   # bar 4: the 8.0 resolution, then it rings out
    for q in kicks: M.add('drums', kick(0.38, 140, 48, 1.4, 0.18), tb + q * BEAT, 0.82); M.sidechain(tb + q * BEAT, 0.35)
    for q in (1, 3):
        if 0 < bi < 4: M.add('drums', over(clap() * 0.8, snap() * 0.5), tb + q * BEAT, 0.45, 0, 0.2)
    if 0 < bi < 4:
        for e in range(8): M.add('drums', hat(e % 4 == 2), tb + e * BEAT / 2 + (swing if e % 2 else 0), 0.09 if e % 2 else 0.06, 0.35)
    for e in ((3, 7, 11, 14) if bi < 4 else ()):
        M.add('drums', abs_click(1.0 + 0.1 * (e % 3), 0.5, e + bi * 16), tb + e * BEAT / 4, 0.4, -0.4 + 0.25 * (e % 4))
    # bass: bouncy octaves
    pat = [(0, 0, 0.4), (0.75, 12, 0.2), (1.5, 0, 0.35), (2.5, 7, 0.3), (3.0, 12, 0.2), (3.5, 10 if name in ('Am', 'G') else 11, 0.3)]
    for q, iv, d in (pat if 0 < bi < 4 else (pat[:1] + pat[2:3] if bi == 0 else [])):
        M.add('music', fbass(root - 12 + iv, d), tb + q * BEAT, 0.6)
    # clav: syncopated chord stabs
    if 1 <= bi <= 3:
        for q in (0.5, 1.25, 2.5, 3.25):
            for j, m in enumerate(tones): M.add('music', clav(m + 12, 0.18, 1.0 if q in (0.5, 2.5) else 0.7), tb + q * BEAT + j * 0.004, 0.32, -0.25 + 0.25 * j, 0.15)
    elif bi == 0:
        for q in (1.0, 2.0, 3.0):
            M.add('music', clav(tones[0] + 24, 0.16, 0.6), tb + q * BEAT, 0.25, 0.3, 0.2)
    # glockenspiel melody once the lamp is lit
    if bi in GL_MEL:
        for e, sN in enumerate(GL_MEL[bi]):
            if sN: M.add('music', glock(nm(sN), 1.4), tb + e * BEAT / 2, 0.42, 0.25, 0.45)
    if bi == 4:   # the resolving chord lands with the beam on 8.0 and rings out
        for j, m in enumerate(tones + [tones[0] + 12]): M.add('music', clav(m + 12, 0.9, 1.0), tb + j * 0.012, 0.4, -0.2 + 0.13 * j, 0.45)
        M.add('music', fbass(root - 12, 1.6), tb, 0.6)
        M.add('music', pad([x + 12 for x in tones], BAR * 0.95, 1600, 0.006), tb, 0.3, 0, 0.6)


# ---------------- SFX ----------------
def beam_pass():
    # the lighthouse beam crossing the lens: an airy swell with a soft glassy shimmer on top
    n = t2n(1.6); t = np.arange(n) / SR
    air = svf_bp(noise(n), 900 + 2600 * np.exp(-((t - 0.25) / 0.35) ** 2), 0.5) * np.exp(-((t - 0.2) / 0.45) ** 2) * 0.3
    return over(air, glock(nm('E7'), 1.4) * 0.5, glock(nm('B6'), 1.4) * 0.3)


def brick_click():
    return over(abs_click(1.0, 0.8, 1), np.pad(abs_click(0.82, 1.0, 2), (t2n(0.022), 0)))


def brick_snap():
    n = t2n(0.25); t = np.arange(n) / SR
    thud = sine(150 * np.exp(-t / 0.03) + 70, n) * np.exp(-t / 0.05) * 0.4
    return over(thud, abs_click(0.9, 1.1, 3), np.pad(abs_click(0.75, 1.2, 4), (t2n(0.03), 0)))


def brick_rain():
    out = np.zeros(t2n(2.4)); r = np.random.default_rng(11); tt = 0.0; k = 0
    while tt < 2.2:
        c = abs_click(0.8 + r.random() * 0.5, 0.35 + 0.3 * r.random(), k)
        i = t2n(tt); out[i:i + len(c)] += c[: len(out) - i]
        tt += 0.11 * (1 - 0.75 * tt / 2.2) + r.random() * 0.02; k += 1
    return out


def swoosh_low():
    return whoosh(0.7, False, 250, 3200, 0.6)


def lamp_on():
    n = t2n(1.6); t = np.arange(n) / SR
    hum = (sine(110, n) * 0.5 + sine(220, n) * 0.25) * np.clip(t / 0.4, 0, 1) * np.exp(-t / 0.9) * 0.18
    return over(hum, glock(nm('E7'), 1.2) * 0.6, np.pad(glock(nm('B7'), 0.9) * 0.4, (t2n(0.06), 0)))


def tile_click():
    return over(abs_click(1.25, 0.9, 7), np.pad(abs_click(1.05, 0.7, 8), (t2n(0.015), 0)))


SFX_NEW = {'beam_pass': beam_pass, 'brick_click': brick_click, 'brick_snap': brick_snap, 'brick_rain': brick_rain, 'swoosh_low': swoosh_low, 'lamp_on': lamp_on, 'tile_click': tile_click}
