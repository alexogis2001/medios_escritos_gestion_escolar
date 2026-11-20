let R=DS.calixta,ds="calixta",HM=true;
const F={s:{n:"Supervisor",i:0},a:{n:"Agente",i:1},c:{n:"Canal",i:2},e:{n:"Estatus",i:3},d:{n:"Día",i:4},r:{n:"Área",i:5}};
const P=[{id:"p1",t:"Sin tipificación",sub:"Resultado vacío",sa:"Tipificación: Sistema o No tipificado",h:"Conteo de Resultado",ha:"Conteo de Tipificación",k:6},
{id:"p2",t:"Sin matrícula",sub:"ID Externo vacío",sa:"Matrícula vacía",h:"Conteo de ID Externo",ha:"Conteo de matrícula",k:7},
{id:"p3",t:"Sin etiquetas",sub:"Etiquetas vacías",h:"Conteo de Etiquetas",k:8}];
const ex={s:new Set(),a:new Set(),c:new Set(),e:new Set(),d:new Set(),r:new Set()};
const closed=new Set();let sortMode="alpha",allOpen=true;
const cmp=(a,b)=>String(a).localeCompare(String(b),"es",{numeric:true});
const opts=k=>{let rows=R;if(k==="a")rows=R.filter(r=>!ex.s.has(r[0]));return [...new Set(rows.map(r=>r[F[k].i]))].sort(cmp)};
const esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const openSet=new Set();
function bar(){
  const el=document.getElementById("bar");
  let h="";
  for(const k of Object.keys(F)){
    const o=opts(k),n=o.filter(x=>!ex[k].has(x)).length,on=n<o.length;
    h+=`<details class="f${on?" on":""}" data-k="${k}"${openSet.has(k)?" open":""}><summary>${F[k].n}: ${n===o.length?"todos":n+" de "+o.length}</summary><div class="pop"><div class="ctl"><button data-all="${k}">Todos</button><button data-none="${k}">Ninguno</button></div>${o.map(x=>`<label><input type="checkbox" data-k="${k}" value="${esc(x)}"${ex[k].has(x)?"":" checked"}>${esc(x)}</label>`).join("")}</div></details>`;
  }
  h+=`<span class="sp"></span><button class="btn o" id="srt">Orden: ${sortMode==="alpha"?"A–Z":"mayor a menor"}</button><button class="btn o" id="tg">${allOpen?"Contraer":"Expandir"} todo</button><button class="btn o" id="rs">Restablecer</button>`;
  el.innerHTML=h;
}
function rows(){return R.filter(r=>!ex.s.has(r[0])&&!ex.a.has(r[1])&&!ex.c.has(r[2])&&!ex.e.has(r[3])&&!ex.d.has(String(r[4]))&&!ex.r.has(r[5]))}
function panel(p,rs){
  const g=new Map();let tot=0;
  for(const r of rs)if(r[p.k]){tot++;if(!g.has(r[0]))g.set(r[0],new Map());const m=g.get(r[0]);m.set(r[1],(m.get(r[1])||0)+1)}
  const sum=m=>[...m.values()].reduce((a,b)=>a+b,0);
  let sups=[...g.entries()].map(([s,m])=>({s,m,t:sum(m)}));
  sups.sort(sortMode==="alpha"?(a,b)=>cmp(a.s,b.s):(a,b)=>b.t-a.t);
  const max=Math.max(1,...sups.flatMap(x=>[...x.m.values()]));
  const pct=rs.length?(tot/rs.length*100).toFixed(1):"0.0";
  let b="";
  for(const x of sups){
    const c=closed.has(p.id+x.s);
    b+=`<tr class="s${c?" c":""}" data-t="${esc(p.id+x.s)}"><td>${esc(x.s)}</td><td class="n">${x.t}</td></tr>`;
    if(!c){let ag=[...x.m.entries()];ag.sort(sortMode==="alpha"?(a,b)=>cmp(a[0],b[0]):(a,b)=>b[1]-a[1]);
      for(const [a,n] of ag)b+=`<tr class="a"><td>${esc(a)}</td><td class="n"><div class="v"><i style="width:${Math.max(3,n/max*70)}px"></i>${n}</div></td></tr>`}
  }
  return `<h2><span></span>${p.t}</h2><p>${ds==="atom"&&p.sa?p.sa:p.sub}</p><div class="big">${tot}<small>${pct}% de ${rs.length} chats filtrados</small></div>`+
  (tot?`<div class="sc"><table><thead><tr><th>Supervisor / Agente</th><th class="n">${ds==="atom"&&p.ha?p.ha:p.h}</th></tr></thead><tbody>${b}<tr class="t"><td>Suma total</td><td class="n">${tot}</td></tr></tbody></table></div>`:`<div class="empty">Sin registros con los filtros actuales.</div>`);
}
const css=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const PAL=["#5b5bd6","#0fa89a","#f08c00","#e5487f","#8b5cf6","#3fb950","#ef5350","#2f9fd6"];
const CH={};let tab="captura",DET=[],LAST=[];
const sh=s=>s.split(" ").slice(0,2).join(" ");
function mk(id,type,labels,sets,o={}){
  if(typeof Chart==="undefined")return;
  if(CH[id])CH[id].destroy();
  Chart.defaults.color=css("--mut");Chart.defaults.borderColor=css("--line");Chart.defaults.font.family='"Plus Jakarta Sans",system-ui,sans-serif';Chart.defaults.elements.bar.borderRadius=6;Chart.defaults.plugins.legend.labels.usePointStyle=true;Chart.defaults.elements.line.borderWidth=3;Chart.defaults.elements.point.radius=3;
  const dn=type==="doughnut";
  CH[id]=new Chart(document.getElementById(id),{type,data:{labels,datasets:sets},options:Object.assign({responsive:true,maintainAspectRatio:false,animation:false,plugins:{legend:{display:sets.length>1||dn,position:"bottom"}}},o)});
}
const cnt=(L,f)=>{const m=new Map();for(const r of L){const k=f(r);m.set(k,(m.get(k)||0)+1)}return [...m].sort((a,b)=>b[1]-a[1])};
const HB={indexAxis:"y"};
function charts1(L){
  const ks=[[6,"Sin tipificación","--c1"],[7,"Sin matrícula","--c2"],[8,"Sin etiquetas","--c3"]].filter(k=>!(ds==="atom"&&k[0]===8));
  const g=new Map();for(const r of L){if(!(r[6]||r[7]||r[8]))continue;if(!g.has(r[0]))g.set(r[0],[0,0,0,0]);const a=g.get(r[0]);a[0]+=r[6];a[1]+=r[7];a[2]+=r[8];a[3]++}
  const S=[...g].sort((a,b)=>b[1][3]-a[1][3]);
  mk("c1","bar",S.map(x=>sh(x[0])),ks.map((k,i)=>({label:k[1],data:S.map(x=>x[1][i]),backgroundColor:css(k[2])})),{indexAxis:"y",scales:{x:{stacked:true},y:{stacked:true}}});
  const dy=[...new Set(L.map(r=>+r[4]))].sort((a,b)=>a-b);
  mk("c2","line",dy.map(d=>"Día "+d),ks.map(k=>({label:k[1],data:dy.map(d=>L.filter(r=>+r[4]===d).reduce((s,r)=>s+r[k[0]],0)),borderColor:css(k[2]),backgroundColor:css(k[2]),tension:.25})));
  const T=cnt(L.filter(r=>r[6]||r[7]||r[8]),r=>r[1]).slice(0,10);
  mk("c3","bar",T.map(x=>x[0]),[{label:"Chats incompletos",data:T.map(x=>x[1]),backgroundColor:css("--c1")}],{indexAxis:"y",plugins:{legend:{display:false}}});
}
const fmt=s=>!s?"–":(s>=3600?Math.floor(s/3600)+":":"")+String(Math.floor(s%3600/60)).padStart(s>=3600?2:1,"0")+":"+String(Math.round(s%60)).padStart(2,"0");
const med=a=>{a=a.filter(x=>x>0).sort((x,y)=>x-y);return a.length?a[a.length>>1]:0};
function stats(L){const n=L.length,av=k=>n?L.reduce((s,r)=>s+r[k],0)/n:0,sm=k=>L.reduce((s,r)=>s+r[k],0);
  return{n,cer:L.filter(r=>r[3]==="Cerrado").length,ven:sm(14),t:sm(6),m:sm(7),l:sm(8),mc:av(16),ma:av(17),pr:med(L.map(r=>r[18])),ta:med(L.map(r=>r[19]))}}
const SS={tsup:[1,-1],tag:[1,-1]};
const COLS=["Chats","Cerrados","Con venta","% venta","Sin tipif.","Sin matrícula","Sin etiquetas","Msj. contacto","Msj. agente","1.ª resp. (mediana)"];
const vc=i=>!(ds==="atom"&&i===6);
const cell=(i,v)=>(i===7||i===8)&&!HM?"–":i===3?v.toFixed(1)+"%":i===7||i===8?v.toFixed(1):i===9?fmt(v):v;
const row=s=>[s.n,s.cer,s.ven,s.n?s.ven/s.n*100:0,s.t,s.m,s.l,s.mc,s.ma,s.pr];
function gt(L,kf,id,lab){
  const g=new Map();for(const r of L){const k=kf(r);if(!g.has(k))g.set(k,[]);g.get(k).push(r)}
  const a=[...g].map(([k,l])=>[k,row(stats(l))]);const [ci,dr]=SS[id];
  a.sort(ci<0?(x,y)=>cmp(x[0],y[0])*dr:(x,y)=>(x[1][ci]-y[1][ci])*dr);
  const th=(i,n)=>`<th class="${i<0?"":"n"}" data-s="${i}" data-tb="${id}">${n}${ci===i?(dr<0?" ↓":" ↑"):""}</th>`;
  document.getElementById(id).innerHTML=`<table><thead><tr>${th(-1,lab)}${COLS.map((c,i)=>vc(i)?th(i,c):"").join("")}</tr></thead><tbody>${a.map(([k,v])=>`<tr><td>${esc(k)}</td>${v.map((x,i)=>vc(i)?`<td class="n">${cell(i,x)}</td>`:"").join("")}</tr>`).join("")}<tr class="t"><td>Suma total</td>${row(stats(L)).map((x,i)=>vc(i)?`<td class="n">${cell(i,x)}</td>`:"").join("")}</tr></tbody></table>`;
}
function an(L){
  const s=stats(L),n=s.n,p=x=>n?(x/n*100).toFixed(1)+"%":"–",sc=L.filter(r=>r[15]>=0);
  const K=[[n,"Chats"],[s.cer+" · "+p(s.cer),"Cerrados"],[s.ven+" · "+p(s.ven),"Con venta"],[p(n-s.t),"Con tipificación"],[p(n-s.m),"Con matrícula"],...(ds==="atom"?[]:[[p(n-s.l),"Con etiquetas"]]),[HM?s.mc.toFixed(1)+" / "+s.ma.toFixed(1):"n/d","Msj. contacto / agente (prom.)"],[fmt(s.pr),"1.ª respuesta (mediana)"],[fmt(s.ta),"Tiempo de atención (mediana)"],[sc.length?(sc.reduce((a,r)=>a+r[15],0)/sc.length).toFixed(0)+" · "+sc.length+" chats":"–","Score promedio"]];
  document.getElementById("kp").innerHTML=K.map(k=>`<div><b>${k[0]}</b><span>${k[1]}</span></div>`).join("");
  const dy=[...new Set(L.map(r=>+r[4]))].sort((a,b)=>a-b);
  mk("a1","bar",dy.map(d=>"Día "+d),[{label:"Chats",data:dy.map(d=>L.filter(r=>+r[4]===d).length),backgroundColor:PAL[0]},{label:"Con venta",data:dy.map(d=>L.filter(r=>+r[4]===d&&r[14]).length),backgroundColor:PAL[1]}]);
  const hb=(id,A,c)=>mk(id,"bar",A.map(x=>x[0]),[{data:A.map(x=>x[1]),backgroundColor:c}],{indexAxis:"y",plugins:{legend:{display:false}}});
  hb("a2",cnt(L,r=>r[12]),PAL[0]);hb("a3",cnt(L,r=>r[13]),PAL[2]);
  const cn=cnt(L,r=>r[2]);mk("a4","doughnut",cn.map(x=>x[0]),[{data:cn.map(x=>x[1]),backgroundColor:PAL,borderWidth:0}]);
  const et=cnt(L.flatMap(r=>r[20].split(",").filter(x=>x&&x!=="Vacio").map(x=>[x])),r=>r[0]).slice(0,12);hb("a5",et,PAL[3]);
  const sg=cnt(sc,r=>r[15]).sort((a,b)=>a[0]-b[0]);mk("a6","bar",sg.map(x=>x[0]),[{data:sg.map(x=>x[1]),backgroundColor:PAL[4]}],{plugins:{legend:{display:false}}});
  PML=pmCount(L);pmLim=50;
  hb("a7",PML.slice(0,12).map(x=>[x.t.length>48?x.t.slice(0,47)+"…":x.t,x.n]),PAL[5]);
  const nm=ds==="atom"?"Primer mensaje":"Primer mensaje (V2)";
  document.getElementById("pmh").textContent=nm+" · top 12";document.getElementById("pmt").textContent=nm;pmTable();
  gt(L,r=>r[0],"tsup","Supervisor");gt(L,r=>r[1],"tag","Agente");wk(L);
  const rs=cnt(L,r=>r[12]).map(x=>x[0]),ss=[...new Set(L.map(r=>r[0]))].sort(cmp),m={};
  for(const r of L){const k=r[12]+"|"+r[0];m[k]=(m[k]||0)+1}const mx=Math.max(1,...Object.values(m));
  document.getElementById("tpv").innerHTML=`<table class="hm"><thead><tr><th>Resultado</th>${ss.map(x=>`<th class="n">${esc(sh(x))}</th>`).join("")}<th class="n">Total</th></tr></thead><tbody>${rs.map(a=>`<tr><td style="text-align:left">${esc(a)}</td>${ss.map(x=>{const v=m[a+"|"+x]||0;return `<td style="background:color-mix(in srgb,var(--c1) ${Math.round(v/mx*55)}%,transparent)">${v||""}</td>`}).join("")}<td><b>${L.filter(r=>r[12]===a).length}</b></td></tr>`).join("")}</tbody></table>`;
}
function show(){
  const h=location.hash.slice(1),nd=h.startsWith("atom")?"atom":"calixta";
  tab=h.endsWith("analisis")?"analisis":"captura";
  if(nd!==ds){ds=nd;R=DS[ds];for(const k in ex)ex[k].clear();closed.clear();openSet.clear();allOpen=true;lim=100;document.getElementById("q").value="";bar()}
  HM=R.some(r=>r[16]||r[17]);document.getElementById("lk8").hidden=ds==="atom";document.getElementById("wks").hidden=ds==="atom";
  const $=i=>document.getElementById(i);
  $("v1").hidden=tab!=="captura";$("v2").hidden=tab!=="analisis";
  $("eb").textContent="Matriz "+(ds==="atom"?"Atom":"Calixta")+" · Control de calidad de captura";
  $("t1").href="#"+ds+"-captura";$("t2").href="#"+ds+"-analisis";$("d1").href="#calixta-"+tab;$("d2").href="#atom-"+tab;
  $("t1").toggleAttribute("aria-current",tab==="captura");$("t2").toggleAttribute("aria-current",tab==="analisis");
  $("d1").toggleAttribute("aria-current",ds==="calixta");$("d2").toggleAttribute("aria-current",ds==="atom");
  draw()}
addEventListener("hashchange",show);
const LKS={calixta:"https://utelvars.calixtachat.com/messenger/#!/",atom:"https://app.atomchat.io/conversations/"};const LK=()=>LKS[ds];
function xl(sheets,name,hl){
  if(typeof XLSX==="undefined"){alert("No se pudo cargar la librería de Excel. Revisa tu conexión a internet.");return}
  const wb=XLSX.utils.book_new();
  for(const [n,A] of sheets){
    const ws=XLSX.utils.aoa_to_sheet(A);
    ws["!cols"]=A[0].map((_,i)=>({wch:Math.min(48,Math.max(10,...A.slice(0,200).map(r=>String(r[i]==null?"":r[i]).length)))}));
    if(n===sheets[0][0]&&hl!=null)for(let i=1;i<A.length;i++){const c=ws[XLSX.utils.encode_cell({r:i,c:hl})];if(c)c.l={Target:c.v}}
    XLSX.utils.book_append_sheet(wb,ws,n);
  }
  XLSX.writeFile(wb,name);
}
const ORIG={};
async function loadOrig(){
  if(ORIG[ds])return ORIG[ds];
  const el=document.getElementById("orig-"+ds);
  if(el){ORIG[ds]=JSON.parse(el.textContent);return ORIG[ds]}
  await new Promise((ok,no)=>{const s=document.createElement("script");s.src="orig_"+ds+".js";s.onload=ok;s.onerror=no;document.head.appendChild(s)});
  return ORIG[ds];
}
async function xo(){
  const b=document.getElementById("xo"),tx=b.textContent;b.disabled=true;b.textContent="Preparando…";
  try{const O=await loadOrig();await xl([["Dataset original",[O.h,...O.r]]],"dataset_original_"+ds+".xlsx")}
  catch(e){alert("No se pudo cargar el dataset original.")}
  finally{b.disabled=false;b.textContent=tx}
}
const WKS=[["Semana 1","1–8"],["Semana 2","9–15"],["Semana 3","16–22"],["Semana 4","23–30"]];
const wkOf=d=>d<=8?0:d<=15?1:d<=22?2:3;
const WD={s:["Supervisor",0],a:["Agente",1],c:["Canal",2],e:["Estatus",3],r:["Área",5],x:["Resultado",12],z:["Razón de cierre",13]};
let WKX=[];
function wk(L){
  if(ds==="atom")return;
  const k1=document.getElementById("wk1").value;let k2=document.getElementById("wk2").value;if(k2===k1)k2="n";
  const i1=WD[k1][1],i2=k2==="n"?-1:WD[k2][1],m=new Map();
  for(const r of L){const w=wkOf(+r[4]),a=r[i1];if(!m.has(a))m.set(a,{w:[0,0,0,0],t:0,s:new Map()});const e=m.get(a);e.w[w]++;e.t++;
    if(i2>=0){const b=r[i2];if(!e.s.has(b))e.s.set(b,{w:[0,0,0,0],t:0});const f=e.s.get(b);f.w[w]++;f.t++}}
  const G=[...m].sort((a,b)=>cmp(a[0],b[0]));
  const all=[];for(const [,e] of G){if(i2>=0)for(const f of e.s.values())all.push(...f.w);else all.push(...e.w)}
  const mx=Math.max(1,...all),tw=[0,0,0,0];
  const sh=v=>v?`style="background:color-mix(in srgb,var(--c1) ${Math.round(v/mx*55)}%,transparent)"`:"";
  const cells=(w,t)=>w.map(v=>`<td class="n" ${sh(v)}>${v||"–"}</td>`).join("")+`<td class="n"><b>${t}</b></td>`;
  let b="";WKX=[[WD[k1][0],i2>=0?WD[k2][0]:"",...WKS.map(x=>x[0]+" ("+x[1]+")"),"Total"]];
  for(const [a,e] of G){
    e.w.forEach((v,i)=>tw[i]+=v);
    b+=`<tr class="${i2>=0?"s":"a"}" style="cursor:default"><td>${i2>=0?"":""}${esc(a)}</td>${cells(e.w,e.t)}</tr>`;
    WKX.push([a,i2>=0?"(total)":"",...e.w,e.t]);
    if(i2>=0)for(const [c,f] of [...e.s].sort((x,y)=>y[1].t-x[1].t)){b+=`<tr class="a"><td>${esc(c)}</td>${cells(f.w,f.t)}</tr>`;WKX.push([a,c,...f.w,f.t])}
  }
  const T=tw.reduce((x,y)=>x+y,0);
  b+=`<tr class="t"><td>Suma total</td>${tw.map(v=>`<td class="n">${v}</td>`).join("")}<td class="n">${T}</td></tr>`;
  WKX.push(["Suma total","",...tw,T]);
  document.getElementById("wkt").innerHTML=`<table><thead><tr><th>${WD[k1][0]}</th>${WKS.map(x=>`<th class="n">${x[0]}<small>${x[1]} nov</small></th>`).join("")}<th class="n">Total</th></tr></thead><tbody>${b}</tbody></table>`;
}
const YN=v=>v?"Sí":"";
const AT=()=>ds==="atom";
let PML=[],pmLim=50;
function pmCount(L){const m=new Map();for(const r of L){const raw=r[21]||"(sin mensaje)",k=raw.toLowerCase(),e=m.get(k);if(e)e.n++;else m.set(k,{t:raw,n:1})}return [...m.values()].sort((a,b)=>b.n-a.n)}
function pmTable(){
  const q=document.getElementById("pmq").value.trim().toLowerCase(),tot=LAST.length;
  const A=q?PML.filter(x=>x.t.toLowerCase().includes(q)):PML;
  document.getElementById("pmsub").textContent=`${PML.length} mensajes distintos en ${tot} chats${q?" · "+A.length+" coinciden con la búsqueda":""}. Se agrupan sin distinguir mayúsculas${ds==="atom"?" y el nombre del contacto aparece como {nombre}":""}.`;
  document.getElementById("pmtb").innerHTML=A.length?`<div class="sc"><table><thead><tr><th>#</th><th>Mensaje</th><th class="n">Chats</th><th class="n">% del total</th></tr></thead><tbody>${A.slice(0,pmLim).map((x,i)=>`<tr><td>${i+1}</td><td title="${esc(x.t)}">${esc(x.t)}</td><td class="n">${x.n}</td><td class="n">${tot?(x.n/tot*100).toFixed(1):"0.0"}%</td></tr>`).join("")}</tbody></table></div>`+(A.length>pmLim?`<div class="more"><button class="btn o" id="pmm">Mostrar más (${A.length-pmLim} restantes)</button></div>`:""):`<div class="empty">Sin mensajes con los filtros actuales.</div>`;
}
function xd(){
  const H=["Chat ID","Supervisor","Agente","Contacto","Canal","Estatus","Fecha de inicio","Área","Falta tipificación","Falta matrícula"];if(!AT())H.push("Falta etiquetas");H.push("Liga");
  const A=[H,...DET.map(r=>{const o=[r[9],r[0],r[1],r[11],r[2],r[3],r[10],r[5],YN(r[6]),YN(r[7])];if(!AT())o.push(YN(r[8]));o.push(LK()+r[9]);return o})];
  xl([["Chats incompletos",A]],"chats_incompletos_"+ds+".xlsx",H.length-1);
}
function xa(){
  const idx=COLS.map((_,i)=>i).filter(vc);
  const f=v=>idx.map(i=>{const x=v[i];return i===9?fmt(x):i===3||i===7||i===8?+x.toFixed(1):x});
  const g=(kf,lab)=>{const m=new Map();for(const r of LAST){const k=kf(r);if(!m.has(k))m.set(k,[]);m.get(k).push(r)}
    return [[lab,...idx.map(i=>COLS[i])],...[...m].sort((a,b)=>cmp(a[0],b[0])).map(([k,l])=>[k,...f(row(stats(l)))]),["Suma total",...f(row(stats(LAST)))]]};
  const H=["Chat ID","Supervisor","Agente","Contacto","Canal","Estatus","Día","Fecha de inicio","Área","Resultado","Razón de cierre","Con venta","Score","Msj. contacto","Msj. agente","1.ª respuesta (seg)","Tiempo de atención (seg)","Etiquetas","Primer mensaje","Sin tipificación","Sin matrícula"];if(!AT())H.push("Sin etiquetas");H.push("Liga");
  const C=[H,...LAST.map(r=>{const o=[r[9],r[0],r[1],r[11],r[2],r[3],+r[4],r[10],r[5],r[12],r[13],YN(r[14]),r[15]<0?"":r[15],r[16],r[17],r[18],r[19],r[20],r[21],YN(r[6]),YN(r[7])];if(!AT())o.push(YN(r[8]));o.push(LK()+r[9]);return o})];
  const tot=LAST.length,M=[["Primer mensaje","Chats","% del total"],...pmCount(LAST).map(x=>[x.t,x.n,tot?+(x.n/tot*100).toFixed(1):0])];
  xl([["Por supervisor",g(r=>r[0],"Supervisor")],["Por agente",g(r=>r[1],"Agente")],["Por canal",g(r=>r[2],"Canal")],["Por día",g(r=>+r[4],"Día")],["Por resultado",g(r=>r[12],"Resultado")],...(AT()?[]:[["Por semana",WKX]]),["Primer mensaje",M],["Todos los chats",C]],"analisis_funnel_upselling_"+ds+".xlsx");
}
let lim=100;
function detail(rs){
  const ks=[...document.querySelectorAll(".dk:checked")].map(x=>+x.value);
  const q=document.getElementById("q").value.trim().toLowerCase();
  let L=rs.filter(r=>ks.some(k=>r[k]));
  if(q)L=L.filter(r=>[r[9],r[0],r[1],r[11]].join(" ").toLowerCase().includes(q));
  L.sort((a,b)=>String(b[9]).localeCompare(String(a[9]),"es",{numeric:true}));DET=L;
  document.getElementById("dsub").textContent=`${L.length} chats con al menos un dato vacío según los filtros. El ID abre el chat en Calixta.`;
  const lb={6:"Tipificación",7:"Matrícula",8:"Etiquetas"};
  const body=L.slice(0,lim).map(r=>`<tr><td><a href="${LK()}${r[9]}" target="_blank" rel="noopener">${r[9]}</a></td><td>${esc(r[0])}</td><td>${esc(r[1])}</td><td>${esc(r[11])}</td><td>${esc(r[2])}</td><td>${esc(r[3])}</td><td>${esc(r[10])}</td><td>${[6,7,8].filter(k=>r[k]).map(k=>`<span class="tg k${k}">${lb[k]}</span>`).join("")}</td><td><a href="${LK()}${r[9]}" target="_blank" rel="noopener">${LK()}${r[9]}</a></td></tr>`).join("");
  document.getElementById("dtb").innerHTML=L.length?`<div class="sc"><table><thead><tr><th>Chat ID</th><th>Supervisor</th><th>Agente</th><th>Contacto</th><th>Canal</th><th>Estatus</th><th>Fecha de inicio</th><th>Falta</th><th>Liga</th></tr></thead><tbody>${body}</tbody></table></div>`+(L.length>lim?`<div class="more"><button class="btn o" id="mr">Mostrar más (${Math.min(100,L.length-lim)} de ${L.length-lim} restantes)</button></div>`:""):`<div class="empty">Sin chats con los filtros actuales.</div>`;
}
function draw(){
  const rs=rows();LAST=rs;
  document.getElementById("sub").textContent=`${rs.length} de ${R.length} chats · 1 al ${Math.max(...R.map(r=>+r[4]))} de noviembre · toca un supervisor para contraer sus agentes`;
  for(const p of P)document.getElementById(p.id).innerHTML=panel(p,rs);document.getElementById("p3").hidden=ds==="atom";
  lim=100;detail(rs);if(tab==='captura')charts1(rs);else an(rs);
}
function all(){bar();draw()}
document.addEventListener("toggle",e=>{const d=e.target;if(d.dataset&&d.dataset.k&&d.tagName==="DETAILS"){d.open?openSet.add(d.dataset.k):openSet.delete(d.dataset.k)}},true);
document.addEventListener("click",e=>{
  const t=e.target;
  if(t.dataset.all){ex[t.dataset.all].clear();all();return}
  if(t.dataset.none){opts(t.dataset.none).forEach(x=>ex[t.dataset.none].add(x));all();return}
  if(t.id==="pmm"){pmLim+=100;pmTable();return}
  if(t.id==="xd"){xd();return}
  if(t.id==="xo"){xo();return}
  if(t.id==="xa"){xa();return}
  if(t.id==="mr"){lim+=100;detail(rows());return}
  if(t.id==="srt"){sortMode=sortMode==="alpha"?"desc":"alpha";all();return}
  if(t.id==="tg"){allOpen=!allOpen;closed.clear();if(!allOpen)for(const p of P)for(const r of R)closed.add(p.id+r[0]);all();return}
  if(t.id==="rs"){for(const k in ex)ex[k].clear();closed.clear();allOpen=true;all();return}
  const th=t.closest&&t.closest("th[data-s]");if(th){const i=+th.dataset.s,id=th.dataset.tb,c=SS[id];SS[id]=c[0]===i?[i,-c[1]]:[i,i<0?1:-1];draw();return}
  const tr=t.closest&&t.closest("tr.s");
  if(tr){const k=tr.dataset.t;closed.has(k)?closed.delete(k):closed.add(k);draw()}
});
document.addEventListener("change",e=>{
  const t=e.target;if(t.classList.contains("dk")){lim=100;detail(rows());return}if(t.type!=="checkbox")return;
  const k=t.dataset.k;t.checked?ex[k].delete(t.value):ex[k].add(t.value);all();
});
document.getElementById("q").addEventListener("input",()=>{lim=100;detail(rows())});
document.getElementById("pmq").addEventListener("input",()=>{pmLim=50;pmTable()});
for(const id of ["wk1","wk2"])document.getElementById(id).addEventListener("change",()=>wk(LAST));
bar();show();matchMedia("(prefers-color-scheme: dark)").addEventListener("change",()=>draw());
