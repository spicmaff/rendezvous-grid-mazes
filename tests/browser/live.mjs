// MIT. Optional live Chromium QA; dependencies and evidence stay outside the source tree.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {initialize,step,pairRun,distance} from '../../site/model.mjs';
const require=createRequire(import.meta.url);
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const out=path.resolve(process.env.BROWSER_QA_OUTPUT||path.join(root,'../browser-qa'));
assert(!out.startsWith(root+path.sep),'Evidence must be outside repository source');
const base=new URL(process.env.SHOWCASE_URL);
assert(base.protocol==='https:'||(process.env.LOCAL_BROWSER_QA==='1'&&base.protocol==='http:'&&['127.0.0.1','localhost'].includes(base.hostname)),'HTTPS required except explicit loopback preflight');
const sha=execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim();
const digest=b=>createHash('sha256').update(b).digest('hex');
const read=async p=>JSON.parse(await fs.readFile(path.join(root,p),'utf8'));
const examples=await read('site/data/examples.json'),family=await read('site/data/family.json');
const realization=await read('site/data/realization.json');
const evidence={commit:sha,url:base.href,started_at:new Date().toISOString(),status:'RUNNING',checks:[],screenshots:[],assets:[],console:[],exceptions:[],runtime_requests:[],failed_requests:[],bad_responses:[],external_requests:[],layouts:[]};
await fs.mkdir(path.join(out,'screenshots'),{recursive:true});
const record=(name,detail={})=>{evidence.checks.push({name,status:'PASS',...detail});console.log('PASS_BROWSER_CHECK',name);};
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function fetchBytes(url){const r=await fetch(url);assert.equal(r.status,200,url.href||url);return Buffer.from(await r.arrayBuffer());}
async function allFiles(dir){const list=[];for(const item of await fs.readdir(dir,{withFileTypes:true})){const p=path.join(dir,item.name);list.push(...(item.isDirectory()?await allFiles(p):[p]));}return list.sort();}
let browser;
try{
 // Wait for CDN publication of the current HTML, then verify every deployed build byte.
 const expected=await fs.readFile(path.join(root,'dist/index.html'));let current;
 for(let attempt=0;attempt<20;attempt++){
  const u=new URL(base);u.searchParams.set('qa_commit',sha);u.searchParams.set('qa_attempt',String(attempt));
  current=await fetchBytes(u);if(current.equals(expected))break;
  await delay(2000);
 }
 assert(current.equals(expected),'Deployed HTML differs from checked-out commit');
 const files=await allFiles(path.join(root,'dist'));let cursor=0;
 await Promise.all(Array.from({length:6},async()=>{while(cursor<files.length){const p=files[cursor++],rel=path.relative(path.join(root,'dist'),p).split(path.sep).join('/');const bytes=await fs.readFile(p),remote=await fetchBytes(new URL(rel,base));assert(remote.equals(bytes),'Deployed byte mismatch: '+rel);evidence.assets.push({path:rel,bytes:bytes.length,sha256:digest(bytes),status:200});}}));
 evidence.assets.sort((a,b)=>a.path.localeCompare(b.path));record('all-deployed-files-byte-identical',{count:files.length});
 browser=await chromium.launch();evidence.browser=browser.version();evidence.playwright=require(path.join(path.dirname(require.resolve(process.env.PLAYWRIGHT_MODULE||'playwright')),'package.json')).version;
 const routes=['overview','simulator','geometry','periods','hierarchy','three','tests','host','reproduce','paper'];
 async function makePage(options,label){const context=await browser.newContext(options),page=await context.newPage();page.setDefaultTimeout(15000);
  page.on('console',m=>{if(['error','warning'].includes(m.type()))evidence.console.push({context:label,type:m.type(),message:m.text()});});
  page.on('pageerror',e=>evidence.exceptions.push({context:label,message:e.message}));
  page.on('requestfailed',r=>evidence.failed_requests.push({context:label,url:r.url(),error:r.failure()?.errorText}));
  page.on('response',r=>{if(r.status()>=400)evidence.bad_responses.push({context:label,url:r.url(),status:r.status()});});
  page.on('request',r=>{evidence.runtime_requests.push({context:label,url:r.url(),type:r.resourceType()});if(new URL(r.url()).origin!==base.origin)evidence.external_requests.push({context:label,url:r.url()});});
  await page.goto(base.href);await page.waitForFunction(()=>document.documentElement.dataset.ready==='true');
  assert(await page.locator('#load-error').isHidden());return {context,page};
 }
 async function layout(page,label){const data=await page.evaluate(()=>({viewport:{width:innerWidth,height:innerHeight},width:document.documentElement.scrollWidth,overflow:Array.from(document.querySelectorAll('body *')).filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.right>innerWidth+1&&!e.closest('nav,.table-scroll,.comparison-scroll');}).slice(0,12).map(e=>({tag:e.tagName,id:e.id,class:e.className?.baseVal??e.className}))}));evidence.layouts.push({context:label,...data});assert(data.width<=data.viewport.width+1,`${label} whole-page overflow: ${JSON.stringify(data)}`);}
 async function settled(page,id='host-canvas'){await page.waitForFunction(id=>document.getElementById(id).dataset.moving!=='true',id);}
 async function shot(page,name,fullPage=true){await page.waitForFunction(()=>document.getAnimations().every(a=>a.playState!=='running'));if(await page.locator('#host').isVisible())await settled(page);await page.screenshot({path:path.join(out,'screenshots',name+'.png'),fullPage});evidence.screenshots.push(name+'.png');}
 async function route(page,id){await page.locator(`nav a[href="#${id}"]`).click();await page.waitForFunction(id=>!document.getElementById(id).hidden,id);assert.equal(await page.locator('section.page:visible').count(),1);assert(await page.locator('#'+id+' h1').isVisible());}
 const desktop=await makePage({viewport:{width:1440,height:900},colorScheme:'light'},'desktop-light');
 const p=desktop.page;
 const runtime=await p.evaluate(()=>[document.querySelector('script[type=module]').src,document.querySelector('link[rel=stylesheet]').href]);
 for(const url of runtime){const u=new URL(url),file=u.pathname.split('/').at(-1),bytes=await fs.readFile(path.join(root,'dist',file));assert.equal(u.searchParams.get('v'),digest(bytes).slice(0,16));assert((await fetchBytes(u)).equals(bytes));}
 assert.equal(await p.locator('#sim-grid .agent').count(),2);record('content-versioned-runtime-cache-refresh',{runtime});
 for(const id of routes){await route(p,id);await layout(p,'desktop-'+id);await shot(p,'desktop-'+id);}
 record('all-ten-desktop-views',{routes,viewport:{width:1440,height:900}});
 // Compare every visible position/state/time slice with the released Python-derived fixture traces.
 await route(p,'simulator');
 for(const preset of examples.presets){await p.locator('#preset').selectOption(preset.id);
  assert((await p.locator('#preset-kind').innerText()).includes('both initial states 0'));
  const run=initialize(preset.cells,preset.table,preset.starts);assert.deepEqual(pairRun(preset.cells,preset.table,preset.starts),preset.replay);
  while(true){const metrics=await p.locator('#agent-metrics .metric').allTextContents();assert.equal(metrics.length,2);
   metrics.forEach((text,i)=>{assert(text.includes('q='+run.tags[i][1]),`${preset.id}: state at t=${run.time}`);assert(text.includes('cell ('+preset.cells[run.tags[i][0]].join(',')+')'),`${preset.id}: position at t=${run.time}`);});
   const status=await p.locator('#sim-status').innerText();
   if(run.status==='success')assert(status.includes('Rendezvous at integer time '+run.time));
   else if(run.status==='cycle')assert(status.includes(`preperiod ${run.preperiod}, period ${run.period}`));
   else assert(status.includes('Integer time '+run.time+' ·'));
   if(run.status!=='running')break;await p.locator('#step').click();step(run);
  }
  await p.locator('#reset').click();assert((await p.locator('#sim-status').innerText()).includes('Integer time 0'));
  record('preset-trace-'+preset.id,{terminal:run.status,time:run.time});
 }
 // Read the visible SVG transforms: both copies must share one interpolation fraction.
 await p.locator('#preset').selectOption('astar-u');await p.locator('#reset').click();
 const points=()=>p.locator('#sim-grid .agent').evaluateAll(nodes=>nodes.map(a=>{const m=a.transform.baseVal.consolidate().matrix;return {x:m.e,y:m.f,tx:+a.dataset.x,ty:+a.dataset.y,cell:+a.dataset.cell,q:+a.dataset.state};}));
 const initial=await points();await p.locator('#step').click();
 await p.waitForFunction(()=>document.getElementById('sim-grid').dataset.moving==='true');
 const sample=await p.evaluate(()=>new Promise(resolve=>setTimeout(()=>{resolve([...document.querySelectorAll('#sim-grid .agent')].map(a=>{const m=a.transform.baseVal.consolidate().matrix;return {x:m.e,y:m.f,tx:+a.dataset.x,ty:+a.dataset.y};}));},100)));
 const fractions=sample.map((a,i)=>Math.hypot(a.x-initial[i].x,a.y-initial[i].y)/Math.hypot(a.tx-initial[i].x,a.ty-initial[i].y));
 assert(fractions.every(t=>t>0&&t<1),'An actual intermediate position must be visible');assert(Math.abs(fractions[0]-fractions[1])<1e-9,'A and B must move synchronously');
 await settled(p,'sim-grid');const end=await points();end.forEach(a=>{assert.equal(a.x,a.tx);assert.equal(a.y,a.ty);});
 assert.equal(await p.locator('#transition-table td[data-agents="A"],#transition-table td[data-agents="AB"]').count(),1);assert.equal(await p.locator('#transition-table td[data-agents="B"],#transition-table td[data-agents="AB"]').count(),1);
 await p.locator('#step').click();await p.locator('#reset').click();await p.waitForTimeout(450);assert.deepEqual(await points(),initial);assert.equal(await p.locator('#sim-grid').getAttribute('data-moving'),'false');
 await p.locator('#speed').selectOption('350');await p.locator('#run').click();await p.waitForFunction(()=>document.getElementById('sim-grid').dataset.moving==='true');await p.locator('#run').click();await settled(p,'sim-grid');const paused=await points();await p.waitForTimeout(450);assert.deepEqual(await points(),paused);
 record('synchronous-svg-interpolation-exact-endpoints-reset-and-pause',{fractions});
 await p.locator('#preset').selectOption('astar-u');await p.locator('#speed').selectOption('900');await p.locator('#run').click();assert.equal(await p.locator('#run').innerText(),'Pause');await p.locator('#run').click();assert.equal(await p.locator('#run').innerText(),'Run');await p.locator('#reset').click();
 await p.locator('#speed').selectOption('100');await p.locator('#run').click();await p.waitForFunction(()=>document.getElementById('sim-status').textContent.includes('exact product cycle'));await p.locator('#reset').click();record('run-pause-reset-cycle');
 await p.locator('#start-b').selectOption('0,1');assert((await p.locator('#sim-status').innerText()).includes('Rendezvous at integer time 0'));record('time-zero-adjacency');
 await p.locator('#preset').selectOption('toy-line');await p.locator('#simulator summary').filter({hasText:'Edit the induced maze cells'}).click();
 await p.locator('#cells').fill('0,0\n1,0\n2,0');await p.locator('#apply-cells').click();assert.equal(await p.locator('#sim-error').innerText(),'');assert((await p.locator('#preset-kind').innerText()).includes('Illustrative'));
 await p.locator('#start-b').selectOption('2,0');await p.locator('#step').click();assert((await p.locator('#sim-status').innerText()).includes('Rendezvous at integer time 1'));
 await p.locator('#transition-table select[data-q="0"][data-m="2"][data-part="1"]').selectOption('1');assert((await p.locator('#sim-status').innerText()).includes('Integer time 0'));
 assert((await p.locator('#agent-metrics').innerText()).includes('A · q=0'));assert((await p.locator('#agent-metrics').innerText()).includes('B · q=0'));
 const directions=await p.locator('#transition-table select[data-part="0"] option').allTextContents();assert(directions.every(x=>'NESW'.includes(x)));record('maze-table-edit-state-zero-compulsory-actions');
 await route(p,'geometry');for(const s of ['1','2','3','4']){await p.locator('#capacity-s').selectOption(s);await p.locator('#capacity-step').click();assert((await p.locator('#capacity-message').innerText()).includes('≤ '+s));}await p.locator('#capacity-reset').click();record('support-capacity-controls');
 await route(p,'periods');for(const [s,n,result] of [['3','8','22'],['4','7','24'],['100000000000000000000','2','200000000000000000000']]){await p.locator('#period-s').fill(s);await p.locator('#period-n').fill(n);await p.locator('#period-calculate').click();assert.equal(await p.locator('#period-result').innerText(),result);}
 await p.locator('#period-step').click();await p.locator('#period-reset').click();await p.locator('#period-s').fill('1');await p.locator('#period-calculate').click();assert((await p.locator('#period-error').innerText()).length>0);record('sharp-period-bigint-and-invalid-input');
 await route(p,'three');const three=await p.locator('#three').innerText();assert(three.includes('Universal three-state path rendezvous remains open'));assert(three.includes('Cycle realization ≠ accessibility from state 0'));
 const nand=realization.examples.find(x=>x.id==='saturated_nand8');
 for(const bits of ['00','01','10']){await p.locator(`[data-bits="${bits}"]`).click();assert((await p.locator('#nand-status').innerText()).includes('exact released witness'));await p.locator('#nand-step').click();assert((await p.locator('#nand-status').innerText()).includes(`vertex ${nand.word[1]}, state ${nand.witnesses[bits][1]}`));}
 await p.locator('[data-bits="11"]').click();assert((await p.locator('#nand-status').innerText()).includes('impossible'));assert(await p.locator('#nand-step').isDisabled());await p.locator('[data-bits="00"]').click();
 await p.getByRole('link',{name:'Replay the accessible completion',exact:true}).click();await p.waitForFunction(()=>document.getElementById('preset').value==='basin-good');await route(p,'three');await p.getByRole('link',{name:'Replay the inaccessible completion',exact:true}).click();await p.waitForFunction(()=>document.getElementById('preset').value==='basin-bad');record('three-state-positive-negative-nand-and-basins');
 await route(p,'tests');assert((await p.locator('#tests').innerText()).includes('44 is optimal only inside the fixed 144 candidates'));assert.equal(await p.locator('#test-gallery button').count(),144);
 await p.locator('#test-selected').check();assert.equal(await p.locator('#test-gallery button').count(),44);await p.locator('#test-selected').uncheck();
 await p.locator('#test-search').fill('H091');assert.equal(await p.locator('#test-gallery button').count(),1);await p.locator('#test-gallery button').click();assert.equal(await p.locator('#test-detail h2').innerText(),'H091');await p.locator('#test-search').fill('no-such-candidate');assert.equal(await p.locator('#test-gallery button').count(),0);assert.equal(await p.locator('#test-detail h2').innerText(),'No matching test');await p.locator('#test-search').fill('');assert.equal(await p.locator('#test-search').evaluate(e=>e===document.activeElement),true);
 for(const id of ['H001','H144']){await p.locator(`#test-gallery button[data-id="${id}"]`).click();assert.equal(await p.locator('#test-detail h2').innerText(),id);}
 await p.locator('#test-size').selectOption('7');assert((await p.locator('#test-gallery button').count())<144);await p.locator('#test-size').selectOption('all');await p.locator('#test-type').selectOption('tree');assert((await p.locator('#test-gallery button').count())<144);await p.locator('#test-type').selectOption('all');record('candidate-search-selection-filters-detail');
 await route(p,'host');assert((await p.locator('#host-check').innerText()).includes('5212 vertices · 5211 induced edges'));assert((await p.locator('#host').innerText()).includes('Neither exact minimum is known'));
 async function canvasHash(page){await settled(page);return digest(await page.locator('#host-canvas').screenshot());}
 await p.locator('#host-piece').selectOption({index:1});await settled(p);
 const camera=()=>p.locator('#host-canvas').evaluate(el=>({x:+el.dataset.cx,y:+el.dataset.cy,z:+el.dataset.zoom}));
 const cameraStart=await camera();await p.locator('#host-piece').selectOption({index:172});
 await p.waitForFunction(()=>document.getElementById('host-canvas').dataset.moving==='true');await p.waitForTimeout(100);const cameraMid=await camera();await settled(p);const cameraEnd=await camera();
 assert(cameraMid.x>Math.min(cameraStart.x,cameraEnd.x)&&cameraMid.x<Math.max(cameraStart.x,cameraEnd.x));assert(cameraEnd.z>cameraMid.z,'Long travel must zoom back in to the exact selected fragment');
 await p.locator('#host-plus').click();await p.locator('#host-fit').click();await settled(p);assert.equal(await p.locator('#host-piece').inputValue(),'all');
 record('camera-interpolation-long-flight-and-interruption',{cameraStart,cameraMid,cameraEnd});
 await p.locator('#host-fit').click();await shot(p,'desktop-host-overview');let before=await canvasHash(p);await p.locator('#host-plus').click();assert.notEqual(await canvasHash(p),before);await p.locator('#host-minus').click();
 await p.locator('#host-piece').selectOption({index:1});await shot(p,'desktop-host-fragment');await p.locator('#host-piece-fit').click();before=await canvasHash(p);await p.locator('#host-right').click();assert.notEqual(await canvasHash(p),before);await p.locator('#host-left').click();
 await p.locator('#host-canvas').press('ArrowDown');await p.locator('#host-canvas').press('+');await p.locator('#host-canvas').press('-');await p.locator('#host-canvas').press('Home');
 const box=await p.locator('#host-canvas').boundingBox();await p.mouse.move(box.x+box.width/2,box.y+box.height/2);await p.mouse.down();await p.mouse.move(box.x+box.width/2-80,box.y+box.height/2-30,{steps:6});await p.mouse.up();
 await p.mouse.wheel(0,-200);await p.locator('#host-mini').click({position:{x:120,y:35}});await p.locator('#host-fit').click();record('host-fit-zoom-pan-drag-minimap-keyboard');
 for(const id of ['reproduce','paper']){await route(p,id);await p.locator('#'+id+' details').first().locator('summary').click();}
 await p.locator('#copy-citation').click();await p.waitForFunction(()=>/Copied|Select the BibTeX/.test(document.getElementById('copy-citation').textContent));record('paper-citation-source-links');
 const paperHref=await p.locator('#paper a').filter({hasText:'Read the canonical PDF'}).getAttribute('href');assert.equal(paperHref,'research/paper/main.pdf');const pdf=await fetchBytes(new URL(paperHref,base));assert(pdf.equals(await fs.readFile(path.join(root,'research/paper/main.pdf'))));record('canonical-pdf-byte-identity',{bytes:pdf.length,sha256:digest(pdf)});
 const mobile=await makePage({viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:1,colorScheme:'light'},'mobile-light');const m=mobile.page;
 for(const id of routes){await route(m,id);await layout(m,'mobile-'+id);if(['overview','simulator','three','tests','host','reproduce'].includes(id))await shot(m,'mobile-'+id);}
 await route(m,'simulator');await m.locator('#step').click();await m.locator('#reset').click();await m.locator('#transition-table select').first().selectOption({index:0});record('mobile-simulator');
 await route(m,'tests');await m.locator('#test-selected').check();assert.equal(await m.locator('#test-gallery button').count(),44);await m.locator('#test-gallery button').first().click();await m.locator('#test-search').fill('H');record('mobile-candidate-controls');
 await route(m,'host');await m.locator('#host-piece').selectOption({index:1});await m.locator('#host-plus').click();await m.locator('#host-minus').click();await m.locator('#host-piece-fit').click();await m.locator('#host-canvas').scrollIntoViewIfNeeded();const mb=await m.locator('#host-canvas').boundingBox();
 // A real Chromium touch sequence; pointer handlers must repaint and release cleanly.
 const cdp=await mobile.context.newCDPSession(m);before=await canvasHash(m);await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:mb.x+mb.width/2,y:mb.y+100}]});await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:mb.x+mb.width/2-40,y:mb.y+130}]});await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});assert.notEqual(await canvasHash(m),before);await m.locator('#host-fit').click();record('mobile-host-touch-pan');
 await route(p,'overview');await p.locator('#theme').click();assert.equal(await p.locator('html').getAttribute('data-theme'),'dark');await shot(p,'desktop-dark-overview');await route(p,'host');await p.locator('#host-piece').selectOption({index:1});await shot(p,'desktop-dark-host');await layout(p,'desktop-dark-host');await p.locator('#theme').click();
 await route(m,'overview');await m.locator('#theme').click();assert.equal(await m.locator('html').getAttribute('data-theme'),'dark');await shot(m,'mobile-dark-overview');record('light-dark-themes');
 await p.emulateMedia({reducedMotion:'reduce'});assert(await p.evaluate(()=>matchMedia('(prefers-reduced-motion: reduce)').matches));await route(p,'simulator');await p.locator('#preset').selectOption('astar-u');await p.locator('#step').click();assert((await p.locator('#sim-status').innerText()).includes('Integer time 1'));await route(p,'host');await p.locator('#host-fit').click();await shot(p,'desktop-reduced-motion-host');assert.equal(await p.locator('#host-canvas').getAttribute('data-moving'),'false');assert.equal(await p.locator('#sim-grid').getAttribute('data-moving'),'false');assert.equal(await p.evaluate(()=>document.getAnimations().filter(a=>a.playState==='running').length),0);record('reduced-motion-interactions');
 // Capture a short real Chromium recording of the finished motion, not a generated mockup.
 const film=await makePage({viewport:{width:1000,height:760},colorScheme:'light',recordVideo:{dir:path.join(out,'video'),size:{width:1000,height:760}}},'motion-film');
 await route(film.page,'simulator');await film.page.locator('#sim-grid').scrollIntoViewIfNeeded();await film.page.locator('#speed').selectOption('900');await film.page.locator('#run').click();await film.page.waitForFunction(()=>document.getElementById('sim-status').textContent.includes('exact product cycle'));await settled(film.page,'sim-grid');await film.page.waitForTimeout(600);
 await route(film.page,'host');await film.page.locator('#host-canvas').scrollIntoViewIfNeeded();await film.page.locator('#host-piece').selectOption({index:1});await settled(film.page);await film.page.locator('#host-piece').selectOption({index:172});await settled(film.page);await film.page.waitForTimeout(600);await film.context.close();record('real-chromium-motion-recording');
 assert.equal(evidence.exceptions.length,0,'Uncaught browser exceptions');assert.equal(evidence.console.filter(x=>x.type==='error').length,0,'Browser console errors');assert.equal(evidence.failed_requests.length,0,'Failed browser requests');assert.equal(evidence.bad_responses.length,0,'HTTP errors in browser');assert.equal(evidence.external_requests.length,0,'Unexpected external runtime request');
 record('console-network-health');await desktop.context.close();await mobile.context.close();evidence.status='PASS_LIVE_CHROMIUM_QA';
}catch(e){evidence.status='FAIL_LIVE_CHROMIUM_QA';evidence.failure={message:e.message,stack:e.stack};process.exitCode=1;console.error(e.stack);}
finally{if(browser)await browser.close();evidence.finished_at=new Date().toISOString();await fs.writeFile(path.join(out,'evidence.json'),JSON.stringify(evidence,null,2)+'\n');console.log(evidence.status,sha);}
