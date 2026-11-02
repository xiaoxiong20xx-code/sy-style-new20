# 25 木版年画 · 配乐：民间喜庆锣鼓 —— 梆子起头、笛子领奏，钩子处唢呐进来、大小锣铙钹齐响（每印一色一记锣）
# audio/make_audio.py 把 synth.py 的全部函数注入本模块：np, SR, BEAT, BAR, t2n, mtof, nm, sine, noise, lp, hp, bp, expenv, adsr, polyblep_saw, flute, woodblock ...


def suona(m, dur, vel=1.0):
    """唢呐：双簧的鼻音 + 起音上滑 + 揉音"""
    n = t2n(dur); t = np.arange(n) / SR
    slide = -1.2 * np.exp(-t / 0.035)                                   # scoop up into the note
    vib = 0.18 * np.sin(2 * np.pi * 6.2 * t) * np.clip((t - 0.12) / 0.2, 0, 1)
    f = mtof(m + slide + vib)
    x = polyblep_saw(f, n)
    x = np.tanh(x * 2.2)
    y = bp(x, 700, 1500) * 1.2 + bp(x, 2200, 3400) * 0.8 + lp(x, 600) * 0.3
    y += bp(noise(n), 1500, 5000) * 0.03
    return y * adsr(n, 0.012, 0.06, 0.85, 0.05) * 0.4 * vel


def dizi(m, dur, vel=1.0):
    """笛子：带笛膜的清亮音色"""
    n = t2n(dur); t = np.arange(n) / SR
    y = flute(m, dur)
    y += bp(noise(n), mtof(m) * 2, mtof(m) * 6) * 0.04 * adsr(n, 0.02, 0.1, 0.7, 0.1)   # membrane buzz
    return y * vel


def gong_big(vel=1.0):
    """大锣：音高下滑的 '哐'"""
    n = t2n(2.2); t = np.arange(n) / SR; y = np.zeros(n)
    for r, a, d in ((1.0, 1.0, 1.2), (1.47, 0.6, 0.8), (2.09, 0.45, 0.5), (2.56, 0.3, 0.35), (3.4, 0.2, 0.2)):
        f = 180 * r * (1 - 0.06 * (1 - np.exp(-t / 0.25)))
        y += a * sine(f, n) * np.exp(-t / d)
    y += bp(noise(n), 300, 3000) * np.exp(-t / 0.05) * 0.5
    return np.tanh(y * 0.9) * 0.45 * vel


def gong_small(vel=1.0):
    """小锣：音高上扬的 '台'"""
    n = t2n(0.9); t = np.arange(n) / SR; y = np.zeros(n)
    for r, a, d in ((1.0, 1.0, 0.45), (1.52, 0.5, 0.3), (2.3, 0.3, 0.15)):
        f = 620 * r * (1 + 0.09 * (1 - np.exp(-t / 0.08)))
        y += a * sine(f, n) * np.exp(-t / d)
    y += hp(noise(n), 3000) * np.exp(-t / 0.01) * 0.3
    return y * 0.32 * vel


def cymbal(vel=1.0, dur=0.6):
    """铙钹"""
    n = t2n(dur); t = np.arange(n) / SR
    y = bp(noise(n), 2500, 11000) * np.exp(-t / (dur * 0.35)) * 0.5
    for f in (3150, 4420, 5870, 7310): y += np.sin(2 * np.pi * f * t) * np.exp(-t / 0.15) * 0.05
    return y * vel


def tanggu(vel=1.0):
    """堂鼓"""
    n = t2n(0.35); t = np.arange(n) / SR
    return (sine(110 + 70 * np.exp(-t / 0.02), n) * np.exp(-t / 0.12) + bp(noise(n), 200, 2500) * np.exp(-t / 0.015) * 0.4) * 0.7 * vel


PENT = {'G4': 67, 'A4': 69, 'C5': 72, 'D5': 74, 'E5': 76, 'G5': 79, 'A5': 81, 'C6': 84, 'D6': 86}
MEL = [   # (note, start in beats, length in beats) per bar
    [('E5', 1, 0.5), ('G5', 1.5, 0.5), ('A5', 2, 1), ('G5', 3, 0.5), ('E5', 3.5, 0.5)],
    [('D5', 0, 0.5), ('E5', 0.5, 0.5), ('G5', 1, 1), ('E5', 2, 0.5), ('D5', 2.5, 0.5), ('C5', 3, 1)],
    [('G5', 0, 0.5), ('A5', 0.5, 0.5), ('C6', 1, 0.5), ('A5', 1.5, 0.5), ('G5', 2, 0.5), ('E5', 2.5, 0.5), ('G5', 3, 1)],
    [('A5', 0, 0.75), ('G5', 0.75, 0.25), ('E5', 1, 0.5), ('D5', 1.5, 0.5), ('E5', 2, 0.5), ('G5', 2.5, 0.5), ('D6', 3, 0.5), ('C6', 3.5, 0.5)],
    [('C6', 0, 3.6)],
]


def mus(M, tb, name, root, tones, bi):
    for (nt, b0, ln) in MEL[bi]:
        m = PENT[nt]
        if bi <= 1:
            M.add('music', dizi(m, ln * BEAT * 0.95), tb + b0 * BEAT, 0.55, 0.15, 0.4)
        else:
            M.add('music', suona(m, ln * BEAT * 0.97), tb + b0 * BEAT, 0.62, 0.0, 0.3)
            M.add('music', dizi(m + 12, ln * BEAT * 0.95, 0.6), tb + b0 * BEAT, 0.25, 0.3, 0.4)
    # bass drone on the tonic/fifth (sheng-like)
    M.add('music', pad([48, 55, 60], BAR * 1.02, 1200, 0.004), tb, 0.22 if bi < 2 else 0.3, 0, 0.4)
    # clapper keeps time from the start
    for q in range(4): M.add('drums', woodblock(1300 if q % 2 == 0 else 1050), tb + q * BEAT, 0.45 if bi < 2 else 0.3, 0.3)
    if bi == 1:
        for e in range(8):
            if e in (0, 3, 4, 6): M.add('drums', tanggu(0.8), tb + e * BEAT / 2, 0.6, -0.1, 0.2)
        for q in (1, 3): M.add('drums', gong_small(0.7), tb + q * BEAT, 0.5, 0.25, 0.3)
    if bi in (2, 3):     # 锣鼓喧天: a gong on every colour (each beat), cymbals on the offbeats, drum rolls
        for q in range(4):
            M.add('drums', gong_big(0.9 if q == 0 else 0.6), tb + q * BEAT, 0.6, -0.15, 0.35)
            M.add('drums', cymbal(0.9), tb + q * BEAT + BEAT / 2, 0.5, 0.2, 0.25)
        for e in range(16):
            if e % 4 in (0, 2, 3): M.add('drums', tanggu(0.6 + 0.4 * (e % 4 == 0)), tb + e * BEAT / 4, 0.5, 0, 0.15)
        for q in (1, 3): M.add('drums', gong_small(0.8), tb + q * BEAT + BEAT * 0.25, 0.45, 0.3, 0.3)
    if bi == 4:
        M.add('drums', gong_big(1.0), tb, 0.75, 0, 0.4)
        M.add('drums', cymbal(1.0, 1.4), tb, 0.6, 0.2, 0.4)


# ---------- SFX ----------
def ink_brush():
    n = t2n(0.45); t = np.arange(n) / SR; u = t / 0.45
    return bp(noise(n), 600, 3500) * np.sin(np.pi * u) ** 1.5 * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * t)) * 0.35


def paper_flip():
    n = t2n(0.5); t = np.arange(n) / SR; u = t / 0.5
    y = bp(noise(n), 900, 7000) * np.sin(np.pi * u) ** 2 * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 14 * t))) * 0.35
    k = t2n(0.4); m = n - k
    y[k:] += (lp(noise(m), 1200) * np.exp(-np.arange(m) / SR / 0.02) * 0.4)[:m]
    return y


def flip_fast():
    n = t2n(0.3); t = np.arange(n) / SR; u = t / 0.3
    return bp(noise(n), 1200, 8000) * np.sin(np.pi * u) ** 2 * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 22 * t))) * 0.35


def palm_rub():
    n = t2n(0.5); t = np.arange(n) / SR; u = t / 0.5
    am = 0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 11 * t))
    return bp(noise(n), 1800, 9000) * am * np.sin(np.pi * u) ** 0.8 * 0.4 + lp(noise(n), 400) * np.sin(np.pi * u) * 0.12


def print_beat():
    n = t2n(0.25); t = np.arange(n) / SR
    return lp(noise(n), 1500) * np.exp(-t / 0.018) * 0.6 + bp(noise(n), 2000, 7000) * np.exp(-t / 0.006) * 0.3


def gong_title():
    y = gong_small(1.0); c = cymbal(0.6, 0.8); y[:len(c)] += c
    return y


SFX_NEW = {'ink_brush': ink_brush, 'paper_flip': paper_flip, 'flip_fast': flip_fast, 'palm_rub': palm_rub, 'print_beat': print_beat,
           'gong_small': gong_title}
