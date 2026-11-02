# 28 彩色玻璃窗 — a stone chapel at dawn: a wordless choir ("aah" formants), a soft pipe organ, tubular bells and
# glass chimes. One bell per pane-band on the beat (rising), the choir and organ pedal open up when the sun breaks
# through, harp-like plucks while the light slides over the floor, and a full D major chord on the title.
# (synth.py's functions are injected into this module by audio/make_audio.py)

_r = np.random.default_rng(2828)
D3, Fs3, A3, B3, D4, E4, Fs4, G4, A4, B4, Cs5, D5, E5, Fs5, A5 = 50, 54, 57, 59, 62, 64, 66, 67, 69, 71, 73, 74, 76, 78, 81
CH = {0: [D4, Fs4, A4, D5], 1: [B3, D4, Fs4, B4], 2: [G4 - 12, B3, D4, G4], 3: [A3, Cs5 - 12, E4, A4], 4: [D4, Fs4, A4, D5]}
BASS = {0: D3, 1: B3 - 12, 2: G4 - 24, 3: A3 - 12, 4: D3}


def choir(ms, dur, vowel='a', amp=1.0):
    n = t2n(dur); t = np.arange(n) / SR
    src = np.zeros(n)
    for m in ms:
        for v in range(3):
            f = mtof(m) * (1 + 0.006 * (v - 1)) * (1 + 0.004 * np.sin(2 * np.pi * (5.1 + 0.4 * v) * t + v))
            src += polyblep_saw(f, n) * 0.3
    src = lp(src, 3500)
    F = {'a': [(800, 1.0), (1150, 0.6), (2900, 0.25)], 'o': [(450, 1.0), (800, 0.55), (2830, 0.15)]}[vowel]
    y = sum(a * bp(src, f * 0.88, f * 1.12) for f, a in F)
    y += bp(noise(n), 900, 4000) * 0.02                          # breath
    return y / max(1, len(ms)) * adsr(n, 0.45, 0.4, 0.9, 0.9) * 1.6 * amp


def organ(ms, dur, amp=1.0):
    n = t2n(dur); t = np.arange(n) / SR; y = np.zeros(n)
    for m in ms:
        f = mtof(m)
        for h, a in ((0.5, 0.5), (1, 1.0), (2, 0.55), (3, 0.25), (4, 0.3), (8, 0.08)):
            y += a * np.sin(2 * np.pi * f * h * t * (1 + 0.0007 * np.sin(2 * np.pi * 0.7 * t)))
    y *= 1 + 0.03 * np.sin(2 * np.pi * 6.2 * t)
    return y / max(1, len(ms)) * adsr(n, 0.12, 0.2, 0.85, 0.6) * 0.18 * amp


def tubular(m, dur=3.0, amp=1.0):
    n = t2n(dur); t = np.arange(n) / SR; f = mtof(m)
    y = np.zeros(n)
    for r, a, d in ((1.0, 1.0, 1.8), (2.76, 0.5, 1.1), (5.4, 0.3, 0.6), (8.93, 0.15, 0.3)):
        y += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / d)
    return y * (1 - np.exp(-t / 0.002)) * 0.22 * amp


def harp(m, dur=1.6):
    return ks(m, dur, 0.45, 0.998) * 0.7


def mus(M, tb, name, root, tones, bi):
    ch = CH[bi]
    if bi == 0:
        M.add('music', organ([x for x in ch[:3]], BAR + 0.4, 0.6), tb, 0.45, 0, 0.6)
        M.add('music', choir([D4, A4], BAR + 0.4, 'o', 0.5), tb, 0.35, 0, 0.7)
    elif bi == 1:
        M.add('music', organ(ch[:3], BAR + 0.4, 0.75), tb, 0.5, 0, 0.6)
        M.add('music', choir([B3, Fs4], BAR + 0.4, 'o', 0.6), tb, 0.4, 0, 0.7)
        M.add('music', organ([BASS[bi]], BAR, 0.6), tb, 0.4, 0, 0.3)
    elif bi == 2:   # the sun breaks through
        M.add('music', choir(ch + [ch[1] + 12], BAR + 0.6, 'a', 1.2), tb, 0.6, 0, 0.8)
        M.add('music', organ(ch, BAR + 0.4, 1.0), tb, 0.55, 0, 0.6)
        M.add('music', organ([BASS[bi], BASS[bi] + 12], BAR + 0.4, 1.2), tb, 0.6, 0, 0.3)
        M.add('music', tubular(G4 + 12, 3.5), tb, 0.45, -0.2, 0.7)
        for e, m in enumerate([G4, B4, D5, G4 + 12, D5, B4, G4 + 12, B4 + 12]):
            M.add('music', harp(m + 0, 1.4), tb + e * BEAT / 2, 0.3, -0.3 + 0.08 * e, 0.6)
    elif bi == 3:   # the light slides over the floor
        M.add('music', choir([A3, E4, A4], BAR + 0.4, 'a', 0.9), tb, 0.5, 0, 0.8)
        M.add('music', organ(ch, BAR + 0.4, 0.8), tb, 0.45, 0, 0.6)
        M.add('music', organ([BASS[bi]], BAR + 0.4, 1.0), tb, 0.5, 0, 0.3)
        for e, m in enumerate([A4, Cs5, E5, A5, E5, Cs5, A4, E5]):
            M.add('music', harp(m, 1.4), tb + e * BEAT / 2, 0.3, 0.3 - 0.08 * e, 0.6)
    else:           # the title: full chord, bells ringing out
        M.add('music', choir([D4, Fs4, A4, D5], BAR + 1.2, 'a', 1.1), tb, 0.6, 0, 0.9)
        M.add('music', organ([D3, D4, A4, D5, Fs5], BAR + 1.2, 1.0), tb, 0.55, 0, 0.7)
        M.add('music', tubular(D5, 3.5), tb, 0.5, -0.25, 0.8)
        M.add('music', tubular(A4, 3.5), tb + BEAT, 0.35, 0.25, 0.8)
        M.add('music', tubular(Fs5, 3.0), tb + BEAT * 2, 0.3, 0.0, 0.8)


# ---------------- sound effects ----------------
def glass_ting(m, amp=1.0):
    n = t2n(2.2); t = np.arange(n) / SR; f = mtof(m)
    y = np.zeros(n)
    for r, a, d in ((1.0, 1.0, 1.2), (2.32, 0.45, 0.6), (4.25, 0.25, 0.3), (6.8, 0.12, 0.15)):
        y += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / d)
    y += hp(noise(n), 5000) * np.exp(-t / 0.01) * 0.1
    return y * 0.22 * amp


PANE = [D5, E5, Fs5, A5, 83, 86, 88]   # D E F# A B D E, rising with the light


def sun_burst():
    n = t2n(2.6); t = np.arange(n) / SR
    swell_ = svf_bp(noise(n), 400 + 5000 * np.clip(t / 0.5, 0, 1), 0.5) * np.clip(t / 0.08, 0, 1) * np.exp(-np.clip(t - 0.08, 0, None) / 0.9) * 0.25
    boom = sine(42 + 30 * np.exp(-t / 0.1), n) * np.exp(-t / 0.9) * 0.5
    shim = sum(glass_ting(m, 0.45) for m in (A5, D5 + 12, Fs5 + 12))
    out = swell_ + boom
    out[:len(shim)] += shim[:n]
    return out


def air_move():
    n = t2n(1.6); t = np.arange(n) / SR
    return svf_bp(noise(n), 300 + 900 * np.sin(np.pi * t / 1.6), 0.6) * np.sin(np.pi * t / 1.6) ** 2 * 0.3


def letter_on():
    return glass_ting(int(_r.choice([D5 + 12, A5, Fs5 + 12, E5 + 12])), 0.6)


def title_glow():
    out = np.zeros(t2n(2.4))
    for i, m in enumerate([D5 + 12, A5, Fs5 + 12, D5 + 24]):
        g = glass_ting(m, 0.55); k = t2n(i * 0.07); out[k:k + len(g)] += g[: len(out) - k]
    return out


SFX_NEW = {f'pane_{i + 1}': (lambda m=m: glass_ting(m)) for i, m in enumerate(PANE)}
SFX_NEW.update({'sun_burst': sun_burst, 'air_move': air_move, 'letter_on': letter_on, 'title_glow': title_glow})
