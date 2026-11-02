# 26 立体书 · 配乐：八音盒 + 钢片琴 + 竖琴分解和弦 + 柔和弦乐（睡前故事、夜晚的魔法）
# 音效：翻开硬壳书（book_open）、纸艺立起（flap）、镜头穿过纸片（paper_pass）、拉条（tab_slide）
import numpy as np


def musicbox(m, dur=1.4):
    n = t2n(dur); t = np.arange(n) / SR; f = mtof(m)
    y = sine(f, n) * np.exp(-t / 0.9) + 0.45 * sine(f * 2.0, n) * np.exp(-t / 0.35) + 0.25 * sine(f * 5.04, n) * np.exp(-t / 0.08) + 0.12 * sine(f * 8.9, n) * np.exp(-t / 0.03)
    return y * (1 - np.exp(-t / 0.0015)) * 0.33


def celesta(m, dur=1.2):
    n = t2n(dur); t = np.arange(n) / SR; f = mtof(m)
    y = sine(f, n) * np.exp(-t / 0.6) + 0.3 * sine(f * 3, n) * np.exp(-t / 0.15) + 0.15 * sine(f * 4.2, n) * np.exp(-t / 0.05)
    return y * (1 - np.exp(-t / 0.002)) * 0.3


TUNE = {'Am': ['E6', 'A6', 'C7', 'B6', 'A6', 'E6', None, 'G6'], 'F': ['A6', None, 'C7', 'A6', 'F6', 'G6', 'A6', None],
        'C': ['G6', 'E6', 'C6', 'E6', 'G6', 'C7', None, 'B6'], 'G': ['D7', 'B6', 'G6', None, 'A6', 'B6', 'D7', None]}


def mus(M, tb, name, root, tones, bi):
    last = bi == 4
    # harp: rising arpeggio across two octaves on every bar
    arp = [tones[0] - 12, tones[2] - 12, tones[0], tones[1], tones[2], tones[0] + 12, tones[1] + 12, tones[2] + 12]
    for e, m in enumerate(arp[: 6 if last else 8]):
        M.add('music', ks(m, 1.6, 0.55, 0.998), tb + e * BEAT / 4, 0.3, -0.35 + 0.1 * e, 0.5)
    if not last:
        for e, m in enumerate(arp[::-1][2:6]):
            M.add('music', ks(m, 1.2, 0.5, 0.997), tb + 2 * BEAT + e * BEAT / 2, 0.22, 0.3 - 0.1 * e, 0.5)
    # music-box tune (from bar 0 lightly, fuller from bar 1)
    mel = TUNE[name]
    for e, sN in enumerate(mel):
        if sN and (bi > 0 or e % 2 == 0) and not (last and e > 2):
            M.add('music', musicbox(nm(sN) - 12, 1.5), tb + e * BEAT / 2, 0.5 if bi else 0.35, 0.2, 0.55)
            if bi in (2, 3): M.add('music', celesta(nm(sN), 1.0), tb + e * BEAT / 2 + 0.005, 0.18, -0.25, 0.6)
    # strings: soft bed, swelling for the flight through the forest
    M.add('music', strings([x + 12 for x in tones], BAR * (1.8 if last else 1.03), 1800 if bi < 2 else 2600), tb, 0.3 if bi < 2 else 0.42, 0, 0.6)
    M.add('music', strings([root - 12], BAR * (1.8 if last else 1.03), 700), tb, 0.35, 0, 0.3)
    # a heartbeat of a pulse: soft kick on 1, tiny shaker
    if not last:
        M.add('drums', soft_kick() * 0.8, tb, 0.42)
        for q in range(4): M.add('drums', lp(shaker(), 7000), tb + q * BEAT + BEAT / 2, 0.05, 0.35)
    if last:
        for j, m in enumerate(tones + [tones[0] + 12]):
            M.add('music', musicbox(m + 12, 2.6), tb + 0.02 * j, 0.35, -0.3 + 0.2 * j, 0.6)


def sfx_book_open():
    dur = 1.0; n = t2n(dur); t = np.arange(n) / SR
    creak = bp((np.sin(2 * np.pi * (70 + 40 * t) * t) > 0.96).astype(float) + noise(n) * 0.02, 300, 2500) * np.sin(np.pi * np.clip(t / 0.45, 0, 1)) * 0.5
    swoosh = svf_bp(noise(n), 400 + 2600 * (t / dur), 0.6) * np.sin(np.pi * t / dur) ** 2 * 0.4
    thump = np.zeros(n); k = t2n(0.82); m = t2n(0.15); tt = np.arange(m) / SR
    thump[k:k + m] = (sine(90 * np.exp(-tt / 0.06) + 50, m) * np.exp(-tt / 0.05) * 0.6 + lp(noise(m), 1500) * np.exp(-tt / 0.01) * 0.3)
    return creak + swoosh + thump


def sfx_flap():
    n = t2n(0.18); t = np.arange(n) / SR
    snap_ = bp(noise(n), 1200, 7000) * np.exp(-t / 0.012) * 0.6
    body = sine(180 * np.exp(-t / 0.03) + 90, n) * np.exp(-t / 0.04) * 0.35
    rustle = bp(noise(n), 2500, 9000) * np.exp(-t / 0.05) * np.abs(np.sin(2 * np.pi * 60 * t)) * 0.25
    return snap_ + body + rustle


def sfx_paper_pass():
    dur = 0.45; n = t2n(dur); t = np.arange(n) / SR
    fl = 0.5 + 0.5 * np.sin(2 * np.pi * 38 * t) * np.sin(2 * np.pi * 9 * t)
    return svf_bp(noise(n), 900 + 3500 * np.sin(np.pi * t / dur), 0.5) * fl * np.sin(np.pi * t / dur) ** 1.5 * 0.55


def sfx_tab_slide():
    dur = 0.34; n = t2n(dur); t = np.arange(n) / SR
    return bp(noise(n), 1500, 6000) * (0.6 + 0.4 * np.sin(2 * np.pi * 70 * t)) * np.sin(np.pi * t / dur) * 0.45


SFX_NEW = {'book_open': sfx_book_open, 'flap': sfx_flap, 'paper_pass': sfx_paper_pass, 'tab_slide': sfx_tab_slide}


def sfx_moon_set():
    # the moon card bumps against its stop: a soft papery knock
    n = t2n(0.2); t = np.arange(n) / SR
    return sine(320 * np.exp(-t / 0.03) + 140, n) * np.exp(-t / 0.04) * 0.5 + bp(noise(n), 900, 5000) * np.exp(-t / 0.01) * 0.35


SFX_NEW['moon_set'] = sfx_moon_set
