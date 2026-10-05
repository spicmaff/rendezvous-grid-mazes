// MIT. Pure paper-model semantics; directions and bit masks use NESW.
export const DIRS=[[0,1],[1,0],[0,-1],[-1,0]], LETTERS='NESW';
export const key=p=>p.join(',');
export const distance=(a,b)=>Math.abs(a[0]-b[0])+Math.abs(a[1]-b[1]);
export const maskName=m=>[...LETTERS].filter((_,i)=>m&(1<<i)).join('')||'∅';
export function graph(cells){
 if(!Array.isArray(cells)||!cells.length||cells.some(p=>!Array.isArray(p)||p.length!==2||p.some(x=>!Number.isSafeInteger(x))))throw Error('Cells must be integer coordinate pairs.');
 const index=new Map(cells.map((p,i)=>[key(p),i]));if(index.size!==cells.length)throw Error('Duplicate cells.');
 const adjacent=cells.map(([x,y])=>DIRS.map(([dx,dy])=>index.get(key([x+dx,y+dy]))??-1));
 const masks=adjacent.map(a=>a.reduce((m,v,d)=>v<0?m:m|(1<<d),0));
 const seen=new Set([0]),todo=[0];while(todo.length){for(const j of adjacent[todo.pop()])if(j>=0&&!seen.has(j)){seen.add(j);todo.push(j);}}
 return {index,adjacent,masks,connected:seen.size===cells.length,vertices:cells.length,edges:masks.reduce((s,m)=>s+popcount(m),0)/2,max_degree:Math.max(...masks.map(popcount))};
}
function popcount(m){let n=0;while(m){m&=m-1;n++;}return n;}
export function defaultTable(s){return Array.from({length:s},()=>Array.from({length:15},(_,i)=>[DIRS.findIndex((_,d)=>(i+1)&(1<<d)),0]));}
export function validateTable(table){
 const s=table.length;if(!s)throw Error('At least one state required.');
 for(let q=0;q<s;q++){if(table[q].length!==15)throw Error('Every nonempty mask needs a row.');for(let m=1;m<16;m++){const a=table[q][m-1];if(!a||a.length!==2||!Number.isInteger(a[0])||a[0]<0||a[0]>3||!(m&(1<<a[0]))||!Number.isInteger(a[1])||a[1]<0||a[1]>=s)throw Error(`Illegal compulsory move at state ${q}, mask ${maskName(m)}.`);}}
}
export function advance(cells,g,table,tags){
 // Both next tags are calculated from the same old time slice.
 return tags.map(([v,q])=>{const m=g.masks[v];if(!m)throw Error('A singleton has only time-zero success.');const [d,r]=table[q][m-1];if(!(m&(1<<d))||r<0||r>=table.length)throw Error('Illegal compulsory move.');return [g.adjacent[v][d],r];});
}
export function initialize(cells,table,starts){
 const g=graph(cells);if(!g.connected)throw Error('Maze must be connected.');validateTable(table);
 const ids=starts.map(p=>g.index.get(key(p)));if(ids.length!==2||ids.some(i=>i===undefined))throw Error('Both starts must be cells of the maze.');
 const tags=ids.map(v=>[v,0]);return {cells,table,g,tags,time:0,seen:new Map(),status:distance(cells[ids[0]],cells[ids[1]])<=1?'success':'running',preperiod:null,period:null};
}
export function jointKey(tags){return tags.flat().join(':');}
export function step(run){
 if(run.status!=='running')return run;
 run.seen.set(jointKey(run.tags),run.time);run.tags=advance(run.cells,run.g,run.table,run.tags);run.time++;
 if(distance(...run.tags.map(([v])=>run.cells[v]))<=1)run.status='success';
 else if(run.seen.has(jointKey(run.tags))){run.status='cycle';run.preperiod=run.seen.get(jointKey(run.tags));run.period=run.time-run.preperiod;}
 return run;
}
export function pairRun(cells,table,starts){
 const r=initialize(cells,table,starts),trace=[];
 while(r.status==='running'){trace.push([...r.tags.flat(),distance(...r.tags.map(([v])=>cells[v]))]);step(r);}
 return r.status==='success'?{success:true,time:r.time,trace}:{success:false,preperiod:r.preperiod,period:r.period,trace};
}
export function maximumPeriod(s,n){
 s=BigInt(s);n=BigInt(n);if(s<2n||n<2n)throw Error('Use s ≥ 2 and n ≥ 2.');return n===2n?2n*s:n%2n===0n?s*n-2n:s*(n-1n);
}
export function alternatingPath(n){let xy=[[0,0]];for(let i=0;i<n-1;i++){const [x,y]=xy.at(-1);xy.push(i%2?[x,y+1]:[x+1,y]);}return xy;}
export function sharpTable(s,n){
 const F=defaultTable(s),p=s-1;const put=(q,m,d,r)=>F[q][m-1]=[LETTERS.indexOf(d),r];
 if(n===2){for(let q=0;q<s;q++){put(q,2,'E',q);put(q,8,'W',(q+1)%s);}return F;}
 put(0,6,'S',p);put(0,9,'N',1);
 for(let i=1;i<p;i++){put(i,6,'E',i);put(i,9,'W',i+1);}put(p,6,'E',0);put(p,9,'W',0);
 if(p===1)put(0,2,'E',0);else{put(0,2,'E',1);for(let i=2;i<p;i++)put(i,2,'E',i);put(p,2,'E',0);}
 put(0,8,'W',0);for(let i=1;i<p;i++)put(i,8,'W',i+1);put(1,4,'S',p);return F;
}
export function primitiveOrbit(cells,table){let g=graph(cells),tag=[0,0],seen=new Map(),tags=[];while(!seen.has(tag.join(':'))){seen.set(tag.join(':'),tags.length);tags.push(tag);tag=advance(cells,g,table,[tag])[0];}return {tags:tags.slice(seen.get(tag.join(':'))),preperiod:seen.get(tag.join(':'))};}
export function checkHost(cells){const g=graph(cells);if(g.vertices!==5212||g.edges!==5211||!g.connected||g.max_degree!==3)throw Error('Canonical host failed structural validation. Expected 5212 vertices, 5211 edges, connected tree, maximum degree 3.');return {...g,tree:g.connected&&g.edges===g.vertices-1};}
