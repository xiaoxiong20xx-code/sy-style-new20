# 字体和许可证

这些字体都允许免费再分发，原样放在这里，渲染时由 `render.js` 直接加载（按 `fonts.json` 登记的名字），**不会装进你的电脑系统**。

| 文件 | 字体族名（场景里写的名字） | 谁用到 | 许可证 |
|---|---|---|---|
| NotoSansCJKsc-Regular / Medium / Bold.otf | Noto Sans CJK SC（思源黑体） | 22 粉笔黑板、26 立体书、33 美式漫画 | SIL OFL 1.1，见 `LICENSE-NotoSansCJK.txt` |
| Inter-Medium / SemiBold / Bold.otf | Inter | 34 孔版套印、36 热成像 | SIL OFL 1.1，见 `LICENSE-Inter.txt` |
| DejaVuSansMono.ttf、DejaVuSansMono-Bold.ttf | DejaVu Sans Mono | 35 字符画、36 热成像 | Bitstream Vera 许可 + 公有领域，见 `LICENSE-DejaVu.txt` |
| texgyreheroscn-bold / bolditalic.otf | TeX Gyre Heros Cn | 33 美式漫画 | GUST Font License，见 `LICENSE-TeXGyre.txt` |

只放了这 20 条片子实际用到的字重。思源黑体是完整字库（不是子集），场景里改成任何常用汉字都能正常显示。

## 想换别的字体或字重

1. 把字体文件（.otf / .ttf）放进这个文件夹。
2. 在 `fonts.json` 里加一行，`family` 写场景里要用的名字，`weight` 写字重（400 常规、500 中等、700 粗体……）。
3. 在上面的表里补上它的许可证（只用允许再分发的字体，比如 OFL 协议的）。
4. 先 `node make.js still 编号 秒数` 出一张图看效果。
