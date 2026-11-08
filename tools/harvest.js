/* Floor Copilot catalog harvest. Paste into a browser tab on homedepot.com (store 121 selected).
   Optional, before pasting: window.HV_WATCH=["LF30S8210S","123456789"] (lines of data/watchlist.txt).
   Progress: HV.phase ("list" > "watch" > "specs" > "done"), HV.done / HV.total.
   Results: HV.rows (catalog rows, 31 fields, see CLAUDE.md) and HV.report (what was skipped and why).
   HV.reportText() gives a short plain-text summary. */
window.HV={phase:"list",items:{},errors:[],done:0,total:0,rows:null,
 report:{cats:{},specFailed:[],dropped:[],watchFound:[],watchMissing:[]}};
HV.reportText=()=>{const r=HV.report,L=[];
 for(const [c,v] of Object.entries(r.cats))L.push(`${c}: site says ${v.total}, listed ${v.listed}, kept ${v.kept??"?"}`);
 L.push(`rows: ${HV.rows?HV.rows.length:0}`);
 L.push(`dropped: ${r.dropped.length}`+(r.dropped.length?" ("+Object.entries(r.dropped.reduce((a,d)=>(a[d.reason]=(a[d.reason]||0)+1,a),{})).map(([k,v])=>k+" "+v).join(", ")+")":""));
 r.dropped.slice(0,60).forEach(d=>L.push(`  ${d.reason}: ${d.brand||"?"} ${d.model||"?"} (${d.id})`));
 L.push(`watchlist found: ${r.watchFound.join(", ")||"none"}`);
 L.push(`watchlist missing: ${r.watchMissing.join(", ")||"none"}`);
 if(HV.errors.length)L.push(`errors: ${HV.errors.length} (first: ${HV.errors.slice(0,5).join("; ")})`);
 return L.join("\n")};
(async()=>{
const sl=ms=>new Promise(r=>setTimeout(r,ms));
const bal=(s,st)=>{let d=0,inS=false,esc=false;for(let i=st;i<s.length;i++){const c=s[i];if(inS){if(esc)esc=false;else if(c==='\\')esc=true;else if(c==='"')inS=false;continue}if(c==='"')inS=true;else if(c==='{')d++;else if(c==='}'){d--;if(d===0)return s.slice(st,i+1)}}};
const apollo=h=>{const i=h.indexOf('__APOLLO_STATE__=');return i<0?null:JSON.parse(bal(h,i+17))};
const normM=v=>String(v||"").toUpperCase().replace(/[^A-Z0-9]/g,"");
const cats={FD:"https://www.homedepot.com/b/Appliances-Refrigerators-French-Door-Refrigerators/N-5yc1vZc3oo",SS:"https://www.homedepot.com/b/Appliances-Refrigerators-Side-by-Side-Refrigerators/N-5yc1vZc3q0",TF:"https://www.homedepot.com/b/Appliances-Refrigerators-Top-Freezer-Refrigerators/N-5yc1vZc3ns",BF:"https://www.homedepot.com/b/Appliances-Refrigerators-Bottom-Freezer-Refrigerators/N-5yc1vZc3p6",FL:"https://www.homedepot.com/b/Appliances-Refrigerators-Freezerless-Refrigerators/N-5yc1vZc3p9"};
const item=(o,cat)=>{const pk=k=>Object.keys(o).find(x=>x.startsWith(k));const p=o[pk("pricing")]||{};const fu=JSON.stringify(o[pk("fulfillment")]||{});
 return {id:o.itemId,cat,brand:o.identifiers?.brandName,label:o.identifiers?.productLabel,model:o.identifiers?.modelNumber,price:p.value??null,orig:p.original??null,promo:p.promotion?.savingsCenterPromos||"",rating:o.reviews?.ratingsReviews?.averageRating??null,reviews:o.reviews?.ratingsReviews?.totalReviews??null,avail:o.availabilityType?.type,deliv:(fu.match(/"earliestDeliveryDate":"([^"]+)"/)||[])[1]||""}};
// Collects every product object in an Apollo state blob.
const walk=(o,cat,out)=>{if(!o||typeof o!=="object")return;if(Array.isArray(o)){o.forEach(x=>walk(x,cat,out));return}
 if(o.itemId&&/^\d{9}$/.test(o.itemId)&&o.identifiers&&Object.keys(o).some(k=>k.startsWith("pricing"))&&!out[o.itemId])out[o.itemId]=item(o,cat);
 for(const k in o)walk(o[k],cat,out)};

// 1. Category listings, 12 per page, until the site's own total.
for(const [cat,url] of Object.entries(cats)){let tot=12,listed=0;
 for(let n=0;n<tot&&n<3000;n+=12){let ok=false;
  for(let t=0;t<3&&!ok;t++){try{const h=await fetch(url+(n?"?Nao="+n:"")).then(r=>r.text());
    if(n===0){const m=h.match(/"totalProducts":(\d+)/);tot=m?+m[1]:0}
    const got={};walk(apollo(h),cat,got);for(const [id,x] of Object.entries(got))if(!HV.items[id]){HV.items[id]=x;listed++}ok=true}
   catch(e){HV.errors.push(`${cat} page ${n}: ${e.message}`);await sl(2000*(t+1))}}
  await sl(300)}
 HV.report.cats[cat]={total:tot,listed}}

// 2. Watchlist: models or item ids that must be in the catalog even if the listings missed them.
HV.phase="watch";
const watch=(window.HV_WATCH||[]).map(s=>String(s).trim()).filter(s=>s&&!s.startsWith("#"));
const have=w=>Object.values(HV.items).find(x=>x.id===w||normM(x.model)===normM(w));
for(const w of watch){let x=have(w);
 if(!x){const url=/^\d{9}$/.test(w)?"https://www.homedepot.com/p/"+w:"https://www.homedepot.com/s/"+encodeURIComponent(w);
  for(let t=0;t<3&&!x;t++){try{const h=await fetch(url).then(r=>r.text());const got={};walk(apollo(h),"?",got);
    x=Object.values(got).find(g=>g.id===w||normM(g.model)===normM(w));if(x){x.watch=true;HV.items[x.id]=x}else break}
   catch(e){HV.errors.push(`watch ${w}: ${e.message}`);await sl(2000*(t+1))}}
  await sl(300)}
 (x?HV.report.watchFound:HV.report.watchMissing).push(x?`${w} (${x.id})`:w)}

// 3. Spec pages, 2 at a time, with retries. A fridge whose page never loads is reported, not silently lost.
HV.phase="specs";const ids=Object.keys(HV.items);HV.total=ids.length;let i=0;
const want=["Product Width (in.)","Refrigerator Width (in.)","Height to Top of Door Hinge (in.)","Overall Product Height (in.)","Product Height (in.)","Depth (Including Handles) (in.)","Depth (Excluding Handles) (in.)","Product Depth (in.)","Depth (Less Door) (in.)","Depth With Door Open 90 Degrees (in.)","Total Capacity (cu. ft.)","Refrigerator Capacity (cu. ft.)","Ice/Water Dispenser","Installation Depth","Certifications and Listings","Water Filter Replacement Model#","Returnable","Manufacturer Warranty","Remote Access","Appliance Type","General Features"];
const g=(h,re)=>(h.match(re)||[])[1]??null;
const page=async id=>{for(const wait of [0,1000,3000,8000]){if(wait)await sl(wait);
  try{const h=await fetch('https://www.homedepot.com/p/'+id).then(r=>r.text());if(h.length>=200000&&h.includes('"specName"'))return h;HV.errors.push(id+" short page")}
  catch(e){HV.errors.push(id+": "+e.message)}}return null};
const w=async()=>{while(i<ids.length){const id=ids[i++];const x=HV.items[id];const h=await page(id);
 if(!h){HV.report.specFailed.push(id);HV.done++;continue}
 const s={};let m;const re=/"specName":"([^"]+)","specValue":"([^"]*)"/g;while((m=re.exec(h)))if(want.includes(m[1]))s[m[1]]=m[2];
 const feat=(g(h,/"keyProductFeaturesItems":(.{0,2500})/)||"")+(g(h,/"description":"(.{0,2500})/)||"")+(g(h,/"bulletList":\[(.{0,1500})/)||"")+(s["General Features"]||"");
 Object.assign(x,{s,sku:g(h,/"storeSkuNumber":"([^"]+)"/),kwh:g(h,/Yearly Use of (\d{3,4}) ?kWh/i),garage:/garage[- ]ready/i.test(x.label+" "+feat),zero:/zero[\s-]*clearance/i.test(feat),rev:/reversible/i.test(feat)});
 HV.done++;await sl(250)}};
await Promise.all([w(),w()]);

// 4. Rows.
const n=v=>{const m=(v||"").match(/[\d.]+/);return m?+(+m[0]).toFixed(3):""};
const T={"French Door Refrigerator":"FD","Side-by-Side Refrigerator":"SS","Top Freezer Refrigerator":"TF","Bottom Freezer Refrigerator":"BF"};
const guess=l=>/side[- ]by[- ]side/i.test(l)?"SS":/top freezer/i.test(l)?"TF":/bottom freezer/i.test(l)?"BF":/freezerless|all refrigerator/i.test(l)?"FL":"FD";
const clean=t=>(t||"").replace(/[|\n`]/g," ").replace(/\$\{/g,"").replace(/\\/g,"").replace(/\s+/g," ").trim();
const war=w=>{if(!w)return"";w=clean(w);return w.length<=44?w:w.slice(0,44).replace(/\s\S*$/,"")+"…"};
const why=x=>!x.s?"spec page failed":x.brand==="Unbranded"?"unbranded":!n(x.s["Product Width (in.)"]||x.s["Refrigerator Width (in.)"])?"no width":!n(x.s["Total Capacity (cu. ft.)"]||x.s["Refrigerator Capacity (cu. ft.)"])?"no capacity":"";
const keep=[];for(const x of Object.values(HV.items)){const r=why(x);if(r)HV.report.dropped.push({id:x.id,model:x.model,brand:x.brand,reason:r,watch:!!x.watch});else keep.push(x)}
for(const c of Object.keys(HV.report.cats))HV.report.cats[c].kept=keep.filter(x=>x.cat===c).length;
HV.rows=keep.map(x=>{const s=x.s;
 const type=T[s["Appliance Type"]]||(x.cat==="FL"?"FL":x.cat==="?"?guess(x.label+" "+s["Appliance Type"]):x.cat);const pr=x.promo||"";
 const promo=(/Buy More Save More|Spend More/.test(pr)?"B":"")+(/Special Buy/.test(pr)?"S":"");
 const av=x.avail==="Online"?"O":x.avail==="Browse Only"?"B":"S";
 const filt=s["Water Filter Replacement Model#"];const f=(filt&&!/n\/a|none/i.test(filt))?clean(filt).slice(0,24):"";
 return [x.id,x.sku||"",clean(x.model),clean(x.brand),clean(x.label).slice(0,95),type,x.price??"",x.orig??"",x.rating?(+x.rating).toFixed(1):"",x.reviews??"",
  n(s["Product Width (in.)"]||s["Refrigerator Width (in.)"]),n(s["Height to Top of Door Hinge (in.)"]||s["Overall Product Height (in.)"]||s["Product Height (in.)"]),n(s["Depth (Including Handles) (in.)"]||s["Product Depth (in.)"]),n(s["Depth (Less Door) (in.)"])||n(s["Product Depth (in.)"]),n(s["Depth With Door Open 90 Degrees (in.)"]),n(s["Total Capacity (cu. ft.)"]||s["Refrigerator Capacity (cu. ft.)"]),x.kwh??"",
  clean(s["Ice/Water Dispenser"]||"None"),s["Installation Depth"]==="Counter Depth"?"C":"S",/energy star/i.test(s["Certifications and Listings"]||"")?1:0,f,s["Returnable"]==="Non-Returnable"?"N":"R",x.garage?1:0,s["Remote Access"]?1:0,war(s["Manufacturer Warranty"]),promo,av,
  n(s["Depth (Excluding Handles) (in.)"]),x.zero?1:0,x.rev?1:0,x.deliv].join("|")});
HV.phase="done"})();"started"
