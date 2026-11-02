# 39 光绘长曝光 · 配乐：夜色里的电吉他泛音 + 磁带延迟、慵懒的半拍律动；钢丝棉点燃时整段炸开
# audio/make_audio.py 把 synth.py 的全部函数注入本模块：np, SR, BEAT, BAR, t2n, mtof, nm, sine, noise, lp, hp, bp, expenv, adsr, ks, sub, kick, rim, hat ...


def tape_delay(x, time=0.375, fb=0.42, mix=0.45, tone=2600):
    """简单的磁带延迟：每次回声都更暗一点"""
    d = t2n(time); y = np.copy(x); echo = np.copy(x)
    out = np.zeros(len(x) + d * 6); out[:len(x)] += x
    for k in range(1, 6):
        echo = lp(echo, tone) * fb
        out[d * k:d * k + len(echo)] += echo * mix
    return out


def gtr(m, dur=1.6, vel=1.0, bright=0.55):
    """干净电吉他：拨弦 + 轻微失真 + 拾音器带通"""
    y = ks(m, dur, bright, 0.9982)
    y = np.tanh(y * 1.8) / 1.8
    y = bp(y, 120, 4200) * 1.4
    return y * 0.5 * vel


def harmonic(m, dur=2.2, vel=1.0):
    """泛音：清亮的正弦 + 一点拨弦噪声"""
    n = t2n(dur); f = mtof(m); t = np.arange(n) / SR
    y = sine(f, n) * np.exp(-t / 0.9) + 0.25 * sine(2 * f, n) * np.exp(-t / 0.3)
    y += bp(noise(n), f, min(f * 4, 12000)) * np.exp(-t / 0.004) * 0.3
    return y * (1 - np.exp(-t / 0.002)) * 0.28 * vel


def sub_pulse(m, dur):
    n = t2n(dur); t = np.arange(n) / SR
    return sine(mtof(m), n) * adsr(n, 0.02, 0.2, 0.75, 0.15) * (1 + 0.1 * np.sin(2 * np.pi * 2 * t))


ROOT = [40, 36, 43, 38, 40]                  # Em  C  G  D  Em  (night, minor)
CHORD = [[64, 67, 71, 74], [60, 64, 67, 71], [62, 67, 71, 74], [62, 66, 69, 72], [64, 67, 71, 76]]


def mus(M, tb, name, root, tones, bi):
    r, ch = ROOT[bi], CHORD[bi]
    if bi == 4:      # the shutter has closed: one ringing chord and the echo dies away
        for j, m in enumerate(ch):
            M.add('music', tape_delay(gtr(m, 2.4, 0.9), 0.375, 0.42, 0.35), tb + 0.018 * j, 0.42, -0.3 + 0.2 * j, 0.45)
        M.add('music', tape_delay(harmonic(ch[3] + 12, 2.6), 0.5, 0.45, 0.4), tb + 0.01, 0.5, 0.3, 0.5)
        M.add('music', sub_pulse(r - 12, BAR * 0.9), tb, 0.5)
        M.add('drums', kick(0.5, 120, 44, 1.2, 0.08), tb, 0.8)
        return
    # guitar: slow arpeggio through the tape echo
    pat = [0, 2, 1, 3] if bi != 2 else [0, 2, 3, 1, 2, 3, 1, 0]
    step = BEAT if bi != 2 else BEAT / 2
    for k, j in enumerate(pat):
        x = tape_delay(gtr(ch[j], 1.4, 0.8 if k % 2 else 1.0), 0.375, 0.4, 0.35)
        M.add('music', x, tb + k * step, 0.46, -0.35 + 0.7 * (k % 2), 0.35)
    if bi in (0, 4):
        M.add('music', tape_delay(harmonic(ch[3] + 12, 2.4), 0.5, 0.45, 0.4), tb + 1.5 * BEAT, 0.5, 0.3, 0.5)
    M.add('music', sub_pulse(r - 12, BAR * 0.95), tb, 0.5)
    # half-time groove, gets busier when the wool burns
    if bi >= 1:
        M.add('drums', kick(0.45, 120, 44, 1.2, 0.08), tb, 0.75)
        M.add('drums', kick(0.45, 120, 44, 1.2, 0.08), tb + 2.5 * BEAT, 0.55)
        M.add('drums', lp(clap(), 5000), tb + 2 * BEAT, 0.42, 0, 0.35)
        sw = BEAT / 2 * 0.16
        for e in range(8): M.add('drums', hat(), tb + e * BEAT / 2 + (sw if e % 2 else 0), 0.09 if bi != 2 else 0.13, 0.3)
        M.sidechain(tb, 0.35)
    if bi == 2:
        for q in (1, 3): M.add('drums', kick(0.4, 140, 46, 1.4, 0.12), tb + q * BEAT, 0.6)
        M.add('drums', rim(), tb + 3.5 * BEAT, 0.4, 0.2)
        M.add('music', pad([x + 12 for x in ch[:3]], BAR, 2400, 0.01), tb, 0.3, 0, 0.5)
    if bi == 3: M.add('music', pad([x for x in ch[:3]], BAR, 1600, 0.008), tb, 0.25, 0, 0.5)


# ---------- SFX ----------
def shutter(close=False):
    n = t2n(0.25); t = np.arange(n) / SR
    y = bp(noise(n), 1500, 6500) * (1 - np.exp(-t / 0.0015)) * np.exp(-t / 0.006) * 0.55
    k = t2n(0.045 if not close else 0.03)
    y[k:] += bp(noise(n - k), 1200, 6000)[: n - k] * (1 - np.exp(-t[: n - k] / 0.0015)) * np.exp(-t[: n - k] / 0.008) * 0.45
    y += sine(180 + 90 * np.exp(-t / 0.01), n) * np.exp(-t / 0.03) * 0.35
    return y


def tube_swoosh():
    n = t2n(0.35); t = np.arange(n) / SR; u = t / 0.35
    y = svf_bp(noise(n), 700 + 2500 * u, 0.7) * np.sin(np.pi * u) ** 2 * 0.5
    y += sine(110, n) * 0.02 * np.sin(np.pi * u)                     # a faint mains hum from the LED driver
    return y


def wool_ignite():
    n = t2n(0.9); t = np.arange(n) / SR
    y = hp(noise(n), 3000) * np.exp(-t / 0.01) * 0.5                  # flint
    k = t2n(0.08)
    y[k:] += lp(noise(n - k), 1800)[: n - k] * (1 - np.exp(-t[: n - k] / 0.05)) * np.exp(-t[: n - k] / 0.4) * 0.6   # whump
    return y


def wool_spin(dur=2.7):
    """旋转的钢丝棉：每圈一次呼啸（每秒 2.6 圈）+ 噼啪的火花"""
    n = t2n(dur); t = np.arange(n) / SR
    env = np.clip(t / 0.15, 0, 1) * np.clip((dur - t) / 0.5, 0, 1)
    whoosh = bp(noise(n), 400, 3500) * (0.45 + 0.55 * np.sin(2 * np.pi * 2.6 * t) ** 2) * 0.5
    y = whoosh * env
    r = np.random.default_rng(39)
    for i in range(int(dur * 160)):
        s0 = int(r.random() * (n - 800)); m = t2n(0.004 + r.random() * 0.01)
        y[s0:s0 + m] += bp(noise(m), 2500, 8000) * np.exp(-np.arange(m) / SR / 0.002) * (0.1 + 0.2 * r.random()) * env[s0]
    y += lp(noise(n), 300) * 0.15 * env                                 # roar
    return y


def pen_click():
    n = t2n(0.08); t = np.arange(n) / SR
    return (bp(noise(n), 2000, 7000) * (1 - np.exp(-t / 0.001)) * np.exp(-t / 0.004) + sine(2400, n) * np.exp(-t / 0.01) * 0.3) * 0.45


def pen_write(dur=1.7):
    n = t2n(dur); t = np.arange(n) / SR
    am = 0.5 + 0.5 * np.sin(2 * np.pi * 6 * t + 2 * np.sin(2 * np.pi * 1.7 * t))
    return bp(noise(n), 2000, 7000) * am * 0.08 * np.clip(t / 0.1, 0, 1) * np.clip((dur - t) / 0.2, 0, 1) + sine(880, n) * 0.012 * am


def tube_flick():
    n = t2n(0.18); t = np.arange(n) / SR; u = t / 0.18
    return svf_bp(noise(n), 1500 + 4000 * u, 0.7) * np.sin(np.pi * u) ** 2 * 0.45


SFX_NEW = {'tube_flick': tube_flick, 'shutter_open': lambda: shutter(False), 'shutter_close': lambda: shutter(True), 'tube_swoosh': tube_swoosh,
           'wool_ignite': wool_ignite, 'wool_spin': wool_spin, 'pen_click': pen_click, 'pen_write': pen_write}
