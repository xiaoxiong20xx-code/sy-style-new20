# 24 湿拓流彩 — ebru is Turkish: an oud-like plucked string in D Hijaz, bendir frame drum (maqsum), finger cymbals,
# a breathy ney and a low drone. Sparse while the drops fall, full groove on the comb, airy over the paper, cadence on the print.
# (synth.py's functions are injected into this module by audio/make_audio.py)

D4, Eb4, Fs4, G4, A4, Bb4, C5, D5 = 62, 63, 66, 67, 69, 70, 72, 74
_r = np.random.default_rng(2424)


def oud(m, dur=0.9, bright=0.55):
    # plucked fretless lute: KS string + short pick noise + hollow body resonance, a tiny pitch drop at the attack
    y = ks(m, dur, bright, 0.9955)
    n = len(y); t = np.arange(n) / SR
    y = y + 0.25 * bp(y, 180, 700)
    y += bp(noise(n), 1500, 5000) * np.exp(-t / 0.006) * 0.12
    return y * 0.9


def dum():
    n = t2n(0.5); t = np.arange(n) / SR
    y = sine(58 + 40 * np.exp(-t / 0.03), n) * np.exp(-t / 0.22)
    y += lp(noise(n), 500) * np.exp(-t / 0.03) * 0.35
    return y * 0.95


def tek():
    n = t2n(0.16); t = np.arange(n) / SR
    y = bp(noise(n), 1800, 6000) * np.exp(-t / 0.02) * 0.6
    y += sine(420, n) * np.exp(-t / 0.035) * 0.2          # the skin's ring near the rim
    return y


def zil(dur=1.1, amp=1.0):
    n = t2n(dur); t = np.arange(n) / SR
    y = np.zeros(n)
    for f, a, d in ((2960, 1.0, 0.7), (4410, 0.6, 0.5), (6150, 0.45, 0.35), (7930, 0.3, 0.25)):
        y += a * np.sin(2 * np.pi * f * t * (1 + 0.0015 * np.sin(2 * np.pi * 6 * t))) * np.exp(-t / d)
    return y * (1 - np.exp(-t / 0.0015)) * 0.12 * amp


def ney(m, dur):
    n = t2n(dur); f = mtof(m); t = np.arange(n) / SR
    vib = 1 + 0.007 * np.sin(2 * np.pi * 4.6 * t) * np.clip((t - 0.25) / 0.4, 0, 1)
    y = sine(f * vib, n) + 0.18 * sine(2 * f * vib, n) + 0.06 * sine(3 * f * vib, n)
    y += bp(noise(n), f * 0.9, f * 4) * 0.22                # breath
    return y * adsr(n, 0.18, 0.2, 0.85, 0.35) * 0.32


def drone(ms, dur, cut=650):
    n = t2n(dur); y = np.zeros(n)
    for m in ms:
        f = mtof(m)
        for d in (-0.004, 0.0, 0.005):
            y += polyblep_saw(f * (1 + d), n) * 0.3
    return lp(y, cut, 2) / len(ms) * adsr(n, 0.6, 0.3, 0.9, 0.8)


MAQSUM = ['D', 'T', None, 'T', 'D', None, 'T', None]


def mus(M, tb, name, root, tones, bi):
    E8 = BEAT / 2
    if bi == 0:      # the drops: one oud note answers each drop
        M.add('music', drone([D4 - 24, A4 - 24], BAR + 0.4), tb, 0.55, 0, 0.3)
        for k, m in enumerate([D4, A4, Bb4, A4]):
            M.add('music', oud(m, 1.1), tb + k * BEAT, 0.5, -0.25 + 0.15 * k, 0.35)
        M.add('music', ney(D5, BAR * 0.9), tb + 0.1, 0.25, 0.2, 0.5)
    elif bi == 1:    # the volleys: the groove arrives
        M.add('music', drone([D4 - 24, A4 - 24], BAR + 0.4), tb, 0.55, 0, 0.3)
        for e, m in enumerate([D4, Fs4, A4, Fs4, G4, A4, Bb4, A4]):
            M.add('music', oud(m, 0.6), tb + e * E8, 0.45 if e % 2 == 0 else 0.33, -0.2 + 0.05 * e, 0.3)
        for e, h in enumerate(MAQSUM):
            if h == 'D': M.add('drums', dum(), tb + e * E8, 0.75 if e == 0 else 0.55)
            elif h == 'T': M.add('drums', tek(), tb + e * E8, 0.45, 0.2)
    elif bi == 2:    # the comb: full maqsum, zils, a running oud line
        M.add('music', drone([D4 - 24, A4 - 24, D4 - 12], BAR + 0.4, 900), tb, 0.6, 0, 0.3)
        run = [D5, C5, Bb4, A4, Bb4, A4, G4, Fs4, G4, Fs4, Eb4, D4, Eb4, Fs4, G4, A4]
        for s, m in enumerate(run):
            M.add('music', oud(m, 0.45, 0.6), tb + s * BEAT / 4, 0.36 if s % 4 == 0 else 0.26, 0.15 * np.sin(s), 0.25)
        for e, h in enumerate(MAQSUM):
            if h == 'D': M.add('drums', dum(), tb + e * E8, 0.85)
            elif h == 'T': M.add('drums', tek(), tb + e * E8, 0.5, 0.2)
            if e % 2 == 1: M.add('drums', zil(0.6), tb + e * E8, 0.5, 0.35, 0.3)
        M.add('music', ney(A4, BAR * 0.95), tb, 0.32, -0.1, 0.5)
    elif bi == 3:    # the paper: air, ney melody over the drone
        M.add('music', drone([D4 - 24, A4 - 24], BAR + 0.4, 520), tb, 0.55, 0, 0.35)
        for k, (m, d) in enumerate([(A4, 0.9), (Bb4, 0.4), (A4, 0.6), (G4, 0.5), (Fs4, 1.0)]):
            off = [0, 0.9, 1.3, 1.9, 2.4][k] * BEAT
            M.add('music', ney(m, d * BEAT * 1.6), tb + off, 0.36, 0.1, 0.55)
        for e in (0, 4): M.add('drums', dum(), tb + e * E8, 0.4)
        for e in (3, 6): M.add('drums', tek(), tb + e * E8, 0.25, 0.25)
    else:            # the print: cadence, a strummed chord and cymbals ringing out
        M.add('music', drone([D4 - 24, A4 - 24, D4 - 12], BAR + 1.0, 800), tb, 0.6, 0, 0.4)
        for j, m in enumerate([D4 - 12, A4 - 12, D4, Fs4, A4, D5]):
            M.add('music', oud(m, 2.4, 0.5), tb + j * 0.025, 0.42, -0.3 + 0.12 * j, 0.45)
        M.add('drums', dum(), tb, 0.85)
        M.add('drums', zil(1.6), tb + BEAT, 0.7, -0.3, 0.5); M.add('drums', zil(1.6), tb + BEAT + 0.06, 0.5, 0.35, 0.5)
        M.add('music', oud(A4, 1.2), tb + BEAT * 1.5, 0.3, 0.2, 0.4)
        M.add('music', oud(D5, 1.6), tb + BEAT * 2, 0.32, 0.25, 0.45)
        M.add('music', ney(D5, BAR * 0.9), tb + BEAT * 0.5, 0.22, 0.1, 0.6)


# ---------------- sound effects ----------------
def plink(f0=900, amp=0.45):
    n = t2n(0.16); t = np.arange(n) / SR
    return sine(f0 + 1600 * (t / 0.16) ** 0.55, n) * np.exp(-t / 0.045) * amp


def drip_volley():
    out = np.zeros(t2n(0.4))
    for i in range(6):
        p = plink(700 + _r.random() * 700, 0.22 + 0.12 * _r.random()); k = t2n(_r.random() * 0.06)
        out[k:k + len(p)] += p
    return out


def comb_drag(dur=0.6, bright=1.0):
    n = t2n(dur); t = np.arange(n) / SR
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.7
    fc = 380 + 1400 * bright * (t / dur)
    y = svf_bp(noise(n), fc, 0.35) * 0.55
    y *= 0.7 + 0.3 * np.sin(2 * np.pi * (18 if bright < 1.2 else 34) * t)     # pins passing through the size
    y += sine(130 + 50 * np.sin(2 * np.pi * 7 * t), n) * 0.08                    # low wet gurgle
    return y * env


def paper_lay():
    n = t2n(1.0); t = np.arange(n) / SR
    air = svf_bp(noise(n), 400 + 1400 * (t / 1.0), 0.5) * np.sin(np.pi * t / 1.0) ** 2 * 0.3
    return air


def wet_contact():
    n = t2n(0.75); t = np.arange(n) / SR
    y = lp(noise(n), 1400) * np.sin(np.pi * t / 0.75) ** 0.8 * 0.25
    y += sine(110 * np.exp(-t / 0.08) + 50, n) * np.exp(-t / 0.07) * 0.35
    return y


def paper_peel():
    n = t2n(0.6); t = np.arange(n) / SR
    crackle = np.zeros(n)
    for k in _r.integers(0, n - 200, 140): crackle[k:k + 60] += hp(noise(60), 2500) * (k / n) * 0.5
    y = bp(noise(n), 700, 4500) * (t / 0.6) ** 1.5 * 0.3 + crackle
    y[-t2n(0.06):] *= np.linspace(1, 0, t2n(0.06))
    return y


def reveal_shimmer():
    return over(zil(1.8, 0.9), np.concatenate([np.zeros(t2n(0.05)), zil(1.6, 0.6)]))


def paper_peel_long():
    n = t2n(1.3); t = np.arange(n) / SR
    crackle = np.zeros(n)
    win = np.hanning(140)
    for k in _r.integers(0, n - 200, 220): crackle[k:k + 140] += bp(noise(140), 1800, 7000) * win * (0.3 + 0.5 * (k / n)) * 0.3   # soft wet tearing, no hard clicks
    suck = lp(noise(n), 900) * np.sin(np.pi * np.clip(t / 1.25, 0, 1)) ** 2 * 0.2
    y = bp(noise(n), 700, 4500) * np.sin(np.pi * np.clip(t / 1.25, 0, 1)) * 0.22 + crackle + suck
    drips = np.zeros(n)
    for i in range(5):
        p_ = plink(500 + 300 * i, 0.15); k = t2n(0.5 + i * 0.16); drips[k:k + len(p_)] += p_[: n - k]
    return y + drips


SFX_NEW = {'paper_peel_long': paper_peel_long, 'drip_volley': drip_volley, 'comb_drag': lambda: comb_drag(0.6, 1.0), 'comb_fine': lambda: comb_drag(0.85, 1.5),
           'paper_lay': paper_lay, 'wet_contact': wet_contact, 'paper_peel': paper_peel, 'reveal_shimmer': reveal_shimmer}
