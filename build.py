import base64, os, io
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))

def datauri(name, mime='image/png'):
    with open(os.path.join(ROOT, name), 'rb') as f:
        b = base64.b64encode(f.read()).decode('ascii')
    return 'data:' + mime + ';base64,' + b

def soushiki_datauri():
    # 1920x1080(16:9)を 256x144(同16:9) へ縮小してPNG化（埋め込みサイズ削減・実描画と等倍）
    im = Image.open(os.path.join(ROOT, 'soushiki.jpg')).convert('RGB').resize((256, 144), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, 'PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('ascii')

IMGS = {
    '__BG__':    datauri('haikei2.png'),
    '__SANMA__': datauri('sanma.png'),
    '__YAS__':   datauri('yasushi.png'),
    '__HM__':    datauri('hm.png'),
    '__RAMEN__': datauri('ramen.png'),
    '__GETA__':  datauri('geta.png'),
    '__TOKEI__': datauri('tokei.png'),
    '__TAKO__':  datauri('takoyaki.png'),
    '__BGM__':   datauri('sanma.mp3', 'audio/mpeg'),
    '__RIKISHI__':  datauri('rikishi_goonies2.png'),
    '__SE1__':      datauri('rikishi1.mp3', 'audio/mpeg'),
    '__SE2__':      datauri('rikishi2.mp3', 'audio/mpeg'),
    '__SOUSHIKI__': soushiki_datauri(),
    '__FAVICON__':  datauri('takoyaki.png'),
}

SITE_URL = 'https://hotatecurry.github.io/sanma-boat-race/'

HTML = r'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>ボートレース — さんま VS やすし</title>
<meta name="description" content="A/B交互連打で やすしに勝て！ ファミコン風ボートレース・ミニゲーム。タコ焼きでスピードアップ、力士に当たると…！？">
<link rel="icon" type="image/png" href="__FAVICON__">
<!-- OGP / Twitter Card -->
<meta property="og:type" content="website">
<meta property="og:site_name" content="ボートレース">
<meta property="og:title" content="ボートレース — さんま VS やすし">
<meta property="og:description" content="A/B交互連打で やすしに勝て！ ファミコン風ボートレース・ミニゲーム。タコ焼きでスピードアップ、力士に当たると…！？">
<meta property="og:url" content="__SITE_URL__">
<meta property="og:image" content="__SITE_URL__og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="ボートレース — さんま VS やすし">
<meta name="twitter:description" content="A/B交互連打で やすしに勝て！ ファミコン風ボートレース・ミニゲーム。">
<meta name="twitter:image" content="__SITE_URL__og.png">
<style>
  * { box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
  html,body { margin:0; height:100%; background:#000; }
  body { display:flex; flex-direction:column; align-items:center; justify-content:center;
    font-family:"MS Gothic","Hiragino Kaku Gothic ProN",monospace;
    gap:10px; padding:8px; touch-action:none; user-select:none; }
  #screen { width:min(88vw,420px); height:auto; aspect-ratio:256/240;
    image-rendering:pixelated; image-rendering:crisp-edges; border:4px solid #444; background:#000; }
  #pad { display:flex; width:100%; max-width:420px; justify-content:space-between; align-items:center; }
  .group { display:flex; gap:16px; }
  .dpad { display:flex; flex-direction:column; gap:12px; }
  .btn { width:74px; height:74px; border-radius:14px; background:#c0392b; border:4px solid #7a1d13;
    color:#fff; font-size:26px; font-weight:bold; font-family:monospace;
    display:flex; align-items:center; justify-content:center; touch-action:none; user-select:none; }
  .btn.dir { background:#2c3e50; border-color:#16222e; border-radius:50%; }
  .btn:active { filter:brightness(1.3); transform:translateY(2px); }
  #hint { color:#888; font-size:11px; text-align:center; }
</style>
</head>
<body>
<canvas id="screen" width="256" height="240"></canvas>
<div id="pad">
  <div class="dpad"><div class="btn dir" id="bUp">▲</div><div class="btn dir" id="bDown">▼</div></div>
  <div class="group"><div class="btn" id="bB">B</div><div class="btn" id="bA">A</div></div>
</div>
<div id="hint">▲▼ で レーンいどう、A/B こうごに れんだ！（PC: レーン=↑↓ / こぐ=Z(B)・X(A)）</div>

<script>
const cv=document.getElementById('screen'), ctx=cv.getContext('2d');
ctx.imageSmoothingEnabled=false;

// ==== 画像（base64埋め込み・外部依存なし）====
function mkImg(src){ const i=new Image(); i.src=src; return i; }
const bgImg=mkImg('__BG__');
const sanmaImg=mkImg('__SANMA__');       // 自キャラ（さんま）
const yasushiImg=mkImg('__YAS__');       // 敵（やすし）
const hmImg=mkImg('__HM__');             // お邪魔：木槌
const ramenImg=mkImg('__RAMEN__');       // お邪魔：丼
const getaImg=mkImg('__GETA__');         // お邪魔：下駄
const tokeiImg=mkImg('__TOKEI__');       // 時計：取ると敵が止まる
const takoyakiImg=mkImg('__TAKO__');     // たこ焼き：スピードアップ
const OBS_IMGS=[hmImg,ramenImg,getaImg];

// ==== BGM（レース中だけループ再生・base64埋め込み）====
const bgm=new Audio('__BGM__');
bgm.loop=true; bgm.volume=0.5;
let bgmWanted=false;                                  // レース中で鳴らしたい状態か
function bgmPlay(){ bgmWanted=true; const p=bgm.play(); if(p&&p.catch) p.catch(()=>{}); }
function bgmStop(){ bgmWanted=false; bgm.pause(); try{ bgm.currentTime=0; }catch(e){} }
// 初回はブラウザの自動再生制限で鳴らない場合があるので、最初の操作で解除して鳴らす
function bgmUnlock(){ if(bgmWanted){ const p=bgm.play(); if(p&&p.catch) p.catch(()=>{}); } }
window.addEventListener('pointerdown', bgmUnlock);
window.addEventListener('keydown', bgmUnlock);

// ==== 力士（極稀・当たるとゲームオーバー）関連アセット ====
const rikishiImg=mkImg('__RIKISHI__');    // お邪魔：力士
const soushikiImg=mkImg('__SOUSHIKI__');  // ゲームオーバー画像
const se1=new Audio('__SE1__');           // 力士に当たった時のSE
const se2=new Audio('__SE2__');           // ゲームオーバー画面のSE
function playSe(a){ try{ a.currentTime=0; }catch(e){} const p=a.play(); if(p&&p.catch) p.catch(()=>{}); }
// 力士に接触 → 全停止＋爆発＋BGM停止＋SE1
function triggerRikishi(cx,cy){ state='rikishi'; tState=0; exX=cx; exY=cy; bgmStop(); playSe(se1); }
// SE1が鳴り終わったら → 葬式画面へ切替＋SE2
function enterGameover(){ if(state==='gameover') return; state='gameover'; tState=0; playSe(se2); }
se1.addEventListener('ended', enterGameover);

const W=256,H=240;
const RACE_LEN=300, FULL=1.5, WEAK=0.35;
const AI_SPEED_MAX=17, AI_SPEED_MIN=11, AI_SPEED_INT=3; // 敵の速さ: 約3秒ごとに最遅〜最速でランダム変化
const AI_SPEED_MID=(AI_SPEED_MAX+AI_SPEED_MIN)/2;
const AI_SPEED_BIAS=2; // 大きいほど最速が出にくく遅め寄り（1=一様, 2=二乗で遅め寄り）
const PACE=2/3;        // レース進行の全体スピード倍率（自機と敵に等倍で効く。小さいほど長時間プレイ・勝敗バランスは不変）
const rightStart=200, leftEnd=12;
const BOOST_MULT=1.6, BOOST_TIME=2.6;
const OBS_SPEED=88, STUN_TIME=1.6, HAZARD_PR=0.33;
const FREEZE_TIME=2.4;                    // 時計で敵が止まる秒数
const CLOCK_CHANCE=0.09;                  // お邪魔スポーン時に時計になる確率（稀）
const RIKISHI_CHANCE=CLOCK_CHANCE/2;      // 力士の出現率（時計のさらに半分＝極稀）
const RIKISHI_SCALE=1.7;                  // 力士の表示倍率（お邪魔より少し大きめ）
const ITEM_PR=0.12;                       // たこ焼きが出始める進行率（早め）
const ITEM_LIFE=4.0;                      // たこ焼きが消えるまでの秒数

// レーン A,B,C,D（各スプライトの上端Y）。A=やすし固定、自機は初期C
const LANES=[72,104,136,168];
const YAS_LANE=0;
function laneWaterY(i){ return LANES[i]+13; }   // 各レーンの水面中心Y（お邪魔・アイテムの中心）

let state='countdown', tState=0, blink=0, lastTs=0;
let playerDist=0, aiDist=0, lastKey=null, result=null;
let aiSpeed=AI_SPEED_MAX, aiSpeedTimer=0;
let laneIdx=2, playerY=LANES[2], pOar=0, aOar=0;
let boostTimer=0, stunTimer=0, freezeTimer=0;
let exX=0, exY=0;                          // 爆発エフェクトの中心
let items=[], itemTimer=0;                 // たこ焼き（前方に出現→漕いで取る）
let obstacles=[], spawnTimer=0;            // お邪魔＆時計（左→右にレーン直進）

const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const lerp=(a,b,t)=>a+(b-a)*t;

function reset(){
  playerDist=0; aiDist=0; lastKey=null; result=null;
  laneIdx=2; playerY=LANES[2]; pOar=0; aOar=0;
  boostTimer=0; stunTimer=0; freezeTimer=0;
  items=[]; itemTimer=0;
  obstacles=[]; spawnTimer=0;
  rollAiSpeed();
}
// 敵の速さを最遅〜最速の間で抽選し直す
function rollAiSpeed(){ aiSpeed=AI_SPEED_MIN+Math.pow(Math.random(),AI_SPEED_BIAS)*(AI_SPEED_MAX-AI_SPEED_MIN); aiSpeedTimer=AI_SPEED_INT; }
reset();

function press(side){
  if(state==='gameover'){ if(se2.ended||tState>5){ reset(); state='countdown'; tState=0; } return; }
  if(state==='rikishi') return;   // 爆発〜SE1中は操作不可
  if(state==='result'){ if(tState>1.2){ reset(); state='countdown'; tState=0; } return; }
  if(state==='race' && stunTimer<=0){
    let gain=(side!==lastKey)?FULL:WEAK;
    if(boostTimer>0) gain*=BOOST_MULT;
    playerDist+=gain*PACE; lastKey=side; pOar=1;
    if(playerDist>=RACE_LEN && result===null){ playerDist=RACE_LEN; result='win'; state='result'; tState=0; bgmStop(); }
  }
}

// レーン移動（1回押すごとに1レーン）
function moveLane(d){ if(state==='race' && stunTimer<=0){ laneIdx=clamp(laneIdx+d,0,LANES.length-1); } }

function boatX(d){ return rightStart-(d/RACE_LEN)*(rightStart-leftEnd); }
function overlap(a,b){ return a.x<b.x+b.w && a.x+a.w>b.x && a.y<b.y+b.h && a.y+a.h>b.y; }

// お邪魔／時計を1体、ランダムなレーンに生成（左端から右へ直進）
function spawnHazard(){
  const lane=Math.floor(Math.random()*LANES.length);
  const y=laneWaterY(lane);
  const r=Math.random();
  const hasClock=obstacles.some(o=>o.type==='clock');
  const hasRikishi=obstacles.some(o=>o.type==='rikishi');
  if(!hasRikishi && r<RIKISHI_CHANCE){
    obstacles.push({type:'rikishi', x:-20, y, img:rikishiImg});
  } else if(!hasClock && r<RIKISHI_CHANCE+CLOCK_CHANCE){
    obstacles.push({type:'clock', x:-16, y, img:tokeiImg});
  } else {
    obstacles.push({type:'obs', x:-16, y, img:OBS_IMGS[Math.floor(Math.random()*OBS_IMGS.length)]});
  }
}

function update(dt){
  tState+=dt; blink+=dt;
  if(state==='countdown'){ if(tState>3.4){ state='race'; tState=0; bgmPlay(); } return; }
  if(state==='rikishi'){ if(se1.ended || tState>6) enterGameover(); return; } // SE1終了で葬式画面へ
  if(state!=='race') return;   // result / gameover は動かさない

  // 敵（時計で止まっている間は進まない）。速さは約3秒ごとにランダム更新
  if(freezeTimer>0){ freezeTimer=Math.max(0,freezeTimer-dt); }
  else {
    aiSpeedTimer-=dt; if(aiSpeedTimer<=0) rollAiSpeed();
    aiDist+=aiSpeed*PACE*dt; aOar=(Math.sin(tState*18)>0)?1:0;
    if(aiDist>=RACE_LEN && result===null){ aiDist=RACE_LEN; result='lose'; state='result'; tState=0; bgmStop(); }
  }

  if(boostTimer>0) boostTimer=Math.max(0,boostTimer-dt);
  if(stunTimer>0) stunTimer=Math.max(0,stunTimer-dt);
  if(pOar>0) pOar=Math.max(0,pOar-dt*6);

  // レーンへスナップ（なめらかに素早く寄せる）
  playerY=lerp(playerY, LANES[laneIdx], Math.min(1,dt*16));

  const pr=playerDist/RACE_LEN;
  const px=boatX(playerDist), ax=boatX(aiDist);
  const pbox={x:px+4,y:playerY+7,w:28,h:16};

  // 敵（やすし・レーンA）と衝突 → レーンBへ戻され、お邪魔と同じく一定時間硬直
  if(stunTimer<=0){
    const yb={x:ax+4,y:LANES[YAS_LANE]+7,w:28,h:16};
    if(overlap(pbox,yb)){ stunTimer=STUN_TIME; laneIdx=1; }
  }

  // たこ焼き（スピードアップ・自機の少し前方に短時間だけ出現）
  if(pr>ITEM_PR){
    itemTimer-=dt;
    if(itemTimer<=0 && items.length<2){
      const lane=Math.floor(Math.random()*LANES.length);
      const ix=clamp(px-(22+Math.random()*20), leftEnd+16, px-16);
      items.push({x:ix, y:laneWaterY(lane), t:ITEM_LIFE});
      itemTimer=lerp(2.6,1.8, clamp((pr-ITEM_PR)/0.6,0,1));
    }
  }
  for(const it of items){
    it.t-=dt;
    const ibox={x:it.x-8,y:it.y-8,w:16,h:16};
    if(overlap(pbox,ibox)){ it.hit=true; boostTimer=BOOST_TIME; }
  }
  items=items.filter(it=>!it.hit && it.t>0 && px>it.x-24);

  // お邪魔＆時計（左→右へレーン直進）
  if(pr>HAZARD_PR){
    spawnTimer-=dt;
    const maxOnScreen=2+Math.floor(clamp((pr-HAZARD_PR)/0.6,0,1)*2); // 2→4体
    if(spawnTimer<=0 && obstacles.length<maxOnScreen){
      spawnHazard();
      spawnTimer=lerp(1.9,0.85,clamp((pr-HAZARD_PR)/0.6,0,1));
    }
  }
  const spd=OBS_SPEED*(1+pr*0.25);
  for(const o of obstacles){
    o.x+=spd*dt;
    const hw=(o.type==='rikishi')?11:8;
    const box={x:o.x-hw,y:o.y-hw,w:hw*2,h:hw*2};
    if(o.type==='clock'){
      if(overlap(pbox,box)){ o.hit=true; freezeTimer=FREEZE_TIME; }
    } else if(o.type==='rikishi'){
      if(overlap(pbox,box)){ o.hit=true; triggerRikishi(px+24, playerY+12); return; }
    } else {
      if(stunTimer<=0 && overlap(pbox,box)) stunTimer=STUN_TIME;
    }
  }
  obstacles=obstacles.filter(o=>!o.hit && o.x<=W+20);
}

function txt(s,x,y,size,color,align){
  ctx.fillStyle=color; ctx.textAlign=align||'left'; ctx.textBaseline='top';
  ctx.font='bold '+size+'px "MS Gothic",monospace';
  ctx.fillText(s,Math.round(x),Math.round(y));
}

function drawBg(){
  if(bgImg.complete && bgImg.naturalWidth) ctx.drawImage(bgImg,0,0,W,H);
  else { ctx.fillStyle='#60a0ff'; ctx.fillRect(0,0,W,H); }
}

// 中心指定で拡大描画（ニアレストネイバー）
function drawImgC(img,cx,cy,scale){
  if(!(img.complete&&img.naturalWidth)) return;
  const w=Math.round(img.width*scale), h=Math.round(img.height*scale);
  ctx.drawImage(img, Math.round(cx-w/2), Math.round(cy-h/2), w, h);
}

// 艇スプライト（浮遊バウンド／ブースト水しぶき／硬直シェイク）
function drawSprite(img,x,y,o){
  x=Math.round(x); y=Math.round(y);
  if(!o.frozen) y+=Math.round(Math.sin(tState*6+(o.phase||0))*1);
  if(o.spin) x+=Math.round(Math.sin(tState*30)*2);
  if(o.boost){ ctx.fillStyle='#fff';
    for(let i=0;i<3;i++){ ctx.fillRect(x+44+Math.random()*8, y+8+i*4, 6,1); } }
  if(img.complete && img.naturalWidth) ctx.drawImage(img,x,y);
  else { ctx.fillStyle=o.fb||'#d94f2a'; ctx.fillRect(x+2,y+8,30,10); }
  if(o.spin) txt('！',x+14,y-10,14,'#ff5a5a','center');
}

function drawHazard(o){
  if(o.type==='clock'){
    if(blink%0.34<0.17){ ctx.strokeStyle='#fff700'; ctx.lineWidth=1;
      ctx.strokeRect(Math.round(o.x-12),Math.round(o.y-12),24,24); }
    drawImgC(o.img,o.x,o.y,1.7);
  } else if(o.type==='rikishi'){
    if(blink%0.3<0.15){ ctx.strokeStyle='#ff3b00'; ctx.lineWidth=1;
      ctx.strokeRect(Math.round(o.x-15),Math.round(o.y-19),30,38); }
    drawImgC(o.img,o.x,o.y,RIKISHI_SCALE);
  } else {
    drawImgC(o.img,o.x,o.y,1.6);
  }
}

// 爆発エフェクト（tは発生からの経過秒）
function drawExplosion(cx,cy,t){
  if(t<0.14){ ctx.fillStyle='rgba(255,255,255,'+((1-t/0.14)*0.85).toFixed(3)+')'; ctx.fillRect(0,0,W,H); }
  const cols=['#ff3b00','#ff8a2a','#ffe37a','#fff'];
  const r=Math.min(72, 34+t*70);
  for(let i=0;i<cols.length;i++){
    const rr=r*(1-i*0.22); if(rr<=0) continue;
    ctx.fillStyle=cols[i]; ctx.beginPath(); ctx.arc(cx,cy,rr,0,Math.PI*2); ctx.fill();
  }
  ctx.fillStyle='#fff';
  for(let i=0;i<12;i++){ const a=i/12*Math.PI*2+t*4, d=r*1.15;
    ctx.fillRect(Math.round(cx+Math.cos(a)*d)-1, Math.round(cy+Math.sin(a)*d)-1, 3,3); }
}

// ゲームオーバー画面（葬式画像を全画面・上下は黒帯＝画像の黒背景と一体化）
function drawGameover(){
  ctx.fillStyle='#000'; ctx.fillRect(0,0,W,H);
  if(soushikiImg.complete && soushikiImg.naturalWidth) ctx.drawImage(soushikiImg,0,48,256,144);
  else txt('GAME OVER',128,110,20,'#fff','center');
  if((se2.ended||tState>5) && blink%1<0.5) txt('A/B か Z/X で さいしょから',128,214,11,'#fff','center');
}

function draw(){
  if(state==='gameover'){ drawGameover(); return; }
  drawBg();
  const px=boatX(playerDist), ax=boatX(aiDist);
  for(const o of obstacles) drawHazard(o);
  for(const it of items) drawImgC(takoyakiImg, it.x, it.y, 1.6);
  // やすし（上レーンA）→ 自キャラ（手前）の順で重ねる
  drawSprite(yasushiImg, ax, LANES[YAS_LANE], {phase:0, fb:'#2ecc71', frozen:freezeTimer>0, boost:(freezeTimer<=0 && aiSpeed>AI_SPEED_MID)});
  if(freezeTimer>0 && blink%0.5<0.3) txt('Zzz',ax+26,LANES[YAS_LANE]-12,12,'#fff','center');
  drawSprite(sanmaImg, px, playerY, {boost:boostTimer>0, spin:stunTimer>0, phase:1.7, fb:'#d94f2a'});

  // 上部HUD（観客席の上に半透明帯）
  ctx.fillStyle='rgba(0,0,0,0.42)'; ctx.fillRect(0,0,W,28);
  txt('ボートレース',128,3,12,'#fff','center');
  ctx.fillStyle='#000'; ctx.fillRect(68,18,120,6);
  ctx.fillStyle='#ffd23f'; ctx.fillRect(68,18,120*(playerDist/RACE_LEN),6);
  ctx.fillStyle='#8affb0'; ctx.fillRect(68+120*(aiDist/RACE_LEN)-1,18,2,6);

  const b=(blink%1<0.5);
  if(state==='countdown'){
    let s=tState<1?'3':tState<2?'2':tState<3?'1':'スタート！';
    txt(s,128,92,tState<3?30:20,'#fff','center');
  } else if(state==='race'){
    if(stunTimer>0 && b) txt('うごけない！',128,222,12,'#ff8a8a','center');
    else if(freezeTimer>0 && b) txt('やすし ストップ！',128,222,12,'#8fe0ff','center');
    else if(boostTimer>0) txt('スピードアップ！',128,222,12,'#fff700','center');
    else if(b) txt('こうごに れんだ！',128,222,11,'#ffd23f','center');
  } else if(state==='result'){
    ctx.fillStyle='rgba(0,0,0,.75)'; ctx.fillRect(28,92,200,64);
    if(result==='win') txt('かった！！',128,100,22,'#ffd23f','center');
    else txt('まけた…',128,100,22,'#7fd0ff','center');
    if(tState>1.2 && b) txt('もういちど？ A/B か Z/X',128,132,11,'#fff','center');
  } else if(state==='rikishi'){
    drawExplosion(exX,exY,tState);
  }
}

function loop(ts){ if(!lastTs)lastTs=ts; let dt=Math.min(0.05,(ts-lastTs)/1000); lastTs=ts; update(dt); draw(); requestAnimationFrame(loop); }
requestAnimationFrame(loop);

// ==== 入力 ====
document.getElementById('bUp').addEventListener('pointerdown',e=>{e.preventDefault();moveLane(-1);});
document.getElementById('bDown').addEventListener('pointerdown',e=>{e.preventDefault();moveLane(1);});
document.getElementById('bA').addEventListener('pointerdown',e=>{e.preventDefault();press('A');});
document.getElementById('bB').addEventListener('pointerdown',e=>{e.preventDefault();press('B');});
window.addEventListener('keydown',e=>{
  const k=e.key.toLowerCase();
  if(k==='arrowup'||k==='w'){ e.preventDefault(); if(!e.repeat) moveLane(-1); return; }
  if(k==='arrowdown'||k==='s'){ e.preventDefault(); if(!e.repeat) moveLane(1); return; }
  if(e.repeat) return;
  if(k==='x'){ e.preventDefault(); press('A'); }        // Xキー = Aボタン
  else if(k==='z'){ e.preventDefault(); press('B'); }   // Zキー = Bボタン
});
</script>
</body>
</html>
'''

for k,v in IMGS.items():
    HTML = HTML.replace(k, v)
HTML = HTML.replace('__SITE_URL__', SITE_URL)

# index.html = 公開用（GitHub Pages ルート）。boat-race.html も同内容で残す（開発時の互換）
for name in ('index.html', 'boat-race.html'):
    with open(os.path.join(ROOT, name), 'w', encoding='utf-8') as f:
        f.write(HTML)

print('written', len(HTML), 'bytes -> index.html, boat-race.html')
