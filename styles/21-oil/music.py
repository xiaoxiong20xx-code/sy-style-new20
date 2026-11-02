# 21 油画厚涂 · 配乐：室内弦乐 + 钢琴分解和弦 + 小提琴旋律（温暖、浪漫，像画室里的老唱片）
# 音效：调色刀刮颜料（knife）、一串点涂（dabs）、钩子时刻的低频涌起（rise）
import numpy as np


def bowed(m, dur, cut=1800, vib=0.005, att=0.22):
    n = t2n(dur); t = np.arange(n) / SR
    f = mtof(m) * (1 + vib * np.sin(2 * np.pi * 5.4 * t) * np.clip((t - 0.15) / 0.3, 0, 1))
    y = polyblep_saw(f, n) * 0.55 + polyblep_saw(f * 1.004, n) * 0.35 + sine(f, n) * 0.2
    y = lp(y, cut, 2)
    y += bp(noise(n), mtof(m) * 1.5, min(mtof(m) * 6, 9000)) * 0.03          # bow hair
    return y * adsr(n, att, 0.3, 0.85, 0.35) * 0.42


MEL = {'Am': ['E5', None, 'A5', None, 'C6', 'B5', 'A5', None], 'F': ['C6', None, 'A5', None, 'G5', 'F5', 'E5', None],
       'C': ['E5', 'G5', 'C6', None, 'D6', None, 'E6', None], 'G': ['D6', None, 'B5', None, 'G5', 'A5', 'B5', None]}


def mus(M, tb, name, root, tones, bi):
    last = bi == 4
    # string section + cello
    M.add('music', strings([x + 12 for x in tones] + [tones[0] + 24], BAR * (1.6 if last else 1.03), 2800 if bi >= 2 else 2100), tb, 0.48 if bi != 2 else 0.6, 0, 0.6)
    M.add('music', bowed(root - 12, BAR * (1.5 if last else 1.0), 900, 0.003, 0.12), tb, 0.6, -0.15, 0.3)
    # piano: rolling eighth-note arpeggio (ringing)
    arp = [tones[0], tones[1], tones[2], tones[0] + 12, tones[2] + 12, tones[1] + 12, tones[2], tones[1]]
    steps = 0 if last else 8
    for e in range(steps):
        M.add('music', piano(arp[e] + 12, 1.6, 0.75 if e % 2 == 0 else 0.55), tb + e * BEAT / 2, 0.4, -0.3 + 0.6 * (e % 2), 0.45)
    if last:   # the knife lifts on 8.0: one rolled chord, left to ring out
        for j, m in enumerate(tones + [tones[0] + 12, tones[1] + 12]):
            M.add('music', piano(m + 12, 2.8, 0.75), tb + j * 0.035, 0.38, -0.3 + 0.15 * j, 0.6)
    # violin melody from bar 1
    if 1 <= bi <= 3:
        mel = MEL[name]
        e = 0
        while e < 8:
            sN = mel[e]
            if sN:
                L = 1
                while e + L < 8 and mel[e + L] is None: L += 1
                M.add('music', bowed(nm(sN), BEAT / 2 * L * 1.05, 3600, 0.007, 0.08), tb + e * BEAT / 2, 0.36, 0.2, 0.55)
            e += 1
    # gentle pulse
    M.add('drums', soft_kick(), tb, 0.5)
    if not last:
        M.add('drums', soft_kick(), tb + 2 * BEAT, 0.38)
        for q in range(4): M.add('drums', lp(shaker(), 6000), tb + q * BEAT + BEAT / 2, 0.08, 0.35)
    if bi == 2:   # the hook: timpani hit + soft cymbal swell into it
        M.add('drums', taiko() * 1.2, tb + 0.5, 0.7, 0, 0.5)
        n = t2n(0.9); tt = np.arange(n) / SR
        M.add('drums', hp(noise(n), 5000) * (tt / 0.9) ** 2 * 0.25, tb + 0.5 - 0.9, 0.6, 0, 0.4)


def sfx_knife():
    # palette knife dragged through thick paint on linen: gritty scrape + wet smear + tiny clicks
    dur = 0.78; n = t2n(dur); t = np.arange(n) / SR
    am = (0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 23 * t + 3 * np.sin(2 * np.pi * 3.1 * t)))) * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.5
    scrape = bp(noise(n), 1800, 7000) * am * 0.35
    smear = lp(noise(n), 700) * np.sin(np.pi * t / dur) * 0.45
    r = np.random.default_rng(11); clk = np.zeros(n)
    for _ in range(14):
        k = int(r.random() * (n - 300)); clk[k:k + 300] += hp(noise(300), 3000) * np.exp(-np.arange(300) / 40) * 0.25
    land = sine(110 * np.exp(-t / 0.05) + 60, n) * np.exp(-t / 0.06) * 0.35
    return scrape + smear + clk + land


def sfx_dabs():
    out = np.zeros(t2n(0.75))
    for i in range(7):
        n = t2n(0.07); tt = np.arange(n) / SR
        d = bp(noise(n), 900, 5000) * np.sin(np.pi * tt / 0.07) * 0.5 + lp(noise(n), 400) * np.exp(-tt / 0.02) * 0.3
        k = t2n(i * 0.085); out[k:k + n] += d * (0.7 + 0.3 * (i % 2))
    return out


def sfx_rise():
    dur = 1.1; n = t2n(dur); t = np.arange(n) / SR
    body = sine(42 + 18 * (t / dur), n) * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5 * 0.7
    air = svf_bp(noise(n), 200 * (12 ** (t / dur)), 0.5) * (t / dur) ** 2 * np.exp(-((t / dur - 0.8) ** 2) / 0.05) * 0.35
    return body + air


SFX_NEW = {'knife': sfx_knife, 'dabs': sfx_dabs, 'rise': sfx_rise}
