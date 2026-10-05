// MIT UI code. Explanatory prose in the page is CC BY 4.0.
import {DIRS,LETTERS,key,distance,maskName,graph,defaultTable,initialize,step,maximumPeriod,alternatingPath,sharpTable,primitiveOrbit,checkHost} from './model.mjs';
import {animate,mix,smooth} from './motion.mjs';
const $=id=>document.getElementById(id), clone=x=>JSON.parse(JSON.stringify(x));
let assets,claims,sim,preset,timer=null,theme='light',hostView=null;
const reducedMotion=matchMedia('(prefers-reduced-motion: reduce)');
const gridViews=new Map();let cameraMotion=null,cameraGoal=null;
const motionAllowed=()=>!reducedMotion.matches&&!document.hidden;
const entries=new Map();
function enter(el){entries.get(el)?.cancel();if(motionAllowed()){const a=el?.animate?.([{opacity:0,transform:'translateY(10px)'},{opacity:1,transform:'translateY(0)'}],{duration:300,easing:'cubic-bezier(.2,.7,.2,1)'});if(a){entries.set(el,a);a.onfinish=a.oncancel=()=>{if(entries.get(el)===a)entries.delete(el);};}}}
function finishEntries(){for(const a of entries.values())a.finish();entries.clear();}
let heroTimer=null,heroTime=0;
function stopHero(){if(heroTimer){clearInterval(heroTimer);heroTimer=null;}}
function startHero(){stopHero();if(!assets||$('overview').hidden||!motionAllowed()||!globalThis.requestAnimationFrame)return;
 heroTimer=setInterval(()=>{const r=$('hero-grid').getBoundingClientRect();if(!motionAllowed()||$('overview').hidden){stopHero();return;}if(r.bottom<0||r.top>innerHeight)return;
 const p=assets.examples.presets[0],trace=p.replay.trace;heroTime=heroTime+1<trace.length?heroTime+1:p.replay.preperiod;const t=trace[heroTime];
 renderGrid('hero-grid',p.cells,[[t[0],t[1]],[t[2],t[3]]],{label:`Exact A-star replay, recorded slice ${heroTime}, Manhattan distance ${t[4]}.`},{duration:620});
 },1500);
}
function renderWord(id,tokens,index){const el=$(id),signature=JSON.stringify(tokens);if(el.dataset.word!==signature){el.innerHTML=tokens.map((text,i)=>`<span class="${i===index?'active':''}">${text}</span>`).join('');el.dataset.word=signature;}el.querySelectorAll('span').forEach((span,i)=>{span.classList.toggle('active',i===index);if(i===index)span.setAttribute('aria-current','step');else span.removeAttribute('aria-current');});}
function settleGrids(){for(const view of gridViews.values())view.motion?.finish();}
function gridLayout(cells){const xs=cells.map(p=>p[0]),ys=cells.map(p=>p[1]),xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys),z=Math.min(72,440/(xmax-xmin+1),250/(ymax-ymin+1));
 const ox=(520-z*(xmax-xmin))/2,oy=(300-z*(ymax-ymin))/2;
 return {z,xy:([x,y])=>[ox+(x-xmin)*z,oy+(ymax-y)*z]};
}
function renderGrid(id,cells,tags=[],options={},motion={}){
 const el=$(id),signature=JSON.stringify([cells,options.phases,options.multiplicity,options.indices,tags.length]);
 let view=gridViews.get(id),changed=!view||view.signature!==signature;
 if(changed){view?.motion?.cancel();el.innerHTML=svgGrid(cells,tags,options);view={signature,positions:[],tags:[],visited:new Set()};gridViews.set(id,view);}
 const svg=el.querySelector('svg');
 if(!svg){el.innerHTML=svgGrid(cells,tags,options);return;}
 const {xy}=gridLayout(cells),overlap=tags.length>1&&tags[0][0]===tags[1][0];
 const target=tags.map(([v],i)=>{const [x,y]=xy(cells[v]);return [x+(overlap?(i?9:-9):0),y];});
 const agents=[...svg.querySelectorAll('.agent')];
 const from=view.positions.length===target.length?view.positions.map(p=>[...p]):target;
 view.motion?.cancel();
 if(motion.snap)view.visited.clear();
 const active=new Map();
 tags.forEach(([v],i)=>{const old=view.tags[i]?.[0];if(!motion.snap&&old!==undefined&&old!==v&&distance(cells[old],cells[v])===1){const edge=[old,v].sort((a,b)=>a-b).join('-');active.set(edge,(active.get(edge)||'')+(i?'B':'A'));if(motion.contour)view.visited.add(edge);}});
 svg.querySelectorAll('[data-edge]').forEach(e=>{e.dataset.active=active.get(e.dataset.edge)||'';e.dataset.visited=String(view.visited.has(e.dataset.edge));});
 svg.setAttribute('aria-label',options.label||'Exact grid coordinates');const title=svg.querySelector('title');if(title)title.textContent=options.label||'Exact grid coordinates';
 agents.forEach((a,i)=>{a.dataset.cell=String(tags[i][0]);a.dataset.state=String(tags[i][1]);a.dataset.x=String(target[i][0]);a.dataset.y=String(target[i][1]);if(tags.length===1)a.querySelector('text').textContent=String(tags[i][1]);});
 view.tags=tags.map(t=>[...t]);
 const moving=!changed&&!motion.snap&&motionAllowed()&&!el.closest('.page')?.hidden&&from.some((p,i)=>p.some((v,j)=>v!==target[i][j]));
 el.dataset.moving=String(moving);
 const update=t=>{view.positions=target.map((p,i)=>p.map((v,j)=>mix(from[i][j],v,t)));agents.forEach((a,i)=>a.setAttribute('transform',`translate(${view.positions[i].join(' ')})`));};
 view.motion=animate({duration:moving?(motion.duration||380):0,update,complete:()=>{el.dataset.moving='false';}});
 if(changed&&motionAllowed()&&!el.closest('.page')?.hidden)svg.classList.add('build-in');
}
reducedMotion.addEventListener?.('change',()=>{stopHero();settleGrids();cameraMotion?.finish();finishEntries();startHero();});
document.addEventListener?.('visibilitychange',()=>{if(document.hidden){stopHero();pause();settleGrids();cameraMotion?.finish();finishEntries();}else startHero();});
function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function svgGrid(cells,tags=[],options={}){
 const g=graph(cells),{z,xy}=gridLayout(cells);
 let s=`<svg class="grid-figure" viewBox="0 0 520 300" role="img" aria-label="${esc(options.label||'Induced grid maze; north up; all unit-distance edges included')}"><title>${esc(options.label||'Exact grid coordinates')}</title><g class="maze-edges">`,order=0;
 for(let i=0;i<cells.length;i++)for(let d=0;d<4;d++){const j=g.adjacent[i][d];if(j>i){const [x,y]=xy(cells[i]),[a,b]=xy(cells[j]),doubled=options.phases?.[Math.min(i,j)]&&options.phases[Math.min(i,j)]!=='-';s+=`<line data-edge="${i}-${j}" pathLength="1" style="--order:${Math.min(order++,18)}" x1="${x}" y1="${y}" x2="${a}" y2="${b}" stroke-width="${doubled?5:2}"/>`;}}
 s+='</g><g class="maze-cells">';
 cells.forEach((p,i)=>{const [x,y]=xy(p);s+=`<rect data-cell="${i}" style="--order:${Math.min(i,18)}" x="${x-z*.29}" y="${y-z*.29}" width="${z*.58}" height="${z*.58}" rx="4"/>`;});s+='</g><g class="maze-labels">';
 for(let i=0;i<cells.length;i++)for(let d=0;d<4;d++){const j=g.adjacent[i][d];if(j>i){const [x,y]=xy(cells[i]),[a,b]=xy(cells[j]),doubled=options.phases?.[Math.min(i,j)]&&options.phases[Math.min(i,j)]!=='-';if(doubled)s+=`<text x="${(x+a)/2+8}" y="${(y+b)/2-8}" font-size="12">×2 / η${options.phases[Math.min(i,j)]}</text>`;if(options.multiplicity)s+=`<text x="${(x+a)/2+8}" y="${(y+b)/2-8}" font-size="12">k=${options.multiplicity[d%2===0?'N':'E']||1}</text>`;}}
 if(options.indices)cells.forEach((p,i)=>{const [x,y]=xy(p);s+=`<text x="${x}" y="${y+5}" text-anchor="middle" font-size="13">${i}</text>`;});s+='</g>';
 tags.forEach(([v,q],i)=>{const [x,y]=xy(cells[v]),overlap=tags.length>1&&tags[0][0]===tags[1][0],px=x+(overlap?(i?9:-9):0),r=Math.max(7,Math.min(21,z*.32));s+=`<g class="agent" data-agent="${i?'B':'A'}" transform="translate(${px} ${y})">`;s+=i===1?`<rect class="agent-b" x="${-r}" y="${-r}" width="${2*r}" height="${2*r}" rx="4"/>`:`<circle class="agent-a" cx="0" cy="0" r="${r}"/>`;s+=`<text class="agent-text" x="0" y="4" text-anchor="middle" font-size="${Math.max(10,r*.65)}">${tags.length===1?q:(i?'B':'A')}</text></g>`;});
 return s+'<text x="478" y="25" font-size="12">N ↑</text></svg>';
}
function sourceHTML(id){const c=claims.get(id);if(!c)return '';return `<details><summary>Source · ${esc(c.paper_label)}</summary><div class="source-links"><a href="${esc(c.paper_source)}">Paper source</a>${c.data_sources.map((x,i)=>`<a href="${esc(x)}">Data ${c.data_sources.length>1?i+1:''}</a>`).join('')}${c.semantic_sources.map((x,i)=>`<a href="${esc(x)}">Checker ${c.semantic_sources.length>1?i+1:''}</a>`).join('')}</div><p>${esc(c.status)} · ${esc(c.presentation)}.</p></details>`;}
function route(){
 stopHero();pause();settleGrids();cameraMotion?.finish();finishEntries();
 const raw=location.hash.slice(1)||'overview',id=raw.split('?')[0];const target=document.querySelector('section.page#'+CSS.escape(id))||$('overview');
 document.querySelectorAll('section.page').forEach(p=>p.hidden=p!==target);document.querySelectorAll('nav a').forEach(a=>{if(a.hash==='#'+target.id)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
 if(raw.includes('?preset=')&&assets){const code=new URLSearchParams(raw.split('?')[1]).get('preset');if(assets.examples.presets.some(p=>p.id===code)&&preset?.id!==code)loadPreset(code);}
 enter(target);target.querySelectorAll?.('.grid-figure').forEach(svg=>{svg.classList.remove('build-in');if(motionAllowed()){void svg.getBoundingClientRect();svg.classList.add('build-in');}});
 if(target.id==='host'&&hostView)hostDraw();document.title=target.id==='overview'?'Memory, Recurrent Geometry, and Rendezvous Traps':target.querySelector('h1').textContent+' · Memory / Geometry';
 if(target.id==='overview')startHero();pause();
}
window.addEventListener('hashchange',()=>{route();window.scrollTo(0,0);});route();
function setTheme(value){theme=value;document.documentElement.dataset.theme=value;$('theme').textContent=value==='light'?'Dark mode':'Light mode';try{localStorage.setItem('maze-theme',value);}catch{}if(hostView)hostDraw();}
let savedTheme;try{savedTheme=localStorage.getItem('maze-theme');}catch{}
setTheme(['light','dark'].includes(savedTheme)?savedTheme:matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');$('theme').onclick=()=>setTheme(theme==='light'?'dark':'light');
function pause(settle=true){if(timer){clearInterval(timer);timer=null;}if($('run'))$('run').textContent='Run';if(settle)gridViews.get('sim-grid')?.motion?.finish();}
function resetSim(){pause();sim=initialize(preset.cells,preset.table,preset.starts);renderSim(true);}
function markToy(){preset.kind='Illustrative · edited by reader';preset.claim='toy';preset.id='edited';}
function renderSim(snap=false){
 renderGrid('sim-grid',sim.cells,sim.tags,{label:`At integer time ${sim.time}, A and B have Manhattan distance ${distance(...sim.tags.map(([v])=>sim.cells[v]))}.`},{snap,duration:timer?Math.min(520,+$('speed').value*.78):380});
 const d=distance(...sim.tags.map(([v])=>sim.cells[v]));
 $('sim-status').textContent=sim.status==='success'?`Rendezvous at integer time ${sim.time} · Manhattan distance ${d} ≤ 1`:sim.status==='cycle'?`No rendezvous · exact product cycle detected · preperiod ${sim.preperiod}, period ${sim.period}`:`Integer time ${sim.time} · Manhattan distance ${d} · compulsory synchronous movement`;
 $('agent-metrics').innerHTML=sim.tags.map(([v,q],i)=>`<div class="metric"><strong>${i?'B':'A'} · q=${q}</strong><span>cell (${sim.cells[v]}) · open mask ${maskName(sim.g.masks[v])}</span></div>`).join('');
 $('preset-kind').textContent=preset.kind+' · both initial states 0';if(snap)$('sim-source').innerHTML=sourceHTML(preset.claim);$('sim-status').dataset.status=sim.status;highlightRules();$('step').disabled=sim.status!=='running';$('run').disabled=sim.status!=='running';if(sim.status!=='running')pause(false);
}
function highlightRules(){
 $('transition-table').querySelectorAll('td[data-mask]').forEach(td=>{const names=sim.tags.flatMap(([v,q],i)=>sim.g.masks[v]===+td.dataset.mask&&q===+td.dataset.state?[i?'B':'A']:[]).join('');td.dataset.agents=names;});
}
function tableEditor(){
 $('transition-table').innerHTML='<caption>All legal nonempty compass masks. Each action is direction, then next state.</caption><thead><tr><th>Mask</th>'+preset.table.map((_,q)=>`<th>State ${q}</th>`).join('')+'</tr></thead><tbody>'+Array.from({length:15},(_,i)=>{const m=i+1;return `<tr><td>${maskName(m)}</td>`+preset.table.map((row,q)=>{const [d,r]=row[i];return `<td data-mask="${m}" data-state="${q}"><div class="table-pair"><select data-q="${q}" data-m="${m}" data-part="0" aria-label="Direction for state ${q}, mask ${maskName(m)}">${[...LETTERS].map((l,j)=>m&(1<<j)?`<option value="${j}"${j===d?' selected':''}>${l}</option>`:'').join('')}</select><select data-q="${q}" data-m="${m}" data-part="1" aria-label="Next state for state ${q}, mask ${maskName(m)}">${preset.table.map((_,j)=>`<option${j===r?' selected':''}>${j}</option>`).join('')}</select></div></td>`;}).join('')+'</tr>';}).join('')+'</tbody>';
 $('transition-table').onchange=e=>{const {q,m,part}=e.target.dataset;if(q!==undefined){preset.table[+q][+m-1][+part]=+e.target.value;markToy();resetSim();}};
}
function startsEditor(){['a','b'].forEach((name,i)=>{$('start-'+name).innerHTML=preset.cells.map(p=>`<option value="${key(p)}"${key(p)===key(preset.starts[i])?' selected':''}>(${p})</option>`).join('');$('start-'+name).onchange=e=>{preset.starts[i]=e.target.value.split(',').map(Number);markToy();resetSim();};});$('cells').value=preset.cells.map(key).join('\n');}
function loadPreset(id){preset=clone(assets.examples.presets.find(x=>x.id===id)||assets.examples.presets[0]);$('preset').value=preset.id;$('state-count').value=preset.states;startsEditor();tableEditor();resetSim();$('sim-error').textContent='';}
function setupSim(){
 $('preset').innerHTML=assets.examples.presets.map(p=>`<option value="${p.id}">${p.label}</option>`).join('');$('preset').onchange=e=>{location.hash='simulator?preset='+e.target.value;loadPreset(e.target.value);};loadPreset('astar-u');
 $('step').onclick=()=>{step(sim);renderSim();};$('reset').onclick=resetSim;$('run').onclick=()=>{if(timer){pause();return;}if(sim.status!=='running')return;$('run').textContent='Pause';timer=setInterval(()=>{step(sim);renderSim();},+$('speed').value);};$('speed').onchange=pause;
 $('state-count').onchange=e=>{preset.states=+e.target.value;preset.table=defaultTable(preset.states);markToy();tableEditor();resetSim();};
 $('apply-cells').onclick=()=>{try{const cells=$('cells').value.trim().split(/\n/).map(line=>{if(!/^\s*-?\d+\s*,\s*-?\d+\s*$/.test(line))throw Error('Use one integer x,y pair per line.');return line.split(',').map(Number);});if(cells.length>64)throw Error('Use at most 64 cells in this educational sandbox.');const g=graph(cells);if(!g.connected)throw Error('The induced grid maze must be connected.');preset.cells=cells;preset.starts=preset.starts.map((p,i)=>g.index.has(key(p))?p:cells[i?cells.length-1:0]);markToy();startsEditor();resetSim();$('sim-error').textContent='';}catch(e){$('sim-error').textContent=e.message;}};
}
let capT=0;
function renderCapacity(){const s=+$('capacity-s').value,d=Math.min(s,4),cells=[[0,0],...DIRS.slice(0,d)],L=2*d,t=capT%L,v=t%2?1+Math.floor(t/2):0,q=t%2?0:Math.floor(t/2);
 renderGrid('capacity-grid',cells,[[v,q]],{label:`Exact degree-${d} grid star; tagged step ${t}.`,multiplicity:{N:1,E:1}},{snap:capT===0,contour:true});
 renderWord('capacity-tags',Array.from({length:L},(_,i)=>i%2?'leaf '+Math.floor(i/2)+'₀':'centre '+Math.floor(i/2)),t);
 $('capacity-message').textContent=`Centre capacity: r = ${d} × 1 = ${d} ≤ ${s}. Primitive tagged period L = ${L}.`;
 $('capacity-conclusion').textContent=s===1?'One state forces a single-edge tree support.':s===2?'Two states force path-shaped tree support.':'With '+s+' states, degree-'+d+' branching is possible on a grid tree. Capacity is only the geometric constraint.';
}
function setupCapacity(){$('capacity-s').onchange=()=>{capT=0;renderCapacity();};$('capacity-step').onclick=()=>{capT++;renderCapacity();};$('capacity-reset').onclick=()=>{capT=0;renderCapacity();};renderCapacity();}
let periodOrbit=null,periodTime=0,periodCells=null,periodBudget=3,periodCapped=false;
function drawPeriod(){if(!periodOrbit)return;const tag=periodOrbit.tags[periodTime%periodOrbit.tags.length];renderGrid('period-grid',periodCells,[tag],{label:'Exact alternating-family construction at tagged step '+periodTime,multiplicity:periodCells.length===2?{E:periodBudget}:{E:periodBudget-1,N:1}},{snap:periodTime===0,contour:true});$('period-orbit').textContent=`Tagged step ${periodTime%periodOrbit.tags.length} of ${periodOrbit.tags.length}. Cell ${tag[0]}, state ${tag[1]}. ${periodCells.length}-vertex visual replay, ${periodBudget} states.${periodCapped?" The calculator is exact for your input; the visual replay is capped at s=12,n=60.":""}`;}
function calculatePeriod(){try{const s=$('period-s').value.trim(),n=$('period-n').value.trim();if(!/^\d+$/.test(s)||!/^\d+$/.test(n))throw Error('Enter integer s ≥ 2 and n ≥ 2.');const result=maximumPeriod(s,n);$('period-result').textContent=result.toString();$('period-formula').textContent=BigInt(n)===2n?'Lmax(s,2) = 2s':BigInt(n)%2n===0n?'Lmax(s,n) = sn − 2 (even n)':'Lmax(s,n) = s(n − 1) (odd n)';$('period-error').textContent='';periodBudget=Number(BigInt(s)>12n?12n:BigInt(s));const nn=Number(BigInt(n)>60n?60n:BigInt(n));periodCapped=BigInt(s)>12n||BigInt(n)>60n;periodCells=alternatingPath(nn);periodOrbit=primitiveOrbit(periodCells,sharpTable(periodBudget,nn));periodTime=0;drawPeriod();$('period-step').disabled=false;$('period-reset').disabled=false;}catch(e){$('period-error').textContent=e.message;$('period-result').textContent='—';periodOrbit=null;gridViews.get('period-grid')?.motion?.cancel();gridViews.delete('period-grid');$('period-grid').dataset.moving='false';$('period-step').disabled=true;$('period-reset').disabled=true;$('period-grid').textContent='Choose valid parameters to inspect a construction.';}}
function setupPeriods(){$('period-calculate').onclick=calculatePeriod;['period-s','period-n'].forEach(id=>$(id).onkeydown=e=>{if(e.key==='Enter')calculatePeriod();});$('period-step').onclick=()=>{periodTime++;drawPeriod();};$('period-reset').onclick=()=>{periodTime=0;drawPeriod();};calculatePeriod();}
let nandBits='00',nandTime=0;
function renderNand(){const p=assets.realization.examples.find(x=>x.id==='saturated_nand8'),q=p.witnesses[nandBits],i=nandTime%p.word.length;
 renderGrid('nand-grid',p.cells,q?[[p.word[i],q[i]]]:[],{phases:p.phases,indices:true,label:'Exact NAND specification ENENNNE; doubled edges and fixed insertion phases shown.'},{snap:nandTime===0,contour:true});
 $('nand-status').textContent=q?`Correspondences ${nandBits} · exact released witness · occurrence ${i}/${p.word.length-1}, vertex ${p.word[i]}, state ${q[i]}`:'Correspondences 11 are impossible: this fixed specification would require four distinct states at the straight NS mask.';
 renderWord('nand-word',q?p.word.map((v,j)=>`${v}₍${q[j]}₎`):[],i);$('nand-step').disabled=!q;$('nand-buttons').querySelectorAll('button').forEach(b=>b.dataset.selected=b.dataset.bits===nandBits);
}
function setupThree(){$('nand-buttons').onclick=e=>{if(!e.target.dataset.bits)return;nandBits=e.target.dataset.bits;nandTime=0;renderNand();};$('nand-step').onclick=()=>{nandTime++;renderNand();};renderNand();const p=assets.realization.examples.find(x=>x.id==='staircase6');$('staircase-grid').innerHTML=svgGrid(p.cells,[],{phases:p.phases,indices:true,label:'Six-vertex staircase with north-edge insertion phases 0 and 1; no three-state realization.'});}
let selectedTest='H001';
function showTest(id){selectedTest=id;const p=assets.family.instances.find(x=>x.id===id),packed=assets.family.packing.filter(w=>w.trapped.includes(id));
 $('test-detail').innerHTML=`<p class="eyebrow">${p.geometry_id} · ${p.orbit_id}</p><h2>${p.id}</h2><span class="badge ${p.selected?'cert':''}">${p.selected?'Selected in certified 44':'Full 144 family'}</span>${svgGrid(p.cells,p.starts.map(s=>[p.cells.findIndex(v=>key(v)===key(s)),0]),{label:`Test ${p.id}, ${p.size} cells and two state-0 starts.`})}<p class="small">${p.size} cells · ${p.graph_type} · modules ${p.schemas.join(', ')}<br>A starts at (${p.starts[0]}); B at (${p.starts[1]}).<br>Absolute compass orientation is preserved.</p><details><summary>Proof provenance</summary><ul class="text-list">${p.provenance.map(x=>`<li>${esc(x.leaf_id)} · inverse of ${esc(x.normalizer)}</li>`).join('')}</ul></details><p class="small">Packing memberships: ${packed.length?packed.map(x=>`${esc(x.id)} traps ${x.trapped.join(', ')}`).join('; '):'not in a saved packing trapped-set'}.</p><div class="source-links"><a href="research/supplement/obstructions/basis144/family.json">Exact candidate family</a><a href="research/supplement/obstructions/basis144/functions/${p.id}.json">Physical decision DAG</a></div><div class="source">${sourceHTML(p.selected?'family44':'family144')}</div>`;
 $('test-gallery').querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.id===id)));enter($('test-detail'));
}
function filterTests(){const search=$('test-search').value.toLowerCase().trim(),size=$('test-size').value,type=$('test-type').value,selected=$('test-selected').checked;
 const visible=assets.family.instances.filter(p=>(!selected||p.selected)&&(size==='all'||p.size===+size)&&(type==='all'||(type==='tree'?p.graph_type!=='path':p.graph_type==='path'))&&(!search||[p.id,p.geometry_id,...p.schemas].some(x=>x.toLowerCase().includes(search))));
 $('test-count').textContent=`Showing ${visible.length} of 144 oriented tests · 44 selected overall.`;
 $('test-gallery').innerHTML=visible.length?visible.map(p=>`<button class="test-card" data-id="${p.id}" aria-pressed="${p.id===selectedTest}"><strong>${p.id}</strong> <span class="muted">${p.size} cells</span>${svgGrid(p.cells,p.starts.map(s=>[p.cells.findIndex(v=>key(v)===key(s)),0]),{label:`Test ${p.id}; north up; exact starts A and B.`})}<span class="badge ${p.selected?'cert':''}">${p.selected?'Selected 44':p.schemas.join(' / ')}</span></button>`).join(''):'<p>No tests match these filters.</p>';
 enter($('test-gallery'));if(!visible.length)$('test-detail').innerHTML='<h2>No matching test</h2><p class="small">Adjust the search or filters to inspect an exact candidate.</p>';
 if(visible.length&&!visible.some(p=>p.id===selectedTest))showTest(visible[0].id);else if(visible.length&&!$('test-detail').querySelector('.eyebrow'))showTest(selectedTest);
}
function setupTests(){['test-search','test-size','test-type','test-selected'].forEach(id=>$(id).oninput=filterTests);$('test-gallery').onclick=e=>{const b=e.target.closest('button[data-id]');if(b)showTest(b.dataset.id);};filterTests();showTest('H001');}
function css(name){return getComputedStyle(document.documentElement).getPropertyValue(name).trim();}
function canvasSize(canvas){const r=canvas.getBoundingClientRect(),dpr=Math.min(devicePixelRatio||1,2);if(canvas.width!==Math.round(r.width*dpr)||canvas.height!==Math.round(r.height*dpr)){canvas.width=Math.round(r.width*dpr);canvas.height=Math.round(r.height*dpr);}const ctx=canvas.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);return {ctx,w:r.width,h:r.height};}
function hostDraw(){if(!hostView||$('host').hidden)return;const {ctx,w,h}=canvasSize($('host-canvas'));if(!w)return;
 const {cx,cy,z,piece}=hostView,hdata=assets.host,colors=Object.fromEntries(['panel','muted','teal','pale','accent','line'].map(k=>[k,css('--'+k)]));
 $('host-canvas').dataset.cx=String(cx);$('host-canvas').dataset.cy=String(cy);$('host-canvas').dataset.zoom=String(z);
 const project=([x,y])=>[(x-cx)*z+w/2,(cy-y)*z+h/2];ctx.fillStyle=colors.panel;ctx.fillRect(0,0,w,h);
 const highlighted=new Set(piece?.cells.map(key)||[]);ctx.strokeStyle=colors.muted;ctx.lineWidth=z<3?1:1.5;ctx.beginPath();hdata.cells.forEach((p,i)=>{const [x,y]=project(p);if(x<-z||x>w+z||y<-z||y>h+z)return;for(const j of hostView.g.adjacent[i])if(j>i){const [a,b]=project(hdata.cells[j]);ctx.moveTo(x,y);ctx.lineTo(a,b);}});ctx.stroke();
 if(z>=2){for(const p of hdata.cells){const [x,y]=project(p);if(x<-z||x>w+z||y<-z||y>h+z)continue;ctx.fillStyle=highlighted.has(key(p))?colors.teal:colors.pale;const a=Math.max(1,z*.52);ctx.fillRect(x-a/2,y-a/2,a,a);if(z>8){ctx.strokeStyle=colors.line;ctx.strokeRect(x-a/2,y-a/2,a,a);}}}
 if(piece){const originals=new Set(piece.original_images.map(key));for(const p of piece.cells){const [x,y]=project(p);ctx.fillStyle=originals.has(key(p))?colors.teal:colors.accent;const a=Math.max(2,z*.44);ctx.fillRect(x-a/2,y-a/2,a,a);}piece.starts.forEach((p,i)=>{const [x,y]=project(p);ctx.fillStyle=i?colors.accent:colors.teal;ctx.strokeStyle=colors.panel;ctx.lineWidth=2;ctx.beginPath();const r=Math.max(6,z*.34);if(i)ctx.rect(x-r,y-r,2*r,2*r);else ctx.arc(x,y,r,0,Math.PI*2);ctx.fill();ctx.stroke();if(z>12){ctx.fillStyle=colors.panel;ctx.font='bold 12px system-ui';ctx.textAlign='center';ctx.fillText(i?'B':'A',x,y+4);}});}
 ctx.fillStyle=colors.muted;ctx.font='12px system-ui';ctx.textAlign='left';ctx.fillText(`North ↑ · ${z.toFixed(2)} px / cell · exact coordinates`,16,25);
 const mini=canvasSize($('host-mini')),mx=x=>10+x/1431*(mini.w-20),my=y=>mini.h-10-y/13*(mini.h-20);mini.ctx.fillStyle=colors.pale;mini.ctx.fillRect(0,0,mini.w,mini.h);mini.ctx.strokeStyle=colors.muted;mini.ctx.lineWidth=1;if(typeof Path2D!=='undefined'){
  if(!hostView.miniPath||hostView.miniSize!==`${mini.w},${mini.h}`){const path=new Path2D();hdata.cells.forEach((p,i)=>{for(const j of hostView.g.adjacent[i])if(j>i){path.moveTo(mx(p[0]),my(p[1]));path.lineTo(mx(hdata.cells[j][0]),my(hdata.cells[j][1]));}});hostView.miniPath=path;hostView.miniSize=`${mini.w},${mini.h}`;}
  mini.ctx.stroke(hostView.miniPath);
 }else{mini.ctx.beginPath();hdata.cells.forEach((p,i)=>{for(const j of hostView.g.adjacent[i])if(j>i){mini.ctx.moveTo(mx(p[0]),my(p[1]));mini.ctx.lineTo(mx(hdata.cells[j][0]),my(hdata.cells[j][1]));}});mini.ctx.stroke();}
 mini.ctx.strokeStyle=colors.accent;mini.ctx.lineWidth=2;const a=mx(cx-w/2/z),b=mx(cx+w/2/z);mini.ctx.strokeRect(a,3,b-a,mini.h-6);
}
function stopCamera(settle=false){if(settle)cameraMotion?.finish();else cameraMotion?.cancel();cameraMotion=null;cameraGoal=null;if($('host-canvas'))$('host-canvas').dataset.moving='false';}
function moveHost(target,{duration=360,flight=false}={}){
 cameraMotion?.cancel();const from={cx:hostView.cx,cy:hostView.cy,z:hostView.z};cameraGoal=target;
 const r=$('host-canvas').getBoundingClientRect(),travel=Math.min(from.z,target.z,Math.max(.2,r.width/(Math.abs(target.cx-from.cx)+r.width/Math.min(from.z,target.z))));
 const moving=motionAllowed()&&!$('host').hidden&&Object.keys(from).some(k=>Math.abs(from[k]-target[k])>1e-8);
 $('host-canvas').dataset.moving=String(moving);
 cameraMotion=animate({duration:moving?duration:0,update:t=>{
  hostView.cx=mix(from.cx,target.cx,t);hostView.cy=mix(from.cy,target.cy,t);
  hostView.z=flight&&travel<Math.min(from.z,target.z)*.8?(t<.5?Math.exp(mix(Math.log(from.z),Math.log(travel),smooth(t*2))):Math.exp(mix(Math.log(travel),Math.log(target.z),smooth((t-.5)*2)))):Math.exp(mix(Math.log(from.z),Math.log(target.z),t));
  if(t===1)Object.assign(hostView,target);hostDraw();
 },complete:()=>{$('host-canvas').dataset.moving='false';cameraGoal=null;}});
}
function fitHost(piece=null){const cells=piece?piece.cells:assets.host.cells,xs=cells.map(p=>p[0]),ys=cells.map(p=>p[1]),r=$('host-canvas').getBoundingClientRect();
 moveHost({cx:(Math.min(...xs)+Math.max(...xs))/2,cy:(Math.min(...ys)+Math.max(...ys))/2,z:Math.min((r.width-50)/(Math.max(...xs)-Math.min(...xs)+2),(r.height-65)/(Math.max(...ys)-Math.min(...ys)+2))},{duration:720,flight:true});
}
function zoomHost(f,at=null){const r=$('host-canvas').getBoundingClientRect(),from=cameraGoal||hostView,z=from.z,nz=Math.max(.2,Math.min(75,z*f)),target={cx:from.cx,cy:from.cy,z:nz};if(at){const dx=at[0]-r.width/2,dy=at[1]-r.height/2;target.cx+=dx/z-dx/nz;target.cy-=dy/z-dy/nz;}moveHost(target,{duration:260});}
function panHost(dx,dy){const from=cameraGoal||hostView;moveHost({cx:from.cx+dx/from.z,cy:from.cy+dy/from.z,z:from.z});}
function pieceInfo(){const p=hostView.piece;$('host-piece-info').innerHTML=p?`<h2>${p.id} · from ${p.instance_id}</h2><p>Attachment method: ${p.method.kind==='cut'?'unused-cut stretching':'clean boundary gate'}. Highlighted cells come directly from this fragment’s canonical local coordinates plus its global offset.</p><p class="small">${p.cells.length} fragment cells. Saved starts A (${p.starts[0]}), B (${p.starts[1]}), port (${p.port}). These are recorded fragment starts; choosing a protected witness depends on the controller and proof branch.</p><p class="small">Teal cells: original gadget images. Rust cells: added local corridors. A is a circle; B is a square. Provenance: ${p.provenance.map(x=>`${esc(x.leaf_id)} / ${esc(x.normalizer)}`).join('; ')}.</p><div class="source">${sourceHTML('host')}</div>`:'<h2>All 172 fragments</h2><p>The construction has 2792 fragment cells, 990 stalk cells and 1430 rail cells. The long, thin layout follows the released coordinates. Select a fragment for legible cell-level inspection.</p><p class="small">The overview compresses the horizontal and vertical axes independently to make the full rail readable; the main view uses equal scales.</p>';}
function setupHost(){try{const g=checkHost(assets.host.cells);hostView={g,cx:45,cy:6,z:9,piece:null};$('host-check').textContent='Validated before rendering: 5212 vertices · 5211 induced edges · connected tree · maximum degree 3.';}catch(e){$('host-check').textContent=e.message;$('host-canvas').hidden=true;return;}
 $('host-piece').innerHTML='<option value="all">Entire host</option>'+assets.host.pieces.map(p=>`<option value="${p.id}">${p.id} · ${p.instance_id}</option>`).join('');$('host-piece').onchange=e=>{hostView.piece=assets.host.pieces.find(p=>p.id===e.target.value)||null;pieceInfo();enter($('host-piece-info'));if(hostView.piece)fitHost(hostView.piece);else fitHost();};pieceInfo();
 $('host-fit').onclick=()=>{hostView.piece=null;$('host-piece').value='all';pieceInfo();fitHost();};$('host-piece-fit').onclick=()=>fitHost(hostView.piece);$('host-plus').onclick=()=>zoomHost(1.5);$('host-minus').onclick=()=>zoomHost(1/1.5);$('host-left').onclick=()=>panHost(-120,0);$('host-right').onclick=()=>panHost(120,0);
 const canvas=$('host-canvas');let drag=null;canvas.onpointerdown=e=>{if(e.button!==undefined&&e.button!==0)return;stopCamera();drag=[e.clientX,e.clientY,hostView.cx,hostView.cy];canvas.setPointerCapture(e.pointerId);};canvas.onpointermove=e=>{if(!drag)return;hostView.cx=drag[2]-(e.clientX-drag[0])/hostView.z;hostView.cy=drag[3]+(e.clientY-drag[1])/hostView.z;hostDraw();};canvas.onpointerup=()=>drag=null;canvas.onpointercancel=()=>drag=null;canvas.onlostpointercapture=()=>drag=null;
 canvas.addEventListener('wheel',e=>{e.preventDefault();const r=canvas.getBoundingClientRect();zoomHost(e.deltaY<0?1.15:1/1.15,[e.clientX-r.left,e.clientY-r.top]);},{passive:false});
 canvas.onkeydown=e=>{if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','=','-','Home'].includes(e.key))e.preventDefault();if(e.key==='Home')fitHost();else if(e.key==='+'||e.key==='=')zoomHost(1.5);else if(e.key==='-')zoomHost(1/1.5);else{const delta={ArrowLeft:[-100,0],ArrowRight:[100,0],ArrowUp:[0,100],ArrowDown:[0,-100]}[e.key];if(delta)panHost(...delta);}};
 $('host-mini').onpointerdown=e=>{const r=$('host-mini').getBoundingClientRect();moveHost({cx:Math.max(0,Math.min(1431,(e.clientX-r.left-10)/(r.width-20)*1431)),cy:hostView.cy,z:hostView.z},{duration:600,flight:true});};window.addEventListener('resize',()=>{stopCamera(true);hostView.miniPath=null;hostDraw();});
}
function setupPaper(){const config=assets.config;$('publication-links').innerHTML='<h3>Publication destinations</h3>'+[['repository_url','GitHub repository'],['arxiv_url','arXiv'],['doi_url','DOI'],['journal_url','Journal']].map(([k,name])=>`<p class="small" style="margin-bottom:8px">${name}: ${config[k]?`<a href="${esc(config[k])}">${esc(config[k])}</a>`:'<strong>not yet set</strong>'}</p>`).join('');$('copy-citation').onclick=async()=>{try{await navigator.clipboard.writeText($('bibtex').textContent);$('copy-citation').textContent='Copied';}catch{$('copy-citation').textContent='Select the BibTeX text to copy';}};}
try{
 const paths={examples:'data/examples.json',family:'data/family.json',host:'data/host.json',realization:'data/realization.json',claims:'claims.json',config:'config.json'};
 const results=await Promise.all(Object.entries(paths).map(async([name,url])=>{const r=await fetch(url);if(!r.ok)throw Error(`${url}: HTTP ${r.status}`);return [name,await r.json()];}));assets=Object.fromEntries(results);claims=new Map(assets.claims.components.map(c=>[c.id,c]));
 document.querySelectorAll('[data-source]').forEach(el=>el.innerHTML=sourceHTML(el.dataset.source));
 const hero=assets.examples.presets[0];renderGrid('hero-grid',hero.cells,hero.starts.map(p=>[hero.cells.findIndex(v=>key(v)===key(p)),0]),{label:'Exact seven-cell U trap for A-star; initially separated agents A and B.'});
 setupSim();setupCapacity();setupPeriods();setupThree();setupTests();setupHost();setupPaper();route();document.documentElement.dataset.ready='true';
}catch(e){$('load-error').hidden=false;$('load-error').textContent=`Interactive canonical assets could not be loaded: ${e.message}. Serve the built site over HTTP and check the data/ files. The canonical paper and reproduction commands remain available.`;document.querySelectorAll('main button,main input,main select,main textarea').forEach(x=>x.disabled=true);}
