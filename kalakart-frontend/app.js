// KALAKART tabbed SPA + SHILP AI FastAPI wiring (DB-backed catalog + EN/HI + voice).
function defaultApiBase(){
  try{
    const saved = localStorage.getItem('shilp_api');
    if(saved) return saved.replace(/\/$/, '');
    if(location.protocol === 'file:') return 'http://127.0.0.1:8000';
    const h = location.hostname;
    if(h === 'localhost' || h === '127.0.0.1' || h === '') return 'http://127.0.0.1:8000';
    return location.origin.replace(/\/$/, ''); // live deploy: UI + API same origin
  }catch(e){ return 'http://127.0.0.1:8000'; }
}
let API_BASE = defaultApiBase();
/* backend may return relative /static/... paths — resolve against the gateway */
function imgURL(u){
  if(!u) return '';
  if(/^https?:\/\//i.test(u) || u.startsWith('data:')) return u;
  return API_BASE + (u.startsWith('/') ? u : '/' + u);
}
let lastListing = null, lastPrice = 1250, rawFileBlob = null, lastProductId = 'kk_prod_001';

/* ================= LANGUAGE (EN / HI) ================= */
let LANG = localStorage.getItem('shilp_lang') || 'en';
function applyLang(){
  document.documentElement.lang = LANG === 'hi' ? 'hi' : 'en';
  document.body.classList.toggle('hindi', LANG === 'hi');
  document.querySelectorAll('[data-en]').forEach(el=>{
    const v = LANG === 'hi' ? el.getAttribute('data-hi') : el.getAttribute('data-en');
    if(v != null) el.innerHTML = v;
  });
  document.querySelectorAll('[data-en-ph]').forEach(el=>{
    const v = LANG === 'hi' ? el.getAttribute('data-hi-ph') : el.getAttribute('data-en-ph');
    if(v != null) el.setAttribute('placeholder', v);
  });
  const b = document.getElementById('langBtn');
  if(b) b.textContent = LANG === 'hi' ? 'EN' : 'हिं';
  const mb = document.getElementById('micBtn');
  if(mb && typeof recInt !== 'undefined' && !recInt)
    mb.innerHTML = '🎙 ' + (LANG === 'hi' ? 'रिकॉर्ड करें' : 'Tap to record') + ' <span id="recTime">00:00</span>';
  const s = document.getElementById('setLang');
  if(s) s.value = LANG === 'hi' ? 'hi' : (localStorage.getItem('shilp_lang_full') === 'both' ? 'both' : 'en');
}
function toggleLang(){
  LANG = LANG === 'hi' ? 'en' : 'hi';
  localStorage.setItem('shilp_lang', LANG);
  localStorage.setItem('shilp_lang_full', LANG);
  document.getElementById('pLang').value = LANG;
  applyLang();
}
function setLangFromSelect(v){
  // "both" = keep English UI, assistant answers bilingual
  if(v === 'hi'){ LANG = 'hi'; }
  else if(v === 'en'){ LANG = 'en'; }
  else { localStorage.setItem('shilp_lang_full', 'both'); document.getElementById('pLang').value = 'hi'; return; }
  localStorage.setItem('shilp_lang', LANG);
  localStorage.setItem('shilp_lang_full', v);
  document.getElementById('pLang').value = LANG;
  applyLang();
}
const recLang = () => LANG === 'hi' ? 'hi-IN' : 'en-IN';
function L(hi, en){ return LANG === 'hi' ? hi : en; }

/* ---------- TAB ROUTER (switching, not single page) ---------- */
const TABS = ['home','marketplace','products','listings','orders','assistant','trending','settings'];
function showTab(name){
  if(!TABS.includes(name)) name = 'home';
  document.querySelectorAll('.tab-page').forEach(s=>s.classList.remove('active'));
  const page = document.getElementById('tab-' + name);
  if(page) page.classList.add('active');
  document.querySelectorAll('#sideNav button').forEach(b=>b.classList.toggle('active', b.dataset.tab === name));
  document.body.classList.remove('nav-open');
  try{ location.hash = '#/' + name; }catch(e){}
  document.querySelector('.content').scrollIntoView({behavior:'smooth', block:'start'});
  if(name === 'orders'){ requestAnimationFrame(()=>{ drawCharts(); }); loadOrders(); }
  if(name === 'marketplace'){ loadCatalog(); }
}
document.getElementById('sideNav').addEventListener('click', e=>{
  const b = e.target.closest('button[data-tab]');
  if(b) showTab(b.dataset.tab);
});
(function initRoute(){
  const h = (location.hash || '').replace('#/','').replace('#','');
  if(TABS.includes(h)) showTab(h); else showTab('home');
})();
window.addEventListener('hashchange', ()=>{
  const h = (location.hash || '').replace('#/','');
  if(TABS.includes(h)) showTab(h);
});
function toggleDark(){ document.body.classList.toggle('dark'); }
function topSearchGo(q){
  showTabSilent('marketplace');
  filterMarket(q);
}
function showTabSilent(name){
  document.querySelectorAll('.tab-page').forEach(s=>s.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  document.querySelectorAll('#sideNav button').forEach(b=>b.classList.toggle('active', b.dataset.tab === name));
}

/* ---------- CATALOG DATA (fallback; DB is primary) ---------- */
const cats = [
  {n:"Pottery & Ceramics", img:"https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?w=400&q=60&auto=format&fit=crop"},
  {n:"Textiles & Weaving", img:"https://images.unsplash.com/photo-1558769132-cb1aea458c5e?w=400&q=60&auto=format&fit=crop"},
  {n:"Woodwork & Carving", img:"https://images.unsplash.com/photo-1610701596007-11502861dcfa?w=400&q=60&auto=format&fit=crop"},
  {n:"Paintings & Art", img:"https://images.unsplash.com/photo-1579783902614-a3fb3927b6a5?w=400&q=60&auto=format&fit=crop"},
  {n:"Metalwork & Brass", img:"https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=400&q=60&auto=format&fit=crop"},
  {n:"Bamboo & Natural Fibres", img:"https://images.unsplash.com/photo-1595231776515-ddffb1f4eb73?w=400&q=60&auto=format&fit=crop"},
];
const products = [
  {n:"Terracotta Vase", p:"₹1,300", by:"By Meera Kumbhar", img:"https://images.unsplash.com/photo-1578500494198-246f612d3b3d?w=500&q=60&auto=format&fit=crop", tag:"Trending", cat:"Pottery"},
  {n:"Handwoven Dupatta", p:"₹1,800", by:"Varanasi, UP", img:"https://images.unsplash.com/photo-1583391733956-6c78276477e2?w=500&q=60&auto=format&fit=crop", tag:"Rising", cat:"Textiles"},
  {n:"Brass Diya Set", p:"₹950", by:"Moradabad, UP", img:"https://images.unsplash.com/photo-1602523961358-f9f03dd557db?w=500&q=60&auto=format&fit=crop", tag:"Viral", cat:"Metalwork"},
  {n:"Madhubani Painting", p:"₹2,400", by:"Bihar", img:"https://images.unsplash.com/photo-1579783902614-a3fb3927b6a5?w=500&q=60&auto=format&fit=crop", tag:"Most Saved", cat:"Paintings"},
  {n:"Wooden Carved Box", p:"₹1,600", by:"Saharanpur, UP", img:"https://images.unsplash.com/photo-1610701596007-11502861dcfa?w=500&q=60&auto=format&fit=crop", tag:"Emerging", cat:"Woodwork"},
  {n:"Embroidered Cushion", p:"₹750", by:"Kutch, Gujarat", img:"https://images.unsplash.com/photo-1584100936595-c065efbdec1e?w=500&q=60&auto=format&fit=crop", tag:"New", cat:"Textiles"},
];
const trending = [
  {n:"Blue Pottery", p:"Jaipur • 4.9★", img:"https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?w=500&q=60&auto=format&fit=crop", tag:"+42%"},
  {n:"Handloom Textiles", p:"Varanasi, UP", img:"https://images.unsplash.com/photo-1558769132-cb1aea458c5e?w=500&q=60&auto=format&fit=crop", tag:"Rising"},
  {n:"Terracotta Art", p:"Nandur Community", img:"https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?w=500&q=60&auto=format&fit=crop", tag:"Popular"},
  {n:"Madhubani Paintings", p:"Bihar", img:"https://images.unsplash.com/photo-1579783902614-a3fb3927b6a5?w=500&q=60&auto=format&fit=crop", tag:"Most Saved"},
  {n:"Wood Carvings", p:"Saharanpur, UP", img:"https://images.unsplash.com/photo-1533090161767-e6ffed986c88?w=500&q=60&auto=format&fit=crop", tag:"Emerging"},
  {n:"Brass Home Decor", p:"Moradabad, UP", img:"https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=500&q=60&auto=format&fit=crop", tag:"Viral"},
];
const PRESETS = {
  banarasi: {pName:'Banarasi Silk Saree', pCraft:'Banarasi Silk', pMaterial:'Silk, Zari', pLocation:'Varanasi, UP', pHours:40, pCost:3500, story:'वाराणसी की असली बनारसी साड़ी — शुद्ध रेशम पर सोने-चाँदी की ज़री, 40 घंटे की बुनाई।'},
  pottery: {pName:'Handpainted Blue Pottery Plate', pCraft:'Jaipur Blue Pottery', pMaterial:'Quartz, Glass, Clay', pLocation:'Jaipur, Rajasthan', pHours:8, pCost:400, story:'ये थाली जयपुर की नीली मिट्टी से हाथ से बनाई है, फूल-पत्ती हाथ से पेंट की है।'},
  dokra: {pName:'Bastar Dokra Elephant', pCraft:'Bastar Dokra', pMaterial:'Brass, Clay, Wax', pLocation:'Bastar, Chhattisgarh', pHours:16, pCost:900, story:'बस्तर की 4000 साल पुरानी ढोकरा कला — मोम-साँचे में ढला पीतल का हाथी।'},
};
let dbProducts = [];   // live rows from backend

function cardHTML(p){
  return `<div class="prod-card" onclick="selectProductCard('${p.id || ''}')" style="cursor:pointer;" title="Click to view & export"><img loading="lazy" src="${p.img}" alt="${p.n}" onerror="this.style.display='none'"/><div><span class="badge">◉ ${p.tag||''}</span><br><b>${p.n}</b><br><small>${p.by||p.p||''} ${p.p && p.by?'• '+p.p:''}</small></div></div>`;
}
document.getElementById('catGrid').innerHTML = cats.map(c=>`<div class="cat-card"><img loading="lazy" src="${c.img}" alt="${c.n}" onerror="this.style.display='none'"/><div>${c.n}</div></div>`).join('');
function renderMarket(list){ document.getElementById('marketGrid').innerHTML = list.map(cardHTML).join(''); }
renderMarket(products);
document.getElementById('trendGrid').innerHTML = trending.map(cardHTML).join('');
document.getElementById('artisanGrid').innerHTML = products.slice(0,3).map(cardHTML).join('');

/* ---------- LIVE CATALOG from backend DB ---------- */
function dbToCard(p){
  const name = p.name || p.title_en || 'Handcrafted Craft';
  const priceVal = p.price || p.retail_price || 1250;
  const artName = (typeof p.artisan === 'object' ? p.artisan?.name : p.artisan) || 'Rukmini Devi';
  const loc = p.location || '';
  const img = p.image_url || (p.media && p.media.enhanced_studio_url) || 'https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?w=500';
  const tag = (p.tags && p.tags[0]) || p.craft || p.craft_type || 'GI Certified';
  const cat = p.craft || p.craft_type || '';
  return {
    id: p.id || 'kk_prod_001',
    n: name,
    p: '₹' + Number(priceVal).toLocaleString('en-IN'),
    priceNum: Number(priceVal) || 0,
    by: 'By ' + artName + (loc ? ' • ' + loc : ''),
    artisan: artName,
    location: loc,
    img: imgURL(img),
    tag: tag,
    cat: cat,
    desc: p.description || p.story_en || '',
    rating: p.rating || 4.5,
    reviews: p.reviews_count || 12,
    tags: p.tags || [],
    raw: p
  };
}
async function loadCatalog(){
  try{
    const r = await fetch(API_BASE + '/api/v1/products');
    if(!r.ok) throw 0;
    const j = await r.json();
    if(j.products && j.products.length){
      dbProducts = j.products;
      const list = dbProducts.map(dbToCard);
      renderMarket(list);
      document.getElementById('artisanGrid').innerHTML = list.slice(0, 3).map(cardHTML).join('');
      const note = document.getElementById('dbNote');
      if(note) note.textContent = L('● डेटाबेस से लाइव (' + list.length + ' उत्पाद)', '● live from database (' + list.length + ' products)');
      return true;
    }
  }catch(e){}
  const note = document.getElementById('dbNote');
  if(note) note.textContent = L('○ ऑफ़लाइन — नमूना सूची', '○ offline — sample list');
  return false;
}
/* offline outbox — products created while backend is down sync later */
function getOutbox(){ try{ return JSON.parse(localStorage.getItem('shilp_pending') || '[]'); }catch(e){ return []; } }
function setOutbox(a){ try{ localStorage.setItem('shilp_pending', JSON.stringify(a)); }catch(e){} }
function updateDbNote(){
  const n = document.getElementById('dbNote'); if(!n) return;
  const k = getOutbox().length;
  if(k) n.textContent = L('● ' + k + ' उत्पाद सिंक बाकी', '● ' + k + ' product(s) pending sync');
}
async function flushOutbox(){
  const box = getOutbox(); if(!box.length) return;
  const rest = [];
  for(const p of box){
    try{ const r = await fetch(API_BASE + '/api/v1/products', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(p)});
      if(!r.ok) rest.push(p);
    }catch(e){ rest.push(p); }
  }
  setOutbox(rest); updateDbNote();
  if(!rest.length) loadCatalog();
}
async function saveProductToDB(){
  const payload = {
    name: document.getElementById('pName').value,
    craft: document.getElementById('pCraft').value,
    price: lastPrice || parseFloat(document.getElementById('pCost').value || 0),
    location: document.getElementById('pLocation').value,
    artisan: document.getElementById('pArtisan').value,
    image_url: '', description: document.getElementById('storyText').value,
    tags: lastListing?.tags || ['handmade'], status: 'DRAFT' };
  try{
    const r = await fetch(API_BASE + '/api/v1/products', {method:'POST',
      headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
    if(r.ok){ loadCatalog(); return true; }
    throw 0;
  }catch(e){
    const box = getOutbox(); box.push(payload); setOutbox(box); updateDbNote();
    return false;
  }
}

/* ---------- LIVE ORDERS from backend DB ---------- */
async function loadOrders(){
  try{
    const r = await fetch(API_BASE + '/api/v1/orders');
    if(!r.ok) throw 0;
    const j = await r.json();
    const tb = document.getElementById('ordersBody');
    if(tb && j.orders && j.orders.length){
      tb.innerHTML = j.orders.map(o=>{
        const cls = o.status === 'Shipped' ? 'ship' : o.status === 'Processing' ? 'proc' : 'conf';
        return `<tr><td>${o.product}</td><td>${o.buyer}</td><td>₹${Number(o.amount).toLocaleString('en-IN')}</td><td><span class="st ${cls}">${o.status}</span></td></tr>`;
      }).join('');
      const n = document.getElementById('ordersNote');
      if(n) n.textContent = L('● डेटाबेस से लाइव', '● live from database');
    }
  }catch(e){}
}

function applyPreset(k){
  const p = PRESETS[k]; if(!p) return;
  showTab('products');
  document.getElementById('pName').value = p.pName;
  document.getElementById('pCraft').value = p.pCraft;
  document.getElementById('pMaterial').value = p.pMaterial;
  document.getElementById('pLocation').value = p.pLocation;
  document.getElementById('pHours').value = p.pHours;
  document.getElementById('pCost').value = p.pCost;
  document.getElementById('bCost').value = p.pCost;
  document.getElementById('bHours').value = p.pHours;
  document.getElementById('storyText').value = p.story;
}

function currentMarketList(){
  return dbProducts.length ? dbProducts.map(dbToCard) : products;
}
function filterMarket(q){
  q=(q||'').toLowerCase();
  renderMarket(currentMarketList().filter(p=>(p.n+p.by+p.cat).toLowerCase().includes(q)));
}
document.querySelectorAll('.chips').forEach(bar=>{
  bar.addEventListener('click',e=>{
    if(e.target.tagName==='BUTTON'){
      bar.querySelectorAll('button').forEach(b=>b.classList.remove('active'));
      e.target.classList.add('active');
      const t=e.target.textContent.toLowerCase();
      const list = currentMarketList();
      if(t.includes('all')||t.includes('trending now')) renderMarket(list);
      else renderMarket(list.filter(p=>(p.cat||'').toLowerCase().includes(t.slice(0,4))).length?list.filter(p=>(p.cat||'').toLowerCase().includes(t.slice(0,4))):list);
    }
  });
});

/* ---------- Charts ---------- */
function lineChart(id, data, color){
  const c=document.getElementById(id);
  if(!c) return;
  try{
    const ctx=c.getContext('2d'); const W=c.width=(c.offsetWidth||600)*2; const H=c.height=280;
    ctx.clearRect(0,0,W,H); ctx.strokeStyle=color||'#8b1a22'; ctx.lineWidth=4; ctx.beginPath();
    const max=Math.max(...data), min=Math.min(...data);
    data.forEach((v,i)=>{const x=20+i*(W-40)/(data.length-1); const y=H-20-((v-min)/(max-min||1))*(H-60); i?ctx.lineTo(x,y):ctx.moveTo(x,y);});
    ctx.stroke();
    ctx.lineTo(W-20,H-20); ctx.lineTo(20,H-20); ctx.closePath(); ctx.fillStyle='rgba(139,26,34,.12)'; ctx.fill();
  }catch(e){}
}
function drawCharts(){
  lineChart('salesChart',[12,19,15,26,22,31,28],'#8b1a22');
  lineChart('earnChart',[8,14,11,18,16,24,22],'#c99a2b');
}
drawCharts();

/* ---------- Backend health ---------- */
async function pingBackend(){
  const el = document.getElementById('apiStatus');
  try{
    const r = await fetch(API_BASE + '/api/v1/health', {signal: AbortSignal.timeout(10000)});
    if(r.ok){ el.textContent='● live :8000'; el.classList.add('live');
      const bar = document.getElementById('offlineBar'); if(bar) bar.hidden = true;
      const s=document.getElementById('setStatus'); if(s) s.textContent='✅ Connected to ' + API_BASE;
      loadCatalog(); loadOrders(); flushOutbox();
      return true; }
  }catch(e){}
  el.textContent='● offline (local mode)'; el.classList.remove('live');
  const bar = document.getElementById('offlineBar'); if(bar) bar.hidden = false;
  const s=document.getElementById('setStatus'); if(s) s.textContent='⚠ Offline — check gateway URL & backend running.';
  return false;
}

/* ---------- one-tap diagnostics: tests every AI feature, shows exactly what fails ---------- */
async function runDiagnostics(){
  const box = document.getElementById('diagOut');
  box.innerHTML = '';
  const line = (name, ok, extra)=>{
    box.innerHTML += `<div class="diag ${ok ? 'ok' : 'bad'}">${ok ? '✅' : '❌'} <b>${name}</b><br><small>${extra || ''}</small></div>`;
  };
  const t = async (name, fn)=>{
    try{ const extra = await fn(); line(name, true, extra); return true; }
    catch(e){ line(name, false, (e && e.message) || e); return false; }
  };
  line('Test started', true, API_BASE);
  await t('1 · Gateway reachable', async ()=>{
    const r = await fetch(API_BASE + '/api/v1/health', {signal: AbortSignal.timeout(10000)});
    if(!r.ok) throw new Error('HTTP ' + r.status);
    const j = await r.json();
    return `products=${j.db.products} orders=${j.db.orders}`;
  });
  await t('2 · Photo enhancing (Vision Studio)', async ()=>{
    const f = await makePlaceholderPhoto();
    const fd = new FormData(); fd.append('file', f, 'diag.jpg');
    fd.append('product_name', 'Diag Plate'); fd.append('craft_type', 'Pottery');
    fd.append('material', 'Clay'); fd.append('location', 'Jaipur');
    fd.append('story_text', 'test'); fd.append('language', 'en'); fd.append('artisan', 'Diag');
    const r = await fetch(API_BASE + '/api/v1/media/process-raw', {method:'POST', body: fd, signal: AbortSignal.timeout(90000)});
    if(!r.ok){ let m = 'HTTP ' + r.status; try{ const j = await r.json(); if(j.detail) m = j.detail; }catch(e){} throw new Error(m); }
    const j = await r.json();
    return `engine=${j.studio.engine} title="${j.listing.title_en.slice(0, 40)}"`;
  });
  await t('3 · AI companion (Shilpi)', async ()=>{
    const r = await fetch(API_BASE + '/api/v1/assistant/shilpi', {method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({query: 'namaste, daam kaise rakhen?', lang: 'hi'}), signal: AbortSignal.timeout(30000)});
    if(!r.ok){ let m = 'HTTP ' + r.status; try{ const j = await r.json(); if(j.detail) m = j.detail; }catch(e){} throw new Error(m); }
    const j = await r.json();
    return `${j.engine} → "${j.answer.slice(0, 60)}…"`;
  });
  await t('4 · Bargaining shield', async ()=>{
    const r = await fetch(API_BASE + '/api/v1/pricing/bargain-shield', {method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({material_cost: 400, labour_hours: 8, buyer_offer: 800}), signal: AbortSignal.timeout(15000)});
    if(!r.ok) throw new Error('HTTP ' + r.status);
    return (await r.json()).verdict_code;
  });
  await t('5 · Products database', async ()=>{
    const r = await fetch(API_BASE + '/api/v1/products', {signal: AbortSignal.timeout(10000)});
    if(!r.ok) throw new Error('HTTP ' + r.status);
    return (await r.json()).products.length + ' products';
  });
  line('Done', true, L('सब ✅ = सब काम कर रहा', 'all ✅ = everything works'));
}
pingBackend(); setInterval(pingBackend, 20000);
// slow cold boot (Windows Python can take 10s+) — retry a few times on load
(async function bootRetry(){ for(let i=0;i<4;i++){ const el=document.getElementById('apiStatus'); if(el && el.classList.contains('live')) return; await new Promise(r=>setTimeout(r,4000)); pingBackend(); } })();
function saveApi(){
  const v = document.getElementById('apiInput').value.trim().replace(/\/$/,'');
  localStorage.setItem('shilp_api', v); API_BASE = v; pingBackend();
}
(function(){ const i=document.getElementById('apiInput'); if(i) i.value = API_BASE; })();

/* ---------- Camera / upload ---------- */
const fileInput = document.getElementById('fileInput');
fileInput.addEventListener('change', ()=>{
  const f = fileInput.files[0]; if(!f) return;
  rawFileBlob = f;
  document.getElementById('fileName').textContent = f.name + ' • ' + Math.round(f.size/1024) + ' KB';
  const url = URL.createObjectURL(f);
  const prev = document.getElementById('rawPreview'); prev.src = url; prev.hidden = false;
  document.getElementById('rawBox').innerHTML = `<img src="${url}" class="preview-img" />`;
});
let camStream = null;
async function openCamera(){
  try{
    if(!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia)
      throw new Error(L('यह डिवाइस कैमरा नहीं देता', 'this device has no camera API'));
    camStream = await navigator.mediaDevices.getUserMedia({video:{width:1280, facingMode:'environment'}, audio:false});
    const v = document.getElementById('camVideo'); v.srcObject = camStream; v.hidden = false; await v.play();
    document.getElementById('camRow').hidden = false;
  }catch(e){ alert((LANG === 'hi' ? 'कैमरा नहीं खुला: ' : 'Camera blocked: ') + e.message + (LANG === 'hi' ? ' — गैलरी से अपलोड करें।' : ' — use Upload instead.')); }
}
function closeCamera(){
  if(camStream) camStream.getTracks().forEach(t=>t.stop());
  document.getElementById('camVideo').hidden = true; document.getElementById('camRow').hidden = true;
}
function snapPhoto(){
  const v = document.getElementById('camVideo'), c = document.getElementById('camCanvas');
  c.width = v.videoWidth || 1280; c.height = v.videoHeight || 720;
  c.getContext('2d').drawImage(v, 0, 0);
  c.toBlob(b=>{ rawFileBlob = new File([b], 'capture.jpg', {type:'image/jpeg'});
    const url = URL.createObjectURL(rawFileBlob);
    const prev = document.getElementById('rawPreview'); prev.src = url; prev.hidden = false;
    document.getElementById('rawBox').innerHTML = `<img src="${url}" class="preview-img" />`;
    document.getElementById('fileName').textContent = 'capture.jpg • live camera';
  }, 'image/jpeg', .9);
}

/* ---------- VOICE-TO-TEXT (Web Speech API, speaks YOUR language) ---------- */
function getSR(){
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  return SR ? new SR() : null;
}
/* Tap once to START, tap again to STOP. On stop, speech → English → title/description. */
let activeRec = null, storyNew = false;
function dictateToggle(){
  if(activeRec){ try{ activeRec.stop(); }catch(e){ activeRec = null; stopRecTimer(); } return; }
  const out = document.getElementById('dictateOut');
  const r = getSR();
  if(!r){ out.textContent = L('यह ब्राउज़र आवाज़ नहीं समझता — कृपया लिखें। (Chrome/Edge में खोलें)', 'Voice typing not supported here — please type instead. (Open in Chrome/Edge)'); return; }
  const box = document.getElementById('storyText');
  storyNew = false;
  r.lang = recLang(); r.interimResults = true; r.maxAlternatives = 1;
  r.continuous = true;
  activeRec = r;
  out.textContent = L('🎙 सुन रही हूँ… रोकने के लिए फिर दबाएं।', '🎙 Listening… tap again to stop.');
  r.onresult = e=>{
    let interim = '';
    for(let i = e.resultIndex; i < e.results.length; i++){
      const t = e.results[i][0].transcript;
      if(e.results[i].isFinal){
        box.value = (box.value ? box.value + ' ' : '') + t.trim();
        storyNew = true;
        out.textContent = L('✓ सुना: ', '✓ Heard: ') + t.trim();
      } else interim += t;
    }
    if(interim) out.textContent = '…' + interim;
  };
  r.onerror = e=>{
    out.textContent = e.error === 'not-allowed' ? L('माइक की अनुमति दें, फिर बोलें।', 'Please allow microphone access, then speak.')
      : e.error === 'no-speech' ? L('कुछ सुनाई नहीं दिया — फिर से बोलें।', 'No speech heard — please try again.')
      : e.error === 'audio-capture' ? L('माइक नहीं मिला।', 'No microphone found.')
      : e.error === 'aborted' ? '' : 'Mic: ' + e.error;
    if(e.error !== 'no-speech'){ activeRec = null; stopRecTimer(); }
  };
  r.onend = ()=>{ activeRec = null; stopRecTimer(); if(storyNew) autoFillFromStory(); };
  try{ r.start(); startRecTimer(); }catch(e){ activeRec = null; out.textContent = 'Mic busy — tap again.'; }
}
/* speech → English → auto-fill title + description, then user presses Next */
async function autoFillFromStory(){
  const story = document.getElementById('storyText').value.trim();
  const out = document.getElementById('dictateOut');
  if(!story) return;
  out.textContent = L('⏳ बात को अंग्रेज़ी में बदलकर शीर्षक/विवरण भर रहे…', '⏳ Converting to English & filling title/description…');
  try{
    const r = await fetch(API_BASE + '/api/v1/catalog/from-story', {method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({story_text: story, product_name: document.getElementById('pName').value, language: LANG}),
      signal: AbortSignal.timeout(30000)});
    if(!r.ok) throw 0;
    const j = await r.json();
    if(j.title_en) document.getElementById('mTitle').value = j.title_en;
    if(j.description_en) document.getElementById('mDesc').value = j.description_en;
    if(j.story_en || j.description_en) document.getElementById('craftStory').textContent = j.story_en || j.description_en;
    const sel = document.getElementById('pCraft');
    if(j.craft_guess){
      const g = j.craft_guess.toLowerCase();
      [...sel.options].forEach(o=>{ if(o.text.toLowerCase() === g || (g.length > 3 && o.text.toLowerCase().includes(g))) sel.value = o.text; });
    }
    out.textContent = L('✅ शीर्षक व विवरण भर गए (' + j.engine + ') — अब Next दबाएं।', '✅ Title & description filled (' + j.engine + ') — press Next.');
  }catch(e){
    document.getElementById('mTitle').value = document.getElementById('pName').value;
    document.getElementById('mDesc').value = story.slice(0, 120);
    out.textContent = L('✅ बोली बात जुड़ गई — अब Next दबाएं।', '✅ Your words were added — press Next.');
  }
}
/* recording timer pill */
let recInt = null, sec = 0;
function startRecTimer(){
  stopRecTimer(); sec = 0;
  const btn = document.getElementById('micBtn');
  btn.classList.add('rec');
  const tick = ()=>{ const m = String(Math.floor(sec/60)).padStart(2,'0'), s = String(sec%60).padStart(2,'0');
    btn.innerHTML = '⏹ ' + L('रोकें ', 'STOP ') + m + ':' + s; };
  tick();
  recInt = setInterval(()=>{ sec++; tick(); if(sec >= 120){ if(activeRec){ try{activeRec.stop();}catch(e){} } stopRecTimer(); } }, 1000);
}
function stopRecTimer(){
  if(recInt){ clearInterval(recInt); recInt = null; }
  const btn = document.getElementById('micBtn');
  if(btn){ btn.classList.remove('rec'); btn.innerHTML = '🎙 ' + L('रिकॉर्ड करें', 'Tap to record') + ' <span id="recTime">00:00</span>'; }
}
function dictateStory(){ dictateToggle(); } // legacy button hook
document.getElementById('micBtn').onclick = function(){ dictateToggle(); };

/* ---------- AI MAGIC → Vision Studio ---------- */
function animateSteps(){
  const steps=document.querySelectorAll('#aiSteps .step');
  steps.forEach(s=>s.classList.remove('active','done'));
  let i=0;
  return new Promise(res=>{
    const iv=setInterval(()=>{
      if(i>0) steps[i-1].classList.replace('active','done');
      if(i>=steps.length){clearInterval(iv);res();return;}
      steps[i].classList.add('active'); i++;
    },350);
  });
}
/* offline-proof sample photo: drawn locally, zero network needed */
function makePlaceholderPhoto(){
  return new Promise(res=>{
    const c = document.createElement('canvas'); c.width = 800; c.height = 800;
    const x = c.getContext('2d');
    const g = x.createLinearGradient(0, 0, 800, 800);
    g.addColorStop(0, '#7d1a24'); g.addColorStop(.55, '#b4563a'); g.addColorStop(1, '#e8a06a');
    x.fillStyle = g; x.fillRect(0, 0, 800, 800);
    x.strokeStyle = 'rgba(247,236,212,.8)'; x.lineWidth = 10;
    x.beginPath(); x.arc(400, 350, 190, 0, Math.PI * 2); x.stroke();
    x.fillStyle = '#f7ecd4'; x.textAlign = 'center';
    x.font = '150px serif'; x.fillText('🏺', 400, 415);
    x.font = '700 40px sans-serif';
    const label = (document.getElementById('pName').value || 'Handmade Craft').slice(0, 26);
    x.fillText(label, 400, 640);
    c.toBlob(b=>res(new File([b], 'sample.jpg', {type:'image/jpeg'})), 'image/jpeg', .85);
  });
}
async function runAIMagic(){
  const btn = document.getElementById('aiBtn');
  btn.disabled = true;
  btn.textContent = L('⏳ Vision Studio चल रहा…', '⏳ Vision Studio running…');
  const status = document.getElementById('aiStatus');
  status.textContent = L('आपकी फ़ोटो बाज़ार-तैयार उत्पाद बन रही…', 'Turning your raw photo into a marketplace-ready product…');
  animateSteps();
  const fd = new FormData();
  if(rawFileBlob){ fd.append('file', rawFileBlob, rawFileBlob.name || 'craft.jpg'); }
  else {
    // No photo chosen: try the hero artisan photo, else draw one locally (always works)
    let blob = null;
    try{
      const hp = document.querySelector('.hero-photo');
      if(hp && hp.src && hp.src.startsWith('http')){
        const resp = await fetch(hp.src, {signal: AbortSignal.timeout(8000)});
        if(resp.ok) blob = await resp.blob();
      }
    }catch(e){}
    if(!blob || !String(blob.type || '').startsWith('image')) blob = await makePlaceholderPhoto();
    fd.append('file', blob, 'sample.jpg');
  }
  fd.append('product_name', document.getElementById('pName').value);
  fd.append('craft_type', document.getElementById('pCraft').value);
  fd.append('material', document.getElementById('pMaterial').value);
  fd.append('location', document.getElementById('pLocation').value);
  fd.append('story_text', document.getElementById('storyText').value);
  fd.append('language', document.getElementById('pLang').value);
  fd.append('artisan', document.getElementById('pArtisan').value);
  try{
    const r = await fetch(API_BASE + '/api/v1/media/process-raw', {method:'POST', body: fd, signal: AbortSignal.timeout(120000)});
    if(!r.ok){ let msg = 'HTTP ' + r.status; try{ const j = await r.json(); if(j.detail) msg = j.detail; }catch(e){} throw new Error(msg); }
    const j = await r.json();
    showAIResult(j);
    status.textContent = L('✅ तैयार — 1080p + MoSJE सील + लिस्टिंग ड्राफ्ट। अब दाम देखें → 5× प्रकाशित करें।', '✅ Vision Studio done — 1080p + MoSJE seal + listing draft ready. See My Listings → Publish 5×.');
  }catch(e){
    if(e && (e.name === 'TimeoutError' || e.name === 'AbortError')){
      status.textContent = L('⏳ Vision Studio को समय लग रहा है (पहली बार AI मॉडल लोड होता है)। 1–2 मिनट रुककर Next फिर दबाएं।', '⏳ Vision Studio is taking long (first run loads the AI model). Wait 1–2 min and press Next again.');
    } else if(e && e.message === 'Failed to fetch'){
      status.textContent = L('❌ बैकएंड से संपर्क नहीं हुआ — क्या uvicorn :8000 पर चल रहा है? Settings → Test connection दबाएं।', '❌ Could not reach backend — is uvicorn running on :8000? Press Settings → Test connection.');
    } else {
      status.textContent = '❌ ' + ((e && e.message) || e);
    }
    localFallback();
  }
  btn.disabled = false;
  applyLang(); // restore translated button label
  await checkPrice();
  await saveProductToDB(); // new listing joins the marketplace DB
  showTab('listings');
}
function showAIResult(j){
  if(j.product_id) lastProductId = j.product_id;
  const img = document.getElementById('aiImage');
  img.src = j.image_data_url; img.hidden = false;
  document.getElementById('aiBox').hidden = true;
  document.getElementById('engineNote').textContent = `Engine: ${j.studio.engine} • Canvas ${j.studio.canvas} • Seal ${j.studio.seal}`;
  lastListing = j.listing;
  document.getElementById('listingCard').hidden = false;
  document.getElementById('listTitleEn').textContent = j.listing.title_en;
  document.getElementById('listTitleHi').textContent = j.listing.title_hi;
  document.getElementById('listDesc').textContent = j.listing.description_en;
  document.getElementById('listTags').innerHTML = j.listing.tags.map(t=>`<span>${t}</span>`).join('');
  document.getElementById('craftStory').textContent = j.listing.description_hi;
  document.getElementById('mTitle').value = j.listing.title_en;
  document.getElementById('mDesc').value = j.listing.description_en.slice(0,120);
}
function localFallback(){
  const cost=parseFloat(document.getElementById('pCost').value||'400');
  const suggest=Math.round(cost*3.125);
  document.getElementById('suggestPrice').textContent=suggest.toLocaleString('en-IN');
  document.getElementById('aiBox').hidden = false;
  document.getElementById('aiBox').innerHTML = '🔵<small>Local preview — start backend for 1080p seal</small>';
}

/* ---------- Bargaining Shield ---------- */
async function checkPrice(){
  const payload = {
    material_cost: parseFloat(document.getElementById('bCost').value || document.getElementById('pCost').value || 400),
    labour_hours: parseFloat(document.getElementById('bHours').value || document.getElementById('pHours').value || 8),
    wage_per_hour: parseFloat(document.getElementById('bWage').value || 80),
    overhead_pct: 12, profit_pct: 25,
    buyer_offer: parseFloat(document.getElementById('offer').value || 0),
  };
  const box=document.getElementById('shield');
  try{
    const r = await fetch(API_BASE + '/api/v1/pricing/bargain-shield', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
    if(!r.ok) throw 0;
    const j = await r.json();
    lastPrice = j.suggested_price;
    document.getElementById('suggestPrice').textContent = j.suggested_price.toLocaleString('en-IN');
    document.getElementById('floorNote').textContent = `Floor ₹${j.floor_price.toLocaleString('en-IN')} • Wholesale ₹${j.wholesale_price.toLocaleString('en-IN')}`;
    box.innerHTML = `<b>${j.verdict}</b><small>${j.message_en}</small>`;
    box.style.background = j.verdict_code==='TOO_LOW' ? 'radial-gradient(#8b1a22,#5c0e14)' : j.verdict_code==='NEGOTIABLE' ? 'radial-gradient(#b7791f,#7a4a00)' : 'radial-gradient(#1a7a4a,#0d4a2a)';
    document.getElementById('breakup').innerHTML = `<div><span>Material Cost</span><b>₹${j.material_cost}</b></div><div><span>Labour (${j.labour_hours}h × ₹${j.wage_per_hour})</span><b>₹${j.labour_cost}</b></div><div><span>Suggested Price</span><b>₹${j.suggested_price}</b></div><div><span>Dignity Floor</span><b>₹${j.floor_price}</b></div>`;
    document.getElementById('shieldMsg').textContent = '🇮🇳 ' + j.message_hi;
    return j;
  }catch(e){
    const suggest = Math.round(payload.material_cost * 3.125), offer = payload.buyer_offer;
    const pct=Math.round((1-offer/suggest)*100);
    if(offer<suggest*0.85){box.innerHTML=`<b>Too Low</b><small>The offer is ${pct}% below suggested price.</small>`;box.style.background='radial-gradient(#8b1a22,#5c0e14)';}
    else if(offer<suggest){box.innerHTML=`<b>Negotiable</b><small>Close! ${pct}% below. Counter at ₹${suggest}.</small>`;box.style.background='radial-gradient(#b7791f,#7a4a00)';}
    else{box.innerHTML=`<b>Fair ✓</b><small>Great! At or above suggested price.</small>`;box.style.background='radial-gradient(#1a7a4a,#0d4a2a)';}
    document.getElementById('suggestPrice').textContent = suggest.toLocaleString('en-IN');
  }
}

/* ---------- Publish multi ---------- */
async function publishMulti(){
  const st = document.getElementById('pubStatus'); st.textContent = L('⏳ 5 चैनलों पर प्रकाशित हो रहा…', '⏳ Publishing to 5 channels…');
  const payload = {
    product_name: document.getElementById('pName').value,
    craft_type: document.getElementById('pCraft').value,
    price_inr: lastPrice || 1250,
    description: document.getElementById('mDesc').value || document.getElementById('storyText').value,
    tags: lastListing?.tags || ['handmade','indian-craft'],
    location: document.getElementById('pLocation').value,
    image_url: 'vision-studio-1080p.jpg',
  };
  try{
    const r = await fetch(API_BASE + '/api/v1/channels/publish-multi', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
    if(!r.ok) throw 0;
    const j = await r.json(); renderChannels(j.channels);
    st.textContent = '✅ ' + j.channels.summary;
  }catch(e){
    st.textContent = L('⚠ बैकएंड ऑफ़लाइन — नमूना चैनल दिख रहे हैं।', '⚠ Backend offline — showing sample channel payloads.');
    renderChannels({amazon_in:{marketplace:'Amazon.in',asin:'B0SAMPLE01',price_inr:payload.price_inr,status:'SAMPLE'},flipkart:{marketplace:'Flipkart',fsn:'FSNSAMPLE',price_inr:payload.price_inr,status:'SAMPLE'},gem:{marketplace:'GeM',quota:'Handicrafts',price_inr:payload.price_inr,status:'SAMPLE'},etsy:{marketplace:'Etsy',price_usd:Math.round(payload.price_inr/83+6),status:'SAMPLE'},ondc_beckn:{marketplace:'ONDC (Beckn)',status:'SAMPLE'},summary:'Sample preview — start backend for live ASIN/FSN/Beckn JSON.'});
  }
}
function renderChannels(ch){
  const grid = document.getElementById('chanGrid');
  const cards = [
    ['🟠 Amazon.in', ch.amazon_in?.asin || '', `₹${ch.amazon_in?.price_inr ?? ''}`, ch.amazon_in?.status],
    ['🔵 Flipkart', ch.flipkart?.fsn || '', `₹${ch.flipkart?.price_inr ?? ''}`, ch.flipkart?.status],
    ['🏛 GeM Govt', ch.gem?.quota || '', `₹${ch.gem?.price_inr ?? ''}`, ch.gem?.status],
    ['🟤 Etsy Export', (ch.etsy?.price_usd ? '$'+ch.etsy.price_usd : ''), (ch.etsy?.tags_13||[]).slice(0,4).join(', '), ch.etsy?.status],
    ['🟣 ONDC Beckn', 'retail • on_search', JSON.stringify(ch.ondc_beckn?.beckn?.message?.catalog?.price || {}), ch.ondc_beckn?.status],
  ];
  grid.innerHTML = cards.map(([t,a,b,s])=>`<div class="chan"><b>${t}</b><code>${a}</code><small>${b}</small><span class="ok">${s||''}</span></div>`).join('');
}

/* ---------- Shilpi ---------- */
function quickAsk(el){ document.getElementById('shilpiQ').value = el.textContent; askShilpiBackend(); }
async function askShilpiBackend(){
  const q = document.getElementById('shilpiQ').value;
  const el = document.getElementById('saathiText'); el.textContent = L('⏳ सोच रही हूँ…', '⏳ Thinking…');
  try{
    const r = await fetch(API_BASE + '/api/v1/assistant/shilpi', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({query: q, lang: LANG}), signal: AbortSignal.timeout(30000)});
    if(!r.ok){ let msg = 'HTTP ' + r.status; try{ const j = await r.json(); if(j.detail) msg = j.detail; }catch(e){} throw new Error(msg); }
    const j = await r.json();
    el.textContent = j.answer;
    document.getElementById('shilpiEngine').textContent = 'Engine: ' + j.engine + ' • topic: ' + j.topic;
    if(j.audio_mp3_base64){ const a = document.getElementById('shilpiAudio'); a.src = 'data:audio/mp3;base64,' + j.audio_mp3_base64; a.hidden = false; a.play().catch(()=>{}); }
    else speak(el.textContent);
  }catch(e){
    const why = (e && e.message === 'Failed to fetch')
      ? L('बैकएंड बंद है — लोकल जवाब। Start backend :8000', 'Backend unreachable — local answer. Start backend :8000')
      : L('एरर: ', 'Error: ') + ((e && e.message) || e);
    document.getElementById('shilpiEngine').textContent = '⚠ ' + why;
    speakSaathi();
  }
}
function speak(t){ try{ speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(t); u.lang = /[\u0900-\u097F]/.test(t) ? 'hi-IN' : 'en-IN'; speechSynthesis.speak(u);}catch(e){} }
function speakSaathi(){
  const el=document.getElementById('saathiText');
  const msgs = LANG === 'hi'
    ? ["नमस्ते! आपकी Blue Pottery थाली ट्रेंड कर रही है। दाम ₹1,250 रखें — मुनाफा 20% रहेगा।","सरकारी योजना: PM Vishwakarma में ₹15,000 टूलकिट + 5% ब्याज पर लोन मिलता है।","ऑर्डर अपडेट: 7 पेंडिंग में से 3 आज शिप करें — SLA बचा रहेगा।"]
    : ["Hello! Your Blue Pottery plate is trending. Keep ₹1,250 — margin stays near 20%.","Scheme alert: PM Vishwakarma gives a ₹15,000 toolkit plus loans at 5%.","Orders: ship 3 of your 7 pending orders today to protect your SLA."];
  el.textContent=msgs[Math.floor(Math.random()*msgs.length)]; speak(el.textContent);
}
function openShilpi(){ document.getElementById('shilpiModal').hidden = false; }
function closeShilpi(){ document.getElementById('shilpiModal').hidden = true; }
function modalListen(){
  const r = getSR();
  if(!r){ alert(L('यह ब्राउज़र आवाज़ नहीं समझता — लिखकर पूछें।', 'Web Speech not supported in this browser — type instead.')); return; }
  r.lang = recLang();
  document.getElementById('mSaathiText').textContent = L('🎙 सुन रही हूँ…', '🎙 Listening…');
  r.onresult = e=>{ document.getElementById('mQ').value = e.results[0][0].transcript; modalAsk(); };
  r.onerror = e=>{ document.getElementById('mSaathiText').textContent = 'Mic: ' + e.error; };
  try{ r.start(); }catch(e){}
}
async function modalAsk(){
  const q = document.getElementById('mQ').value;
  document.getElementById('mSaathiText').textContent = '⏳…';
  try{
    const r = await fetch(API_BASE + '/api/v1/assistant/shilpi', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({query: q, lang: LANG}), signal: AbortSignal.timeout(30000)});
    if(!r.ok){ let msg = 'HTTP ' + r.status; try{ const j = await r.json(); if(j.detail) msg = j.detail; }catch(e){} throw new Error(msg); }
    const j = await r.json();
    document.getElementById('mSaathiText').textContent = j.answer;
    if(j.audio_mp3_base64){ const a = document.getElementById('mAudio'); a.src='data:audio/mp3;base64,'+j.audio_mp3_base64; a.hidden=false; a.play().catch(()=>{});} else speak(j.answer);
  }catch(e){
    document.getElementById('mSaathiText').textContent = (e && e.message === 'Failed to fetch')
      ? L('बैकएंड बंद है — uvicorn :8000 चलाएं।', 'Backend unreachable — start uvicorn on :8000.')
      : L('एरर: ', 'Error: ') + ((e && e.message) || e);
  }
}

/* ---------- boot ---------- */
applyLang();
loadCatalog();
loadOrders();
if('serviceWorker' in navigator){ window.addEventListener('load', ()=> navigator.serviceWorker.register('sw.js').catch(()=>{})); }

/* ================= KALAKART ENTERPRISE FEATURES ================= */

/* 1. Select Product from Catalog into My Listings */
function selectProductCard(pid){
  if(!pid) return;
  lastProductId = pid;
  const found = dbProducts.find(p => p.id === pid);
  if(found){
    const name = found.name || found.title_en || 'Handcrafted Craft';
    const priceVal = found.price || found.retail_price || 1250;
    const desc = found.description || found.story_en || '';
    const img = found.image_url || '';
    
    lastPrice = priceVal;
    document.getElementById('suggestPrice').textContent = Number(priceVal).toLocaleString('en-IN');
    document.getElementById('floorNote').textContent = `Floor ₹${Math.round(priceVal*0.4)} • Wholesale ₹${Math.round(priceVal*0.75)}`;
    document.getElementById('mTitle').value = name;
    document.getElementById('mDesc').value = desc.slice(0, 150);
    document.getElementById('craftStory').textContent = desc;
    
    const prodImg = document.querySelector('#tab-listings .prod-img img');
    if(prodImg && img){ prodImg.src = img; }
    
    showTab('listings');
  }
}

/* 2. 1-Click Demo Voice Note (Zero-friction presentation demo) */
function playDemoVoiceNote(){
  const demoTranscript = "यह जयपुर की प्रसिद्ध ब्लू पॉटरी की गोल थाली है। इसे क्वार्ट्ज़, कांच और मुल्तानी मिट्टी से हाथ से बनाया गया है। इसमें 8 घंटे लगे हैं और कच्चा माल 400 रुपये का लगा है।";
  const box = document.getElementById('storyText');
  box.value = demoTranscript;
  
  const out = document.getElementById('dictateOut');
  out.textContent = L('🎙 डेमो वॉयस नोट लोड हुआ — AI से विवरण भर रहे हैं...', '🎙 Demo voice note loaded — AI filling catalog details...');
  
  // Also pre-fill form fields
  document.getElementById('pName').value = "Handpainted Blue Pottery Plate";
  document.getElementById('pCraft').value = "Jaipur Blue Pottery";
  document.getElementById('pMaterial').value = "Quartz, Glass, Multani Clay";
  document.getElementById('pLocation').value = "Jaipur, Rajasthan";
  document.getElementById('pHours').value = "8";
  document.getElementById('pCost').value = "400";
  document.getElementById('bCost').value = "400";
  document.getElementById('bHours').value = "8";
  
  // Trigger speech AI autofill
  autoFillFromStory();
}

/* 3. Random Forest 109MB ML Fair Pricing Prediction */
async function runMLPricing(){
  const matCost = parseFloat(document.getElementById('bCost').value || document.getElementById('pCost').value || 400);
  const labHours = parseFloat(document.getElementById('bHours').value || document.getElementById('pHours').value || 8);
  const craft = document.getElementById('pCraft').value || "Jaipur Blue Pottery";
  const mat = document.getElementById('pMaterial').value || "Quartz, Glass, Clay";
  
  openInfoModal(
    L("🤖 रैंडम फ़ॉरेस्ट AI मूल्य मॉडल", "🤖 Random Forest ML Fair Pricing"),
    "<p class='muted'>Calculating fair price using 109MB trained model (300 estimators, 50,000 handicraft records)...</p>"
  );
  
  try {
    const r = await fetch(API_BASE + '/api/v1/pricing/predict', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        material_cost: matCost,
        labor_hours: labHours,
        craft_type: craft,
        material: mat
      })
    });
    if(!r.ok) throw 0;
    const res = await r.json();
    
    // Update listings tab
    lastPrice = res.recommended_retail_price;
    document.getElementById('suggestPrice').textContent = Number(res.recommended_retail_price).toLocaleString('en-IN');
    document.getElementById('floorNote').textContent = `Floor ₹${Number(res.cost_floor).toLocaleString('en-IN')} • Wholesale ₹${Number(res.wholesale_b2b_price).toLocaleString('en-IN')}`;
    
    const html = `
      <div style="background:#fff8ee;border:1px solid #e8d0a8;border-radius:12px;padding:16px;margin-bottom:14px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
          <span style="font-size:12px;background:#7a1620;color:#fff;padding:3px 10px;border-radius:12px;font-weight:600;">${res.model_version || 'RandomForest-v1.0 (300 Trees)'}</span>
          <b style="color:#2a7a40;font-size:15px;">✓ MoSJE Wage-Floor Protected</b>
        </div>
        <h2 style="font-family:serif;font-size:32px;color:#7a1620;margin:8px 0;">₹ ${Number(res.recommended_retail_price).toLocaleString('en-IN')} <small style="font-size:14px;color:#666;font-weight:normal;">(Fair Retail Price)</small></h2>
        <p style="margin:6px 0;color:#444;"><b>Living Wage Floor:</b> ₹ ${Number(res.cost_floor).toLocaleString('en-IN')} &nbsp;•&nbsp; <b>B2B Wholesale Price:</b> ₹ ${Number(res.wholesale_b2b_price).toLocaleString('en-IN')}</p>
        <p style="margin:6px 0;color:#444;"><b>Guaranteed Artisan Wage:</b> ₹ ${Number(res.guaranteed_labor_wage).toLocaleString('en-IN')} (${labHours} hrs @ ₹100/hr minimum)</p>
      </div>
      <div style="background:#faf5ee;border-radius:10px;padding:12px;font-size:13px;line-height:1.6;">
        <b>Pricing Rationale:</b><br>
        ${res.explanation || 'Pricing derived by Random Forest regressor with MoSJE skilled craft living wage floor rules.'}
      </div>
      <div style="margin-top:14px;text-align:right;">
        <button class="cta" onclick="closeInfoModal()">Apply to Listing ✓</button>
      </div>
    `;
    openInfoModal(L("🤖 रैंडम फ़ॉरेस्ट AI मूल्य मॉडल", "🤖 Random Forest ML Fair Pricing"), html);
  } catch(e) {
    openInfoModal("Pricing Model", `<p style="color:#c00;">Backend offline. Please start FastAPI on :8000 to run live Random Forest inference.</p>`);
  }
}

/* 4. Mela Standee PDF with Dynamic UPI QR Code */
function downloadMelaPdf(){
  const pid = lastProductId || (dbProducts[0] && dbProducts[0].id) || 'kk_prod_001';
  const url = `${API_BASE}/api/v1/export/mela-standee/${pid}`;
  window.open(url, '_blank');
}

/* 5. Official ONDC Beckn Protocol v1.2 JSON Export */
async function exportOndcJson(){
  const pid = lastProductId || (dbProducts[0] && dbProducts[0].id) || 'kk_prod_001';
  openInfoModal(
    L("🌐 ONDC बेकन v1.2 एक्सपोर्ट", "🌐 Official ONDC Beckn v1.2 Catalog"),
    "<p class='muted'>Generating Beckn v1.2 retail taxonomy JSON payload...</p>"
  );
  try {
    const r = await fetch(`${API_BASE}/api/v1/export/ondc-beckn/${pid}`);
    if(!r.ok) throw 0;
    const json = await r.json();
    const str = JSON.stringify(json, null, 2);
    const html = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
        <span class="badge" style="background:#eef6ee;color:#1e7e34;font-weight:700;">ONDC / Beckn Core v1.2 Validated</span>
        <button class="light-btn" onclick="copyOndcJson()">📋 Copy JSON</button>
      </div>
      <pre id="ondcJsonBlock" style="background:#1e1a18;color:#f3d8a8;padding:14px;border-radius:10px;font-size:11.5px;max-height:400px;overflow:auto;white-space:pre-wrap;font-family:monospace;">${str.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>
      <div style="margin-top:12px;display:flex;justify-content:flex-end;gap:8px;">
        <button class="cta" onclick="downloadOndcJsonFile()">⬇ Download .json</button>
      </div>
    `;
    openInfoModal(L("🌐 ONDC बेकन v1.2 एक्सपोर्ट", "🌐 Official ONDC Beckn v1.2 Catalog"), html);
    window._latestOndcJson = str;
  } catch(e) {
    openInfoModal("ONDC Beckn Export", `<p style="color:#c00;">Could not connect to backend :8000 to generate ONDC Beckn schema.</p>`);
  }
}

function copyOndcJson(){
  if(window._latestOndcJson){
    navigator.clipboard.writeText(window._latestOndcJson).then(()=> alert("ONDC JSON copied to clipboard!"));
  }
}

function downloadOndcJsonFile(){
  if(window._latestOndcJson){
    const blob = new Blob([window._latestOndcJson], {type: 'application/json'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `ondc_beckn_${lastProductId || 'catalog'}.json`;
    a.click();
  }
}

/* 6. Info Modal Utilities */
function openInfoModal(title, html){
  const m = document.getElementById('infoModal');
  if(!m) return;
  document.getElementById('infoModalTitle').innerHTML = title;
  document.getElementById('infoModalBody').innerHTML = html;
  m.hidden = false;
}
function closeInfoModal(){
  const m = document.getElementById('infoModal');
  if(m) m.hidden = true;
}

/* ================= MARKETPLACE V2 — rich artisan cards ================= */
let marketCache = [], sortMode = 'featured', currentPM = null;
function getWish(){ try{ return JSON.parse(localStorage.getItem('shilp_wish') || '[]'); }catch(e){ return []; } }
function inWish(id){ return getWish().includes(id); }
function toggleWish(ev, id){
  ev.stopPropagation();
  let w = getWish();
  w = w.includes(id) ? w.filter(x => x !== id) : [...w, id];
  try{ localStorage.setItem('shilp_wish', JSON.stringify(w)); }catch(e){}
  document.querySelectorAll(`.m-heart[data-w="${id}"]`).forEach(b=>b.classList.toggle('on', w.includes(id)));
}
function mCardHTML(p){
  const price = p.priceNum || parseInt((p.p || '0').replace(/[^\d]/g, '')) || 0;
  const rating = p.rating || 4.5, reviews = p.reviews || 12;
  const av = (p.artisan || p.by || 'K').trim().charAt(0).toUpperCase();
  const wished = inWish(p.id) ? ' on' : '';
  return `<div class="m-card" data-pid="${p.id || ''}">
    <div class="m-img"><img loading="lazy" src="${p.img}" alt="${p.n}" onerror="this.style.display='none'"/>
      <span class="m-tag">◉ ${p.tag || 'Handmade'}</span>
      <button class="m-heart${wished}" data-w="${p.id || ''}" onclick="toggleWish(event,'${p.id || ''}')" title="Wishlist">♥</button>
    </div>
    <div class="m-body">
      <small class="m-craft">${(p.cat || 'Handmade').toUpperCase()}</small>
      <b class="m-name">${p.n}</b>
      <div class="m-art"><span class="m-av">${av}</span><span>${p.artisan || p.by || ''}${p.location ? ' • ' + p.location : ''}</span></div>
      <div class="m-foot"><span class="m-price">₹${price.toLocaleString('en-IN')}</span><span class="m-rate">★ ${rating} (${reviews})</span></div>
    </div>
  </div>`;
}
function renderMarket(list){
  marketCache = list || [];
  const sel = document.getElementById('sortSel');
  const mode = sel ? sel.value : sortMode;
  sortMode = mode;
  const sorted = [...marketCache];
  if(mode === 'low') sorted.sort((a, b) => (a.priceNum || 0) - (b.priceNum || 0));
  else if(mode === 'high') sorted.sort((a, b) => (b.priceNum || 0) - (a.priceNum || 0));
  else if(mode === 'rated') sorted.sort((a, b) => (b.rating || 0) - (a.rating || 0));
  document.getElementById('marketGrid').innerHTML = sorted.map(mCardHTML).join('');
  const mc = document.getElementById('mCount');
  if(mc) mc.textContent = sorted.length + (LANG === 'hi' ? ' उत्पाद' : ' products');
}
function sortMarket(v){ sortMode = v; renderMarket(marketCache); }
document.getElementById('marketGrid').addEventListener('click', e=>{
  if(e.target.closest('.m-heart')) return;
  const card = e.target.closest('.m-card');
  if(card && card.dataset.pid) openProduct(card.dataset.pid);
});
function findCard(id){ return marketCache.find(p => String(p.id) === String(id)); }
function openProduct(id){
  const p = findCard(id); if(!p) return;
  currentPM = p;
  const img = document.getElementById('pmImg');
  img.style.display = ''; img.src = p.img;
  document.getElementById('pmTag').textContent = '◉ ' + (p.tag || 'Handmade');
  document.getElementById('pmCraft').textContent = (p.cat || 'Handmade').toUpperCase();
  document.getElementById('pmName').textContent = p.n;
  document.getElementById('pmAv').textContent = (p.artisan || 'K').trim().charAt(0).toUpperCase();
  document.getElementById('pmArt').textContent = (p.artisan || p.by || '') + (p.location ? ' • ' + p.location : '');
  document.getElementById('pmDesc').textContent = p.desc || p.n;
  document.getElementById('pmTags').innerHTML = (p.tags || []).map(t => `<span>${t}</span>`).join('');
  document.getElementById('pmPrice').textContent = '₹' + ((p.priceNum || 0).toLocaleString('en-IN'));
  document.getElementById('pmRate').textContent = `★ ${p.rating || 4.5} (${p.reviews || 12} reviews)`;
  document.getElementById('prodModal').hidden = false;
}
function closeProduct(){ document.getElementById('prodModal').hidden = true; currentPM = null; }
function pmFair(){
  if(!currentPM) return;
  const price = currentPM.priceNum || 0;
  const raw = currentPM.raw || {};
  document.getElementById('offer').value = price;
  document.getElementById('bCost').value = Math.round(raw.material_cost || price * 0.35);
  document.getElementById('bHours').value = raw.labor_hours || 8;
  closeProduct(); showTab('assistant'); checkPrice();
}
function pmAsk(){
  if(!currentPM) return;
  document.getElementById('shilpiQ').value = `Is ₹${(currentPM.priceNum || 0).toLocaleString('en-IN')} fair for "${currentPM.n}"?`;
  closeProduct(); showTab('assistant'); askShilpiBackend();
}
function pmSelect(){
  if(!currentPM) return;
  const id = currentPM.id; closeProduct();
  if(typeof selectProductCard === 'function') selectProductCard(id);
}

/* ================= AUTH — login / register against backend ================= */
let authMode = 'login';
function authHeaders(){
  const t = localStorage.getItem('shilp_token');
  return t ? {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + t} : {'Content-Type': 'application/json'};
}
function openAuth(mode){
  authMode = mode || 'login';
  document.getElementById('authErr').textContent = '';
  switchAuthTab(authMode);
  document.getElementById('authModal').hidden = false;
}
function closeAuth(){ document.getElementById('authModal').hidden = true; }
function switchAuthTab(mode){
  authMode = mode;
  document.getElementById('tabLogin').classList.toggle('active', mode === 'login');
  document.getElementById('tabRegister').classList.toggle('active', mode === 'register');
  const reg = mode === 'register';
  document.getElementById('regNameWrap').style.display = reg ? '' : 'none';
  document.getElementById('regExtraWrap').style.display = reg ? '' : 'none';
  document.getElementById('authGo').textContent = reg ? (LANG === 'hi' ? 'खाता बनाएं →' : 'Create account →') : 'Login →';
  document.getElementById('authErr').textContent = '';
}
async function doAuth(){
  const err = document.getElementById('authErr');
  err.textContent = '';
  const email = document.getElementById('authEmail').value.trim();
  const pass = document.getElementById('authPass').value;
  try{
    let url, body;
    if(authMode === 'register'){
      const name = document.getElementById('authName').value.trim();
      body = {name, email, password: pass, phone: document.getElementById('authPhone').value.trim(), role: document.getElementById('authRole').value};
      url = API_BASE + '/api/v1/auth/register';
    } else {
      body = {email, password: pass};
      url = API_BASE + '/api/v1/auth/login';
    }
    const r = await fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body), signal: AbortSignal.timeout(15000)});
    const j = await r.json().catch(() => ({}));
    if(!r.ok) throw new Error(j.detail || ('HTTP ' + r.status));
    localStorage.setItem('shilp_token', j.token);
    localStorage.setItem('shilp_user', JSON.stringify(j.user));
    closeAuth(); updateAuthUI();
  }catch(e){
    err.textContent = (e && e.message === 'Failed to fetch')
      ? L('बैकएंड बंद है — पहले backend चलाएं।', 'Backend unreachable — start the backend first.')
      : (e && e.message) || e;
  }
}
function authBtn(){
  if(localStorage.getItem('shilp_token')){ doLogout(); }
  else openAuth('login');
}
async function doLogout(){
  try{ await fetch(API_BASE + '/api/v1/auth/logout', {method: 'POST', headers: authHeaders()}); }catch(e){}
  localStorage.removeItem('shilp_token');
  localStorage.removeItem('shilp_user');
  updateAuthUI();
}
function updateAuthUI(){
  let u = null;
  try{ u = JSON.parse(localStorage.getItem('shilp_user') || 'null'); }catch(e){}
  const btn = document.getElementById('loginBtn');
  const nm = document.getElementById('profileName');
  const av = document.getElementById('avatarCircle');
  if(u){
    if(btn) btn.textContent = LANG === 'hi' ? 'लॉगआउट' : 'Logout';
    if(nm) nm.textContent = u.name.split(' ')[0];
    if(av) av.textContent = u.name.trim().charAt(0).toUpperCase();
    const pa = document.getElementById('pArtisan');
    if(pa && (pa.value === 'Rukmini Art' || !pa.value)) pa.value = u.name;
  } else {
    if(btn) btn.textContent = 'Login';
    if(nm) nm.textContent = 'Priya';
    if(av) av.textContent = 'P';
  }
}
async function refreshMe(){
  const t = localStorage.getItem('shilp_token');
  if(!t){ updateAuthUI(); return; }
  try{
    const r = await fetch(API_BASE + '/api/v1/auth/me', {headers: authHeaders(), signal: AbortSignal.timeout(10000)});
    if(!r.ok) throw 0;
    const j = await r.json();
    localStorage.setItem('shilp_user', JSON.stringify(j.user));
  }catch(e){
    if(e && e.message !== 'Failed to fetch'){ localStorage.removeItem('shilp_token'); localStorage.removeItem('shilp_user'); }
  }
  updateAuthUI();
}

/* use the backend's exact artisan artwork when the gateway is reachable */
function setLocalArt(){
  const hero = document.querySelector('.hero-photo');
  if(hero){
    const probe = new Image();
    probe.onload = ()=>{ hero.onerror = null; hero.src = API_BASE + '/static/img/hero_composition_exact.png'; };
    probe.src = API_BASE + '/static/img/hero_composition_exact.png';
  }
  const map = ['category_pottery.png', 'category_textiles.png', 'category_woodwork.png', 'category_paintings.png', 'category_metalwork.png', 'category_bamboo.png'];
  document.querySelectorAll('#catGrid .cat-card img').forEach((im, i)=>{
    if(!map[i]) return;
    const probe = new Image();
    probe.onload = ()=>{ im.src = API_BASE + '/static/img/' + map[i]; };
    probe.src = API_BASE + '/static/img/' + map[i];
  });
}

/* v2 boot additions */
refreshMe();
setLocalArt();
