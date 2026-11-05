window.HV={phase:"list",items:{},errors:[],done:0,rows:null};
(async()=>{
const sl=ms=>new Promise(r=>setTimeout(r,ms));
const bal=(s,st)=>{let d=0,inS=false,esc=false;for(let i=st;i<s.length;i++){const c=s[i];if(inS){if(esc)esc=false;else if(c==='\\')esc=true;else if(c==='"')inS=false;continue}if(c==='"')inS=true;else if(c==='{')d++;else if(c==='}'){d--;if(d===0)return s.slice(st,i+1)}}};
const cats={FD:"https://www.homedepot.com/b/Appliances-Refrigerators-French-Door-Refrigerators/N-5yc1vZc3oo",SS:"https://www.homedepot.com/b/Appliances-Refrigerators-Side-by-Side-Refrigerators/N-5yc1vZc3q0",TF:"https://www.homedepot.com/b/Appliances-Refrigerators-Top-Freezer-Refrigerators/N-5yc1vZc3ns",BF:"https://www.homedepot.com/b/Appliances-Refrigerators-Bottom-Freezer-Refrigerators/N-5yc1vZc3p6",FL:"https://www.homedepot.com/b/Appliances-Refrigerators-Freezerless-Refrigerators/N-5yc1vZc3p9"};
const take=(o,cat)=>{if(HV.items[o.itemId])return;const pk=k=>Object.keys(o).find(x=>x.startsWith(k));const p=o[pk("pricing")]||{};const fu=JSON.stringify(o[pk("fulfillment")]||{});
 HV.items[o.itemId]={id:o.itemId,cat,brand:o.identifiers?.brandName,label:o.identifiers?.productLabel,model:o.identifiers?.modelNumber,price:p.value??null,orig:p.original??null,promo:p.promotion?.savingsCenterPromos||"",rating:o.reviews?.ratingsReviews?.averageRating??null,reviews:o.reviews?.ratingsReviews?.totalReviews??null,avail:o.availabilityType?.type,deliv:(fu.match(/"earliestDeliveryDate":"([^"]+)"/)||[])[1]||""}};
const walk=(o,cat)=>{if(!o||typeof o!=="object")return;if(Array.isArray(o)){o.forEach(x=>walk(x,cat));return}
 if(o.itemId&&/^\d{9}$/.test(o.itemId)&&o.identifiers&&Object.keys(o).some(k=>k.startsWith("pricing")))take(o,cat);for(const k in o)walk(o[k],cat)};
for(const [cat,url] of Object.entries(cats)){let tot=999;for(let n=0;n<tot&&n<480;n+=12){try{const h=await fetch(url+(n?"?Nao="+n:"")).then(r=>r.text());
 if(n===0){const m=h.match(/"totalProducts":(\d+)/);tot=m?+m[1]:0}walk(JSON.parse(bal(h,h.indexOf('__APOLLO_STATE__=')+17)),cat)}catch(e){HV.errors.push(cat+n+": "+e.message)}await sl(300)}}
HV.phase="specs";const ids=Object.keys(HV.items);HV.total=ids.length;let i=0;
const want=["Product Width (in.)","Refrigerator Width (in.)","Height to Top of Door Hinge (in.)","Overall Product Height (in.)","Product Height (in.)","Depth (Including Handles) (in.)","Depth (Excluding Handles) (in.)","Product Depth (in.)","Depth (Less Door) (in.)","Depth With Door Open 90 Degrees (in.)","Total Capacity (cu. ft.)","Refrigerator Capacity (cu. ft.)","Ice/Water Dispenser","Installation Depth","Certifications and Listings","Water Filter Replacement Model#","Returnable","Manufacturer Warranty","Remote Access","Appliance Type","General Features"];
const g=(h,re)=>(h.match(re)||[])[1]??null;
const w=async()=>{while(i<ids.length){const id=ids[i++];try{const h=await fetch('https://www.homedepot.com/p/'+id).then(r=>r.text());
 if(h.length<200000){HV.errors.push(id+" short");await sl(3000);continue}
 const s={};let m;const re=/"specName":"([^"]+)","specValue":"([^"]*)"/g;while((m=re.exec(h)))if(want.includes(m[1]))s[m[1]]=m[2];
 const feat=(g(h,/"keyProductFeaturesItems":(.{0,2500})/)||"")+(g(h,/"description":"(.{0,2500})/)||"")+(g(h,/"bulletList":\[(.{0,1500})/)||"")+(s["General Features"]||"");
 Object.assign(HV.items[id],{s,sku:g(h,/"storeSkuNumber":"([^"]+)"/),kwh:g(h,/Yearly Use of (\d{3,4}) ?kWh/i),garage:/garage[- ]ready/i.test(HV.items[id].label+" "+feat),zero:/zero[\s-]*clearance/i.test(feat),rev:/reversible/i.test(feat)});HV.done++;
 }catch(e){HV.errors.push(id+": "+e.message)}await sl(150)}};
await Promise.all([w(),w(),w()]);
const n=v=>{const m=(v||"").match(/[\d.]+/);return m?+(+m[0]).toFixed(3):""};
const T={"French Door Refrigerator":"FD","Side-by-Side Refrigerator":"SS","Top Freezer Refrigerator":"TF","Bottom Freezer Refrigerator":"BF"};
const clean=t=>(t||"").replace(/[|\n`]/g," ").replace(/\$\{/g,"").replace(/\\/g,"").replace(/\s+/g," ").trim();
const war=w=>{if(!w)return"";w=clean(w);return w.length<=44?w:w.slice(0,44).replace(/\s\S*$/,"")+"…"};
HV.rows=Object.values(HV.items).filter(x=>x.s&&x.brand!=="Unbranded"&&n(x.s["Product Width (in.)"]||x.s["Refrigerator Width (in.)"])&&n(x.s["Total Capacity (cu. ft.)"]||x.s["Refrigerator Capacity (cu. ft.)"])).map(x=>{const s=x.s;
 const type=T[s["Appliance Type"]]||(x.cat==="FL"?"FL":x.cat);const pr=x.promo||"";
 const promo=(/Buy More Save More|Spend More/.test(pr)?"B":"")+(/Special Buy/.test(pr)?"S":"");
 const av=x.avail==="Online"?"O":x.avail==="Browse Only"?"B":"S";
 const filt=s["Water Filter Replacement Model#"];const f=(filt&&!/n\/a|none/i.test(filt))?clean(filt).slice(0,24):"";
 return [x.id,x.sku||"",clean(x.model),clean(x.brand),clean(x.label).slice(0,95),type,x.price??"",x.orig??"",x.rating?(+x.rating).toFixed(1):"",x.reviews??"",
  n(s["Product Width (in.)"]||s["Refrigerator Width (in.)"]),n(s["Height to Top of Door Hinge (in.)"]||s["Overall Product Height (in.)"]||s["Product Height (in.)"]),n(s["Depth (Including Handles) (in.)"]||s["Product Depth (in.)"]),n(s["Depth (Less Door) (in.)"])||n(s["Product Depth (in.)"]),n(s["Depth With Door Open 90 Degrees (in.)"]),n(s["Total Capacity (cu. ft.)"]||s["Refrigerator Capacity (cu. ft.)"]),x.kwh??"",
  clean(s["Ice/Water Dispenser"]||"None"),s["Installation Depth"]==="Counter Depth"?"C":"S",/energy star/i.test(s["Certifications and Listings"]||"")?1:0,f,s["Returnable"]==="Non-Returnable"?"N":"R",x.garage?1:0,s["Remote Access"]?1:0,war(s["Manufacturer Warranty"]),promo,av,
  n(s["Depth (Excluding Handles) (in.)"]),x.zero?1:0,x.rev?1:0,x.deliv].join("|")});
HV.phase="done"})();"started"