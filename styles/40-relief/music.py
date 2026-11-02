# 40 大理石浮雕 · 配乐：编磬（石磬）+ 大提琴长音 + 低沉堂鼓，博物馆里的庄重与回响
# 音色：石头敲出来的磬声（非谐波泛音、短促的石质起音），区别于其他几首的金属钟、唢呐、合成器。
# audio/make_audio.py 把 synth.py 的全部函数注入本模块：np, SR, BEAT, BAR, t2n, mtof, nm, sine, noise, lp, hp, bp, expenv, adsr, polyblep_saw ...


def qing(m, dur=1.8, vel=1.0):
    """编磬：石板自由振动的非谐波泛音 + 石质敲击声"""
    n = t2n(dur); f = mtof(m); t = np.arange(n) / SR
    y = np.zeros(n)
    for r, a, d in ((1.0, 1.0, 0.95), (2.756, 0.42, 0.32), (5.404, 0.2, 0.11), (8.933, 0.09, 0.045), (1.006, 0.35, 0.8)):
        y += a * np.sin(2 * np.pi * f * r * t + r) * np.exp(-t / d)
    y += bp(noise(n), min(f * 2.0, 9000), min(f * 14, 15000)) * np.exp(-t / 0.006) * 0.55
    y += lp(noise(n), 400) * np.exp(-t / 0.02) * 0.25
    return y * (1 - np.exp(-t / 0.0007)) * 0.3 * vel


def cello(m, dur, cut=1000, vel=1.0):
    n = t2n(dur); t = np.arange(n) / SR
    vib = 1 + 0.0045 * np.sin(2 * np.pi * 4.8 * t) * np.clip((t - 0.4) / 0.6, 0, 1)
    f = mtof(m) * vib
    y = polyblep_saw(f, n) * 0.55 + polyblep_saw(f * 1.0025, n) * 0.45
    y = lp(y, cut) * 0.8 + bp(y, 180, 900) * 0.5
    y += bp(noise(n), 600, 2600) * 0.025
    return y * adsr(n, 0.45, 0.3, 0.85, 0.6) * 0.32 * vel


def drum_low(vel=1.0):
    n = t2n(1.2); t = np.arange(n) / SR
    y = sine(44 + 38 * np.exp(-t / 0.07), n) * np.exp(-t / 0.5)
    y += lp(noise(n), 500) * np.exp(-t / 0.05) * 0.4
    return np.tanh(y * 1.3) * 0.75 * vel


def room(dur):
    n = t2n(dur)
    return lp(noise(n), 260) * 0.05 + bp(noise(n), 900, 2400) * 0.006


PENT = {'A3': 57, 'C4': 60, 'D4': 62, 'E4': 64, 'G4': 67, 'A4': 69, 'C5': 72, 'D5': 74, 'E5': 76, 'G5': 79, 'A5': 81, 'C6': 84, 'E6': 88}
ROOTS = [33, 33, 29, 31, 33]          # A1 A1 F1 G1 A1


def mus(M, tb, name, root, tones, bi):
    r = ROOTS[bi]
    # bowed foundation
    M.add('music', cello(r, BAR * 1.05, 900, 0.9 if bi else 0.7), tb, 0.55, -0.1, 0.35)
    M.add('music', cello(r + 7 + (12 if bi == 2 else 0), BAR * 1.05, 1300, 0.6), tb + 0.02, 0.4, 0.15, 0.4)
    if bi >= 2: M.add('music', cello(r + 12, BAR * 1.05, 1600, 0.55), tb + 0.04, 0.32, 0.3, 0.45)
    M.add('music', room(BAR), tb, 0.6)
    # stone-chime line (eighth-note grid; None = rest)
    lines = [
        [None, None, 'E5', None, None, None, 'A4', None],
        ['C5', None, 'D5', None, 'E5', 'G5', 'E5', None],
        [None, 'A4', 'C5', 'E5', 'A5', 'E5', 'C5', 'E5'],
        ['G5', None, 'E5', 'D5', 'C5', None, 'D5', None],
        ['A4', None, None, None, None, None, None, None],
    ][bi]
    for e, s in enumerate(lines):
        if s: M.add('music', qing(PENT[s], 2.0, 0.85 + 0.15 * (e % 2 == 0)), tb + e * BEAT / 2, 0.55, -0.35 + 0.1 * (e % 7), 0.55)
    # low drum: sparse, ceremonial
    if bi == 1: M.add('drums', drum_low(0.6), tb, 0.6, 0, 0.3); M.add('drums', drum_low(0.45), tb + 2 * BEAT, 0.5, 0, 0.3)
    if bi == 2:
        for q in (1, 3): M.add('drums', drum_low(0.9), tb + q * BEAT, 0.8, 0, 0.35)
        for q in (2, 2.5, 3.5): M.add('drums', drum_low(0.35), tb + q * BEAT, 0.4, 0.2, 0.3)
    if bi == 3: M.add('drums', drum_low(0.7), tb, 0.65, 0, 0.35); M.add('drums', drum_low(0.5), tb + 2.5 * BEAT, 0.5, 0, 0.3)


# ---------- SFX ----------
def spot_on():
    """剧场聚光灯开关：沉重的机械咔哒 + 金属余振 + 电流嗡声渐起"""
    n = t2n(1.6); t = np.arange(n) / SR
    y = sine(85 + 40 * np.exp(-t / 0.02), n) * np.exp(-t / 0.07) * 0.8
    y += hp(noise(n), 2500) * np.exp(-t / 0.004) * 0.6
    y += np.sin(2 * np.pi * 2140 * t) * np.exp(-t / 0.12) * 0.08 + np.sin(2 * np.pi * 3310 * t) * np.exp(-t / 0.07) * 0.05
    hum = (np.sin(2 * np.pi * 100 * t) + 0.4 * np.sin(2 * np.pi * 200 * t) + 0.2 * np.sin(2 * np.pi * 300 * t)) * 0.05
    y += lp(hum, 600) * np.clip(t / 0.3, 0, 1) * np.exp(-t / 1.2)
    return y


def stone_boom():
    """钩子：低沉的石头轰鸣 + 石裂的高频 + 长尾"""
    n = t2n(2.6); t = np.arange(n) / SR
    y = sine(36 + 70 * np.exp(-t / 0.06), n) * np.exp(-t / 0.9) * 1.1
    y += lp(noise(n), 260) * np.exp(-t / 0.5) * 0.5
    y += bp(noise(n), 1800, 7000) * np.exp(-t / 0.03) * 0.35
    y += qing(nm('A3'), 2.6, 1.0) * 0.7 + qing(nm('E4'), 2.6, 0.7) * 0.45
    return np.tanh(y * 1.2) * 0.9


def stone_hum():
    """光线拂过石面的气声：低频气流 + 隐约的泛音"""
    n = t2n(1.8); t = np.arange(n) / SR; u = t / 1.8
    y = bp(noise(n), 300, 1400) * 0.12 + sine(mtof(57), n) * 0.04 + sine(mtof(64), n) * 0.025
    return y * np.sin(np.pi * u) ** 2


def chisel():
    """铁锤敲凿：清脆的金属‘叮’ + 石屑迸裂"""
    n = t2n(0.7); t = np.arange(n) / SR
    y = np.zeros(n)
    for f, a, d in ((3120, 0.35, 0.09), (4710, 0.22, 0.05), (7230, 0.12, 0.025), (1890, 0.15, 0.12)):
        y += a * np.sin(2 * np.pi * f * t) * np.exp(-t / d)
    y += bp(noise(n), 2000, 9000) * np.exp(-t / 0.018) * 0.5
    y += sine(150 + 80 * np.exp(-t / 0.01), n) * np.exp(-t / 0.04) * 0.3
    return y * 0.8


def stone_bell():
    """落版：一组石磬齐鸣 + 低鼓"""
    n = t2n(3.2); y = np.zeros(n)
    for k, (m, g) in enumerate(((nm('A3'), 0.9), (nm('E4'), 0.7), (nm('A4'), 0.6), (nm('E5'), 0.35))):
        x = qing(m, 3.0, g); s0 = t2n(k * 0.012); y[s0:s0 + len(x)] += x[:n - s0]
    d = drum_low(0.8); y[:len(d)] += d * 0.6
    return y


def rake_sweep():
    """the narrow raking lamp runs along the key-fret band: an airy glide that brightens and passes, with a faint stone ring"""
    n = t2n(1.4); t = np.arange(n) / SR; u = np.clip(t / 0.62, 0, 1)
    y = svf_bp(noise(n), 900 + 3200 * u, 0.6) * np.sin(np.pi * u) ** 1.5 * 0.35
    for k, m in enumerate((nm('E6'), nm('A6'), nm('B6'), nm('E7'))):
        x = qing(m, 0.9, 0.35); s0 = t2n(0.12 + 0.12 * k); y[s0:s0 + len(x)] += x[:n - s0] * 0.5
    return y


SFX_NEW = {'spot_on': spot_on, 'stone_boom': stone_boom, 'stone_hum': stone_hum, 'chisel': chisel, 'stone_bell': stone_bell, 'rake_sweep': rake_sweep}
