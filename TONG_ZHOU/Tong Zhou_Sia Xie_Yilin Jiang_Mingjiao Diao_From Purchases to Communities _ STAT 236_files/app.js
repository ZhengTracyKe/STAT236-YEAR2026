'use strict';
const palette={count:'#28658e',jaccard:'#c47b24',weighted:'#328269',bipartite_svd:'#9e5362'};
const methods=Object.keys(palette), levels=['low','medium','high'];
let preference='focused';
const NS='http://www.w3.org/2000/svg';
function node(tag,attrs={},text){const n=document.createElementNS(NS,tag);Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,v));if(text!==undefined)n.textContent=text;return n;}
function update(){
 const density=Number(document.querySelector('#density').value);
 const strength=Number(document.querySelector('#strength').value);
 const data=window.RESULTS.filter(r=>r.mean_purchases===density&&r.preference===preference&&r.r===strength);
 const svg=document.querySelector('#recovery');svg.querySelectorAll('g').forEach(e=>e.remove());
 const g=node('g');svg.append(g);
 const xp=i=>85+i*290, yp=v=>350-v/0.7*300;
 for(let n=0;n<=7;n++){const value=n/10,y=yp(value);g.append(node('line',{x1:65,x2:700,y1:y,y2:y,stroke:'#d8ddd8','stroke-width':1}),node('text',{x:52,y:y+4,'text-anchor':'end',fill:'#59656b','font-size':12},`${n*10}%`));}
 const ref=0.63;g.append(node('line',{x1:65,x2:700,y1:yp(ref),y2:yp(ref),stroke:'#6b7378','stroke-width':1.4,'stroke-dasharray':'6 5'}),node('text',{x:698,y:yp(ref)-7,'text-anchor':'end',fill:'#59656b','font-size':12},'Random labels ≈ 63%'));
 levels.forEach((h,i)=>g.append(node('text',{x:xp(i),y:378,'text-anchor':'middle',fill:'#59656b','font-size':13},h[0].toUpperCase()+h.slice(1))));
 g.append(node('text',{x:380,y:406,'text-anchor':'middle',fill:'#59656b','font-size':12},'Activity heterogeneity'));
 for(const method of methods){
  const a=levels.map(h=>data.find(r=>r.method===method&&r.heterogeneity===h));
  g.append(node('path',{d:a.map((r,i)=>`${i?'L':'M'}${xp(i)},${yp(r.mean)}`).join(' '),fill:'none',stroke:palette[method],'stroke-width':2.4}));
  a.forEach((r,i)=>{const x=xp(i),y=yp(r.mean);g.append(node('line',{x1:x,x2:x,y1:yp(r.ci_low),y2:yp(r.ci_high),stroke:palette[method],'stroke-width':1.5}));for(const v of [r.ci_low,r.ci_high])g.append(node('line',{x1:x-5,x2:x+5,y1:yp(v),y2:yp(v),stroke:palette[method]}));const dot=node('circle',{cx:x,cy:y,r:4.8,fill:palette[method]});dot.append(node('title',{},`${method}, ${levels[i]}: ${(r.mean*100).toFixed(2)}%, 95% CI ${(r.ci_low*100).toFixed(2)}–${(r.ci_high*100).toFixed(2)}%`));g.append(dot);});
 }
 document.querySelector('#chart-desc').textContent=`r=${strength}; mean ${density} purchases per user; ${preference==='focused'?'all users have focused preferences':'the most active 20% have no category preference'}. `+levels.map(h=>`${h} heterogeneity: `+methods.map(m=>`${m} ${(data.find(r=>r.method===m&&r.heterogeneity===h).mean*100).toFixed(2)} percent`).join(', ')).join('. ');
 const tbody=document.querySelector('#result-table');tbody.replaceChildren();
 for(const h of levels){const tr=document.createElement('tr');const th=document.createElement('th');th.scope='row';th.textContent=h[0].toUpperCase()+h.slice(1);tr.append(th);for(const m of methods){const r=data.find(r=>r.method===m&&r.heterogeneity===h),td=document.createElement('td');td.textContent=`${(r.mean*100).toFixed(2)}%`;td.title=`95% MC CI: ${(r.ci_low*100).toFixed(2)}–${(r.ci_high*100).toFixed(2)}%`;tr.append(td);}tbody.append(tr);}
 document.querySelector('#preference-note').textContent=`Focused users have preferred-category weight ${strength} versus 1 elsewhere. Active users broad sets that ratio to 1 for the most active 20%. High heterogeneity at mean 12 means 80% buy 2 products and 20% buy 52; at mean 6, the counts are 1 and 26. Preference strength is r=${strength}.`;
 document.querySelector('#chart-caption').textContent=`Bars show 95% Monte Carlo confidence intervals for means over 100 datasets. Total purchases are matched across activity distributions. Results shown for preference strength r=${strength}.`;
 const focused=preference==='focused';
 document.querySelector('#finding-title').textContent=focused?'Active buyers can carry the signal.':'Less influence does not create more signal.';
 if(strength===4){
  document.querySelector('#finding-title').textContent='Results at r=4.';
  document.querySelector('#finding-text').textContent=focused?'With strong preferences, focused conditions are nearly solved by every projection, so the cost of downweighting active users disappears.':(density===12?'At medium heterogeneity, Count stays near the random-label reference while activity weighting and SVD recover most products. High heterogeneity remains difficult because focused users purchase only two products each.':'Weighting helps at medium heterogeneity. At high heterogeneity, focused users purchase only one product each, so no reweighting can create informative pairs.');
 }else if(strength===3){
  document.querySelector('#finding-title').textContent='Results at r=3.';
  document.querySelector('#finding-text').textContent=focused?(density===12?'Stronger preferences make the focused conditions easy for every method, so the cost of downweighting active users nearly disappears.':'Count and Jaccard still benefit most from concentrated activity. Weighting costs about 9 points at medium heterogeneity, and normalized SVD remains weak at high heterogeneity.'):(density===12?'At medium heterogeneity, activity weighting and SVD improve substantially over Count. High heterogeneity remains difficult because focused users purchase only two products each.':'At high heterogeneity, focused users still purchase only one product each. Increasing preference strength does not create any informative product pairs.');
 }else{
  document.querySelector('#finding-text').textContent=focused?(density===12?'Count and Jaccard improve as activity becomes concentrated. Weighting suppresses useful evidence from focused active users.':'Count and Jaccard improve with concentrated activity. Weighted also improves at high heterogeneity, while normalized SVD remains weak.'):(density===12?'Weighting helps modestly at medium heterogeneity. At high heterogeneity, the remaining focused buyers purchase only two products each, and all methods recover poorly.':'At high heterogeneity, every focused buyer purchases only one product and creates no pairs. Broad buyers provide zero expected category contrast.');
 }
 const statMethod=focused?'count':'weighted', statLevel=focused?'high':'medium';
 const val=data.find(r=>r.method===statMethod&&r.heterogeneity===statLevel).mean;
 document.querySelector('#finding-stat').textContent=`${(val*100).toFixed(2)}%`;
 document.querySelector('#finding-stat-label').textContent=focused?'Count error at high heterogeneity':'Weighted error at medium heterogeneity';
}
document.querySelectorAll('[data-pref]').forEach(button=>button.addEventListener('click',()=>{preference=button.dataset.pref;document.querySelectorAll('[data-pref]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));update();}));
document.querySelector('#density').addEventListener('change',update);
document.querySelector('#strength').addEventListener('change',update);
function schematic(){const g=document.querySelector('#schematic');const users=[[50,72],[50,145],[50,218],[50,291]],groups=[[[210,52],[265,65],[230,107]],[[330,155],[378,184],[327,212]],[[207,253],[257,283],[199,305]]],col=['#28658e','#c47b24','#328269'];groups.forEach((points,k)=>{g.append(node('circle',{cx:k===1?350:230,cy:k===0?80:k===1?184:278,r:56,fill:col[k],'fill-opacity':.07}));points.forEach((p,j)=>{const u=users[k];g.append(node('line',{x1:u[0],y1:u[1],x2:p[0],y2:p[1],stroke:col[k],'stroke-opacity':.38}));points.slice(j+1).forEach(q=>g.append(node('line',{x1:p[0],y1:p[1],x2:q[0],y2:q[1],stroke:col[k],'stroke-width':2})));});});groups.flat().forEach(p=>g.append(node('line',{x1:users[3][0],y1:users[3][1],x2:p[0],y2:p[1],stroke:'#939d99','stroke-opacity':.22})));users.forEach(p=>g.append(node('circle',{cx:p[0],cy:p[1],r:7,fill:'#7b8788'})));groups.forEach((ps,k)=>ps.forEach(p=>g.append(node('circle',{cx:p[0],cy:p[1],r:9,fill:col[k],stroke:'#f6f4ee','stroke-width':2}))));}
schematic();update();
