"""Regenerates site/images/og-image*.jpg and the icons if the name, ward or slogan text changes."""
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import pathlib, os
ROOT = pathlib.Path(__file__).resolve().parent.parent
os.chdir(ROOT)
# Needs Khand-Bold.ttf, MartelSans-Regular.ttf, MartelSans-Bold.ttf (Google Fonts, OFL) in src/fonts/
F = "src/fonts/"
RAQM = ImageFont.Layout.RAQM
def font(name, size): return ImageFont.truetype(F+name, size, layout_engine=RAQM)

GREEN=(11,122,60); DEEP=(6,74,38); RAY=(16,138,70); MUSTARD=(242,193,46); WHITE=(255,255,255)
SAFF=(255,153,51); IND_GREEN=(19,136,8)

def rays(draw, cx, cy, r, step=10, color=RAY):
    for a in range(0, 360, step*2):
        a1, a2 = math.radians(a), math.radians(a+step)
        draw.polygon([(cx,cy),(cx+r*math.cos(a1),cy+r*math.sin(a1)),(cx+r*math.cos(a2),cy+r*math.sin(a2))], fill=color)

def circle_photo(size):
    p = Image.open("site/images/sunil-charora-portrait.webp").convert("RGB").resize((size,size), Image.LANCZOS)
    m = Image.new("L",(size*4,size*4),0); ImageDraw.Draw(m).ellipse((0,0,size*4-1,size*4-1), fill=255)
    m = m.resize((size,size), Image.LANCZOS)
    return p, m

def ribbon(draw, x, y, w, h, notch, fill):
    draw.polygon([(x,y),(x+w,y),(x+w-notch,y+h/2),(x+w,y+h),(x,y+h),(x+notch,y+h/2)], fill=fill)

def og(lang, out):
    W,H = 1200,630
    im = Image.new("RGB",(W,H),GREEN); d = ImageDraw.Draw(im)
    cx, cy = 905, 330
    rays(d, cx, cy, 900)
    # tricolour strip
    d.rectangle((0,0,W//3,9), fill=SAFF); d.rectangle((W//3,0,2*W//3,9), fill=WHITE); d.rectangle((2*W//3,0,W,9), fill=IND_GREEN)
    # portrait with rings
    R = 205
    d.ellipse((cx-R-26,cy-R-26,cx+R+26,cy+R+26), fill=MUSTARD)
    d.ellipse((cx-R-16,cy-R-16,cx+R+16,cy+R+16), fill=GREEN)
    d.ellipse((cx-R-10,cy-R-10,cx+R+10,cy+R+10), fill=WHITE)
    p, m = circle_photo(2*R); im.paste(p,(cx-R,cy-R),m)
    d = ImageDraw.Draw(im)
    if lang=="hi":
        top="जनसंपर्क अभियान 2027, अनूपशहर विधानसभा (67)"; name1="सुनील"; name2="चरौरा"
        slogan="हर सुख-दुख में आपके साथ"; l1="पूर्व जिला पंचायत सदस्य (वार्ड नं. 50), बुलंदशहर"; l2="राष्ट्रीय लोक दल"
        phone="फोन / व्हाट्सएप: 97191 66039"
    else:
        top="Outreach Campaign 2027, Anupshahr Assembly (67)"; name1="Sunil"; name2="Charora"
        slogan="With you in every joy and sorrow"; l1="Former Zila Panchayat Member (Ward 50), Bulandshahr"; l2="Rashtriya Lok Dal (RLD)"
        phone="Call / WhatsApp: 97191 66039"
    x=64
    d.text((x,70), top, font=font("MartelSans-Bold.ttf",26), fill=MUSTARD, anchor="la")
    fn = font("Khand-Bold.ttf", 136 if lang=="hi" else 128)
    d.text((x,98), name1, font=fn, fill=WHITE, anchor="la")
    d.text((x,256), name2, font=fn, fill=WHITE, anchor="la")
    fs = font("Khand-Bold.ttf", 44 if lang=="hi" else 36)
    bb = d.textbbox((0,0), slogan, font=fs, anchor="la"); tw = bb[2]-bb[0]
    ry = 418; rh = 62
    ribbon(d, x, ry, tw+70, rh, 16, MUSTARD)
    d.text((x+35, ry+rh/2), slogan, font=fs, fill=DEEP, anchor="lm")
    d.text((x,502), l1, font=font("MartelSans-Regular.ttf",23), fill=WHITE, anchor="la")
    d.text((x,536), l2, font=font("MartelSans-Bold.ttf",25), fill=WHITE, anchor="la")
    fp = font("MartelSans-Bold.ttf",26)
    bb = d.textbbox((0,0), phone, font=fp, anchor="la")
    d.rectangle((0,H-40,W,H), fill=DEEP)
    d.text((W-40, H-20), phone, font=fp, fill=WHITE, anchor="rm")
    d.text((40, H-20), "जहांगीराबाद–अनूपशहर, बुलंदशहर" if lang=="hi" else "Jahangirabad–Anupshahr, Bulandshahr", font=font("MartelSans-Bold.ttf",22), fill=MUSTARD, anchor="lm")
    im.save(out, "JPEG", quality=86, optimize=True, progressive=True)

og("hi","site/images/og-image.jpg"); og("en","site/images/og-image-en.jpg")

# Icons: "सु" on green, ink-centred
def icon(size, rounded=True):
    s=size*4
    im = Image.new("RGBA",(s,s),(0,0,0,0)); d=ImageDraw.Draw(im)
    if rounded: d.rounded_rectangle((0,0,s-1,s-1), radius=int(s*0.22), fill=GREEN)
    else: d.rectangle((0,0,s,s), fill=GREEN)
    f = font("Khand-Bold.ttf", int(s*0.70))
    l,t,r,b = d.textbbox((0,0), "सु", font=f, anchor="lt")
    w,h = r-l, b-t
    d.text(((s-w)/2 - l, (s-h)/2 - t), "सु", font=f, fill=WHITE, anchor="lt")
    return im.resize((size,size), Image.LANCZOS)
icon(32).save("site/images/favicon-32.png")
icon(192).save("site/images/icon-192.png"); icon(512).save("site/images/icon-512.png")
icon(180, rounded=False).convert("RGB").save("site/images/apple-touch-icon.png")
icon(48).save("site/favicon.ico", sizes=[(16,16),(32,32),(48,48)])
print("ok")
