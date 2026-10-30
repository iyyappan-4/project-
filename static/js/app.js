const ATLAS_V2_BUILD='REAL-TRAFFIC-5055-DIRECTIONAL';
let S=null, chart=null, demoTimer=null;
const $=id=>document.getElementById(id);
const NAMES={N:'NORTH',E:'EAST',S:'SOUTH',W:'WEST'};
async function post(action,data={}){const r=await fetch('/api/control',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,...data})});return r.json()}
async function refresh(){try{const r=await fetch('/api/state');S=await r.json();render()}catch(e){$('connection').className='pill';$('connection').textContent='● OFFLINE'}}
async function tick(){try{const r=await fetch('/api/tick',{method:'POST'});S=await r.json();render()}catch(e){}}
function render(){
 $('connection').textContent=S.running?'● SYSTEM ONLINE':'● PAUSED';$('connection').className='pill '+(S.running?'ok':'');
 $('vehicles').textContent=S.vehicles;$('congestion').textContent=S.congestion+'%';$('congBar').style.width=S.congestion+'%';
 $('wait').textContent=S.avg_wait+'s';$('throughput').textContent=S.throughput;$('decisions').textContent=S.decisions;
 $('densityOut').textContent=S.density+'%';$('density').value=S.density;$('greenRoad').textContent=NAMES[S.phase];$('timer').textContent=String(S.remaining).padStart(2,'0');
 $('mode').textContent=S.ai_enabled?'AI ADAPTIVE':'FIXED CYCLE';$('reason').textContent=S.emergency?S.emergency.kind+' priority override':(S.accident?'Incident response active':'Adaptive pressure optimization');
 ['N','E','S','W'].forEach(r=>{$('q'+r).textContent=S.roads[r].queue;$('sig'+r).classList.toggle('green',r===S.phase)});
 $('incident').style.display=S.accident?'block':'none';$('emergency').style.display=S.emergency?'block':'none';
 let best=S.phase;
 $('roadCards').innerHTML=['N','E','S','W'].map(r=>{let d=S.roads[r],active=r===best;return `<div class="road-card ${active?'active':''}"><div class="rc-top"><span>${NAMES[r]} ${active?'— GREEN':''}</span><span class="score">${d.score.toFixed(1)}</span></div><div class="bar"><i style="width:${Math.min(100,d.score)}%"></i></div><small style="color:#657285;font-size:9px">Queue ${d.queue} · Wait ${d.wait.toFixed(0)}s · Speed ${d.speed} km/h</small></div>`}).join('');
 $('explanation').textContent=S.emergency?`${S.emergency.kind} detected on ${NAMES[S.emergency.road]}. Normal cycle is overridden and ${NAMES[S.emergency.road]} receives priority.`:`${NAMES[best]} selected because it currently has the highest combined traffic pressure. Green time is ${S.green_time}s.`;
 $('logs').innerHTML=S.logs.map(x=>`<div class="log"><time>${x.time}</time><tag>${x.tag}</tag><msg>${x.msg}</msg></div>`).join('');
 $('directionCards').innerHTML=['N','E','S','W'].map(r=>{const d=S.roads[r];return `<div class="direction-card ${r===S.phase?'selected':''}"><div class="direction-title"><b>${NAMES[r]}</b><span>${r===S.phase?'● GREEN':'● RED'}</span></div><div class="direction-stats"><div><small>VEHICLES</small><strong>${d.flow}</strong></div><div><small>CONGESTION</small><strong class="congestion-value">${d.congestion}%</strong></div><div><small>INJECTED</small><strong>${d.injected}</strong></div><div><small>QUEUE</small><strong>${d.queue}</strong></div></div><div class="direction-bar"><i style="width:${d.congestion}%"></i></div><div class="status-line"><span>AVG WAIT <b>${d.wait.toFixed(1)}s</b></span><span>SPEED <b>${d.speed} km/h</b></span></div><div class="direction-input"><input id="inject-${r}" type="number" min="1" max="30" value="8" aria-label="Vehicles to inject on ${NAMES[r]}"><button onclick="injectFromCard('${r}')">+ INJECT</button></div><button class="amb-btn" onclick="emergency('${r}','AMBULANCE')">🚑 AMBULANCE → ${NAMES[r]}</button></div>`}).join('');
 drawCars();updateChart();
}
function drawCars(){
 const box=$('cars');const seen=new Set();
 Object.entries(S.roads).forEach(([r,d])=>d.vehicles.forEach(v=>{const id=`car-${r}-${v.id}`;seen.add(id);let el=document.getElementById(id);if(!el){el=document.createElement('div');el.id=id;el.className='car';box.appendChild(el)}el.classList.toggle('em',S.emergency&&S.emergency.road===r);el.classList.toggle('moving',v.speed>1);const p=Math.max(0,Math.min(118,v.position));const lane=6+Math.min(88,p*0.31);if(r==='N'){el.style.left='calc(50% - 7px)';el.style.top=`${lane}%`;el.style.transform='rotate(180deg)'}if(r==='S'){el.style.left='calc(50% - 7px)';el.style.top=`${100-lane}%`;el.style.transform='rotate(0deg)'}if(r==='E'){el.style.left=`${100-lane}%`;el.style.top='calc(50% - 7px)';el.style.transform='rotate(270deg)'}if(r==='W'){el.style.left=`${lane}%`;el.style.top='calc(50% - 7px)';el.style.transform='rotate(90deg)'}}));
 [...box.children].forEach(el=>{if(!seen.has(el.id))el.remove()});
}
function updateChart(){if(!chart){chart=new Chart($('chart'),{type:'line',data:{labels:[],datasets:[{label:'Congestion %',data:[],borderWidth:2,tension:.35},{label:'Avg wait (s)',data:[],borderWidth:2,tension:.35}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#aeb9c8',font:{size:10}}}},scales:{x:{ticks:{display:false},grid:{color:'#18212b'}},y:{ticks:{color:'#64748b'},grid:{color:'#18212b'}}}}})}let h=S.history;chart.data.labels=h.congestion.map((_,i)=>i);chart.data.datasets[0].data=h.congestion;chart.data.datasets[1].data=h.wait;chart.update('none')}
async function inject(r,count=8){count=Math.max(1,Math.min(30,parseInt(count,10)||8));await post('inject',{road:r,count});await refresh()}
async function injectFromCard(r){const input=$('inject-'+r);await inject(r,input?input.value:8)}
async function emergency(r,k){await post('emergency',{road:r,kind:k});await refresh()}
async function accident(r){await post('accident',{road:r});await refresh()}
async function clearAccident(){await post('clear_accident');await refresh()}
$('density').oninput=async e=>{await post('density',{value:e.target.value});await refresh()}
document.querySelectorAll('[data-density]').forEach(b=>b.onclick=()=>post('density',{value:b.dataset.density}).then(refresh));
$('runBtn').onclick=async()=>{await post('start');await post('ai',{enabled:true});refresh()};
$('demoBtn').onclick=async()=>{let s=await post('demo');$('demoBtn').textContent=s.demo_mode?'■ STOP DEMO':'▶ DEMO MODE';if(s.demo_mode&&!demoTimer){demoTimer=setInterval(async()=>{tick()},1000)}else if(!s.demo_mode&&demoTimer){clearInterval(demoTimer);demoTimer=null}refresh()};
setInterval(tick,1000);refresh();
