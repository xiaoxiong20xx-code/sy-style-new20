# 36 热成像 · 配乐：冷暗的电子氛围——低频正弦脉冲、过滤噪声铺底、像仪器读数一样的玻璃 FM 叮声；
# 热水倒入时暖色和弦慢慢升起，手按上玻璃那一下是「心跳」低鼓（咚-咚），写字时叮声跟着笔画走，最后余温淡出。
# 和 23 扬琴、27 clavinet 放克、30 锣鼓、34 脉冲波电子都不同。
# 音效：相机提示音（cam_beep）、倒水（pour）、蒸汽嘶声（steam_hiss）、壶放下（kettle_down）、摇镜气流（pan_whoosh）、
#      手按玻璃（glass_press）、热印显现（print_glow）、手指划玻璃（finger_squeak）
# audio/make_audio.py 把 synth.py 的全部函数注入本模块：np, SR, BEAT, BAR, t2n, mtof, nm, sine, noise, lp, hp, bp, expenv, adsr, polyblep_saw ...
import numpy as np


def fmping(m, dur=1.6, idx=2.0):
    n = t2n(dur); f = mtof(m); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t + idx * np.exp(-t / 0.25) * np.sin(2 * np.pi * f * 1.41 * t)) * np.exp(-t / 0.6)
    return y * (1 - np.exp(-t / 0.002)) * 0.2


def subpulse(m, dur):
    n = t2n(dur); f = mtof(m); t = np.arange(n) / SR
    return sine(f, n) * np.exp(-t / (dur * 0.5)) * (1 - np.exp(-t / 0.01)) * 0.6


def heart():
    n = t2n(0.5); t = np.arange(n) / SR
    beat = lambda k: sine(55 + 25 * np.exp(-t / 0.03), n) * np.exp(-t / 0.12)
    y = beat(0); y2 = np.zeros(n); d = t2n(0.16); y2[d:] = (beat(0) * 0.7)[: n - d]
    return lp(y + y2, 400) * 0.9


def mus(M, tb, name, root, tones, bi):
    # cold bed: filtered noise + a low drone; warmer chords from the moment the hot water lands
    n = t2n(BAR * 1.05); t = np.arange(n) / SR
    bed = svf_lp(noise(n), 500 + 300 * np.sin(np.pi * t / (BAR * 1.05)), 0.7) * 0.08
    M.add('music', bed, tb, 0.8, 0, 0.6)
    M.add('music', sine(mtof(root - 12), n) * adsr(n, 0.4, 0.3, 0.8, 0.5) * 0.25, tb, 0.7)
    if bi >= 1:
        M.add('music', pad([x + 12 for x in chord_ext(name, tones)], BAR, 1200 + 400 * bi, 0.008), tb, 0.32 + 0.05 * bi, 0, 0.6)
    # pulse: sub on 1 and 3, hats very quiet; the heartbeat in bar 2 (hand on the glass); bar 4 is the resolution: one low hit on 8.0, then it rings out
    for q in ((0,) if bi == 4 else (0, 2)): M.add('drums', subpulse(root - 24 + 12, BEAT * (3.0 if bi == 4 else 0.9)), tb + q * BEAT, 0.6 if bi == 4 else 0.55)
    if bi == 2:
        M.add('drums', heart(), tb + 0.5, 0.9); M.add('drums', heart(), tb + 1.5, 0.7)
    if 1 <= bi <= 3:
        for e in range(8): M.add('drums', hp(noise(t2n(0.03)), 8000) * expenv(t2n(0.03), 0.008), tb + e * BEAT / 2 + BEAT / 4, 0.12, 0.3 if e % 2 else -0.3)
    # glassy pings like instrument readouts; in bars 3-4 they trace the writing
    # bars 3-4 follow the doodle: a ping on each stroke (5.75 cup, 6.75 / 7.25 / 7.75 steam), the tonic on 8.0
    pings = {0: [(0.5, 3), (2.5, 1)], 1: [(0.0, 2), (1.5, 3), (3.0, 4)], 2: [(1.0, 5), (3.5, 3)], 3: [(0.0, 4), (1.5, 4), (2.5, 5), (3.5, 6)], 4: [(0.0, 7)]}
    pent = [tones[0], tones[1], tones[2], tones[0] + 12, tones[1] + 12, tones[2] + 12, tones[0] + 24, tones[1] + 24]
    for q, k in pings[bi]: M.add('music', fmping(pent[k] + 12, 1.6, 2.4), tb + q * BEAT, 0.4, -0.4 + 0.1 * k, 0.6)
    if bi == 4: M.add('music', pad([x + 12 for x in tones], BAR * 1.4, 900, 0.006), tb, 0.34, 0, 0.7)


# ---------------- SFX ----------------
def cam_beep():
    n = t2n(0.09); t = np.arange(n) / SR
    return sine(2600, n) * np.clip(t / 0.003, 0, 1) * np.exp(-t / 0.05) * 0.25


def pour():
    n = t2n(2.4); t = np.arange(n) / SR
    stream = bp(noise(n), 500, 4000) * 0.35 * (0.8 + 0.2 * np.sin(2 * np.pi * 7 * t))
    gl = np.zeros(n); r = np.random.default_rng(3)
    for _ in range(40):
        k = r.integers(0, n - 4000); f = 300 + r.random() * 500 + (k / n) * 400; m = t2n(0.06)
        gl[k:k + m] += sine(f * (1 + 2 * np.arange(m) / SR), m) * np.exp(-np.arange(m) / SR / 0.02) * 0.25
    env = np.clip(t / 0.08, 0, 1) * np.clip((2.4 - t) / 0.3, 0, 1)
    return (stream + gl) * env * 0.8


def steam_hiss():
    n = t2n(2.6); t = np.arange(n) / SR
    return hp(noise(n), 4000) * 0.12 * np.sin(np.pi * t / 2.6) ** 1.5


def kettle_down():
    return over(sfx_thud() * 0.6, glass_clink(nm('A6')) * 0.5)


def pan_whoosh():
    return whoosh(0.7, True, 200, 3000, 0.5)


def glass_press():
    n = t2n(0.6); t = np.arange(n) / SR
    thump = sine(90 * np.exp(-t / 0.06) + 50, n) * np.exp(-t / 0.1) * 0.6
    squeak = sine(1400 + 300 * np.sin(2 * np.pi * 9 * t), n) * np.clip(t / 0.05, 0, 1) * np.exp(-t / 0.12) * 0.05
    return thump + squeak + heart()[: n] * 0.6 if len(heart()) >= n else thump + squeak


def print_glow():
    return over(swell(1.4) * 0.6, fmping(nm('E6'), 1.6, 1.5))


def finger_squeak(dur=0.75):
    n = t2n(dur); t = np.arange(n) / SR
    f = 900 + 500 * np.sin(2 * np.pi * 2.3 * t) + 200 * np.sin(2 * np.pi * 7.1 * t)
    y = svf_bp(noise(n), f, 0.08) * 0.5 + sine(f, n) * 0.04
    gate = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 3.1 * t + 0.4))
    return y * gate * np.sin(np.pi * t / dur) * 0.6


def shutter_clack():
    # the camera's internal shutter (NUC flag) snapping across on capture: a dry two-part click
    n = t2n(0.12); t = np.arange(n) / SR
    c1 = hp(noise(n), 2500) * np.exp(-t / 0.004) * 0.5
    c2 = np.zeros(n); k = t2n(0.035); c2[k:] = (hp(noise(n - k), 1800) * np.exp(-np.arange(n - k) / SR / 0.006) * 0.35)
    return c1 + c2 + sine(1800, n) * np.exp(-t / 0.01) * 0.05


SFX_NEW = {'cam_beep': cam_beep, 'pour': pour, 'steam_hiss': steam_hiss, 'kettle_down': kettle_down, 'pan_whoosh': pan_whoosh,
           'glass_press': glass_press, 'print_glow': print_glow, 'finger_squeak': finger_squeak, 'finger_squeak_s': lambda: finger_squeak(0.27),
           'shutter_clack': shutter_clack}
