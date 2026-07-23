(function(){
  'use strict';

  /* v4.16 — stable theme/audio UI, draggable seek bar, full-screen Mushaf and
     one authoritative native compass path. */
  var surahNames=['الفاتحة','البقرة','آل عمران','النساء','المائدة','الأنعام','الأعراف','الأنفال','التوبة','يونس','هود','يوسف','الرعد','إبراهيم','الحجر','النحل','الإسراء','الكهف','مريم','طه','الأنبياء','الحج','المؤمنون','النور','الفرقان','الشعراء','النمل','القصص','العنكبوت','الروم','لقمان','السجدة','الأحزاب','سبأ','فاطر','يس','الصافات','ص','الزمر','غافر','فصلت','الشورى','الزخرف','الدخان','الجاثية','الأحقاف','محمد','الفتح','الحجرات','ق','الذاريات','الطور','النجم','القمر','الرحمن','الواقعة','الحديد','المجادلة','الحشر','الممتحنة','الصف','الجمعة','المنافقون','التغابن','الطلاق','التحريم','الملك','القلم','الحاقة','المعارج','نوح','الجن','المزمل','المدثر','القيامة','الإنسان','المرسلات','النبأ','النازعات','عبس','التكوير','الانفطار','المطففين','الانشقاق','البروج','الطارق','الأعلى','الغاشية','الفجر','البلد','الشمس','الليل','الضحى','الشرح','التين','العلق','القدر','البينة','الزلزلة','العاديات','القارعة','التكاثر','العصر','الهمزة','الفيل','قريش','الماعون','الكوثر','الكافرون','النصر','المسد','الإخلاص','الفلق','الناس'];
  var oldShowPage=window.showPage;
  var oldDownloadState=window.onNativeAudioDownloadState;
  var audio={items:[],filter:'all',query:'',surah:114,name:'الناس',playing:false,buffering:false,position:0,duration:0,active:false,seeking:false,downloads:{}};
  var listObserver=null;
  var lastNativeHeading=NaN;

  function bridge(){return window.AndroidBridge||null}
  function callBridge(method){
    var nativeBridge=bridge();if(!nativeBridge||typeof nativeBridge[method]!=='function')return false;
    try{nativeBridge[method].apply(nativeBridge,Array.prototype.slice.call(arguments,1));return true}catch(ignore){return false}
  }
  function esc(value){return String(value||'').replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
  function normalize(value){return String(value||'').normalize('NFC').replace(/[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]/g,'').replace(/[أإآٱ]/g,'ا').replace(/ى/g,'ي').replace(/ة/g,'ه').replace(/ـ/g,'').replace(/[^\u0621-\u064A0-9 ]/g,' ').replace(/\s+/g,' ').trim()}
  function arabic(value){return typeof arabicNumber==='function'?arabicNumber(value):String(value)}
  function formatTime(milliseconds){
    var seconds=Math.max(0,Math.floor((Number(milliseconds)||0)/1000));
    var minutes=Math.floor(seconds/60),remaining=String(seconds%60).padStart(2,'0');
    return arabic(minutes)+':'+arabic(remaining);
  }

  /* ---------- Real light/dark theme ---------- */
  function resolvedTheme(preference){
    if(preference==='system')return window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
    return preference==='dark'||preference==='sepia'?preference:'light';
  }
  function applyTheme416(){
    var preference=localStorage.getItem('theme')||'system';
    var theme=resolvedTheme(preference);
    document.documentElement.dataset.theme=theme;
    document.documentElement.dataset.themePreference=preference;
    if(document.body)document.body.dataset.theme=theme;
    var select=document.getElementById('themeSelect');if(select&&select.value!==preference)select.value=preference;
    var meta=document.querySelector('meta[name="theme-color"]');if(meta)meta.content=theme==='dark'?'#031f19':(theme==='sepia'?'#6d5936':'#f3f5f2');
  }
  window.setTheme=function(value){
    value=['system','light','dark','sepia'].indexOf(value)>=0?value:'system';
    localStorage.setItem('theme',value);applyTheme416();
    if(typeof toast==='function')toast('تم تغيير المظهر');
  };
  window.cycleTheme=function(){
    var current=resolvedTheme(localStorage.getItem('theme')||'system');
    window.setTheme(current==='dark'?'light':'dark');
  };

  /* ---------- Stable audio list and filters ---------- */
  function packaged(number){return number>=46&&number<=114}
  function fallbackItem(number){return {surah:number,builtIn:packaged(number),downloaded:false,available:packaged(number),bytes:0}}
  function item(number){return audio.items[number-1]||fallbackItem(number)}
  function isLoaded(data){return !!(data&&((data.builtIn||data.downloaded||data.available))) }
  function sizeLabel(bytes){
    bytes=Number(bytes||0);if(!bytes)return '';
    return bytes<1048576?Math.max(1,Math.round(bytes/1024))+' ك.ب':(bytes/1048576).toFixed(bytes>10485760?0:1)+' م.ب';
  }
  function refreshAvailability(){
    var nativeBridge=bridge();
    if(nativeBridge&&typeof nativeBridge.getAudioAvailabilityJson==='function'){
      try{var parsed=JSON.parse(nativeBridge.getAudioAvailabilityJson()||'{}');if(parsed&&Array.isArray(parsed.items))audio.items=parsed.items}catch(ignore){}
    }
    if(!audio.items.length)audio.items=surahNames.map(function(_,index){return fallbackItem(index+1)});
    renderAudioList();
  }
  function installFilters(){
    var page=document.getElementById('page-audio'),search=page&&page.querySelector('.audio-search');if(!page||!search)return;
    var bar=document.getElementById('audioAvailabilityFilters');
    if(!bar){
      bar=document.createElement('div');bar.id='audioAvailabilityFilters';bar.className='audio-availability-filters';
      bar.innerHTML='<button type="button" data-audio-filter="all">الكل</button><button type="button" data-audio-filter="loaded">المحمّل</button><button type="button" data-audio-filter="missing">غير المحمّل</button>';
      search.parentNode.insertBefore(bar,search);
      bar.addEventListener('click',function(event){
        var button=event.target.closest('[data-audio-filter]');if(!button)return;
        audio.filter=button.dataset.audioFilter||'all';renderAudioList();
      });
    }
    bar.querySelectorAll('button').forEach(function(button){button.classList.toggle('active',button.dataset.audioFilter===audio.filter)});
  }
  function actionMarkup(number,data){
    var state=audio.downloads[number];
    if(state&&state.status==='downloading')return '<span class="v416-download-progress">'+Math.max(0,Math.min(99,state.progress||0))+'٪</span>';
    if(state&&state.status==='queued')return '<span class="v416-download-progress">انتظار</span>';
    if(data.builtIn)return '<span class="audio-local-badge">داخل التطبيق</span>';
    if(data.downloaded||data.available)return '<span class="audio-local-badge downloaded">محمّلة</span>';
    return '<button type="button" class="audio-row-action download" data-v416-action="download" data-surah="'+number+'">تحميل'+(data.bytes?' · '+sizeLabel(data.bytes):'')+'</button>';
  }
  function renderAudioList(){
    installFilters();
    var box=document.getElementById('audioSurahList');if(!box)return;
    var search=document.getElementById('audioSurahSearch');audio.query=normalize(search?search.value:'');
    var html='';
    for(var index=0;index<surahNames.length;index++){
      var number=index+1,name=surahNames[index],data=item(number),loaded=isLoaded(data);
      if(audio.query&&normalize(name).indexOf(audio.query)<0)continue;
      if(audio.filter==='loaded'&&!loaded)continue;
      if(audio.filter==='missing'&&loaded)continue;
      var current=audio.active&&audio.surah===number;
      var subtitle=data.builtIn?'عادل ريان — يعمل دون إنترنت':(loaded?'عادل ريان — محمّلة على الهاتف':'عادل ريان — تحتاج تحميلًا مرة واحدة');
      html+='<div class="compact-audio-row v416-row '+(loaded?'available':'missing')+(current?' current':'')+'" data-surah="'+number+'">'+
        '<button type="button" class="audio-row-main" data-v416-action="'+(loaded?'play':'download')+'" data-surah="'+number+'" data-name="'+esc(name)+'">'+
        '<span class="audio-number">'+arabic(number)+'</span><span class="audio-row-copy"><b>سورة '+esc(name)+'</b><small>'+subtitle+'</small></span><i class="v416-play-icon">'+(current&&audio.playing?'❚❚':'▶')+'</i></button>'+actionMarkup(number,data)+'</div>';
    }
    box.dataset.v416Rendering='1';
    box.innerHTML=html||'<div class="empty">لا توجد سورة مطابقة لهذا القسم.</div>';
    delete box.dataset.v416Rendering;
    var buttons=document.querySelectorAll('#audioAvailabilityFilters button');buttons.forEach(function(button){button.classList.toggle('active',button.dataset.audioFilter===audio.filter)});
  }
  function play(number,name){
    number=Number(number)||1;var data=item(number);if(!isLoaded(data))return startDownload(number);
    audio.surah=number;audio.name=name||surahNames[number-1];audio.buffering=true;audio.active=true;
    updatePlayer();updateCurrentRows();
    if(!callBridge('playSurah',number,audio.name)&&typeof toast==='function')toast('تشغيل الصوت متاح داخل تطبيق Android');
    else callBridge('requestNotificationPermission');
  }
  function startDownload(number){
    number=Number(number)||0;if(number<1||number>114)return;
    audio.downloads[number]={status:'queued',progress:0};renderAudioList();
    if(!callBridge('downloadSurahAudio',number)){
      delete audio.downloads[number];renderAudioList();if(typeof toast==='function')toast('التنزيل متاح داخل تطبيق Android فقط');return;
    }
    callBridge('requestNotificationPermission');if(typeof toast==='function')toast('بدأ تنزيل سورة '+surahNames[number-1]);
  }
  function bindAudioList(){
    var box=document.getElementById('audioSurahList');if(!box)return;
    if(box.dataset.v416Bound!=='1'){
      box.dataset.v416Bound='1';
      box.addEventListener('click',function(event){
        var control=event.target.closest('[data-v416-action]');if(!control)return;
        event.preventDefault();event.stopImmediatePropagation();
        var number=Number(control.dataset.surah||0),action=control.dataset.v416Action;
        if(action==='play')play(number,control.dataset.name||surahNames[number-1]);else startDownload(number);
      },true);
    }
    if(!listObserver){
      listObserver=new MutationObserver(function(){
        if(box.dataset.v416Rendering==='1')return;
        if(box.children.length&&!box.querySelector('.v416-row')&&!box.querySelector('.empty'))setTimeout(renderAudioList,0);
      });
      listObserver.observe(box,{childList:true});
    }
    var input=document.getElementById('audioSurahSearch');
    if(input&&input.dataset.v416Bound!=='1'){
      input.dataset.v416Bound='1';input.addEventListener('input',function(){setTimeout(renderAudioList,25)});
    }
  }

  /* ---------- Player seek bar ---------- */
  function installSeekBar(){
    var player=document.getElementById('audioMiniPlayer');if(!player)return;
    var old=player.querySelector('.offline-audio-progress');if(old)old.remove();
    var wrap=document.getElementById('v416AudioSeek');
    if(!wrap){
      wrap=document.createElement('div');wrap.id='v416AudioSeek';wrap.className='v416-audio-seek';
      wrap.innerHTML='<input id="audioSeekRange" type="range" min="0" max="1000" value="0" step="1" aria-label="موضع التلاوة"><div class="v416-audio-times"><small id="audioElapsed">٠:٠٠</small><small id="audioDuration">٠:٠٠</small></div>';
      player.appendChild(wrap);
      var range=document.getElementById('audioSeekRange');
      var begin=function(){audio.seeking=true};
      range.addEventListener('pointerdown',begin);range.addEventListener('touchstart',begin,{passive:true});
      range.addEventListener('input',function(){
        audio.seeking=true;var target=audio.duration*(Number(this.value)||0)/1000;
        var elapsed=document.getElementById('audioElapsed');if(elapsed)elapsed.textContent=formatTime(target);
      });
      var commit=function(){
        var target=Math.round(audio.duration*(Number(range.value)||0)/1000);
        if(audio.duration>0)callBridge('seekAudio',target);
        audio.position=target;audio.seeking=false;updateSeek();
      };
      range.addEventListener('change',commit);range.addEventListener('pointerup',commit);range.addEventListener('touchend',commit,{passive:true});
    }
  }
  function updateSeek(){
    installSeekBar();var range=document.getElementById('audioSeekRange');
    if(range&&!audio.seeking)range.value=audio.duration?String(Math.round(audio.position*1000/audio.duration)):'0';
    var elapsed=document.getElementById('audioElapsed');if(elapsed&&!audio.seeking)elapsed.textContent=formatTime(audio.position);
    var duration=document.getElementById('audioDuration');if(duration)duration.textContent=formatTime(audio.duration);
  }
  function updatePlayer(){
    installSeekBar();var player=document.getElementById('audioMiniPlayer');if(!player)return;
    player.classList.toggle('hidden',!audio.active);
    var title=document.getElementById('audioMiniTitle');if(title)title.textContent='سورة '+audio.name;
    var artist=player.querySelector('.audio-mini-info small');if(artist)artist.textContent='عادل ريان';
    var button=document.getElementById('audioMainButton');if(button)button.textContent=audio.buffering?'…':(audio.playing?'❚❚':'▶');
    updateSeek();
  }
  function updateCurrentRows(){
    document.querySelectorAll('#audioSurahList .v416-row').forEach(function(row){
      var current=audio.active&&Number(row.dataset.surah)===audio.surah;row.classList.toggle('current',current);
      var icon=row.querySelector('.v416-play-icon');if(icon)icon.textContent=current&&audio.playing?'❚❚':'▶';
    });
  }
  window.playAudioSurah=function(number,name){play(number,name)};
  window.onNativeAudioState=function(playing,surah,name,buffering,position,duration,active,error){
    audio.playing=!!playing;audio.surah=Number(surah)||audio.surah;audio.name=name||surahNames[audio.surah-1]||audio.name;
    audio.buffering=!!buffering;audio.position=Math.max(0,Number(position)||0);audio.duration=Math.max(0,Number(duration)||0);
    audio.active=arguments.length>=7?!!active:true;
    updatePlayer();updateCurrentRows();
    if(error&&typeof toast==='function')toast(error);
  };
  window.onNativeAudioDownloadState=function(number,status,progress,bytes,total,error){
    number=Number(number)||0;if(number){
      audio.downloads[number]={status:String(status||''),progress:Number(progress||0),bytes:Number(bytes||0),total:Number(total||0)};
      if(status==='completed'||status==='error')delete audio.downloads[number];
    }
    if(typeof oldDownloadState==='function')oldDownloadState.apply(this,arguments);
    if(status==='completed'||status==='error')setTimeout(refreshAvailability,80);else renderAudioList();
    if(status==='error'&&error&&typeof toast==='function')toast(error);
  };

  /* ---------- One native compass source ---------- */
  function normalizeDegrees(value){value=Number(value)||0;return (value%360+360)%360}
  function qiblaBearing(latitude,longitude){
    var lat1=Number(latitude)*Math.PI/180,lat2=21.422487*Math.PI/180;
    var deltaLon=(39.826206-Number(longitude))*Math.PI/180;
    var y=Math.sin(deltaLon)*Math.cos(lat2);
    var x=Math.cos(lat1)*Math.sin(lat2)-Math.sin(lat1)*Math.cos(lat2)*Math.cos(deltaLon);
    return normalizeDegrees(Math.atan2(y,x)*180/Math.PI);
  }
  function ensureQiblaStatus(){
    var card=document.querySelector('.qibla-card');if(!card)return null;
    var status=document.getElementById('qiblaSensorStatus');
    if(!status){status=document.createElement('p');status.id='qiblaSensorStatus';status.className='qibla-sensor-status';var button=card.querySelector('.primary-btn');card.insertBefore(status,button||null)}
    return status;
  }
  function sendCompassLocation(){
    if(!window.state||!state.coords)return;
    callBridge('updateCompassLocation',Number(state.coords.lat),Number(state.coords.lon),Number(state.coords.altitude||0));
    callBridge('refreshCompassLocation');
  }
  function renderQibla416(){
    if(!window.state||!state.coords)return;
    state.qibla=qiblaBearing(state.coords.lat,state.coords.lon);
    var degrees=document.getElementById('qiblaDegrees');if(degrees)degrees.textContent=arabic(Math.round(state.qibla));
    var location=document.getElementById('qiblaLocation');if(location)location.textContent='الموقع: '+(state.coords.name||'الموقع الحالي');
    var arrow=document.getElementById('qiblaArrow');if(arrow&&!Number.isFinite(lastNativeHeading)){arrow.classList.add('waiting-heading');arrow.style.transform='translate(-50%,-100%) rotate(0deg)'}
    var status=ensureQiblaStatus();if(status&&!Number.isFinite(lastNativeHeading))status.textContent='ضع الهاتف أفقيًا وانتظر قراءة البوصلة…';
    sendCompassLocation();
  }
  window.renderQibla=renderQibla416;
  window.onNativeHeading=function(heading,accuracy){
    heading=Number(heading);if(!Number.isFinite(heading))return;lastNativeHeading=normalizeDegrees(heading);
    if(window.state&&state.coords)state.qibla=qiblaBearing(state.coords.lat,state.coords.lon);
    var relative=normalizeDegrees((window.state?state.qibla:0)-lastNativeHeading);
    var arrow=document.getElementById('qiblaArrow');if(arrow){arrow.classList.remove('waiting-heading');arrow.style.transform='translate(-50%,-100%) rotate('+relative.toFixed(2)+'deg)'}
    var status=ensureQiblaStatus();if(status){var level=Number(accuracy);status.textContent=level<=0?'حرّك الهاتف على شكل ٨ لمعايرة البوصلة':(level===1?'دقة البوصلة منخفضة — ابتعد عن الحديد والمغناطيس':'اتجاه القبلة جاهز')}
  };
  var oldLocateMe=window.locateMe;
  window.locateMe=function(){
    if(!navigator.geolocation){if(typeof oldLocateMe==='function')oldLocateMe();return}
    navigator.geolocation.getCurrentPosition(function(position){
      state.coords={lat:position.coords.latitude,lon:position.coords.longitude,altitude:position.coords.altitude||0,name:'موقعي الحالي'};
      localStorage.setItem('coords',JSON.stringify(state.coords));if(typeof calculatePrayers==='function')calculatePrayers();renderQibla416();if(typeof toast==='function')toast('تم تحديث الموقع والقبلة');
    },function(){if(typeof toast==='function')toast('تعذر الحصول على الموقع. فعّل إذن الموقع.')},{enableHighAccuracy:true,maximumAge:10000,timeout:15000});
  };

  /* ---------- Page lifecycle ---------- */
  window.showPage=function(name,push){
    if(typeof oldShowPage==='function')oldShowPage(name,push);
    document.body.classList.toggle('audio-page-active',name==='audio');
    if(name==='audio')setTimeout(function(){bindAudioList();refreshAvailability();installSeekBar()},40);
    if(name==='reader'){document.body.classList.add('reader-mode');if(typeof window.refreshMushafImages==='function')requestAnimationFrame(window.refreshMushafImages)}
    else document.body.classList.remove('reader-mode');
    if(name==='qibla')setTimeout(renderQibla416,80);
  };

  function init(){
    applyTheme416();
    if(window.matchMedia){var media=window.matchMedia('(prefers-color-scheme: dark)');var change=function(){if((localStorage.getItem('theme')||'system')==='system')applyTheme416()};if(media.addEventListener)media.addEventListener('change',change)}
    /* Remove browser DeviceOrientation listeners installed by the legacy page. They
       fought the native true-north heading and caused the arrow to point west. */
    try{if(typeof orientationHandler==='function'){window.removeEventListener('deviceorientationabsolute',orientationHandler,true);window.removeEventListener('deviceorientation',orientationHandler,true)}}catch(ignore){}
    bindAudioList();installFilters();installSeekBar();refreshAvailability();renderQibla416();
    setTimeout(function(){bindAudioList();refreshAvailability();installSeekBar();applyTheme416()},350);
    setTimeout(function(){bindAudioList();refreshAvailability();applyTheme416()},950);
    callBridge('audioAction','query');
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
