# 23 刺绣 · 配乐：江南丝竹的细腻——扬琴（双弦击弦、金属泛音）分解和弦 + 二胡滑音旋律 + 木鱼/碰铃，A 小调五声
# 微距段只有扬琴随针脚轻点；拉远揭开全貌时二胡进入、扬琴轮音铺满；片名绣完时碰铃收尾。
# 音效：针穿上（stitch_up）、针落下拉线（stitch_down）、长拉线（thread_pull）、丝绸气流（silk_rush）、光泽流动（shimmer）
# audio/make_audio.py 把 synth.py 的全部函数注入本模块：np, SR, BEAT, BAR, t2n, mtof, nm, sine, noise, lp, hp, bp, expenv, adsr, polyblep_saw ...
import numpy as np

PENT = [nm(x) for x in ['A3', 'C4', 'D4', 'E4', 'G4', 'A4', 'C5', 'D5', 'E5', 'G5', 'A5', 'C6', 'D6', 'E6']]


def yangqin(m, dur=1.4, vel=1.0):
    """hammered dulcimer: two detuned courses, slightly inharmonic partials, felt-tipped hammer click"""
    n = t2n(dur); f = mtof(m); t = np.arange(n) / SR
    y = np.zeros(n)
    for det in (-1.6, 1.6):
        ff = f * 2 ** (det / 1200)
        for k, a, d in [(1, 1.0, 1.1), (2, 0.5, 0.55), (3, 0.32, 0.32), (4, 0.2, 0.2), (5, 0.12, 0.13), (6, 0.07, 0.08)]:
            y += a * np.sin(2 * np.pi * ff * k * (1 + 0.00045 * k * k) * t) * np.exp(-t / d)
    y += hp(noise(n), 2500) * np.exp(-t / 0.004) * 0.35
    return y * 0.16 * vel * (1 - np.exp(-t / 0.0008))


def yq_trem(m, dur, vel=0.8):
    """yangqin tremolo (lun yin): fast alternating hammers"""
    out = np.zeros(t2n(dur + 1.2)); k = 0; tt = 0.0
    while tt < dur:
        b = yangqin(m, 0.7, vel * (0.75 + 0.25 * (k % 2)) * (0.6 + 0.4 * min(1, tt / 0.25)))
        i = t2n(tt); out[i:i + len(b)] += b[: len(out) - i]
        tt += 0.0625; k += 1
    return out


def erhu(m0, m1, dur, vel=1.0):
    """two-string fiddle: bowed saw through nasal formants, slide from m0 to m1, delayed vibrato, bow noise"""
    n = t2n(dur); t = np.arange(n) / SR
    g = np.clip(t / 0.16, 0, 1); g = g * g * (3 - 2 * g)
    f = mtof(m0) + (mtof(m1) - mtof(m0)) * g
    f = f * (1 + 0.011 * np.sin(2 * np.pi * 5.6 * t) * np.clip((t - 0.2) / 0.35, 0, 1))
    y = polyblep_saw(f, n) * 0.7 + polyblep_saw(f * 1.003, n) * 0.3
    y = bp(y, 450, 3800) * 0.8 + bp(y, 900, 1500) * 0.6 + bp(y, 2400, 3200) * 0.35
    y += bp(noise(n), 1500, 6000) * 0.035
    return y * adsr(n, 0.12, 0.25, 0.85, 0.3) * 0.33 * vel


def muyu(f=900):
    n = t2n(0.12); t = np.arange(n) / SR
    return (sine(f * (1 + 0.05 * np.exp(-t / 0.01)), n) * np.exp(-t / 0.035) + bp(noise(n), 600, 3000) * np.exp(-t / 0.006) * 0.4) * 0.5


def pengling():
    out = np.zeros(t2n(2.6))
    for f0, a in [(2793, 1.0), (2803, 0.8), (4180, 0.45), (6150, 0.25)]:
        n = t2n(2.5); t = np.arange(n) / SR
        out[:n] += np.sin(2 * np.pi * f0 * t) * np.exp(-t / 0.9) * a
    out[: t2n(0.004)] += hp(noise(t2n(0.004)), 4000) * 0.5
    return out * 0.13


def tanggu():
    n = t2n(0.7); t = np.arange(n) / SR
    return (sine(85 + 40 * np.exp(-t / 0.05), n) * np.exp(-t / 0.28) + lp(noise(n), 700) * np.exp(-t / 0.03) * 0.4) * 0.75


ERHU = {1: [('E5', 'E5', 1.5), ('D5', 'C5', 0.5)],
        2: [('A4', 'C5', 1.0), ('E5', 'E5', 0.5), ('G5', 'E5', 0.5)],
        3: [('D5', 'D5', 1.0), ('C5', 'C5', 0.5), ('A4', 'A4', 0.5)],
        4: [('C5', 'A4', 1.95)]}


def mus(M, tb, name, root, tones, bi):
    pt = [p for p in PENT if p % 12 in {x % 12 for x in tones} or p % 12 in (2, 7)]
    # yangqin: one note per stitch in the macro bar, rolling eighths after
    if bi == 0:
        for q in range(4):
            if q == 0: continue
            M.add('music', yangqin(pt[4 + q % 3] + 12, 1.6, 0.8), tb + q * BEAT, 0.5, -0.2 + 0.15 * q, 0.5)
        M.add('music', yangqin(root + 12, 2.0, 0.6), tb + 0.02, 0.4, 0, 0.5)
    else:
        seq = [0, 2, 4, 3, 5, 4, 2, 3] if bi % 2 else [0, 3, 5, 4, 6, 5, 3, 1]
        for e, k in enumerate(seq if bi < 4 else []):   # bar 4: only the closing chord on 8.0, ringing out
            M.add('music', yangqin(pt[min(len(pt) - 1, 2 + k)] + 12, 1.4, 0.85 if e % 2 == 0 else 0.6), tb + e * BEAT / 2, 0.42, -0.35 + 0.1 * e, 0.5)
        if bi in (1, 2): M.add('music', yq_trem(pt[5] + 12, BEAT * 1.5, 0.55), tb + 2.5 * BEAT, 0.3, 0.3, 0.6)
    # erhu melody from the reveal
    if bi in ERHU:
        tt = tb
        for a, b, d in ERHU[bi]:
            M.add('music', erhu(nm(a), nm(b), BEAT * d * 2 * 1.02 if bi < 4 else BAR * 1.2), tt, 0.5, 0.15, 0.55)
            tt += BEAT * d * 2
    # low plucked bass on the root
    M.add('music', yangqin(root, 2.2, 0.9), tb, 0.55, -0.1, 0.3)
    if bi in (2, 3): M.add('music', yangqin(root + 7, 1.2, 0.6), tb + 2 * BEAT, 0.4, -0.1, 0.3)
    # percussion: muyu ticks, tanggu on the hook / landing
    for q in ((1, 3) if bi < 4 else ()): M.add('drums', muyu(1000 if q == 1 else 820), tb + q * BEAT, 0.35, 0.25, 0.25)
    if 1 <= bi <= 3:
        for e in range(8): M.add('drums', lp(shaker(), 5000), tb + e * BEAT / 2 + BEAT / 4, 0.05, -0.3)
    if bi in (2, 4): M.add('drums', tanggu(), tb, 0.8, 0, 0.35)
    if bi == 3: M.add('drums', tanggu(), tb + 3.5 * BEAT, 0.4, 0, 0.3)
    if bi == 4:
        for j, m in enumerate([tones[0] + 24, tones[2] + 24, tones[0] + 36]):
            M.add('music', yangqin(m, 2.4, 0.7), tb + j * 0.05, 0.35, -0.2 + 0.2 * j, 0.6)


# ---------------- SFX ----------------
def stitch_up():
    # the point breaking through taut silk: a tiny tick + fibre whisper
    n = t2n(0.18); t = np.arange(n) / SR
    y = bp(noise(n), 3000, 9000) * np.exp(-t / 0.012) * 0.5
    y += bp(noise(n), 1500, 5000) * np.clip(t / 0.03, 0, 1) * np.exp(-t / 0.05) * 0.25
    y += sine(2400, n) * np.exp(-t / 0.004) * 0.15
    return y


def stitch_down():
    # needle down + the thread drawn through the hole: a silky zip rising in pitch
    n = t2n(0.32); t = np.arange(n) / SR
    am = 0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 38 * t + 3 * np.sin(2 * np.pi * 7 * t)))
    y = svf_bp(noise(n), 1800 + 4500 * (t / 0.32) ** 1.3, 0.55) * am * np.sin(np.pi * np.clip(t / 0.32, 0, 1)) ** 1.5 * 0.55
    y[: t2n(0.02)] += bp(noise(t2n(0.02)), 2500, 8000) * 0.35
    return y


def thread_pull():
    n = t2n(0.5); t = np.arange(n) / SR
    am = 0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 30 * t))
    return svf_bp(noise(n), 1400 + 5000 * (t / 0.5) ** 1.5, 0.5) * am * np.sin(np.pi * t / 0.5) ** 1.2 * 0.5


def silk_rush():
    n = t2n(1.8); t = np.arange(n) / SR
    y = svf_bp(noise(n), 500 + 2600 * np.sin(np.pi * t / 1.8) ** 2, 0.7)
    return y * np.sin(np.pi * t / 1.8) ** 2 * 0.55


def shimmer():
    out = np.zeros(t2n(2.4))
    for i, m in enumerate(['E6', 'G6', 'A6', 'C7', 'D7', 'E7']):
        b = bell(nm(m), 1.6, 0.35) * 0.08; k = t2n(i * 0.11); out[k:k + len(b)] += b[: len(out) - k]
    n = t2n(2.0); tt = np.arange(n) / SR
    out[:n] += hp(noise(n), 6000) * np.sin(np.pi * tt / 2.0) ** 2 * 0.04
    return out


SFX_NEW = {'stitch_up': stitch_up, 'stitch_down': stitch_down, 'thread_pull': thread_pull, 'silk_rush': silk_rush, 'shimmer': shimmer}
