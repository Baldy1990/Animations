from PIL import Image, ImageDraw, ImageFont, ImageOps
from pathlib import Path
import math, io, zipfile, json, hashlib

OUT=Path(__file__).resolve().parent
ROOT=OUT/'Helldivers'/ 'Anims'
ROOT.mkdir(parents=True,exist_ok=True)
FONT=SMALL=None
# Integer-grid 5x7 lettering keeps every stroke intact on the monochrome LCD.
GLYPHS={
 'A':['01110','10001','10001','11111','10001','10001','10001'],
 'B':['11110','10001','10001','11110','10001','10001','11110'],
 'C':['01111','10000','10000','10000','10000','10000','01111'],
 'D':['11110','10001','10001','10001','10001','10001','11110'],
 'E':['11111','10000','10000','11110','10000','10000','11111'],
 'F':['11111','10000','10000','11110','10000','10000','10000'],
 'G':['01111','10000','10000','10111','10001','10001','01111'],
 'H':['10001','10001','10001','11111','10001','10001','10001'],
 'I':['11111','00100','00100','00100','00100','00100','11111'],
 'K':['10001','10010','10100','11000','10100','10010','10001'],
 'L':['10000','10000','10000','10000','10000','10000','11111'],
 'M':['10001','11011','10101','10101','10001','10001','10001'],
 'N':['10001','11001','10101','10011','10001','10001','10001'],
 'O':['01110','10001','10001','10001','10001','10001','01110'],
 'P':['11110','10001','10001','11110','10000','10000','10000'],
 'R':['11110','10001','10001','11110','10100','10010','10001'],
 'S':['01111','10000','10000','01110','00001','00001','11110'],
 'T':['11111','00100','00100','00100','00100','00100','00100'],
 'U':['10001','10001','10001','10001','10001','10001','01110'],
 'V':['10001','10001','10001','10001','10001','01010','00100'],
 'Y':['10001','10001','01010','00100','00100','00100','00100'],
 '/':['00001','00001','00010','00100','01000','10000','10000'],
 '.':['00000','00000','00000','00000','00000','00100','00100'],
 ' ':['00000']*7,
}

def text(d,y,s,font=FONT):
    w=len(s)*6-1
    assert w<=128 and y+7<=64
    x=(128-w)//2
    for ch in s:
        for row,bits in enumerate(GLYPHS[ch]):
            for col,bit in enumerate(bits):
                if bit=='1':d.point((x+col,y+row),fill=0)
        x+=6

def canvas(title):
    im=Image.new('1',(128,64),1);d=ImageDraw.Draw(im)
    d.line((0,23,127,23),fill=0);text(d,12,title)
    return im,d

def globe(i):
    im,d=canvas('SUPER EARTH')
    cx,cy,r=64,40,15
    d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=0)
    for lat in [-.55,0,.55]:
        yy=cy+int(lat*r); ww=int(r*math.sqrt(1-lat*lat))
        d.line((cx-ww,yy,cx+ww,yy),fill=0)
    for k in range(4):
        angle=i*math.pi/8+k*math.pi/4
        w=max(1,int(abs(math.cos(angle))*r))
        d.ellipse((cx-w,cy-r,cx+w,cy+r),outline=0)
    for side in [-1,1]:
        for y in range(29,52,6):
            x=cx+side*(r+7)
            d.line((x,y,x+side*5,y-3),fill=0,width=2)
    text(d,55,'MANAGED DEMOCRACY',SMALL)
    return im

def pod(i):
    im,d=canvas('HELLDIVERS // DROP')
    for x,y in [(8,18),(24,35),(108,24),(117,39),(39,20)]:
        d.point((x,(y+i*2)%29+25),fill=0)
    d.line((0,54,127,54),fill=0)
    if i<10:
        y=-8+i*5
        d.polygon([(58,y),(70,y),(74,y+15),(64,y+22),(54,y+15)],outline=0,fill=1)
        d.line((58,y+4,70,y+4),fill=0);d.line((64,y+5,64,y+17),fill=0)
        for x in [55,64,73]:d.line((x,y-8,x,y-2),fill=0)
    else:
        d.polygon([(58,33),(70,33),(74,47),(64,54),(54,47)],outline=0,fill=1)
        n=i-9
        d.line((64-n*7,53,64+n*7,53),fill=0,width=2)
        for side in [-1,1]:
            d.line((64+side*(8+n*3),50,64+side*(12+n*4),47-n),fill=0)
    d.rectangle((0,0,127,23),fill=1)
    text(d,12,'HELLDIVERS // DROP');d.line((0,23,127,23),fill=0)
    text(d,55,'FOR LIBERTY',SMALL)
    return im

def arrow(d,x,y,direction,fill):
    pts=[(-3,-6),(3,-6),(3,0),(6,0),(0,6),(-6,0),(-3,0)]
    angle={'D':0,'U':math.pi,'L':math.pi/2,'R':-math.pi/2}[direction]
    pp=[(round(x+a*math.cos(angle)-b*math.sin(angle)),round(y+a*math.sin(angle)+b*math.cos(angle))) for a,b in pts]
    d.polygon(pp,outline=0,fill=fill)

def strat(i):
    im,d=canvas('STRATAGEM UPLINK')
    code='URDDD';active=min(5,i//2+1)
    for k,a in enumerate(code):
        x=20+k*22
        if k<active:d.rectangle((x-9,25,x+9,44),fill=0)
        arrow(d,x,34,a,1 if k<active else 0)
    d.rectangle((10,48,117,51),outline=0)
    d.rectangle((11,49,11+int(105*min(1,i/10)),50),fill=0)
    text(d,55,'UPLINK READY' if i>=10 else 'TRANSMITTING...',SMALL)
    return im

def lower_for_clock(im):
    # Two extra pixels clear the clock border; retain every rendered pixel.
    assert all(im.getpixel((x,y)) for y in (62,63) for x in range(128))
    shifted=Image.new('1',(128,64),1)
    shifted.paste(im.crop((0,0,128,62)),(0,2))
    return shifted

manifest='Filetype: Flipper Animation Manifest\nVersion: 1\n'
previews=[];proof={}
for name,fn in [('SuperEarth',globe),('HellpodDrop',pod),('Stratagem',strat)]:
    folder=ROOT/name;folder.mkdir(exist_ok=True)
    frames=[ImageOps.invert(lower_for_clock(fn(i)).convert('L')).convert('1') for i in range(16)]
    for i,im in enumerate(frames):
        # Flipper uncompressed bitmap: marker 0, row-major pixels, LSB first.
        raw=bytearray(1024)
        for y in range(64):
            for x in range(128):
                if not im.getpixel((x,y)):raw[y*16+x//8]|=1<<(x%8)
        data=b'\x00'+bytes(raw)
        (folder/f'frame_{i}.bm').write_bytes(data)
        # Decode native bytes and ensure exact agreement with every source pixel.
        for y in range(64):
            for x in range(128):assert bool(raw[y*16+x//8]&(1<<(x%8)))==(not bool(im.getpixel((x,y))))
    meta=('Filetype: Flipper Animation\nVersion: 1\nWidth: 128\nHeight: 64\n'
          'Passive frames: 16\nActive frames: 0\nFrames order: '+' '.join(map(str,range(16)))+
          '\nActive cycles: 0\nFrame rate: 6\nDuration: 8\nActive cooldown: 0\nBubble slots: 0\n')
    (folder/'meta.txt').write_text(meta,encoding='ascii')
    manifest+=f'\nName: {name}\nMin butthurt: 0\nMax butthurt: 14\nMin level: 1\nMax level: 30\nWeight: 1\n'
    frames[4].resize((512,256),Image.Resampling.NEAREST).convert('RGB').save(OUT/f'{name}_preview.png')
    previews.append(frames)
(ROOT/'manifest.txt').write_text(manifest,encoding='ascii')
combined=[]
for i in range(16):
    row=Image.new('RGB',(128*3+8*2,64),(255,255,255))
    for j,frames in enumerate(previews):row.paste(frames[i].convert('RGB'),(j*136,0))
    combined.append(row.resize((1200,192),Image.Resampling.NEAREST))
combined[0].save(OUT/'Helldivers_preview.gif',save_all=True,append_images=combined[1:],duration=167,loop=0)
with zipfile.ZipFile(OUT/'Helldivers_asset_pack.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted((OUT/'Helldivers').rglob('*')):
        if f.is_file():z.write(f,f.relative_to(OUT))
for f in sorted((OUT/'Helldivers').rglob('*')):
    if f.is_file():proof[f.relative_to(OUT/'Helldivers').as_posix()]=hashlib.md5(f.read_bytes()).hexdigest()
(OUT/'Helldivers_checksums.json').write_text(json.dumps(proof,indent=2))
(OUT/'Helldivers_README.txt').write_text('Helldivers-inspired fan animation pack for Momentum firmware.\nThree original 128x64 monochrome loops, 16 frames each, 6 fps.\nCopy Helldivers into SD Card/asset_packs, then select it in Momentum > Interface > Graphics.\nUnofficial fan artwork; no game assets or code included.\n',encoding='ascii')
print(f'Created {len(proof)} native files; all 48 bitmap frames decoded and verified.')
