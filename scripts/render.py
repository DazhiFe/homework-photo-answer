# -*- coding: utf-8 -*-
import os
import platform
import glob
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from engine import load, row_bands, col_groups, vlines

RED = (205, 0, 0)
BLUE = (0, 70, 200)

_HERE = os.path.dirname(os.path.abspath(__file__))


def _bundled():
    """技能自带的开源字体（思源黑体 / Source Han Sans，SIL OFL 可自由分发）"""
    out = []
    for d in (os.path.join(_HERE, 'assets'), os.path.join(_HERE, '..', 'assets')):
        out += sorted(glob.glob(os.path.join(d, '*.otf')))
        out += sorted(glob.glob(os.path.join(d, '*.ttf')))
        out += sorted(glob.glob(os.path.join(d, '*.ttc')))
    return out


def _cjk_candidates():
    """按平台找中文粗体字。注意：微软雅黑不能随项目分发，只能在本机引用。"""
    sysname = platform.system()
    if sysname == 'Windows':
        paths = ['C:/Windows/Fonts/msyhbd.ttc', 'C:/Windows/Fonts/msyh.ttc',
                 'C:/Windows/Fonts/simhei.ttf']
    elif sysname == 'Darwin':
        paths = ['/System/Library/Fonts/PingFang.ttc',
                 '/System/Library/Fonts/STHeiti Medium.ttc',
                 '/Library/Fonts/Arial Unicode.ttf',
                 '/System/Library/Fonts/Hiragino Sans GB.ttc']
    else:  # Linux
        paths = ['/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
                 '/usr/share/fonts/opentype/noto/NotoSansCJKsc-Bold.otf',
                 '/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc',
                 '/usr/share/fonts/google-noto-cjk/NotoSansCJK-Bold.ttc',
                 '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
                 '/usr/share/fonts/truetype/arphic/uming.ttc']
    return paths + _bundled()


def _mono_candidates():
    sysname = platform.system()
    if sysname == 'Windows':
        paths = ['C:/Windows/Fonts/consolab.ttf', 'C:/Windows/Fonts/consola.ttf',
                 'C:/Windows/Fonts/simhei.ttf']
    elif sysname == 'Darwin':
        paths = ['/System/Library/Fonts/Menlo.ttc', '/System/Library/Fonts/Courier.dfont']
    else:
        paths = ['/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',
                 '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf']
    return paths + _bundled()


def font(path, size):
    for p in path:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


CN = _cjk_candidates()
MONO = _mono_candidates()

F_MAIN = font(CN, 30)
F_NOTE = font(CN, 23)

# 找不到任何中文字体时给出明确提示，避免渲染出一堆方块才被发现
try:
    _ok = F_MAIN.getlength('中') > 8
except Exception:
    _ok = False
if not _ok:
    print('[警告] 没找到可用的中文字体，答案会变成方块。'
          '请把任意中文字体放到 scripts/assets/ 目录，'
          '或安装系统字体（Windows 微软雅黑 / macOS 苹方 / Linux noto-cjk）。')

def fit_cn(text, maxw, maxsize=26):
    for s in range(maxsize, 12, -1):
        f = font(CN, s)
        if f.getlength(text) <= maxw: return f
    return font(CN, 12)

def row_center(a, y, x0, x1, thr=125):
    y0 = max(0, y-22); y1 = y+22
    b = a[y0:y1, x0:x1] < thr
    prof = b.sum(axis=1)
    ys = np.where(prof > 0)[0]
    if len(ys) == 0: return y
    runs = []; s = ys[0]; prev = ys[0]
    for v in ys[1:]:
        if v - prev <= 3: prev = v
        else: runs.append((s, prev)); s = v; prev = v
    runs.append((s, prev))
    cy = (y1-y0)//2
    cand = [r for r in runs if r[1]-r[0] <= 70]
    if not cand: return y
    best = min(cand, key=lambda r: abs((r[0]+r[1])/2 - cy))
    return y0 + (best[0]+best[1])//2

def ink_right(a, y, x0, x1, thr=125):
    band = a[max(0,y-17):y+17, x0:x1]
    ink = (band < thr).sum(axis=0) >= 2
    idx = np.where(ink)[0]
    return (x0 + int(idx.max())) if len(idx) else None

def after(d, a, y, x0, x1, text, f=F_MAIN, color=RED, dx=10):
    y = row_center(a, y, x0, x1)
    x = ink_right(a, y, x0, x1)
    if x is None: x = x0
    d.text((x+dx, y), text, font=f, fill=color, anchor='lm')

def put(d, x, y, text, f, color=RED, anchor='mm'):
    d.text((x, y), text, font=f, fill=color, anchor=anchor)

def steps(d, x, y, lines, size=26, dy=34, color=RED):
    f = font(CN, size)
    for i, t in enumerate(lines):
        d.text((x, y+i*dy), t, font=f, fill=color, anchor='lm')

def vblock(img, d, a_arr, a, b, x_right, y_top, y_limit, verify=None):
    final = a*b
    sa, sb = str(a), str(b)
    parts = []
    for i, ch in enumerate(reversed(sb)):
        dg = int(ch)
        if dg: parts.append((a*dg, i))
    W = max(len(str(final)), len(sa)+1, len(sb)+2)
    for v,i in parts: W = max(W, len(str(v))+i+1)
    def place(n, shift=0):
        s = str(n); end = W-1-shift; start = end-len(s)+1
        arr = [' ']*W
        for k,ch in enumerate(s): arr[start+k] = ch
        return ''.join(arr)
    rows = [('t', place(a)), ('t', '×'+place(b)[1:]), ('l', None)]
    for v,i in parts: rows.append(('t', place(v, i)))
    rows.append(('l', None)); rows.append(('t', place(final)))
    n = len(rows) + (1.7 if verify else 0.4)
    lh = int(min(29, max(19, (y_limit - y_top)/n)))
    fs = int(lh*0.80)
    f = font(MONO, fs)
    cw = f.getlength('0')
    xl = x_right - W*cw
    y = y_top
    for kind, s in rows:
        if kind == 'l':
            d.line([(xl-3, y+int(lh*0.42)), (x_right+2, y+int(lh*0.42))], fill=RED, width=2)
        else:
            d.text((xl, y), s, font=f, fill=RED)
        y += lh
    if verify:
        put(d, x_right - 48, min(y+int(lh*0.9), y_limit), verify, F_NOTE, RED, anchor='rm')

def guide_x_right(a_arr, y_top, y_limit, xf0, xf1):
    g = vlines(a_arr, y_top, int(y_top + (y_limit-y_top)*0.75), max(0,xf0-70), min(xf1+170, 1130))
    return (max(g)+10) if g else (xf1+55)

# ------------- 通用渲染 -------------
def render(page, cfg):
    im = Image.open(f'{page}_dk.jpg').convert('RGB')
    a = np.array(im.convert('L'))
    d = ImageDraw.Draw(im)
    for item in cfg.get('after', []):
        y, x0, x1, txt = item[:4]
        fs = item[4] if len(item) > 4 else None
        after(d, a, y, x0, x1, txt, f=(font(CN, fs) if fs else F_MAIN))
    for (x, y, txt, mw) in cfg.get('fills', []):
        f = fit_cn(txt, mw, 27)
        put(d, x, y, txt, f, RED, 'mm')
    for (yf, xf0, xf1, A, B, y_top, y_limit, ver) in cfg.get('verts', []):
        xr = guide_x_right(a, y_top, y_limit, xf0, xf1)
        after(d, a, yf, xf0-15, xf1+15, str(A*B))
        vblock(im, d, a, A, B, xr, y_top, y_limit, ver)
    for (x, y, lines, size, dy) in cfg.get('blocks', []):
        steps(d, x, y, lines, size, dy)
    for (x, y, txt, size) in cfg.get('notes', []):
        d.text((x, y), txt, font=font(CN, size), fill=RED, anchor='lm')
    out = f'answer/{page}_ans.jpg'
    os.makedirs('answer', exist_ok=True)
    im.save(out, quality=93)
    print('saved', out)
    return im
