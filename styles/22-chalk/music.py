# 22 粉笔黑板 · 配乐：课堂纪录片式的拨弦 + 木琴 + 木鱼，好奇、轻快；鲸鱼跃出时整个乐队顶上去（定音鼓 + 弦乐 + 钟琴）
# 音效：粉笔敲板（chalk_tap）、粉笔划线（chalk_line / chalk_long）、侧锋涂（chalk_side）、写字（chalk_taps）、鲸歌（whale）、板擦（erase）
import numpy as np

MEL = {'Am': ['A5', 'C6', 'E6', None, 'D6', 'C6', 'B5', None], 'F': ['A5', None, 'C6', 'F6', 'E6', None, 'C6', None],
       'C': ['G5', 'C6', 'E6', None, 'G6', 'E6', 'D6', None], 'G': ['B5', None, 'D6', 'G6', 'F#6', None, 'D6', 'B5']}


def mus(M, tb, name, root, tones, bi):
    big = bi == 2                       # 4.0–6.0: the breach
    last = bi == 4
    # pizzicato bass walking on the beat
    walk = [root - 12, root - 5, root, root - 5]
    for q in range(1 if last else 4):
        M.add('music', pizz(walk[q], 0.45), tb + q * BEAT, 0.7, -0.15, 0.2)
    # pizzicato chords on the off-beats
    if not last:
        for q in (1, 3):
            for j, m in enumerate(tones):
                M.add('music', pizz(m + 12, 0.3), tb + q * BEAT + BEAT / 2 + j * 0.008, 0.28, -0.3 + 0.3 * j, 0.25)
    # xylophone tune (from bar 1), doubled by glockenspiel in the big bars
    if 1 <= bi <= 3:
        for e, sN in enumerate(MEL[name]):
            if sN:
                M.add('music', xylo(nm(sN) - 12, 0.4), tb + e * BEAT / 2, 0.42, 0.25, 0.3)
                if big: M.add('music', bell(nm(sN), 0.9, 0.5), tb + e * BEAT / 2, 0.1, -0.25, 0.5)
    elif bi == 0:
        for e in (2, 3, 6):
            M.add('music', xylo(tones[e % 3] + 12, 0.35), tb + e * BEAT / 2, 0.3, 0.25, 0.3)
    # woodblock + soft kick + shaker: the classroom clock
    for q in range(4):
        if not last or q < 1:
            M.add('drums', woodblock(1300 if q % 2 else 1000) * 0.9, tb + q * BEAT + (BEAT / 2 if q % 2 else 0), 0.35, 0.3)
    if not last:
        M.add('drums', soft_kick(), tb, 0.6); M.add('drums', soft_kick(), tb + 2 * BEAT, 0.5)
        for s16 in range(8): M.add('drums', shaker(), tb + s16 * BEAT / 2 + BEAT / 4, 0.07, 0.35)
    if big:   # the breach: strings swell under it
        M.add('music', strings([x + 12 for x in tones], BAR * 1.02, 3000), tb, 0.45, 0, 0.6)
        M.add('music', strings([root - 12, root], BAR * 1.02, 900), tb, 0.35, 0, 0.3)
    if bi == 2:
        M.add('drums', taiko() * 1.1, tb + 0.5, 0.8, 0, 0.5)          # the whale breaks the waterline on 4.5
    if bi == 3:                                                           # 6.0: it re-enters; the eraser bar is lighter
        M.add('drums', taiko() * 0.8, tb, 0.5, 0, 0.5)
        M.add('music', strings([x + 12 for x in tones], BAR * 1.02, 1800), tb, 0.22, 0, 0.6)
    if last:   # resolve on 8.0: bell chord + pizz, ringing out to 10 s
        for j, m in enumerate(tones + [tones[0] + 12]):
            M.add('music', bell(m + 24, 2.6, 0.6), tb + j * 0.04, 0.14, -0.3 + 0.2 * j, 0.6)
            M.add('music', pizz(m + 12, 0.6), tb + j * 0.02, 0.32, 0, 0.3)
        M.add('music', strings([x + 12 for x in tones], BAR * 0.95, 2000), tb, 0.3, 0, 0.6)
        M.add('music', upright(root - 12, BAR * 0.8), tb, 0.5)


def _scrape(dur, lo, hi, rate, amp, seed):
    n = t2n(dur); t = np.arange(n) / SR
    r = np.random.default_rng(seed)
    jit = np.cumsum(r.standard_normal(n)) / np.sqrt(n) * 0.0
    am = 0.45 + 0.55 * (np.sin(2 * np.pi * rate * t + 2.3 * np.sin(2 * np.pi * 3.7 * t)) > 0.2)   # stick-slip squeak
    am = lp(am.astype(float), 900)
    y = bp(noise(n), lo, hi) * am * amp
    env = np.clip(t / 0.02, 0, 1) * np.clip((dur - t) / 0.06, 0, 1)
    return y * env


def chalk_tap():
    n = t2n(0.09); t = np.arange(n) / SR
    return hp(noise(n), 2500) * np.exp(-t / 0.004) * 0.7 + sine(1900, n) * np.exp(-t / 0.008) * 0.25 + sine(420, n) * np.exp(-t / 0.02) * 0.25


def chalk_taps():
    out = np.zeros(t2n(0.6)); r = np.random.default_rng(4)
    for i in range(6):
        x = chalk_tap() * (0.55 + 0.4 * r.random()); k = t2n(i * 0.085 + r.random() * 0.02); out[k:k + len(x)] += x
        s = _scrape(0.05, 2500, 7000, 40, 0.25, i); k2 = k + t2n(0.012); out[k2:k2 + len(s)] += s[: len(out) - k2]
    return out


SFX_NEW = {
    'chalk_tap': chalk_tap, 'chalk_taps': chalk_taps,
    'chalk_line': lambda: _scrape(0.42, 2200, 7500, 31, 0.35, 1),
    'chalk_long': lambda: _scrape(1.0, 2000, 7500, 27, 0.33, 2),
    'chalk_side': lambda: _scrape(0.45, 900, 4500, 14, 0.4, 3),
    'whale': lambda: (lambda n, t: (sine(260 + 90 * np.sin(np.pi * t / 1.3) * (1 - t / 1.3) - 60 * t, n) * 0.6 + sine(2 * (260 + 90 * np.sin(np.pi * t / 1.3) * (1 - t / 1.3) - 60 * t), n) * 0.2)
                      * np.sin(np.pi * np.clip(t / 1.3, 0, 1)) ** 1.5 * 0.5)(t2n(1.3), np.arange(t2n(1.3)) / SR),
    'erase': lambda: lp(_scrape(0.7, 300, 2500, 6, 0.55, 5), 3000),
}
