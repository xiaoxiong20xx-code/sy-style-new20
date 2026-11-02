# 35 字符画 — a terminal in a dark room: a Berlin-school analog sequencer (16th-note arpeggio through a resonant
# low-pass that opens as the camera dives into the glass), a pulse bass, clock ticks, a soft kick; CRT power-on thunk,
# high-voltage whine, a mechanical keyboard and a terminal beep.
# (synth.py's functions are injected into this module by audio/make_audio.py)

_r = np.random.default_rng(3535)
A1, A2, C3, D3, E3, F2, G2, A3, C4, D4, E4, G3, G4, A4, C5, E5 = 33, 45, 48, 50, 52, 41, 43, 57, 60, 62, 64, 55, 67, 69, 72, 76
SEQ = {0: [A2, A3, E3, A3, C4, A3, G3, A3], 1: [A2, A3, E3, A3, C4, A3, G3, E4], 2: [F2 + 12, C4, A3, C4, F2 + 24, C4, A3, E4],
       3: [G2 + 12, D4, G3, D4, G2 + 24, D4, 59, D4], 4: [A2, E3, A3, C4, E4, A4, C5, E5]}
BASS = {0: A1, 1: A1, 2: F2 - 12, 3: G2 - 12, 4: A1}
CUT = {0: (250, 600), 1: (600, 1500), 2: (1500, 5200), 3: (2400, 1400), 4: (1200, 2600)}


def seq_note(m, dur, cut, res=0.22):
    n = t2n(dur); f = mtof(m); t = np.arange(n) / SR
    x = polyblep_saw(f, n) * 0.55 + square(f * 0.5, n, 0.5) * 0.25 + polyblep_saw(f * 1.004, n) * 0.35
    fc = cut * (0.35 + 0.65 * np.exp(-t / 0.07)) + 120
    return svf_lp(x, fc, res) * adsr(n, 0.002, 0.06, 0.55, 0.04) * 0.5


def pulse_bass(m, dur):
    n = t2n(dur); f = mtof(m)
    x = square(f, n, 0.32) * 0.5 + sine(f, n) * 0.6
    return lp(x, 420) * adsr(n, 0.004, 0.08, 0.75, 0.05) * 0.8


def clock_tick(amp=1.0):
    n = t2n(0.02)
    return hp(noise(n), 6000) * expenv(n, 0.003) * 0.4 * amp


def mus(M, tb, name, root, tones, bi):
    S = BEAT / 4
    c0, c1 = CUT[bi]
    seq = SEQ[bi]
    for s in range(16):
        if bi == 0 and s < 2: continue                      # the tube warms up first
        if bi == 4: break                                    # the last bar: the sequencer stops, the chord rings
        cut = c0 + (c1 - c0) * (s / 15)
        M.add('music', seq_note(seq[s % 8], S * 0.95, cut), tb + s * S, 0.42 if s % 4 == 0 else 0.3, 0.25 * np.sin(s * 0.9), 0.3)
        M.add('drums', clock_tick(1.2 if s % 4 == 0 else 0.7), tb + s * S, 0.35, 0.4)
    if bi >= 1:
        for q in range(4): M.add('music', pulse_bass(BASS[bi] + (12 if q % 2 else 0), BEAT * 0.45), tb + q * BEAT + BEAT / 2, 0.5)
    if bi in (1, 2, 3):
        for q in range(4): M.add('drums', kick(0.3, 120, 48, 1.2, 0.05), tb + q * BEAT, 0.6 if bi == 2 else 0.45); M.sidechain(tb + q * BEAT, 0.3)
    if bi == 2:
        M.add('music', pad([A3, C4, E4, G4], BAR + 0.5, 1800, 0.01), tb, 0.35, 0, 0.5)
    if bi == 4:   # resolve on 8.0 and ring out
        M.add('music', pad([A3, C4, E4, A4], BAR + 0.2, 2200, 0.01), tb, 0.42, 0, 0.55)
        M.add('music', pulse_bass(A1, BAR * 0.95), tb, 0.5)
        for k, m in enumerate([A3, E4, A4, C5]):
            M.add('music', seq_note(m, 1.4, 1800, 0.3), tb + k * BEAT / 2, 0.3 - 0.04 * k, -0.3 + 0.2 * k, 0.5)


# ---------------- sound effects ----------------
def crt_on():
    n = t2n(1.3); t = np.arange(n) / SR
    thunk = sine(70 + 60 * np.exp(-t / 0.03), n) * np.exp(-t / 0.12) * 0.8
    crack = hp(noise(n), 2500) * np.exp(-t / 0.05) * 0.35
    whine = sine(7800 + 40 * np.sin(2 * np.pi * 3 * t), n) * np.clip((t - 0.1) / 0.3, 0, 1) * np.exp(-t / 0.8) * 0.03
    degauss = sine(60, n) * np.exp(-t / 0.45) * (1 + 0.5 * np.sin(2 * np.pi * 9 * t)) * 0.25
    static = bp(noise(n), 800, 6000) * np.exp(-((t - 0.35) / 0.15) ** 2) * 0.12
    return (thunk + crack + whine + degauss + static) * 0.7


def rain_ticks():
    out = np.zeros(t2n(0.9))
    for i in range(26):
        k = int(_r.random() * (len(out) - 600)); f = 2000 + _r.random() * 3000
        x = sine(f, 300) * expenv(300, 0.0015) * (0.1 + 0.15 * _r.random()); out[k:k + 300] += x
    return out


def dive():
    n = t2n(1.3); t = np.arange(n) / SR
    y = svf_bp(noise(n), 200 * (30 ** (t / 1.3)), 0.4) * (t / 1.3) ** 1.6 * 0.5
    y += sine(55 * (1 + 0.5 * (t / 1.3) ** 2), n) * (t / 1.3) ** 2 * 0.3
    return y * 0.5


def crt_hum_close():
    n = t2n(0.8); t = np.arange(n) / SR
    return (sine(60, n) * 0.25 + sine(120, n) * 0.12 + sine(7800, n) * 0.025) * np.sin(np.pi * t / 0.8)


def rain_out():
    out = np.zeros(t2n(0.8))
    for i in range(18):
        k = int(i / 18 * (len(out) - 800)); f = 3000 - i * 120
        x = sine(f, 400) * expenv(400, 0.002) * 0.22; out[k:k + 400] += x
    return out


def key():
    n = t2n(0.07); t = np.arange(n) / SR
    click = bp(noise(n), 2500, 7000) * np.exp(-t / 0.004) * 0.6
    thock = sine(180 + 120 * np.exp(-t / 0.01), n) * np.exp(-t / 0.02) * 0.35 + lp(noise(n), 1200) * np.exp(-t / 0.012) * 0.25
    return (click + thock) * (0.85 + 0.3 * _r.random())


def printout():
    out = np.zeros(t2n(0.5))
    for i in range(30):
        k = t2n(i * 0.014); x = hp(noise(220), 1800) * expenv(220, 0.002) * 0.3; out[k:k + 220] += x
    return out


def beep_ok():
    n = t2n(0.13)
    return lp(square(880, n, 0.5), 3000) * adsr(n, 0.003, 0.02, 0.8, 0.02) * 0.18


def key_enter():
    x = key() * 1.3
    n = t2n(0.12); t = np.arange(n) / SR
    thunk = sine(120 * np.exp(-t / 0.02) + 60, n) * np.exp(-t / 0.03) * 0.4
    out = np.zeros(max(len(x), n)); out[:len(x)] += x; out[:n] += thunk
    return out


SFX_NEW = {'key_enter': key_enter, 'crt_on': crt_on, 'rain_ticks': rain_ticks, 'dive': dive, 'crt_hum_close': crt_hum_close, 'rain_out': rain_out,
           'key': key, 'printout': printout, 'beep_ok': beep_ok}
