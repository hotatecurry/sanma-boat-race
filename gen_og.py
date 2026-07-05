from PIL import Image, ImageDraw, ImageFont
import os
ROOT = os.path.dirname(os.path.abspath(__file__))
def P(n): return os.path.join(ROOT, n)

# ---- ゲーム画面(256x240)を合成 ----
bg=Image.open(P('haikei2.png')).convert('RGBA')
sanma=Image.open(P('sanma.png')).convert('RGBA'); yas=Image.open(P('yasushi.png')).convert('RGBA')
tako=Image.open(P('takoyaki.png')).convert('RGBA'); ramen=Image.open(P('ramen.png')).convert('RGBA')
rik=Image.open(P('rikishi_goonies2.png')).convert('RGBA'); tokei=Image.open(P('tokei.png')).convert('RGBA')
LANES=[72,104,136,168]
def wy(i): return LANES[i]+13
def sc(im,s): return im.resize((round(im.width*s),round(im.height*s)),Image.NEAREST)
def pc(base,im,cx,cy,s):
    im=sc(im,s); base.alpha_composite(im,(round(cx-im.width/2),round(cy-im.height/2)))
RACE_LEN=300; rs=200; le=12
def bx(d): return round(rs-(d/RACE_LEN)*(rs-le))
scene=bg.copy()
pc(scene,rik,   62, wy(3),1.7)   # 力士 レーンD（チラ見せ）
pc(scene,ramen,150, wy(1),1.6)   # 丼 レーンB
pc(scene,tako,  88, wy(2),1.6)   # たこ焼き レーンC（自機の前方）
pc(scene,tokei,175, wy(2),1.7)   # 時計
px=bx(130); ax=bx(165)
scene.alpha_composite(yas,(ax,LANES[0]))   # やすし先行
scene.alpha_composite(sanma,(px,LANES[2])) # さんま
# HUDバー風（少し雰囲気）
d0=ImageDraw.Draw(scene)
d0.rectangle([0,0,256,28],fill=(0,0,0,110))
d0.rectangle([68,18,188,24],fill=(0,0,0,255)); d0.rectangle([68,18,68+120*0.43,24],fill=(255,210,63,255))

# ---- 1200x630 カード ----
W,H=1200,630
card=Image.new('RGB',(W,H),(11,26,44))
# 上下に水色アクセント帯
ImageDraw.Draw(card).rectangle([0,0,W,8],fill=(46,124,200))
ImageDraw.Draw(card).rectangle([0,H-8,W,H],fill=(46,124,200))

# ゲーム画面を左に配置（境界枠つき）
SCALE=1.98
sc_img=scene.resize((round(256*SCALE),round(240*SCALE)),Image.NEAREST).convert('RGB')
gx,gy=52,(H-sc_img.height)//2
card.paste(Image.new('RGB',(sc_img.width+12,sc_img.height+12),(68,68,68)),(gx-6,gy-6))
card.paste(sc_img,(gx,gy))

draw=ImageDraw.Draw(card)
def font(sz,bold=True):
    for f in (['C:/Windows/Fonts/meiryob.ttc','C:/Windows/Fonts/YuGothB.ttc','C:/Windows/Fonts/msgothic.ttc'] if bold
              else ['C:/Windows/Fonts/meiryo.ttc','C:/Windows/Fonts/YuGothR.ttc','C:/Windows/Fonts/msgothic.ttc']):
        try: return ImageFont.truetype(f,sz)
        except Exception: pass
    return ImageFont.load_default()
def text_sh(x,y,s,fnt,fill,sh=(0,0,0),d=3,anchor='la'):
    draw.text((x+d,y+d),s,font=fnt,fill=sh,anchor=anchor)
    draw.text((x,y),s,font=fnt,fill=fill,anchor=anchor)

tx=gx+sc_img.width+46   # テキスト左端
text_sh(tx,96,'ボートレース',font(80),(255,255,255))
text_sh(tx,196,'さんま VS やすし',font(52),(255,210,63))
draw.rectangle([tx,276,tx+430,280],fill=(46,124,200))
text_sh(tx,300,'A/B 交互連打で 勝て！',font(38),(230,238,245))
text_sh(tx,352,'タコ焼きでスピードUP・力士に注意',font(27,False),(150,170,190),d=2)
# CTA
draw.rounded_rectangle([tx,420,tx+340,486],14,fill=(201,57,43))
text_sh(tx+170,432,'▶ ブラウザで今すぐプレイ',font(26),(255,255,255),d=2,anchor='ma')

card.save(P('og.png'),'PNG')
# プレビュー(縮小)も出す
print('og.png', card.size, os.path.getsize(P('og.png')),'B')
