# 31 建筑投影秀 · 配乐：大场面电子 —— 超锯齿和弦重击 + 脉冲低音 + 低沉战鼓；崩塌时抽空，砸回时整段炸开
# audio/make_audio.py 把 synth.py 的全部函数注入本模块：np, SR, BEAT, BAR, t2n, mtof, nm, sine, noise, lp, hp, bp, expenv, adsr, polyblep_saw, kick, clap, hat ...


def supersaw(ms, dur, cut=3200, amp=1.0, a=0.005, r=0.25):
    n = t2n(dur); y = np.zeros(n)
    for m in ms:
        f = mtof(m)
        for k, d in enumerate((-0.021, -0.012, -0.005, 0.0, 0.005, 0.012, 0.021)):
            y += polyblep_saw(f * (1 + d), n) * (0.7 if k in (0, 6) else 1.0)
    y = lp(y / (7 * len(ms)), cut, 2)
    return y * adsr(n, a, 0.15, 0.7, r) * amp


def stab(ms, dur=0.35):
    n = t2n(dur); t = np.arange(n) / SR
    y = supersaw(ms, dur, 5200, 1.0, 0.002, 0.08)
    return y * np.exp(-t / 0.18)


def pulse_bass(m, dur):
    n = t2n(dur); t = np.arange(n) / SR; f = mtof(m)
    y = polyblep_saw(f, n) * 0.6 + sine(f / 2, n) * 0.8
    fc = 160 + 900 * np.exp(-t / 0.06)
    return svf_lp(y, fc, 0.5) * adsr(n, 0.003, 0.08, 0.7, 0.04)


def war_tom(f0=70, amp=1.0):
    n = t2n(0.8); t = np.arange(n) / SR
    y = sine(f0 + 40 * np.exp(-t / 0.05), n) * np.exp(-t / 0.35) + lp(noise(n), 700) * np.exp(-t / 0.04) * 0.5
    return np.tanh(y * 1.4) * 0.8 * amp


ROOTS = [33, 29, 29, 31, 33]                      # A  F  F  G  A
CH = [[57, 60, 64], [57, 60, 65], [57, 60, 65], [59, 62, 67], [57, 61, 64, 69]]   # Am F F G A(maj) — ends lifted


def mus(M, tb, name, root, tones, bi):
    r, ch = ROOTS[bi], CH[bi]
    if bi == 0:          # build: pulsing sixteenth bass, risers of filter
        for s in range(16):
            M.add('music', pulse_bass(r, BEAT / 4 * 0.85), tb + s * BEAT / 4, 0.35 + 0.25 * (s / 16))
        M.add('music', supersaw([x + 12 for x in ch], BAR, 600 + 0, 0.6, 1.2, 0.3), tb, 0.35, 0, 0.4)
        for q in (2, 3): M.add('music', stab([x + 12 for x in ch]), tb + q * BEAT, 0.45, 0, 0.35)
    elif bi == 1:        # blocks: tom-driven, stabs on every beat
        for q in range(4):
            M.add('drums', war_tom(72 if q % 2 == 0 else 60), tb + q * BEAT, 0.8, -0.2 + 0.4 * (q % 2), 0.3)
            M.add('music', stab([x + 12 for x in ch]), tb + q * BEAT, 0.5, 0, 0.35)
        for s in range(16): M.add('music', pulse_bass(r, BEAT / 4 * 0.85), tb + s * BEAT / 4, 0.55)
        for e in range(8): M.add('drums', hat(), tb + e * BEAT / 2 + BEAT / 4, 0.12, 0.35)
    elif bi == 2:        # the collapse: one huge chord, then the floor drops out (4 - 6 s; the slam lands at 5.5)
        M.add('music', supersaw([x for x in ch] + [ch[0] + 12], BEAT * 1.6, 2600, 1.0, 0.003, 0.4), tb + BEAT, 0.55, 0, 0.5)
        M.add('music', sine(mtof(r - 12), t2n(BEAT * 2)) * np.exp(-np.arange(t2n(BEAT * 2)) / SR / 0.9), tb + BEAT, 0.6)
        M.add('drums', war_tom(55, 1.2), tb + BEAT, 0.9, 0, 0.4)
        # the slam (5.5) drops straight into the four-on-the-floor of the colour section
        M.add('drums', kick(0.5, 160, 42, 1.8, 0.3), tb + 3 * BEAT, 1.0); M.sidechain(tb + 3 * BEAT, 0.6)
        M.add('music', stab([x + 12 for x in CH[3]], 0.5), tb + 3 * BEAT, 0.6, 0, 0.4)
        M.add('drums', kick(0.45, 150, 44, 1.6, 0.2), tb + 3.5 * BEAT, 0.8); M.sidechain(tb + 3.5 * BEAT, 0.5)
    elif bi == 3:        # colour floods: full drop
        for q in range(4):
            M.add('drums', kick(0.45, 150, 44, 1.6, 0.2), tb + q * BEAT, 0.95); M.sidechain(tb + q * BEAT, 0.55)
        for q in (1, 3): M.add('drums', clap(), tb + q * BEAT, 0.55, 0, 0.3)
        for e in range(8): M.add('drums', hat(e % 2 == 1), tb + e * BEAT / 2 + BEAT / 4, 0.14, 0.35)
        M.add('music', supersaw([x + 12 for x in ch], BAR, 3600, 0.75, 0.01, 0.2), tb, 0.5, 0, 0.45)
        for s in range(16):
            m = [ch[0], ch[1], ch[2], ch[1] + 12][s % 4] + 24
            M.add('music', stab([m], 0.18), tb + s * BEAT / 4, 0.18, 0.4 if s % 2 else -0.4, 0.3)
        for e in range(8): M.add('music', pulse_bass(r + (12 if e % 2 else 0), BEAT / 2 * 0.8), tb + e * BEAT / 2, 0.5)
    else:                # title: one held, lifted chord
        M.add('drums', kick(0.55, 150, 42, 1.6, 0.2), tb, 0.9)
        M.add('music', supersaw([x + 12 for x in ch], BAR * 1.2, 3000, 0.8, 0.01, 0.9), tb, 0.55, 0, 0.6)
        M.add('music', sine(mtof(r - 12), t2n(BAR)) * adsr(t2n(BAR), 0.01, 0.3, 0.8, 0.8), tb, 0.55)


# ---------- SFX ----------
def crowd_murmur(dur=3.5):
    n = t2n(dur); t = np.arange(n) / SR; y = np.zeros(n); r = np.random.default_rng(31)
    for k in range(12):
        f = 300 + r.random() * 500
        am = 0.5 + 0.5 * np.sin(2 * np.pi * (2 + r.random() * 3) * t + r.random() * 6)
        y += bp(noise(n), f, f * 2.2) * am * 0.08
    return y * np.clip(t / 0.3, 0, 1) * np.clip((dur - t) / 1.0, 0, 1)


def proj_on():
    n = t2n(1.2); t = np.arange(n) / SR
    y = hp(noise(n), 2500) * np.exp(-t / 0.004) * 0.5                    # relay click
    y += sine(80 + 900 * np.clip(t / 0.8, 0, 1) ** 2, n) * 0.06 * np.clip(t / 0.1, 0, 1) * np.exp(-t / 0.9)
    y += bp(noise(n), 300, 1200) * 0.06 * np.clip(t / 0.4, 0, 1)            # fan
    return y


def hit_bright():
    n = t2n(0.6); t = np.arange(n) / SR
    return stab([nm('A5'), nm('E6')], 0.6)[:n] * 0.9 + hp(noise(n), 4000) * np.exp(-t / 0.03) * 0.3


def block_thud():
    n = t2n(0.5); t = np.arange(n) / SR
    return sine(55 + 50 * np.exp(-t / 0.03), n) * np.exp(-t / 0.18) * 0.9 + lp(noise(n), 900) * np.exp(-t / 0.03) * 0.4


def stone_creak():
    n = t2n(0.6); t = np.arange(n) / SR; u = t / 0.6
    y = bp(noise(n), 200, 900) * (0.3 + 0.7 * u) * 0.5
    pulses = (np.sin(2 * np.pi * (25 + 40 * u) * t) > 0.92).astype(float)
    y += bp(pulses, 300, 2500) * 0.4 * u
    return y


def collapse():
    n = t2n(1.8); t = np.arange(n) / SR; y = np.zeros(n); r = np.random.default_rng(5)
    y += sine(32 + 60 * np.exp(-t / 0.15), n) * np.exp(-t / 0.8) * 1.0          # sub drop
    y += lp(noise(n), 400) * np.exp(-t / 0.6) * 0.6                            # rumble
    for i in range(70):                                                        # debris
        s0 = t2n(0.02 + (i / 70) ** 1.4 * 1.2 + r.random() * 0.05); m = t2n(0.08)
        if s0 + m >= n: continue
        tt = np.arange(m) / SR
        y[s0:s0 + m] += bp(noise(m), 300 + r.random() * 1500, 5000) * np.exp(-tt / 0.02) * (0.25 + 0.3 * r.random())
    return np.tanh(y * 1.2)


def crowd_gasp():
    n = t2n(1.0); t = np.arange(n) / SR; y = np.zeros(n); r = np.random.default_rng(9)
    for k in range(10):
        s0 = t2n(r.random() * 0.12); m = n - s0; tt = np.arange(m) / SR
        v = bp(noise(m), 450 + r.random() * 200, 1100 + r.random() * 400) * np.clip(tt / 0.05, 0, 1) * np.exp(-tt / 0.45)
        y[s0:] += v * 0.12
    return y


def slam_back():
    pre = t2n(0.3); n = t2n(1.6); t = np.arange(n) / SR; y = np.zeros(n)
    u = np.clip(t / 0.3, 0, 1)
    y[:pre] += bp(noise(pre), 300, 6000)[:pre] * (u[:pre] ** 3) * 0.6                 # reverse suck into the hit
    m = n - pre; tt = np.arange(m) / SR
    y[pre:] += sine(40 + 90 * np.exp(-tt / 0.04), m) * np.exp(-tt / 0.5) * 1.1 + lp(noise(m), 2500) * np.exp(-tt / 0.08) * 0.7 + hp(noise(m), 5000) * np.exp(-tt / 0.3) * 0.12
    return np.tanh(y * 1.3)


def title_sweep():
    n = t2n(1.4); t = np.arange(n) / SR; y = np.zeros(n)
    for k, m in enumerate((nm('A6'), nm('C#7'), nm('E7'), nm('A7'), nm('E8'))):
        x = bell(m, 1.0, 0.5) * 0.12; s0 = t2n(k * 0.2); y[s0:s0 + len(x)] += x[:n - s0]
    y += bp(noise(n), 3000, 9000) * np.sin(np.pi * t / 1.4) * 0.06
    return y


def crowd_cheer(dur=2.2):
    n = t2n(dur); t = np.arange(n) / SR; y = np.zeros(n); r = np.random.default_rng(12)
    for i in range(int(dur * 90)):                                            # applause
        s0 = int(r.random() * (n - 2000)); m = t2n(0.02)
        y[s0:s0 + m] += bp(noise(m), 800, 6000) * np.exp(-np.arange(m) / SR / 0.004) * (0.2 + 0.3 * r.random())
    for k in range(8):
        f = 500 + r.random() * 400
        y += bp(noise(n), f, f * 2) * 0.05 * np.clip(t / 0.2, 0, 1)
    return y * np.clip((dur - t) / 0.8, 0, 1)


def bay_hit():
    """a bay of the building lights: a bright stab with a little low thump"""
    n = t2n(0.7); t = np.arange(n) / SR
    y = stab([nm('A5'), nm('C#6'), nm('E6')], 0.7)[:n] * 0.7
    y += sine(70 + 60 * np.exp(-t / 0.02), n) * np.exp(-t / 0.12) * 0.6
    return y


def emblem_on():
    n = t2n(1.6); t = np.arange(n) / SR; y = np.zeros(n)
    for k, m in enumerate((nm('A6'), nm('E7'), nm('A7'))):
        x = bell(m, 1.4, 0.6) * 0.18; s0 = t2n(0.03 * k); y[s0:s0 + len(x)] += x[:n - s0]
    y += sine(55 + 50 * np.exp(-t / 0.03), n) * np.exp(-t / 0.2) * 0.6
    return y


def light_run():
    """light climbing the building: a fast rising shimmer that lands on the emblem"""
    n = t2n(1.2); t = np.arange(n) / SR; u = np.clip(t / 0.36, 0, 1)
    y = svf_bp(noise(n), 500 * (16 ** u), 0.5) * np.sin(np.pi * np.clip(t / 0.5, 0, 1)) ** 1.2 * 0.4
    k = t2n(0.36); m = n - k
    y[k:] += sum(bell(nm(q), 1.0, 0.5)[:m] for q in ('E7', 'A7')) * 0.12
    return y


SFX_NEW = {'bay_hit': bay_hit, 'emblem_on': emblem_on, 'light_run': light_run, 'crowd_murmur': crowd_murmur, 'proj_on': proj_on, 'hit_bright': hit_bright, 'block_thud': block_thud, 'stone_creak': stone_creak,
           'collapse': collapse, 'crowd_gasp': crowd_gasp, 'slam_back': slam_back, 'title_sweep': title_sweep, 'crowd_cheer': crowd_cheer}
