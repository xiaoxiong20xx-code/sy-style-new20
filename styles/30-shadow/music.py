# 30 皮影戏 · 配乐：秦腔/华县皮影的锣鼓经——板胡（尖亮、鼻音重、快颤音）领奏，梆子打板、板鼓催马，
# 大锣「仓」（音高下滑）、小锣「台」（音高上扬）、铙钹「才」。马队奔来时急急风，老虎扑来时一记「仓」，
# 钩子处低频暗涌后全队齐击；灯笼亮起时小锣收住，最后一声大锣余音。和 23 刺绣的江南丝竹（扬琴/二胡）完全不同。
# 音效：灯焰（lamp_flare）、马蹄（hooves）、大锣（gong_big）、马嘶（neigh）、虎啸（roar）、鼓（drum_hit）、
#      梆子滚奏（bangzi_roll）、暗涌（swell_dark）、钹滚（cymbal_roll）、灯笼亮（lantern_on）、小锣（small_gong）
# audio/make_audio.py 把 synth.py 的全部函数注入本模块：np, SR, BEAT, BAR, t2n, mtof, nm, sine, noise, lp, hp, bp, expenv, adsr, polyblep_saw ...
import numpy as np


def banhu(m0, m1, dur, vel=1.0):
    n = t2n(dur); t = np.arange(n) / SR
    g = np.clip(t / 0.07, 0, 1); g = g * g * (3 - 2 * g)
    f = mtof(m0) + (mtof(m1) - mtof(m0)) * g
    f = f * (1 + 0.016 * np.sin(2 * np.pi * 6.4 * t) * np.clip((t - 0.12) / 0.2, 0, 1))
    y = polyblep_saw(f, n) * 0.8 + polyblep_saw(f * 2.002, n) * 0.25
    y = bp(y, 700, 5200) * 0.7 + bp(y, 1100, 1700) * 0.9 + bp(y, 2600, 3600) * 0.6
    y += bp(noise(n), 2000, 7000) * 0.03
    return y * adsr(n, 0.025, 0.12, 0.8, 0.12) * 0.3 * vel


def bangzi(amp=1.0):
    n = t2n(0.09); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * 1850 * t) * np.exp(-t / 0.018) + 0.6 * np.sin(2 * np.pi * 3020 * t) * np.exp(-t / 0.01)
    y += hp(noise(n), 3000) * np.exp(-t / 0.002) * 0.5
    return y * 0.4 * amp


def bangu(amp=1.0):
    n = t2n(0.12); t = np.arange(n) / SR
    y = sine(260 + 180 * np.exp(-t / 0.012), n) * np.exp(-t / 0.04) + bp(noise(n), 1500, 6000) * np.exp(-t / 0.006) * 0.6
    return y * 0.5 * amp


def daluo(amp=1.0, dur=2.6):
    n = t2n(dur); t = np.arange(n) / SR
    f0 = 196 * (1 - 0.13 * (1 - np.exp(-t / 0.25)))
    y = np.zeros(n)
    for k, a, d in [(1, 1.0, 1.6), (1.47, 0.7, 1.1), (2.09, 0.55, 0.8), (2.56, 0.4, 0.6), (3.22, 0.3, 0.45), (4.1, 0.2, 0.3), (5.3, 0.12, 0.2)]:
        y += a * np.sin(2 * np.pi * np.cumsum(f0 * k) / SR) * np.exp(-t / d)
    y += lp(noise(n), 2500) * np.exp(-t / 0.05) * 0.5
    y *= 1 + 0.25 * np.sin(2 * np.pi * 3.2 * t) * np.exp(-t / 0.8)
    return np.tanh(y * 0.6) * 0.55 * amp


def xiaoluo(amp=1.0):
    n = t2n(0.9); t = np.arange(n) / SR
    f0 = 760 * (1 + 0.08 * (1 - np.exp(-t / 0.06)))
    y = np.sin(2 * np.pi * np.cumsum(f0) / SR) * np.exp(-t / 0.35) + 0.4 * np.sin(2 * np.pi * np.cumsum(f0 * 2.3) / SR) * np.exp(-t / 0.15)
    y += hp(noise(n), 3000) * np.exp(-t / 0.004) * 0.4
    return y * 0.3 * amp


def nao(amp=1.0, dur=0.7):
    n = t2n(dur); t = np.arange(n) / SR
    y = hp(noise(n), 3500) * np.exp(-t / (dur * 0.35)) * 0.6
    for f in (3150, 4420, 5870, 7300): y += np.sin(2 * np.pi * f * t) * np.exp(-t / (dur * 0.3)) * 0.06
    return y * 0.45 * amp


def tanggu(amp=1.0):
    n = t2n(0.6); t = np.arange(n) / SR
    return (sine(70 + 45 * np.exp(-t / 0.05), n) * np.exp(-t / 0.25) + lp(noise(n), 800) * np.exp(-t / 0.02) * 0.4) * 0.8 * amp


# banhu lines (start, end, beats)
MEL = {0: [('A5', 'A5', 1), ('C6', 'C6', 0.5), ('A5', 'G5', 0.5), ('E5', 'E5', 1), ('G5', 'A5', 1)],
       1: [('C6', 'C6', 0.5), ('D6', 'D6', 0.5), ('E6', 'E6', 1), ('D6', 'C6', 0.5), ('A5', 'A5', 0.5), ('G5', 'G5', 1)],
       2: [('E6', 'E6', 1.0), ('D6', 'E6', 1.0), ('G6', 'G6', 1.0), ('E6', 'D6', 1.0)],
       3: [('C6', 'C6', 0.5), ('A5', 'A5', 0.5), ('G5', 'A5', 1), ('C6', 'D6', 1), ('E6', 'E6', 1)],
       4: [('A5', 'A5', 2.4)]}


def mus(M, tb, name, root, tones, bi):
    # banhu lead
    tt = tb
    for a, b, bt in MEL[bi]:
        M.add('music', banhu(nm(a), nm(b), BEAT * bt * 1.04 if bi < 4 else BAR * 0.8, 1.0), tt, 0.55, 0.12, 0.35)
        tt += BEAT * bt
    # a low drone (the second banhu an octave down, quieter)
    M.add('music', lp(banhu(root + 12, root + 12, BAR * 1.02, 0.6), 1500), tb, 0.3, -0.2, 0.3)
    # percussion: bangzi keeps time, bangu gallops in bar 0-1, gongs on structure
    # (bar 4 is the 亮相 and its ring-out: one hit on 8.0, nothing after)
    for q in ((0,) if bi == 4 else range(4)): M.add('drums', bangzi(1.0 if q % 2 == 0 else 0.7), tb + q * BEAT, 0.6, 0.35)
    if bi <= 1:
        for s in range(16):
            if s % 4 != 1: M.add('drums', bangu(0.8 if s % 4 == 0 else 0.55), tb + s * BEAT / 4, 0.5, -0.25)
    if bi == 2:
        for s in range(8): M.add('drums', bangu(0.6), tb + s * BEAT / 2, 0.45, -0.25)
        M.add('drums', nao(0.6, 0.5), tb + 1.5 * BEAT, 0.4, 0.2)
    if bi == 3:
        for q in (0, 2): M.add('drums', xiaoluo(0.9), tb + q * BEAT, 0.45, 0.25)
        for q in (1, 3): M.add('drums', nao(0.6, 0.4), tb + q * BEAT, 0.4, -0.2)
    if bi == 4:
        M.add('drums', daluo(0.9, 3.0), tb, 0.8)
        M.add('drums', nao(0.5, 0.9), tb, 0.4)
    M.add('drums', tanggu(0.7 if bi in (0, 1) else 0.5), tb, 0.6)


# ---------------- SFX ----------------
def lamp_flare():
    n = t2n(0.8); t = np.arange(n) / SR
    y = svf_bp(noise(n), 300 + 1200 * np.exp(-t / 0.2), 0.6) * np.clip(t / 0.05, 0, 1) * np.exp(-t / 0.3)
    return y * 0.6


def hooves():
    out = np.zeros(t2n(1.9)); r = np.random.default_rng(4)
    for k in range(7):
        for j, dt in enumerate((0, 0.07, 0.14)):
            tt = k * 0.25 + dt
            n = t2n(0.06); t = np.arange(n) / SR
            c = (sine(520 + 140 * j + r.random() * 40, n) * np.exp(-t / 0.015) + bp(noise(n), 800, 3500) * np.exp(-t / 0.006) * 0.5) * (0.5 + 0.2 * j)
            i = t2n(tt); out[i:i + n] += c[: len(out) - i] * (1 - k / 9)
    return out * 0.6


def gong_big():
    return over(daluo(1.0, 2.4), nao(0.35, 0.7), tanggu(0.8))


def neigh():
    n = t2n(0.9); t = np.arange(n) / SR
    f = 700 * (1 + 0.35 * np.exp(-t / 0.15)) * (1 - 0.35 * t) * (1 + 0.05 * np.sin(2 * np.pi * 18 * t))
    y = bp(polyblep_saw(f, n), 600, 3200) * np.sin(np.pi * np.clip(t / 0.9, 0, 1)) ** 0.7
    return y * 0.25


def whoosh_pup():
    return whoosh(0.5, True, 300, 5000, 0.6)


def roar():
    n = t2n(1.1); t = np.arange(n) / SR
    f = 95 * (1 + 0.25 * np.sin(np.pi * t / 1.1))
    am = 0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 23 * t))
    y = lp(polyblep_saw(f, n), 900) * am * 0.6 + bp(noise(n), 200, 1800) * am * 0.5
    return np.tanh(y * 1.4) * np.sin(np.pi * np.clip(t / 1.1, 0, 1)) ** 0.6 * 0.55


def drum_hit():
    return over(tanggu(1.0), bangu(1.0) * 0.8)


def bangzi_roll():
    out = np.zeros(t2n(0.55)); tt = 0.0; k = 0
    while tt < 0.45:
        b = bangzi(0.6 + 0.4 * tt / 0.45); i = t2n(tt); out[i:i + len(b)] += b[: len(out) - i]
        tt += 0.075 * (1 - 0.5 * tt / 0.45); k += 1
    return out


def swell_dark():
    n = t2n(1.1); t = np.arange(n) / SR
    y = lp(noise(n), 300) * 0.6 + sine(45 + 20 * t, n) * 0.5
    return y * (t / 1.1) ** 2 * 0.7


def cymbal_roll():
    out = np.zeros(t2n(1.4)); tt = 0.0
    while tt < 1.0:
        b = nao(0.35, 0.3); i = t2n(tt); out[i:i + len(b)] += b[: len(out) - i]; tt += 0.06
    return out * np.linspace(1, 0.3, len(out))


def lantern_on():
    n = t2n(1.2); t = np.arange(n) / SR
    return over(xiaoluo(0.5), (sine(150, n) * 0.3 + sine(300, n) * 0.12) * np.clip(t / 0.3, 0, 1) * np.exp(-t / 0.6) * 0.3)


def small_gong():
    return xiaoluo(1.0)


SFX_NEW = {'lamp_flare': lamp_flare, 'hooves': hooves, 'gong_big': gong_big, 'neigh': neigh, 'whoosh_pup': whoosh_pup, 'roar': roar, 'drum_hit': drum_hit,
           'bangzi_roll': bangzi_roll, 'swell_dark': swell_dark, 'cymbal_roll': cymbal_roll, 'lantern_on': lantern_on, 'small_gong': small_gong}
