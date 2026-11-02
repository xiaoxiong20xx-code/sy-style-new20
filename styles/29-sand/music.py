# 29 沙画 — a light box in a dark room: felt piano and a bowed cello, a rainstick for the sand, soft heartbeat on
# the whale, small caravan bells over the dunes. Every finger stroke is a dry scrape of sand on glass.
# (synth.py's functions are injected into this module by audio/make_audio.py)

_r = np.random.default_rng(2929)
A2, C3, D3, E3, F3, G3, A3, B3, C4, D4, E4, F4, G4, Gs4, A4, B4, C5, D5, E5 = 45, 48, 50, 52, 53, 55, 57, 59, 60, 62, 64, 65, 67, 68, 69, 71, 72, 74, 76


def felt(m, dur=2.2, vel=1.0):
    n = t2n(dur); f = mtof(m); t = np.arange(n) / SR
    y = sum(a * np.sin(2 * np.pi * f * k * t * (1 + 0.0004 * k * k)) * np.exp(-t * (0.9 + k * 0.8)) for k, a in [(1, 1), (2, .38), (3, .16), (4, .07), (5, .03)])
    y += lp(noise(n), 900) * np.exp(-t / 0.012) * 0.05           # felt hammer thump
    y = lp(y, 2600)
    return y * (1 - np.exp(-t / 0.004)) * 0.45 * vel


def cello(m, dur, amp=1.0):
    n = t2n(dur); f = mtof(m); t = np.arange(n) / SR
    vib = 1 + 0.0045 * np.sin(2 * np.pi * 5.3 * t) * np.clip((t - 0.3) / 0.5, 0, 1)
    y = polyblep_saw(f * vib, n) * 0.6 + polyblep_saw(f * vib * 1.003, n) * 0.4
    y = lp(y, 1400) + bp(y, 250, 600) * 0.4
    y += bp(noise(n), 1500, 4000) * 0.015                          # bow hair
    return y * adsr(n, 0.35, 0.3, 0.85, 0.6) * 0.22 * amp


def rainstick(dur=1.8, amp=1.0, seed=0):
    n = t2n(dur); t = np.arange(n) / SR
    r = np.random.default_rng(seed + 11)
    y = np.zeros(n)
    k = r.integers(0, n - 400, int(dur * 900))
    for i in k:
        L = 240; y[i:i + L] += hp(r.standard_normal(L), 3000) * np.exp(-np.arange(L) / 40) * (0.3 + 0.7 * r.random())
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.8
    return bp(y, 2500, 11000) * env * 0.08 * amp


def caravan_bell(m, amp=1.0):
    n = t2n(1.4); t = np.arange(n) / SR; f = mtof(m)
    y = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / d) for r, a, d in ((1, 1, 0.5), (2.41, 0.5, 0.25), (3.9, 0.3, 0.12)))
    return y * (1 - np.exp(-t / 0.002)) * 0.16 * amp


def heart():
    n = t2n(0.4); t = np.arange(n) / SR
    return sine(55 + 25 * np.exp(-t / 0.03), n) * np.exp(-t / 0.13) * 0.7


def frame_drum(amp=1.0):
    n = t2n(0.3); t = np.arange(n) / SR
    y = sine(70 + 30 * np.exp(-t / 0.02), n) * np.exp(-t / 0.14) * 0.6 + lp(noise(n), 700) * np.exp(-t / 0.012) * 0.25
    return y * amp


def mus(M, tb, name, root, tones, bi):
    E8 = BEAT / 2
    if bi in (0, 1, 3):   # a soft pulse on every beat so the 120 BPM is felt, kept under the piano
        for q in range(4): M.add('drums', frame_drum(1.0 if q == 0 else 0.7), tb + q * BEAT, 0.32)
    if bi == 1:           # the rainstick rises into the palm sweep on 4.0
        r = rainstick(0.7, 1.6, 9); r *= np.linspace(0.2, 1.0, len(r)) ** 2
        M.add('sfx', r, tb + BAR - 0.7, 0.7, 0.2)
    if bi == 2:
        M.add('drums', frame_drum(1.4), tb, 0.6)   # the low landing of the sweep
    if bi == 0:   # Am9: the pour, the first wave line
        M.add('music', cello(A2, BAR + 0.3), tb, 0.5, -0.1, 0.4)
        for e, m in enumerate([A3, E4, B4, C5, None, E4, B4, A4]):
            if m: M.add('music', felt(m, 2.0, 0.9 if e % 4 == 0 else 0.7), tb + e * E8, 0.5, -0.2 + 0.06 * e, 0.45)
        M.add('sfx', rainstick(BAR, 0.8, 1), tb, 0.6, 0.3)
    elif bi == 1:  # Fmaj7: the wave grows
        M.add('music', cello(F3 - 12, BAR + 0.3), tb, 0.5, -0.1, 0.4)
        M.add('music', cello(C4, BAR + 0.3, 0.6), tb, 0.35, 0.2, 0.45)
        for e, m in enumerate([F3, C4, E4, A4, G4, E4, C4, E4]):
            M.add('music', felt(m, 1.8, 0.75), tb + e * E8, 0.45, 0.2 - 0.06 * e, 0.45)
        M.add('sfx', rainstick(BAR, 0.7, 2), tb + 0.3, 0.5, -0.3)
    elif bi == 2:  # C -> G: the whale (hook): melody rises, a soft heartbeat
        M.add('music', cello(C3, BAR / 2 + 0.2), tb, 0.55, -0.1, 0.4)
        M.add('music', cello(G3 - 12, BAR / 2 + 0.4), tb + BAR / 2, 0.55, -0.1, 0.4)
        M.add('music', cello(E4, BAR + 0.3, 0.7), tb, 0.38, 0.2, 0.5)
        for e, m in enumerate([C4, G4, C5, E5, D5, B4, G4, D5]):
            M.add('music', felt(m, 2.0, 0.9 if e in (0, 3) else 0.72), tb + e * E8, 0.5, -0.25 + 0.07 * e, 0.5)
        for q in range(4): M.add('drums', heart(), tb + q * BEAT, 0.55 if q % 2 == 0 else 0.4); M.add('drums', heart(), tb + q * BEAT + 0.16, 0.25)
    elif bi == 3:  # Dm9 -> E: the desert, caravan bells, a Phrygian turn
        M.add('music', cello(D3, BAR / 2 + 0.2), tb, 0.5, -0.1, 0.4)
        M.add('music', cello(E3, BAR / 2 + 0.4), tb + BAR / 2, 0.5, -0.1, 0.4)
        for e, m in enumerate([D4, A4, E5, F4, E4, Gs4, B4, E5]):
            M.add('music', felt(m, 1.8, 0.7), tb + e * E8, 0.45, 0.2 - 0.05 * e, 0.5)
        for k in range(6): M.add('music', caravan_bell([E5 + 12, B4 + 12, E5 + 12, Gs4 + 12, B4 + 12, E5 + 12][k], 0.8), tb + k * BEAT * 0.66 + 0.1, 0.4, 0.35 - 0.1 * k, 0.5)
        M.add('sfx', rainstick(BAR, 0.6, 3), tb, 0.45, 0.3)
    else:          # Am(add9): the title, ringing out
        M.add('music', cello(A2, BAR + 1.0), tb, 0.55, -0.1, 0.5)
        M.add('music', cello(E3 + 12, BAR + 1.0, 0.6), tb, 0.35, 0.2, 0.5)
        for j, m in enumerate([A3, E4, B4, C5, E5]):
            M.add('music', felt(m, 3.5, 0.8), tb + j * 0.06, 0.45, -0.2 + 0.1 * j, 0.55)
        M.add('music', felt(A4 + 12, 3.0, 0.5), tb + BEAT * 2, 0.35, 0.2, 0.6)
        M.add('sfx', rainstick(1.6, 0.5, 4), tb + BEAT, 0.4, -0.2)


# ---------------- sound effects: sand on glass ----------------
def scrape(dur, lo=900, hi=5000, amp=1.0, seed=0):
    n = t2n(dur); t = np.arange(n) / SR
    r = np.random.default_rng(seed + 300)
    gr = np.zeros(n)
    for i in r.integers(0, n - 120, int(dur * 2600)): gr[i:i + 60] += r.standard_normal(60) * np.exp(-np.arange(60) / 12)
    y = bp(gr, lo, hi) * 0.35 + bp(noise(n), lo, hi) * 0.06
    env = np.clip(t / 0.03, 0, 1) * np.clip((dur - t) / 0.08, 0, 1)
    return y * env * amp


def sand_pour():
    n = t2n(1.0); t = np.arange(n) / SR
    return rainstick(1.0, 2.2, 7) * 1.2 + lp(noise(n), 700) * np.sin(np.pi * t / 1.0) * 0.06


def sand_taps():
    out = np.zeros(t2n(0.5))
    for i in range(6):
        k = t2n(i * 0.05 + _r.random() * 0.01); x = scrape(0.035, 1500, 7000, 1.2, i)
        out[k:k + len(x)] += x[: len(out) - k]
    return out


def sand_flicks():
    out = np.zeros(t2n(0.55))
    for i in range(5):
        k = t2n(i * 0.08); x = scrape(0.07, 1200, 6500, 1.1, 20 + i)
        out[k:k + len(x)] += x[: len(out) - k]
    return out


def sand_sweep():
    n = t2n(0.75); t = np.arange(n) / SR
    y = scrape(0.75, 400, 6000, 1.6, 40) + svf_bp(noise(n), 600 + 2400 * np.sin(np.pi * t / 0.75), 0.6) * np.sin(np.pi * t / 0.75) * 0.15
    return y


def sand_swirl():
    n = t2n(0.5); t = np.arange(n) / SR
    return scrape(0.5, 800, 5000, 1.2, 50) * (0.7 + 0.3 * np.sin(2 * np.pi * 6.4 * t))


def sand_write():
    out = np.zeros(t2n(0.45))
    for i in range(4):
        k = t2n(i * 0.1); x = scrape(0.09, 1000, 5500, 1.0, 60 + i)
        out[k:k + len(x)] += x[: len(out) - k]
    return out


def sand_taps6():
    out = np.zeros(t2n(0.6))
    for i in range(6):
        k = t2n(i * 0.06); x = scrape(0.035, 1500, 7000, 1.2, 80 + i)
        out[k:k + len(x)] += x[: len(out) - k]
    return out


def sand_steps():
    out = np.zeros(t2n(0.6))
    for i in range(7):
        k = t2n(i * 0.045); x = scrape(0.03, 1200, 6000, 1.1, 90 + i)
        out[k:k + len(x)] += x[: len(out) - k]
    return out


def star_bell():
    n = t2n(2.2); t = np.arange(n) / SR
    y = sum(a * np.sin(2 * np.pi * mtof(E5 + 12) * r * t) * np.exp(-t / d) for r, a, d in ((1, 1, 0.9), (2.76, 0.35, 0.4), (5.4, 0.15, 0.2)))
    return y * (1 - np.exp(-t / 0.002)) * 0.14


SFX_NEW = {'sand_taps6': sand_taps6, 'sand_steps': sand_steps, 'star_bell': star_bell, 'sand_pour': sand_pour, 'sand_line': lambda: scrape(0.42, 900, 5000, 1.1, 1), 'sand_taps': sand_taps, 'sand_flicks': sand_flicks,
           'sand_sweep': sand_sweep, 'sand_swirl': sand_swirl, 'sand_write': sand_write}
