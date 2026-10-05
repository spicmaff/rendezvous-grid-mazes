// A dependency-free DOM smoke harness, NOT browser rendering/visual QA.
import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
const root=new URL('../',import.meta.url),html=readFileSync(new URL('site/index.html',root),'utf8');
class Element{
 constructor(attrs={}){this.attrs=attrs;this.id=attrs.id;this.dataset=Object.fromEntries(Object.entries(attrs).filter(([k])=>k.startsWith('data-')).map(([k,v])=>[k.slice(5),v]));this.value='';this.hidden='hidden'in attrs;this.disabled=false;this.textContent='';this._html='';this.checked=false;this.hash=attrs.href?.startsWith('#')?attrs.href:'';}
 set innerHTML(v){this._html=v;}get innerHTML(){return this._html;}
 setAttribute(k,v){this.attrs[k]=v;}removeAttribute(k){delete this.attrs[k];}
 querySelectorAll(selector){return parse(this._html).filter(x=>selector==='button'?x.tag==='button':false);}
 querySelector(selector){if(selector==='h1')return {textContent:this.title};return null;}
 getBoundingClientRect(){return {width:1000,height:460,left:0,top:0};}
 addEventListener(){}getContext(){return new Proxy({}, {get:()=>()=>{},set:()=>true});}
}
function parse(t){return [...t.matchAll(/<(\w+)([^>]+)>/g)].map(m=>{const attrs={};for(const a of m[2].matchAll(/([\w-]+)(?:="([^"]*)")?/g))attrs[a[1]]=a[2]??'';const el=new Element(attrs);el.tag=m[1];return el;});}
test('Actual UI module loads all canonical views and responds to core controls in a minimal DOM harness',async()=>{
 const elements=parse(html),byid=new Map(elements.filter(x=>x.id).map(x=>[x.id,x]));
 const pages=elements.filter(x=>x.tag==='section'&&x.attrs.class==='page');for(const p of pages){const chunk=html.slice(html.indexOf(`<section id="${p.id}"`));p.title=chunk.match(/<h1[^>]*>([^<]+)/)?.[1]||p.id;}
 const nav=elements.filter(x=>x.tag==='a'&&x.hash&&pages.some(p=>x.hash==='#'+p.id));
 globalThis.document={documentElement:{dataset:{}},getElementById:id=>byid.get(id),querySelector:s=>pages.find(p=>s==='section.page#'+p.id),querySelectorAll:s=>s==='section.page'?pages:s==='nav a'?nav:s==='[data-source]'?elements.filter(x=>'source'in x.dataset):s.startsWith('main button')?elements.filter(x=>['button','input','select','textarea'].includes(x.tag)):[]};
 globalThis.CSS={escape:x=>x};globalThis.matchMedia=()=>({matches:false});globalThis.location={hash:'#overview'};globalThis.window={addEventListener(){},scrollTo(){}};globalThis.getComputedStyle=()=>({getPropertyValue:()=> '#fff'});globalThis.devicePixelRatio=1;
 for(const [id,value] of Object.entries({'period-s':'3','period-n':'8','capacity-s':'2','speed':'350','test-size':'all','test-type':'all'}))byid.get(id).value=value;
 globalThis.fetch=async url=>({ok:true,json:async()=>JSON.parse(readFileSync(new URL(url.startsWith('data/')?'site/'+url:'public/'+url,root)))});
 await import('../site/app.mjs');assert.equal(document.documentElement.dataset.ready,'true',byid.get('load-error').textContent);assert.equal(byid.get('load-error').hidden,true);
 assert.match(byid.get('sim-status').textContent,/Integer time 0/);for(let i=0;i<4;i++)byid.get('step').onclick();assert.match(byid.get('sim-status').textContent,/preperiod 2, period 2/);
 byid.get('reset').onclick();assert.match(byid.get('sim-status').textContent,/Integer time 0/);byid.get('state-count').onchange({target:{value:'1'}});assert.match(byid.get('preset-kind').textContent,/Illustrative/);
 byid.get('period-s').value='100000000000000000000';byid.get('period-n').value='8';byid.get('period-calculate').onclick();assert.equal(byid.get('period-result').textContent,'799999999999999999998');
 byid.get('nand-buttons').onclick({target:{dataset:{bits:'11'}}});assert.match(byid.get('nand-status').textContent,/impossible/);assert.equal(byid.get('nand-step').disabled,true);
 byid.get('test-selected').checked=true;byid.get('test-selected').oninput();assert.match(byid.get('test-count').textContent,/Showing 44/);assert.match(byid.get('host-check').textContent,/Validated before rendering/);
 byid.get('host-piece').onchange({target:{value:'UP001'}});assert.match(byid.get('host-piece-info').innerHTML,/UP001/);
});
