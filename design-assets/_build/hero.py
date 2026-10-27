"""Hero / login key visuals (raster). Sources are original GenerateImage outputs (1280x720) in hero/_src/.
Outputs: <name>-1920.{png,webp} (Lanczos 1.5x upscale + light sharpen), <name>-1280.{png,webp} (native),
<name>-crop-1280x960.webp (subject crop for login side panel). desk-bottle also gets a 「德鉴」-labelled variant."""
import io, os, cairosvg
from PIL import Image, ImageFilter
from textlib import T
from art_common import INK, WINE, PAPER, line
OUT = '../hero/'
SRC = OUT + '_src/'
# subject-centre x (fraction of width) for the 4:3 crop
SCENES = {'desk-bottle': 0.66, 'cellar-jars': 0.70, 'ledger-flatlay': 0.62}

def label_overlay(W, H):
    # bottle label (measured on 1280 source): x 729-839, y 399-540 -> scale to W
    k = W / 1280
    x0, x1, y0, y1 = 729*k, 839*k, 399*k, 540*k
    cx = (x0+x1)/2; s = 30*k
    g = line(x0+14*k, y0+16*k, x1-14*k, y0+16*k, INK, 0.8*k, 0.55)
    g += T('德', cx, y0+30*k+s*0.88, s, 'serif', INK, 'middle', opacity=0.86)
    g += T('鉴', cx, y0+30*k+s*0.88+s*1.12, s, 'serif', INK, 'middle', opacity=0.86)
    g += line(x0+14*k, y1-30*k, x1-14*k, y1-30*k, INK, 0.8*k, 0.55)
    g += T('酱香型', cx, y1-15*k, 8*k, 'serifr', INK, 'middle', track=0.3, opacity=0.75)
    sw = 11*k; sx = x1-14*k-sw; sy = y0+30*k+s*2.4
    g += f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{sw:.1f}" height="{sw:.1f}" fill="{WINE}" fill-opacity="0.85"/>'
    g += T('鉴', sx+sw/2, sy+sw/2+sw*0.62*0.36, sw*0.62, 'serif', PAPER, 'middle')
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">{g}</svg>'
    ov = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))).convert('RGBA')
    return ov.filter(ImageFilter.GaussianBlur(0.35*k))

def save(im, base):
    im.save(base + '.png', optimize=True)
    im.save(base + '.webp', quality=88, method=6)

def build():
    out = []
    for name, fx in SCENES.items():
        src = Image.open(SRC + name + '.jpg').convert('RGB')
        variants = {name: src}
        if name == 'desk-bottle':
            lab = src.convert('RGBA'); lab.alpha_composite(label_overlay(*src.size))
            variants[name + '-dejian'] = lab.convert('RGB')
        for vn, im in variants.items():
            big = im.resize((1920, 1080), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 40, 2))
            if vn.endswith('-dejian'):  # redraw label crisply at 1920 rather than upscaling it
                big = src.resize((1920, 1080), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 40, 2)).convert('RGBA')
                big.alpha_composite(label_overlay(1920, 1080)); big = big.convert('RGB')
            save(big, OUT + vn + '-1920')
            save(im, OUT + vn + '-1280')
            cw, ch = 1280, 960
            left = int(min(max(fx*1920 - cw/2, 0), 1920-cw))
            big.crop((left, 60, left+cw, 60+ch)).save(OUT + vn + '-crop-1280x960.webp', quality=88, method=6)
            out.append(vn)
    return out
if __name__ == '__main__': print(build())
