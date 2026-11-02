# 37 凸版烫金 — a print studio after hours: noir lounge. Upright bass, Rhodes-like electric piano, brushes, a press that
# keeps time with a heavy thunk, a clock escapement; celesta glints when the gold appears; a warm D major at the end.
# (synth.py's functions are injected into this module by audio/make_audio.py)

_r = np.random.default_rng(3737)
D2, F2, G2, A2, Bb2, D3, E3, F3, G3, A3, Bb3, C4, D4, E4, F4, Fs4, G4, A4, Bb4, C5, Cs5, D5, E5, F5, Fs5, A5 = \
    38, 41, 43, 45, 46, 50, 52, 53, 55, 57, 58, 60, 62, 64, 65, 66, 67, 69, 70, 72, 73, 74, 76, 77, 78, 81
CH = {0: [F3, A3, C4, E4], 1: [D4 - 12, F3, A3, C4], 2: [Bb3 - 12, D4 - 12, F3, A3], 3: [Cs5 - 24, G3, Bb3, E4], 4: [Fs4 - 12, A3, Cs5 - 12, E4]}
ROOT = {0: D2, 1: Bb2 - 12, 2: G2, 3: A2, 4: D2}
WALK = {0: [D2, F2, A2, C4 - 24], 1: [Bb2 - 12, D2, F2, A2], 2: [G2, Bb2, D3, F3 - 12], 3: [A2, Cs5 - 36, E3 - 12, G2], 4: [D2, D2, D2, D2]}


def rhodes(m, dur=1.6, amp=1.0):
    n = t2n(dur); f = mtof(m); t = np.arange(n) / SR
    I = 1.3 * np.exp(-t / 0.4)
    y = np.sin(2 * np.pi * f * t + I * np.sin(2 * np.pi * f * t)) * np.exp(-t / 1.4)
    y += 0.12 * np.sin(2 * np.pi * f * 7 * t) * np.exp(-t / 0.03)
    y *= 1 + 0.12 * np.sin(2 * np.pi * 4.5 * t)                     # tremolo
    return y * (1 - np.exp(-t / 0.003)) * 0.3 * amp


def celesta(m, dur=1.2, amp=1.0):
    n = t2n(dur); f = mtof(m); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.6) + 0.3 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t / 0.12)
    return y * (1 - np.exp(-t / 0.001)) * 0.22 * amp


def press_thunk(amp=1.0):
    n = t2n(0.5); t = np.arange(n) / SR
    y = sine(48 + 50 * np.exp(-t / 0.02), n) * np.exp(-t / 0.18) * 0.9 + lp(noise(n), 600) * np.exp(-t / 0.03) * 0.4
    return y * amp


def escapement():
    n = t2n(0.05); t = np.arange(n) / SR
    return (bp(noise(n), 2500, 6000) * np.exp(-t / 0.004) * 0.5 + sine(3100, n) * np.exp(-t / 0.01) * 0.1)


def mus(M, tb, name, root, tones, bi):
    ch = CH[bi]
    # the press keeps time: thunk on 1, clock on every 8th, brushes swish on 2 and 4
    if bi < 4:
        M.add('drums', press_thunk(0.9 if bi != 2 else 1.1), tb, 0.7)
        for e in range(8): M.add('drums', escapement(), tb + e * BEAT / 2, 0.28 if e % 2 else 0.4, 0.35)
        for q in (1, 3): M.add('drums', brush(0.3), tb + q * BEAT - 0.05, 0.9, -0.2)
    # upright bass, walking
    for q, m in enumerate(WALK[bi]):
        if bi == 4 and q > 0: break
        M.add('music', upright(m, BEAT * (0.9 if bi < 4 else 3.5)), tb + q * BEAT, 0.62)
    # electric piano: comping on 1 and the "and" of 2
    for j, m in enumerate(ch):
        M.add('music', rhodes(m + 12, 1.8, 0.9), tb + j * 0.012, 0.36, -0.2 + 0.13 * j, 0.35)
        if bi < 4: M.add('music', rhodes(m + 12, 1.2, 0.6), tb + BEAT * 1.5 + j * 0.012, 0.28, -0.2 + 0.13 * j, 0.35)
    if bi == 0:
        M.add('music', rhodes(D5, 1.5), tb + BEAT * 2.5, 0.3, 0.2, 0.4)
    if bi == 2:   # the gold appears
        for e, m in enumerate([D5, F5, A5, C5 + 12, A5, F5, E5, D5]):
            M.add('music', celesta(m, 1.0), tb + e * BEAT / 2, 0.36, 0.3 - 0.08 * e, 0.5)
    if bi == 3:
        for e, m in enumerate([E5, Cs5, A4, G4]): M.add('music', rhodes(m, 1.2, 0.8), tb + BEAT * (1 + e * 0.75), 0.26, 0.2, 0.4)
    if bi == 4:   # D major (with a ninth): warm, golden
        for j, m in enumerate([D4, Fs4, A4, Cs5, E5]):
            M.add('music', rhodes(m, 3.5, 0.9), tb + j * 0.03, 0.36, -0.25 + 0.12 * j, 0.45)
        for e, m in enumerate([A5, Fs5, D5 + 12, A5]):
            M.add('music', celesta(m, 1.6, 0.8), tb + BEAT * (0.5 + e * 0.5), 0.3, 0.3 - 0.15 * e, 0.6)
        M.add('drums', ride(True), tb, 0.35, 0.3)


# ---------------- sound effects ----------------
def press_down():
    n = t2n(0.85); t = np.arange(n) / SR
    y = svf_bp(noise(n), 200 + 500 * (t / 0.85), 0.5) * (t / 0.85) ** 1.5 * 0.3
    y += sine(90 + 40 * (t / 0.85), n) * (t / 0.85) ** 2 * 0.15
    return y


def press_hit():
    n = t2n(1.0); t = np.arange(n) / SR
    boom = sine(42 + 70 * np.exp(-t / 0.03), n) * np.exp(-t / 0.3) * 1.0
    clank = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / d) for f, a, d in ((410, .3, .25), (1130, .2, .12), (2350, .12, .06))) * 0.6
    crunch = bp(noise(n), 300, 3000) * np.exp(-t / 0.025) * 0.5
    return np.tanh((boom + clank + crunch) * 1.3)


def press_lift():
    n = t2n(0.8); t = np.arange(n) / SR
    hiss = hp(noise(n), 3000) * np.exp(-t / 0.25) * 0.15
    creak = sine(260 + 60 * np.sin(2 * np.pi * 3 * t), n) * np.exp(-t / 0.3) * 0.08
    suction = lp(noise(n), 900) * np.exp(-t / 0.04) * 0.3
    return hiss + creak + suction


def foil_peel():
    n = t2n(1.05); t = np.arange(n) / SR
    out = np.zeros(n)
    for k in _r.integers(0, n - 300, 260):
        L = 120 + int(_r.random() * 150); out[k:k + L] += hp(noise(L), 2500) * np.exp(-np.arange(L) / 30) * (0.2 + 0.6 * _r.random())
    env = np.sin(np.pi * np.clip(t / 1.05, 0, 1)) ** 0.6
    return bp(out, 1800, 11000) * env * 0.5 + svf_bp(noise(n), 1500 + 2500 * t / 1.05, 0.6) * env * 0.08


def gold_glint():
    out = np.zeros(t2n(1.6))
    for i, m in enumerate([A5 + 12, D5 + 24, Fs5 + 12, A5 + 24]):
        c = celesta(m, 1.2, 0.8); k = t2n(i * 0.06); out[k:k + len(c)] += c[: len(out) - k]
    return out


def light_sweep():
    n = t2n(1.4); t = np.arange(n) / SR
    return svf_bp(noise(n), 800 + 3000 * np.sin(np.pi * t / 1.4), 0.7) * np.sin(np.pi * t / 1.4) ** 2 * 0.12


SFX_NEW = {'press_down': press_down, 'press_hit': press_hit, 'press_lift': press_lift, 'foil_peel': foil_peel,
           'gold_glint': gold_glint, 'light_sweep': light_sweep, 'final_glint': gold_glint}
