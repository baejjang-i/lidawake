# 앱 아이콘 생성: python icon/make_icon.py → icon/AppIcon.png, icon/AppIcon.icns
# 콘셉트: 커피 마신 맥북 = 잠들지 않는 맥북. 메뉴 막대의 ☕(잠자기 방지) 아이콘과 같은 상징을 쓴다
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

S = 4                      # 슈퍼샘플링 배율
N = 1024 * S
OUT = Path(__file__).parent

AMBER = (255, 190, 80, 255)
CREAM = (255, 232, 180, 255)


def px(v):
    return int(v * S)


DY = 40                    # 맥북 전체를 타일 세로 중앙으로 내림


def box(x0, y0, x1, y1):
    return (px(x0), px(y0 + DY), px(x1), px(y1 + DY))


def vgradient(size, top, bottom):
    w, h = size
    g = Image.new("RGBA", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        g.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(4)))
    return g.resize((w, h))


def layer():
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def paste_gradient(dst, xy, top, bottom, radius):
    x0, y0, x1, y1 = box(*xy)
    m = Image.new("L", (x1 - x0, y1 - y0), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, x1 - x0 - 1, y1 - y0 - 1), radius=px(radius), fill=255)
    dst.paste(vgradient((x1 - x0, y1 - y0), top, bottom), (x0, y0), m)


# macOS 아이콘 그리드: 1024 캔버스 안에 824 둥근 사각형, 밤하늘 배경
mask = Image.new("L", (N, N), 0)
ImageDraw.Draw(mask).rounded_rectangle((px(100), px(100), px(924), px(924)), radius=px(185), fill=255)
art = vgradient((N, N), (28, 30, 74, 255), (66, 44, 112, 255))

# 맥북 그림자
sh, d = layer()
d.rounded_rectangle(box(170, 690, 854, 735), radius=px(30), fill=(0, 0, 0, 140))
art = Image.alpha_composite(art, sh.filter(ImageFilter.GaussianBlur(px(18))))

# 맥북 정면: 화면 테두리(은색) + 디스플레이(어두운 남색)
paste_gradient(art, (222, 232, 802, 650), (232, 235, 242, 255), (196, 201, 212, 255), 40)
paste_gradient(art, (248, 258, 776, 624), (18, 20, 44, 255), (34, 30, 70, 255), 18)

# 화면 속 커피잔 뒤의 따뜻한 빛
glow, d = layer()
d.ellipse(box(372, 330, 652, 590), fill=(255, 170, 60, 150))
art = Image.alpha_composite(art, glow.filter(ImageFilter.GaussianBlur(px(46))))

# 커피잔: 잔 몸통, 손잡이, 받침
cup, d = layer()
d.rounded_rectangle(box(422, 420, 582, 548), radius=px(46), fill=AMBER)
d.rectangle(box(422, 420, 582, 470), fill=AMBER)
d.ellipse(box(556, 444, 630, 518), outline=AMBER, width=px(20))
d.rounded_rectangle(box(392, 556, 612, 578), radius=px(11), fill=AMBER)
d.rectangle(box(436, 420, 568, 434), fill=CREAM)      # 잔 입구의 커피 표면 하이라이트

# 김 3줄 (사인 곡선)
for x0 in (462, 502, 542):
    pts = [(px(x0 + 10 * math.sin(t / 14)), px(400 + DY - t)) for t in range(0, 82, 2)]
    d.line(pts, fill=CREAM, width=px(13), joint="curve")
    for x, y in (pts[0], pts[-1]):
        d.ellipse((x - px(6.5), y - px(6.5), x + px(6.5), y + px(6.5)), fill=CREAM)
art = Image.alpha_composite(art, cup)

# 본체(키보드 쪽): 화면보다 넓은 얇은 판 + 가운데 손가락 홈
paste_gradient(art, (160, 650, 864, 698), (226, 229, 236, 255), (156, 162, 176, 255), 22)
d = ImageDraw.Draw(art)
d.rounded_rectangle(box(452, 650, 572, 664), radius=px(7), fill=(150, 156, 170, 255))

# 초승달(밤 = 원래 잠들 시간)
moon = Image.new("L", (N, N), 0)
md = ImageDraw.Draw(moon)
md.ellipse(box(745, 90, 835, 180), fill=255)
md.ellipse(box(771, 74, 861, 164), fill=0)
art.paste((246, 231, 170, 255), (0, 0), moon)

# 타일 적용 + 바깥 그림자
tile = Image.new("RGBA", (N, N), (0, 0, 0, 0))
tile.paste(art, (0, 0), mask)
shadow = Image.new("RGBA", (N, N), (0, 0, 0, 0))
shadow.paste((0, 0, 0, 110), (0, px(14)), mask.filter(ImageFilter.GaussianBlur(px(18))))
icon = Image.alpha_composite(shadow, tile).resize((1024, 1024), Image.LANCZOS)

icon.save(OUT / "AppIcon.png")
icon.save(OUT / "AppIcon.icns", sizes=[(16, 16), (32, 32), (64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024)])
print("saved", OUT / "AppIcon.png", OUT / "AppIcon.icns")
