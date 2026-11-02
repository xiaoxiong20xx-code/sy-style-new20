# 33 美式漫画 · 配乐：60 年代超级英雄动画式的铜管大乐队 + 冲浪吉他 + 军鼓滚奏（热血、复古）
# 音效：城市夜风（city）、激光（zap）、喷气背包（jet）、KRAKOOM（krakoom）、撕纸（tear）、落地（land）、印刷机（press）、铜管收尾（stinger）
import numpy as np


def surf(m, dur=0.3):
    n = t2n(dur); t = np.arange(n) / SR; f = mtof(m)
    y = ks(m, dur, 0.85, 0.995) * 1.2
    trem = 1 + 0.25 * np.sin(2 * np.pi * 7 * t)
    return np.tanh(lp(y, 4500) * 2.2) * trem * 0.45


def snare():
    n = t2n(0.22); t = np.arange(n) / SR
    return bp(noise(n), 1500, 8000) * np.exp(-t / 0.06) * 0.7 + sine(190, n) * np.exp(-t / 0.03) * 0.45


def roll(dur):
    out = np.zeros(t2n(dur + 0.2)); k = 0; i = 0
    while k < t2n(dur):
        s = snare() * (0.3 + 0.6 * (i / max(1, dur * 16))); out[k:k + len(s)] += s[: len(out) - k]; k += t2n(1 / 16); i += 1
    return out


RIFF = {'Am': ['A3', 'C4', 'E4', 'G4', 'A4', 'G4', 'E4', 'C4'], 'F': ['F3', 'A3', 'C4', 'E4', 'F4', 'E4', 'C4', 'A3'],
        'C': ['C4', 'E4', 'G4', 'B4', 'C5', 'B4', 'G4', 'E4'], 'G': ['G3', 'B3', 'D4', 'F#4', 'G4', 'F#4', 'D4', 'B3']}


def mus(M, tb, name, root, tones, bi):
    last = bi == 4
    # drums: driving rock beat, snare on 2 & 4, hats in 8ths, a fill into the hook bar
    if not last:
        for q in range(4):
            M.add('drums', kick(0.4, 150, 48, 1.5, 0.2), tb + q * BEAT if q % 2 == 0 else tb + q * BEAT + BEAT / 2, 0.75)
            if q % 2: M.add('drums', snare(), tb + q * BEAT, 0.6, 0, 0.25)
        for e in range(8): M.add('drums', hat(e % 4 == 3), tb + e * BEAT / 2, 0.14 if e % 2 else 0.09, 0.35)
    if bi == 1:
        M.add('drums', roll(0.95), tb + 3 * BEAT - 0.45, 0.6, 0, 0.3)
    # bass: driving eighths on the root
    if not last:
        for e in range(8): M.add('music', bass_saw(root - 12 + (12 if e in (3, 7) else 0), BEAT / 2 * 0.8, 700), tb + e * BEAT / 2, 0.42)
    # surf-guitar riff
    if bi in (0, 1):
        for e, sN in enumerate(RIFF[name]): M.add('music', surf(nm(sN) + 12, 0.28), tb + e * BEAT / 2, 0.35, 0.3, 0.3)
    # brass: stabs on the "and" of 2 and on 4; the hook bar gets a heroic fanfare
    if bi in (0, 1):
        for d in (1.5, 3.0): M.add('music', brass([x + 12 for x in tones], BEAT * 0.35), tb + d * BEAT, 0.5, 0, 0.35)
    if bi == 3:   # the cover prints: one stab per plate (6.5, 7.0, 7.5), snare roll into the last one
        for d in (1.0, 2.0, 3.0): M.add('music', brass([x + 12 for x in tones], BEAT * 0.32), tb + d * BEAT, 0.55, 0, 0.3)
        M.add('drums', roll(0.5), tb + 3 * BEAT, 0.55, 0, 0.3)
    if bi == 2:
        fan = [(0, 'E5', 0.75), (0.75, 'A5', 0.25), (1.0, 'C6', 1.0), (2.0, 'B5', 0.5), (2.5, 'C6', 0.5), (3.0, 'E6', 1.0)]
        for d, sN, L in fan:
            M.add('music', brass([nm(sN) - 12, nm(sN) - 5, nm(sN)], BEAT * L * 0.95), tb + d * BEAT, 0.55, 0, 0.4)
        M.add('drums', crash(1.6), tb, 0.45, 0.2, 0.4)
        M.add('music', strings([x + 12 for x in tones], BAR, 3200), tb, 0.35, 0, 0.5)
    if last:   # the black plate lands on 8.0: the big chord, left to ring
        M.add('music', brass([tones[0] + 12, tones[1] + 12, tones[2] + 12, tones[0] + 24], BEAT * 3), tb, 0.55, 0, 0.5)
        M.add('drums', crash(2.0), tb, 0.5, 0, 0.5)
        M.add('drums', kick(0.6, 120, 40, 1.4, 0.2), tb, 0.8)
        M.add('music', bass_saw(root - 12, BEAT * 2.5, 600), tb, 0.45)
        M.add('music', strings([x + 12 for x in tones], BAR * 0.95, 2600), tb, 0.3, 0, 0.6)


def sfx_city():
    dur = 1.6; n = t2n(dur); t = np.arange(n) / SR
    return (lp(noise(n), 500) * 0.25 + bp(noise(n), 300, 1200) * 0.06) * np.clip(t / 0.3, 0, 1) * np.clip((dur - t) / 0.6, 0, 1)


def sfx_zap():
    n = t2n(0.35); t = np.arange(n) / SR
    return np.sign(sine(1800 * np.exp(-t / 0.08) + 300, n)) * np.exp(-t / 0.1) * 0.2


def sfx_jet():
    dur = 0.9; n = t2n(dur); t = np.arange(n) / SR
    roar = lp(noise(n), 1400) * 0.5 + bp(noise(n), 2000, 7000) * 0.15
    return roar * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.6 * (0.8 + 0.2 * np.sin(2 * np.pi * 23 * t))


def sfx_krakoom():
    y = impact(1.0, 1.4) * 1.0
    n = len(y); t = np.arange(n) / SR
    y += np.tanh(lp(noise(n), 2500) * 3) * np.exp(-t / 0.18) * 0.35
    y += sine(55, n) * np.exp(-t / 0.5) * 0.5
    return np.tanh(y * 1.3) * 0.9


def sfx_tear():
    dur = 0.4; n = t2n(dur); t = np.arange(n) / SR
    crk = (np.random.default_rng(3).random(n) > 0.985).astype(float)
    return (bp(noise(n), 1200, 7000) * (0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 45 * t))) * 0.35 + hp(crk, 2000) * 0.5) * np.sin(np.pi * t / dur) ** 0.5


def sfx_press():
    n = t2n(0.25); t = np.arange(n) / SR
    clank = sine(140 * np.exp(-t / 0.04) + 70, n) * np.exp(-t / 0.05) * 0.7 + bp(noise(n), 800, 5000) * np.exp(-t / 0.015) * 0.5
    clank += sine(2300, n) * np.exp(-t / 0.03) * 0.08
    return clank


def sfx_stinger():
    return brass([nm('A4'), nm('C5'), nm('E5'), nm('A5')], 0.8) * 0.9


SFX_NEW = {'city': sfx_city, 'zap': sfx_zap, 'jet': sfx_jet, 'krakoom': sfx_krakoom, 'tear': sfx_tear, 'press': sfx_press, 'stinger': sfx_stinger}
