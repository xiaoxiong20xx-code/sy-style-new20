# 给一个风格合成 10 秒配乐 + 音效（make.js 会自动调用，一般不用手动跑）
#   python audio/make_audio.py styles/35-ascii 35 styles/35-ascii/cues.json frames/35/raw.wav
# 配乐：styles/NN-name/music.py 里的 mus(M, tb, name, root, tones, bi)，每小节调用一次（120 BPM，一小节 2 秒）
#       music.py 里可以直接用 synth.py 的全部乐器函数（marimba、pad、kick、bell、noise、lp……），
#       还可以写 SFX_NEW = {'名字': 无参函数} 加这个风格专属的音效，cues 里直接用名字。
# 音效时间点：cues.json（make.js 从场景的 cues: [...] 导出）
import importlib.util, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent


def main(style_dir, nn, cues_file, out_wav):
    d = pathlib.Path(style_dir)
    cues = json.loads(pathlib.Path(cues_file).read_text(encoding='utf8'))
    sys.path.insert(0, str(HERE))
    import synth
    mp = d / 'music.py'
    if not mp.exists():
        sys.exit(f'{d.name} 缺 music.py')
    spec = importlib.util.spec_from_file_location('music_' + nn, mp)
    m = importlib.util.module_from_spec(spec)
    m.__dict__.update({k: v for k, v in synth.__dict__.items() if not k.startswith('__')})  # music.py 里可直接用 synth 的乐器函数
    spec.loader.exec_module(m)
    synth.EXTRA[nn] = m.mus
    synth.SFX.update(getattr(m, 'SFX_NEW', {}))
    pathlib.Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
    synth.render({'sections': [{'kind': nn, 'start': 0, 'dur': 10, 'cues': cues}], 'global_cues': []}, str(out_wav))


if __name__ == '__main__':
    if len(sys.argv) != 5:
        sys.exit('用法：python audio/make_audio.py <风格文件夹> <编号> <cues.json> <输出.wav>')
    main(*sys.argv[1:])
