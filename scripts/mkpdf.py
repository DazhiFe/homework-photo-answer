# -*- coding: utf-8 -*-
"""把若干张答案图合成一份 A4 多页 PDF。

用法（推荐，直接传文件）：
  python mkpdf.py out.pdf a.jpg b.jpg c.jpg
或改文件顶部的 ORDER 后空跑：
  python mkpdf.py

输出：A4@200dpi，图片等比缩放居中留白（42px），不裁切、不拉伸，可直接打印。
"""
from PIL import Image
import os
import sys

OUT_PDF = '数学练习答案合集.pdf'
ORDER = []          # 可选：写死图片列表

DPI = 200
PW, PH = 1654, 2339      # A4 @ 200dpi
MARGIN = 42


def build(images, out_pdf):
    images = [f for f in images if os.path.exists(f)]
    if not images:
        print('没有可合成的图片。用法: python mkpdf.py out.pdf a.jpg b.jpg')
        return
    pages = []
    for f in images:
        im = Image.open(f).convert('RGB')
        uw, uh = PW - 2 * MARGIN, PH - 2 * MARGIN
        s = min(uw / im.width, uh / im.height)
        w, h = int(im.width * s), int(im.height * s)
        pic = im.resize((w, h), Image.LANCZOS)
        canvas = Image.new('RGB', (PW, PH), (255, 255, 255))
        canvas.paste(pic, ((PW - w) // 2, (PH - h) // 2))
        pages.append(canvas)
    pages[0].save(out_pdf, 'PDF', resolution=DPI, save_all=True,
                  append_images=pages[1:])
    print('PDF:', out_pdf, round(os.path.getsize(out_pdf) / 1024 / 1024, 2), 'MB',
          len(pages), 'pages')


if __name__ == '__main__':
    args = sys.argv[1:]
    if args and not args[0].endswith('.jpg') and not args[0].endswith('.jpeg'):
        build(args[1:], args[0])
    else:
        build(args or ORDER, OUT_PDF)
