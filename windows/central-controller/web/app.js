(() => {
'use strict';
let token = null, busy = false, feedIsDemo = true, currentChannels = []; 
const el=id=>document.getElementById(id);
const toast=(message)=>{const t=el('toast');t.textContent=message;t.style.display='block';clearTimeout(toast.timer);toast.timer=setTimeout(()=>t.style.display='none',6500)};
async function api(path,method='GET',body=null){
  const response=await fetch('/api/'+path,{method,headers:{...(token?{'Authorization':'Bearer '+token}:{}),...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined,cache:'no-store'});
  const obj=await response.json();if(!response.ok)throw Error(obj.error||('HTTP '+response.status));return obj;
}
el('loginform').addEventListener('submit',async ev=>{ev.preventDefault();try{const r=await api('login','POST',{password:el('pw').value});token=r.token;el('pw').value='';el('loginerror').textContent='';el('signin').hidden=true;el('dashboard').hidden=false;el('logout').hidden=false;await refresh()}catch(e){el('loginerror').textContent=e.message}});
el('logout').addEventListener('click',async()=>{try{await api('logout','POST',{})}catch(_){}token=null;el('signin').hidden=false;el('dashboard').hidden=true;el('logout').hidden=true});
function node(tag,text,className){const x=document.createElement(tag);if(text!==undefined)x.textContent=text;if(className)x.className=className;return x}
function control(label,onclick,css='',disabled=false){const b=node('button',label,css);b.disabled=disabled;b.addEventListener('click',onclick);return b}
function renderChannels(data){currentChannels=data;feedIsDemo=data.some(ch=>String(ch.sourceMode).includes('TEST MEDIA'));const root=el('channels');root.replaceChildren();let active=0;
  data.forEach(ch=>{if(['starting','recording','stopping','finalizing'].includes(ch.state))active++;
    const card=node('article',undefined,'channel'), top=node('div',undefined,'channeltop');top.append(node('span','▣  Channel '+ch.channel));top.append(node('span',ch.state.toUpperCase(),'chip '+ch.state));card.append(top);
    const last=ch.last, title=last?.course||'Not assigned';card.append(node('h3',title));card.append(node('div',last?(last.subject+' · '+last.topic):'Ready for a scheduled session','topic'));
    card.append(node('div','Input: '+ch.sourceMode+'  ·  '+(ch.configured?'Configured':'NOT CONFIGURED'),'source'));
    if(last)card.append(node('div','Last session '+last.session_id+' · '+(last.detail||'')+' · NAS: '+last.archive_state,'note'));
    else card.append(node('div','Each channel is an independent FFmpeg recorder.','note'));
    const actions=node('div',undefined,'controls');
    actions.append(control('Start recording',()=>openDialog(ch.channel),'',!ch.configured||activeState(ch.state)));
    actions.append(control('Stop & save MP4',()=>stop(ch.channel),'stop',!['recording','starting'].includes(ch.state)));
    card.append(actions);root.append(card);
  });el('health').textContent=active+' of 4 channels active';
}
function activeState(s){return ['starting','recording','stopping','finalizing'].includes(s)}
const dialog=el('startdialog');
function openDialog(channel, session=null){
  el('channel').value=channel;el('dialogchannel').textContent=channel;
  for(const id of ['sessionId','course','subject','topic','faculty','facultyId'])el(id).value=session?(session[id]||''):'';
  const source=currentChannels.find(ch=>ch.channel==channel);
  const mode=source?.sourceMode||'unconfigured';
  el('recordingwarning').textContent='INPUT MODE: '+mode+'. This does not join Zoom. Only verified media from the configured source will be recorded.';
  el('recordsubmit').textContent=mode.includes('TEST MEDIA')?'Record TEST MEDIA (not Zoom)':'Start configured recording source';
  dialog.showModal();
}
function renderSessions(result){
  el('feedstate').textContent=result.state==='connected'?'Mac Admin connected':'Mac Admin '+result.state;
  el('feedmessage').textContent=result.message||'';
  const root=el('sessions');root.replaceChildren();
  if(result.state!=='connected'){root.append(node('div','No synchronized sessions available. Pair the Mac Admin feed first.','empty'));return}
  if(!result.sessions.length){root.append(node('div','No classes assigned by Admin yet. Create a session in the Mac Admin dashboard.','empty'));return}
  result.sessions.forEach(item=>{
    const card=node('article',undefined,'session-card');
    const now=Date.now()/1000;
    const schedule=(now>=item.startsAt&&now<item.endsAt)?'Within scheduled window':(now<item.startsAt?'Upcoming':'Past');
    card.append(node('strong',item.course+' · '+item.subject));
    card.append(node('div',item.topic,'topic'));
    card.append(node('div','Faculty '+item.facultyId+' · '+new Date(item.startsAt*1000).toLocaleString(),'source'));
    card.append(node('div',schedule+' (not meeting status)','note'));
    const select=node('select');select.setAttribute('aria-label','Select recorder channel for '+item.sessionId);
    currentChannels.forEach(ch=>{const op=node('option','Channel '+ch.channel+' · '+ch.sourceMode);op.value=ch.channel;op.disabled=!ch.configured||activeState(ch.state);select.append(op)});
    const actions=node('div',undefined,'controls');actions.append(select);
    const active=currentChannels.some(ch=>ch.configured&&!activeState(ch.state));
    actions.append(control('Prepare channel',()=>openDialog(select.value,{...item,faculty:item.facultyId}), 'ghost',!active));
    card.append(actions);root.append(card);
  });
}
el('cancel').addEventListener('click',()=>dialog.close());
el('startform').addEventListener('submit',async ev=>{
  ev.preventDefault();if(busy)return;busy=true;
  const obj={channel:el('channel').value};for(const id of ['sessionId','course','subject','topic','faculty','facultyId'])obj[id]=el(id).value;
  try{const res=await api('start','POST',obj);dialog.close();toast('Recorder process started: '+res.id+'. Waiting for actual media.');await refresh()}
  catch(e){toast('Cannot start: '+e.message)}finally{busy=false}
});
async function stop(channel){if(busy)return;busy=true;try{toast('Flushing and validating recording...');const res=await api('stop','POST',{channel});toast('Verified MP4 ready: '+res.recording.id);await refresh()}catch(e){toast('Stop issue: '+e.message)}finally{busy=false}}
async function recover(rid){try{await api('recover','POST',{id:rid});toast('Recovery complete: '+rid);await refresh()}catch(e){toast('Recovery failed: '+e.message)}}
async function retry(rid){try{await api('archive/retry','POST',{id:rid});toast('NAS archive retry started')}catch(e){toast(e.message)}}
async function mediaUrl(rid,disposition='play'){const ticket=await api('media-ticket','POST',{id:rid});return '/media/'+rid+'?ticket='+encodeURIComponent(ticket.ticket)+'&disposition='+disposition}
async function play(rid){try{const url=await mediaUrl(rid);const v=document.createElement('video');v.controls=true;v.autoplay=true;v.preload='metadata';v.src=url;v.style.width='100%';v.style.maxWidth='800px';const old=el('inline-player');if(old){old.pause();old.remove()};v.id='inline-player';el('records').prepend(v)}catch(e){toast(e.message)}}
async function download(rid){try{const url=await mediaUrl(rid,'download');const a=document.createElement('a');a.href=url;a.download='DocTutorials-'+rid+'.mp4';document.body.append(a);a.click();a.remove()}catch(e){toast(e.message)}}
function renderRecordings(list){const root=el('records');const current=el('inline-player');root.replaceChildren();if(current)root.append(current);if(!list.length){root.append(node('div','No finished recordings yet.','empty'));return}
 list.forEach(r=>{const row=node('div',undefined,'record');row.append(node('span','Channel '+r.channel+' · '+r.state));
 const description=node('span',r.course+' / '+r.subject+' / '+r.topic);description.append(node('small',r.faculty_id+' · '+r.session_id));row.append(description);
 row.append(node('span',r.duration?Math.round(r.duration)+' sec':'—'));row.append(node('span','NAS: '+r.archive_state));
 const actions=node('span',undefined,'actions');
 if(r.state==='ready'){actions.append(control('Play',()=>play(r.id),'ghost'));actions.append(control('Download',()=>download(r.id),'ghost'))}
 if(['interrupted','failed'].includes(r.state))actions.append(control('Recover',()=>recover(r.id),'ghost'));
 if(r.state==='ready'&&r.archive_state==='failed')actions.append(control('Retry NAS',()=>retry(r.id),'ghost'));
 row.append(actions);root.append(row)})
}
async function refresh(){if(!token)return;try{const [channels,records,sessions]=await Promise.all([api('channels'),api('recordings'),api('sessions')]);renderChannels(channels.channels);renderSessions(sessions);renderRecordings(records.recordings)}catch(e){toast(e.message)}}
el('refresh').addEventListener('click',refresh);setInterval(()=>{if(token&&!busy)refresh()},3500);
})();
