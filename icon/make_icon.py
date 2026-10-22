# 앱 아이콘 생성: python icon/make_icon.py → icon/AppIcon.png, icon/AppIcon.icns
# 콘셉트: 한밤중(남색 배경 + 달), 거의 덮인 맥북 틈으로 새어 나오는 따뜻한 빛 = "덮어도 깨어 있음"
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

S = 4                      # 슈퍼샘플링 배율
N = 1024 * S
OUT = Path(__file__).parent


def px(v):
    return int(v * S)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def vgradient(size, top, bottom):
    w, h = size
    g = Image.new("RGBA", (1, h))
    for y in range(h):
        g.putpixel((0, y), lerp(top, bottom, y / (h - 1)))
    return g.resize((w, h))


def rot(p, origin, deg):
    a = math.radians(deg)
    x, y = p[0] - origin[0], p[1] - origin[1]
    return (origin[0] + x * math.cos(a) - y * math.sin(a), origin[1] + x * math.sin(a) + y * math.cos(a))


# macOS 아이콘 그리드: 1024 캔버스 안에 824 둥근 사각형
tile_box = (px(100), px(100), px(924), px(924))
mask = Image.new("L", (N, N), 0)
ImageDraw.Draw(mask).rounded_rectangle(tile_box, radius=px(185), fill=255)

art = vgradient((N, N), (20, 24, 62, 255), (58, 42, 104, 255))
d = ImageDraw.Draw(art)

# 별
for x, y, r in [(640, 250, 5), (760, 330, 4), (520, 190, 3), (820, 220, 5), (700, 420, 3), (230, 470, 3), (590, 360, 2.5)]:
    d.ellipse((px(x - r), px(y - r), px(x + r), px(y + r)), fill=(255, 255, 255, 200))

# 초승달
moon = Image.new("L", (N, N), 0)
md = ImageDraw.Draw(moon)
cx, cy, r = 320, 320, 100
md.ellipse((px(cx - r), px(cy - r), px(cx + r), px(cy + r)), fill=255)
md.ellipse((px(cx - r + 55), px(cy - r - 30), px(cx + r + 55), px(cy + r - 30)), fill=0)
art.paste((246, 231, 170, 255), (0, 0), moon)

# 노트북(옆모습): 왼쪽 힌지, 덮개는 거의 닫힘
hinge = (px(200), px(660))
base_top, base_h, length = px(660), px(58), px(580)
lid_angle, lid_t = -6, px(30)

# 틈새 빛: 쐐기 + 열린 쪽으로 퍼지며 옅어지는 빛줄기
tip = rot((hinge[0] + length, hinge[1]), hinge, lid_angle)
wedge = [hinge, (hinge[0] + length, base_top), tip]
beam = Image.new("RGBA", (N, N), (0, 0, 0, 0))
ImageDraw.Draw(beam).polygon(
    [(tip[0] - px(40), tip[1]), (px(1000), tip[1] - px(170)), (px(1000), base_top + px(110)), (tip[0] - px(40), base_top)],
    fill=(255, 200, 96, 255))
fade = Image.new("L", (N, 1))
for x in range(N):
    fade.putpixel((x, 0), int(235 * max(0.0, min(1.0, (px(940) - x) / (px(940) - tip[0])))))
beam.putalpha(Image.composite(fade.resize((N, N)), Image.new("L", (N, N), 0), beam.getchannel("A")))
art = Image.alpha_composite(art, beam.filter(ImageFilter.GaussianBlur(px(30))))
glow = Image.new("RGBA", (N, N), (0, 0, 0, 0))
ImageDraw.Draw(glow).polygon(wedge, fill=(255, 190, 80, 255))
art = Image.alpha_composite(art, glow.filter(ImageFilter.GaussianBlur(px(34))))
d = ImageDraw.Draw(art)
d.polygon(wedge, fill=(255, 222, 150, 255))

# 본체
body = vgradient((length, base_h), (226, 229, 236, 255), (150, 156, 170, 255))
bmask = Image.new("L", (length, base_h), 0)
ImageDraw.Draw(bmask).rounded_rectangle((0, 0, length - 1, base_h - 1), radius=px(14), fill=255)
art.paste(body, (hinge[0], base_top), bmask)

# 덮개 (회전한 얇은 판)
lid = Image.new("RGBA", (N, N), (0, 0, 0, 0))
ld = ImageDraw.Draw(lid)
x0, y0 = hinge
corners = [(x0, y0 - lid_t), (x0 + length, y0 - lid_t), (x0 + length, y0), (x0, y0)]
ld.polygon([rot(c, hinge, lid_angle) for c in corners], fill=(214, 218, 228, 255))
edge = [(x0, y0 - lid_t), (x0 + length, y0 - lid_t), (x0 + length, y0 - lid_t + px(6)), (x0, y0 - lid_t + px(6))]
ld.polygon([rot(c, hinge, lid_angle) for c in edge], fill=(245, 247, 251, 255))
art = Image.alpha_composite(art, lid)

# 힌지
d = ImageDraw.Draw(art)
d.ellipse((hinge[0] - px(22), hinge[1] - px(24), hinge[0] + px(22), hinge[1] + px(20)), fill=(170, 176, 190, 255))

# 타일 적용 + 그림자
tile = Image.new("RGBA", (N, N), (0, 0, 0, 0))
tile.paste(art, (0, 0), mask)
shadow = Image.new("RGBA", (N, N), (0, 0, 0, 0))
shadow.paste((0, 0, 0, 110), (0, px(14)), mask.filter(ImageFilter.GaussianBlur(px(18))))
icon = Image.alpha_composite(shadow, tile).resize((1024, 1024), Image.LANCZOS)

icon.save(OUT / "AppIcon.png")
icon.save(OUT / "AppIcon.icns", sizes=[(16, 16), (32, 32), (64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024)])
print("saved", OUT / "AppIcon.png", OUT / "AppIcon.icns")
