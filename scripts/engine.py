from PIL import Image
import numpy as np

def load(p):
    im = Image.open(f'{p}_dk.jpg').convert('L')
    return np.array(im)

def row_bands(a, y0, y1, x0, x1, thr=120, minv=25):
    band = a[y0:y1, x0:x1]
    prof = (band < thr).sum(axis=1)
    out=[]; iny=False
    for i,v in enumerate(prof):
        if v>minv and not iny: s=i; iny=True
        elif v<=minv and iny:
            out.append((y0+s, y0+i)); iny=False
    if iny: out.append((y0+s, y0+len(prof)))
    return out

def col_groups(a, y0, y1, x0, x1, thr=120, minpx=2, gap=18, minw=8):
    band = a[y0:y1, x0:x1]
    ink = (band < thr).sum(axis=0) >= minpx
    res=[]; s=None; last=-999
    for i,v in enumerate(ink):
        if v:
            if s is None: s=i
            last=i
        else:
            if s is not None and i-last>=gap:
                res.append((x0+s, x0+last)); s=None
    if s is not None: res.append((x0+s, x0+last))
    # merge
    m=[]
    for g in res:
        if m and g[0]-m[-1][1] < 24: m[-1]=(m[-1][0], g[1])
        else: m.append(g)
    return [g for g in m if g[1]-g[0]>=minw]

def vlines(a, y0, y1, x0, x1, thr=140, ratio=0.25):
    """find x positions of long vertical dashed lines"""
    band = a[y0:y1, x0:x1]
    cnt = (band < thr).sum(axis=0)
    h = y1-y0
    xs = [x0+i for i,c in enumerate(cnt) if c > h*ratio]
    # cluster
    cl=[]
    for x in xs:
        if cl and x-cl[-1][-1]<=3: cl[-1].append(x)
        else: cl.append([x])
    return [int(np.mean(c)) for c in cl]

def rings(a, y0, y1, x0, x1, thr=140, hmin=36):
    """detect printed circles: columns whose ink vertical span is taller than text"""
    band = a[y0:y1, x0:x1] < thr
    res=[]
    for i in range(band.shape[1]):
        col = np.where(band[:,i])[0]
        if len(col)>1 and (col.max()-col.min())>=hmin:
            res.append(x0+i)
    cl=[]
    for x in res:
        if cl and x-cl[-1][-1]<=6: cl[-1].append(x)
        else: cl.append([x])
    return [(int(np.mean(c)), len(c)) for c in cl if len(c)>=12]
