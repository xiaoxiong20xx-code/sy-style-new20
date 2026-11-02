# 38 蜡笔童画 · 配乐：尤克里里扫弦 + 玩具钟琴 + 口哨旋律 + 拍手（孩子气、阳光、蹦蹦跳跳）
# 音效：蜡笔涂鸦（scrib / scrib_s）、小狗叫（bark）、小爪子跑（paws）、刹车（skid）
import numpy as np


def whistle(m, dur):
    n = t2n(dur); t = np.arange(n) / SR; f = mtof(m)
    vib = 1 + 0.012 * np.sin(2 * np.pi * 6 * t) * np.clip((t - 0.08) / 0.15, 0, 1)
    y = sine(f * vib, n) + 0.05 * sine(2 * f * vib, n) + bp(noise(n), f * 0.9, f * 1.2) * 0.08
    return y * adsr(n, 0.03, 0.05, 0.85, 0.06) * 0.32


def glock(m, dur=0.8):
    n = t2n(dur); t = np.arange(n) / SR; f = mtof(m)
    return (sine(f, n) * np.exp(-t / 0.5) + 0.3 * sine(f * 2.76, n) * np.exp(-t / 0.12) + 0.15 * sine(f * 5.4, n) * np.exp(-t / 0.04)) * (1 - np.exp(-t / 0.001)) * 0.3


TUNE = {'Am': ['E6', 'C6', 'A5', 'C6', 'E6', None, 'D6', 'C6'], 'F': ['C6', 'A5', 'F5', 'A5', 'C6', None, 'D6', None],
        'C': ['E6', 'G6', 'E6', 'C6', 'D6', 'E6', None, None], 'G': ['D6', 'B5', 'G5', 'B5', 'D6', None, 'G6', None]}


def mus(M, tb, name, root, tones, bi):
    last = bi == 4
    # ukulele: down-down-up-up-down-up strum
    pat = [0, 1, 1.5, 2.5, 3, 3.5]
    for k, d in enumerate(pat if not last else [0]):
        up = d % 1 != 0
        order = list(reversed(tones + [tones[0] + 12])) if up else tones + [tones[0] + 12]
        for j, m in enumerate(order):
            M.add('music', ks(m + 12, 0.45 if not last else 1.5, 0.7, 0.994), tb + d * BEAT + j * 0.011, 0.2 if up else 0.26, -0.25 + 0.15 * j, 0.25)
    # bouncy bass
    for q in range(1 if last else 4):
        M.add('music', marimba(root - 12 + (7 if q % 2 else 0), 0.45), tb + q * BEAT, 0.55, 0, 0.1)
    # whistle tune from bar 1, glockenspiel doubling in bars 2-3 (the dog runs)
    if 1 <= bi <= 3:
        for e, sN in enumerate(TUNE[name]):
            if sN:
                M.add('music', whistle(nm(sN) - 12, BEAT / 2 * 0.9), tb + e * BEAT / 2, 0.42, 0.2, 0.35)
                if bi >= 2: M.add('music', glock(nm(sN), 0.6), tb + e * BEAT / 2, 0.22, -0.25, 0.4)
    # claps + kick + shaker
    if not last:
        M.add('drums', soft_kick(), tb, 0.6); M.add('drums', soft_kick(), tb + 2 * BEAT, 0.5)
        for q in (1, 3): M.add('drums', clap(), tb + q * BEAT, 0.42, 0, 0.3)
        for e in range(8): M.add('drums', shaker(), tb + e * BEAT / 2 + BEAT / 4, 0.1, 0.35)
    if bi == 2: M.add('drums', crash(1.2) * 0.6, tb + 0.25, 0.4, 0, 0.4)
    if last:   # resolve on 8.0 and ring out
        for j, m in enumerate(tones + [tones[0] + 12]): M.add('music', glock(m + 24, 2.2), tb + j * 0.05, 0.25, -0.3 + 0.2 * j, 0.5)
        for j, m in enumerate(tones + [tones[0] + 12]): M.add('music', ks(m + 12, 2.4, 0.6, 0.998), tb + j * 0.025, 0.3, -0.25 + 0.15 * j, 0.4)
        M.add('music', pad([x + 12 for x in tones], BAR * 0.9, 1500), tb, 0.3, 0, 0.5)
        M.add('music', whistle(tones[0] + 12, BEAT * 2.2), tb + 0.02, 0.3, 0.2, 0.5)


def _scrib(dur, rate, seed):
    n = t2n(dur); t = np.arange(n) / SR
    r = np.random.default_rng(seed)
    strokes = np.abs(np.sin(2 * np.pi * rate * t + 1.5 * np.sin(2 * np.pi * 2.1 * t)))
    waxy = bp(noise(n), 700, 5200) * (0.35 + 0.65 * strokes ** 1.5)
    grit = (r.random(n) > 0.993).astype(float); grit = hp(grit, 2500) * 0.3
    return (waxy * 0.5 + grit) * np.clip(t / 0.03, 0, 1) * np.clip((dur - t) / 0.08, 0, 1)


def sfx_bark():
    n = t2n(0.28); t = np.arange(n) / SR
    f = 520 + 380 * np.exp(-t / 0.05) - 200 * t
    y = np.tanh(polyblep_saw(f, n) * 1.5) * 0.5 + bp(noise(n), 600, 3000) * 0.3
    y = bp(y, 300, 3500)
    return y * np.exp(-t / 0.08) * np.clip(t / 0.01, 0, 1) * 0.7


def sfx_paws():
    out = np.zeros(t2n(1.1))
    for i in range(12):
        n = t2n(0.04); tt = np.arange(n) / SR
        x = lp(noise(n), 1800) * np.exp(-tt / 0.008) * 0.5 + sine(240 + 40 * (i % 2), n) * np.exp(-tt / 0.01) * 0.25
        k = t2n(i * 0.085 + (0.02 if i % 2 else 0)); out[k:k + n] += x
    return out


def sfx_skid():
    n = t2n(0.35); t = np.arange(n) / SR
    return bp(noise(n), 1500, 6000) * (0.6 + 0.4 * np.sin(2 * np.pi * 50 * t)) * np.exp(-t / 0.12) * 0.4


SFX_NEW = {'scrib': lambda: _scrib(0.75, 11, 1), 'scrib_s': lambda: _scrib(0.32, 14, 2), 'bark': sfx_bark, 'paws': sfx_paws, 'skid': sfx_skid}
