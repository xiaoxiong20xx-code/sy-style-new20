# 34 孔版套印 · 配乐：印刷车间里的电子流行——机器滚筒的八分音符「咔嚓」当节拍，方波低音切分，
# 两支微微失谐的脉冲波琶音（像荧光粉和蓝两种油墨，左右声道各一支），第二遍套色时加上暖色铺底和拍手，
# 揭开海报时一记上扬后全段齐奏。音色与 27 积木（clavinet 放克）、36 热成像（暗色氛围）都不同。
# 音效：机器运转（riso_run）、出纸（paper_out）、纸落托盘（paper_land）、换滚筒（drum_swap）、揭开上扬（reveal_rise）、定格一击（stamp_hit）、
# 纸边落下（paper_settle）、拉开窗帘（curtain：布料唰声 + 帘环在杆上滑响）
# audio/make_audio.py 把 synth.py 的全部函数注入本模块：np, SR, BEAT, BAR, t2n, mtof, nm, sine, noise, lp, hp, bp, expenv, adsr, polyblep_saw, square ...
import numpy as np


def pulse(m, dur, duty=0.3, cut=3200, det=0.0):
    n = t2n(dur); f = mtof(m) * (1 + det)
    y = square(f, n, duty) * 0.5
    y = svf_lp(y, 500 + cut * np.exp(-np.arange(n) / SR / 0.07), 0.3)
    return y * adsr(n, 0.003, 0.08, 0.5, 0.05) * 0.2


def sqbass(m, dur):
    n = t2n(dur); f = mtof(m)
    y = square(f, n, 0.5) * 0.4 + sine(f, n) * 0.6
    y = svf_lp(y, 180 + 900 * np.exp(-np.arange(n) / SR / 0.06), 0.5)
    return y * adsr(n, 0.002, 0.06, 0.7, 0.03) * 0.55


def chk(amp=1.0, seed=0):
    r = np.random.default_rng(seed)
    n = t2n(0.07); t = np.arange(n) / SR
    y = bp(noise(n), 1800 + r.random() * 600, 7000) * np.exp(-t / 0.012) * 0.6 + sine(900, n) * np.exp(-t / 0.008) * 0.15
    return y * amp


def mus(M, tb, name, root, tones, bi):
    # the machine: kick on the beat, 'chk' on every eighth, a clap on 2 & 4 once the blue drum is in
    # bar 4 (8.0) is the resolution: one last hit, then everything rings out
    for q in ((0,) if bi == 4 else range(4)): M.add('drums', kick(0.35, 120, 45, 1.2, 0.1), tb + q * BEAT, 0.75 if bi else 0.55); M.sidechain(tb + q * BEAT, 0.3)
    for e in (range(8) if bi < 4 else ()): M.add('drums', chk(0.9 if e % 2 else 0.6, bi * 8 + e), tb + e * BEAT / 2, 0.32, 0.3 if e % 2 else -0.3)
    if 1 <= bi <= 3:
        for q in (1, 3): M.add('drums', clap(), tb + q * BEAT, 0.42, 0, 0.2)
        for s in range(16):
            if s % 2: M.add('drums', hat(), tb + s * BEAT / 4, 0.06, 0.4)
    # bass: syncopated roots
    for q, iv, d in ([(0, 0, 0.4), (0.75, 0, 0.2), (1.5, 12, 0.3), (2.5, 7, 0.4), (3.25, 0, 0.2), (3.5, 10 if name in ('Am', 'G') else 11, 0.3)] if bi < 4 else [(0, 0, 1.6)]):
        M.add('music', sqbass(root - 12 + iv, d), tb + q * BEAT, 0.62)
    # two detuned pulse arps: "pink" left, "blue" right (the blue one joins on the second pass)
    arp = [tones[0], tones[2], tones[1] + 12, tones[2], tones[0] + 12, tones[2], tones[1] + 12, tones[2] + 12]
    for e in (range(8) if bi < 4 else ()):
        M.add('music', pulse(arp[e] + 12, BEAT / 2 * 0.9, 0.28, 2600 + 400 * (e % 2)), tb + e * BEAT / 2, 0.36, -0.45, 0.25)
        if bi >= 1: M.add('music', pulse(arp[(e + 3) % 8] + 12, BEAT / 2 * 0.9, 0.45, 2000, 0.004), tb + e * BEAT / 2 + BEAT / 4, 0.3, 0.45, 0.25)
    if bi >= 2:
        M.add('music', pad([x + 12 for x in chord_ext(name, tones)], BAR, 2200, 0.01), tb, 0.36, 0, 0.5)
    if bi == 4:
        for j, m in enumerate(tones + [tones[0] + 12]): M.add('music', pulse(m + 24, 1.9, 0.4, 3000), tb + j * 0.02, 0.35, -0.3 + 0.2 * j, 0.5)


# ---------------- SFX ----------------
def riso_run():
    n = t2n(1.5); t = np.arange(n) / SR
    whirr = bp(noise(n), 300, 1400) * (0.5 + 0.5 * np.sin(2 * np.pi * 11 * t) ** 2) * 0.25
    hum = (sine(98, n) * 0.25 + sine(196, n) * 0.08) * (1 + 0.2 * np.sin(2 * np.pi * 11 * t))
    out = (whirr + hum) * np.clip(t / 0.1, 0, 1) * np.clip((1.5 - t) / 0.3, 0, 1)
    for k in range(int(1.4 / 0.09)):
        c = chk(0.5, 50 + k); i = t2n(k * 0.09); out[i:i + len(c)] += c[: len(out) - i]
    return out * 0.8


def paper_out():
    n = t2n(1.1); t = np.arange(n) / SR
    y = svf_bp(noise(n), 1200 + 2500 * np.sin(np.pi * t / 1.1), 0.5) * np.sin(np.pi * t / 1.1) ** 1.5 * 0.4
    y *= 0.8 + 0.2 * np.sin(2 * np.pi * 23 * t)
    return y


def paper_land():
    return sfx_slap() * 1.1


def drum_swap():
    n = t2n(0.45); t = np.arange(n) / SR
    clunk = sine(110 * np.exp(-t / 0.08) + 60, n) * np.exp(-t / 0.08) * 0.7 + lp(noise(n), 1500) * np.exp(-t / 0.02) * 0.5
    latch = np.zeros(n); k = t2n(0.12); m = t2n(0.05); latch[k:k + m] += hp(noise(m), 2500) * np.exp(-np.arange(m) / SR / 0.006) * 0.6
    return clunk + latch


def reveal_rise():
    return over(riser(1.0) * 0.8, swell(1.2) * 0.4)


def stamp_hit():
    return over(sfx_thud(), chime() * 0.7)


def paper_settle():
    # the curled edge of a sheet dropping onto the stack: a soft puff of air and a dry paper tick
    n = t2n(0.32); t = np.arange(n) / SR
    puff = svf_lp(noise(n), 900 + 1600 * np.exp(-t / 0.05), 0.4) * np.exp(-t / 0.07) * 0.55
    tick = hp(noise(n), 3000) * np.exp(-np.maximum(t - 0.11, 0) / 0.006) * (t > 0.11) * 0.25
    return puff + tick


def curtain():
    # a curtain drawn open: fabric swish and the rings rattling along the rod
    n = t2n(1.5); t = np.arange(n) / SR
    env = np.sin(np.pi * np.clip(t / 1.35, 0, 1)) ** 1.2
    swish = svf_bp(noise(n), 700 + 1400 * env, 0.45) * env * 0.35
    rings = np.zeros(n); r = np.random.default_rng(7)
    for k in range(9):
        i = t2n(0.04 + k * 0.13 + r.random() * 0.03); m = t2n(0.09); tt = np.arange(m) / SR
        f = 2600 + r.random() * 900
        ping = (sine(f, m) * 0.5 + sine(f * 1.47, m) * 0.3 + hp(noise(m), 4000) * 0.4) * np.exp(-tt / 0.018)
        rings[i:i + m] += ping[: n - i] * (0.12 + 0.06 * r.random()) * (1 - k / 12)
    return swish + rings


SFX_NEW = {'riso_run': riso_run, 'paper_out': paper_out, 'paper_land': paper_land, 'drum_swap': drum_swap, 'reveal_rise': reveal_rise, 'stamp_hit': stamp_hit,
           'paper_settle': paper_settle, 'curtain': curtain}
