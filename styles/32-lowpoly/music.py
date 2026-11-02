# 32 低多边形 · 配乐：清晨的竖琴琶音 + 晶体般的 FM 叮当 + 温暖铺底，钩子处鼓组进场（明亮、开阔、几何感）
# audio/make_audio.py 把 synth.py 的全部函数注入本模块：np, SR, BEAT, BAR, t2n, mtof, nm, sine, noise, lp, hp, bp, expenv, adsr, ks, pad, sub, kick ...


def harp(m, dur=1.4, vel=1.0):
    """竖琴：明亮拨弦（Karplus-Strong）+ 指甲起音"""
    y = ks(m, dur, 0.75, 0.9975)
    n = len(y); t = np.arange(n) / SR
    y = y + sine(mtof(m) * 2, n) * np.exp(-t / 0.25) * 0.12
    return y * 0.55 * vel


def facet(m, dur=0.9, vel=1.0):
    """晶面叮：非谐波 FM，带一点玻璃感"""
    n = t2n(dur); f = mtof(m); t = np.arange(n) / SR
    I = 2.2 * np.exp(-t / 0.08)
    y = np.sin(2 * np.pi * f * t + I * np.sin(2 * np.pi * f * 2.76 * t)) * np.exp(-t / 0.35)
    y += 0.3 * np.sin(2 * np.pi * f * 4.07 * t) * np.exp(-t / 0.06)
    return y * (1 - np.exp(-t / 0.001)) * 0.22 * vel


def airpad(ms, dur, cut=2200):
    n = t2n(dur); t = np.arange(n) / SR
    y = pad(ms, dur, cut, 0.008)
    y += bp(noise(n), 2500, 7000) * 0.015 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.7 * t))
    return y


CH = [  # (bass root, chord tones) — D major, open and bright
    (38, [62, 66, 69, 73]),   # Dmaj7
    (35, [59, 62, 66, 69]),   # Bm7
    (31, [59, 62, 66, 69, 71]),  # Gmaj9-ish (over G)
    (33, [61, 64, 69, 71]),   # A6/9
    (38, [62, 66, 69, 74]),   # D
]


def mus(M, tb, name, root, tones, bi):
    r, ch = CH[bi]
    M.add('music', airpad([x for x in ch[:4]], BAR * 1.05, 1600 + 500 * min(bi, 2)), tb, 0.5 if bi else 0.35, 0, 0.5)
    # harp arpeggio: eighths in the dawn, sixteenths once the mountain rises
    arp = ch + [c + 12 for c in ch]
    step = 4 if bi in (2, 3) else 2
    for k in range(4 * step):
        if bi == 0 and k < 2: continue
        if bi == 4 and k > 3: break
        m = arp[(k * 3 + bi) % len(arp)] + (12 if bi >= 2 and k % 4 == 3 else 0)
        M.add('music', harp(m, 1.2, 0.8 if k % step == 0 else 0.55), tb + k * BEAT / step, 0.42, -0.4 + 0.8 * ((k * 5) % 7) / 6, 0.3)
    if bi >= 1: M.add('music', sub(r - 12 + 12, BAR * (0.95 if bi < 4 else 1.3)), tb, 0.42)
    if bi in (2, 3):
        for q in range(4):
            M.add('drums', kick(0.4, 140, 46, 1.3, 0.12), tb + q * BEAT, 0.8); M.sidechain(tb + q * BEAT, 0.42)
        for q in (1, 3): M.add('drums', clap(), tb + q * BEAT, 0.42 if bi == 2 else 0.25, 0, 0.3)
        for e in range(8): M.add('drums', shaker(), tb + e * BEAT / 2 + BEAT / 4, 0.12, 0.35)
        for e in (3, 6, 11, 14): M.add('music', facet(ch[e % len(ch)] + 24, 0.8), tb + e * BEAT / 4, 0.5, 0.45 if e % 2 else -0.45, 0.5)
    if bi == 1:
        for e in range(8): M.add('drums', shaker(), tb + e * BEAT / 2 + BEAT / 4, 0.07, 0.35)
    if bi == 4:
        M.add('drums', kick(0.5, 140, 44, 1.3, 0.12), tb, 0.8)
        for k, m in enumerate(ch + [ch[0] + 24]): M.add('music', facet(m + 12, 2.0, 0.8), tb + 0.02 * k, 0.45, -0.3 + 0.15 * k, 0.6)


# ---------- SFX ----------
def wind_dawn():
    n = t2n(3.5); t = np.arange(n) / SR
    y = bp(noise(n), 300, 1800) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.4 * t + 1)) * 0.25
    y += bp(noise(n), 2000, 6000) * 0.04
    return y * np.sin(np.pi * np.clip(t / 3.5, 0, 1)) ** 1.5


def facet_chime():
    y = np.zeros(t2n(1.2))
    for i, m in enumerate((nm('A6'), nm('E7'), nm('B6'))):
        x = facet(m, 0.9, 0.8); s0 = t2n(i * 0.07); y[s0:s0 + len(x)] += x[:len(y) - s0]
    return y


def card_wave():
    """一大片三角面像纸牌一样翻起：上百个细小的翻牌声，先密后疏 + 气流"""
    dur = 1.6; n = t2n(dur); y = np.zeros(n); r = np.random.default_rng(32)
    for i in range(140):
        u = (i / 140) ** 0.8
        s0 = t2n(u * (dur - 0.1) + r.random() * 0.01)
        m = t2n(0.03); tt = np.arange(m) / SR
        c = bp(noise(m), 1500 + r.random() * 3000, 9000) * np.exp(-tt / 0.006) * (0.35 + 0.4 * r.random())
        c += sine(500 + r.random() * 600, m) * np.exp(-tt / 0.01) * 0.12
        y[s0:s0 + m] += c[:n - s0] * np.sin(np.pi * min(1, i / 140 * 1.1)) ** 0.5
    t = np.arange(n) / SR
    y += bp(noise(n), 400, 3000) * np.sin(np.pi * t / dur) ** 2 * 0.18
    return y


def facet_lock():
    n = t2n(2.2); y = np.zeros(n); t = np.arange(n) / SR
    y += bp(noise(n), 1200, 8000) * np.exp(-t / 0.01) * 0.6
    y += sine(180 + 120 * np.exp(-t / 0.02), n) * np.exp(-t / 0.08) * 0.5
    for k, m in enumerate((nm('D6'), nm('A6'), nm('F#7'))):
        x = facet(m, 1.8, 0.9); s0 = t2n(0.01 * k); y[s0:s0 + len(x)] += x[:n - s0]
    return y


def mountain_land():
    """the last cards slap down and the mountain locks: low thump + wooden clack cluster + a short facet ring"""
    n = t2n(1.4); t = np.arange(n) / SR; y = np.zeros(n)
    y += sine(48 + 70 * np.exp(-t / 0.03), n) * np.exp(-t / 0.25) * 0.9
    y += bp(noise(n), 900, 6000) * np.exp(-t / 0.012) * 0.5
    for k, m in enumerate((nm('D5'), nm('A5'))):
        x = facet(m, 1.0, 0.7); s0 = t2n(0.01 * k); y[s0:s0 + len(x)] += x[:n - s0]
    return y


def leaf_pop():
    """a crown cluster pops open: soft round pluck + a quick leaf rustle"""
    n = t2n(0.6); t = np.arange(n) / SR
    y = sine(520 * (1 + 0.6 * np.exp(-t / 0.012)), n) * np.exp(-t / 0.07) * 0.5
    y += bp(noise(n), 2500, 9000) * np.exp(-t / 0.06) * (0.6 + 0.4 * np.sin(2 * np.pi * 30 * t)) * 0.25
    h = harp(nm('A5'), 0.5, 0.35); y[:len(h)] += h[:n] * 0.6
    return y


SFX_NEW = {'wind_dawn': wind_dawn, 'facet_chime': facet_chime, 'card_wave': card_wave, 'facet_lock': facet_lock,
           'mountain_land': mountain_land, 'leaf_pop': leaf_pop}
