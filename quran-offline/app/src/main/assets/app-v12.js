(function(){
  'use strict';

  /* v4.6 — baked Mushaf-page ornament, non-blocking search, streamed Yasser
     Al-Dosari recitation, native media controls and native prayer alerts. */

  var surahNames=['الفاتحة','البقرة','آل عمران','النساء','المائدة','الأنعام','الأعراف','الأنفال','التوبة','يونس','هود','يوسف','الرعد','إبراهيم','الحجر','النحل','الإسراء','الكهف','مريم','طه','الأنبياء','الحج','المؤمنون','النور','الفرقان','الشعراء','النمل','القصص','العنكبوت','الروم','لقمان','السجدة','الأحزاب','سبأ','فاطر','يس','الصافات','ص','الزمر','غافر','فصلت','الشورى','الزخرف','الدخان','الجاثية','الأحقاف','محمد','الفتح','الحجرات','ق','الذاريات','الطور','النجم','القمر','الرحمن','الواقعة','الحديد','المجادلة','الحشر','الممتحنة','الصف','الجمعة','المنافقون','التغابن','الطلاق','التحريم','الملك','القلم','الحاقة','المعارج','نوح','الجن','المزمل','المدثر','القيامة','الإنسان','المرسلات','النبأ','النازعات','عبس','التكوير','الانفطار','المطففين','الانشقاق','البروج','الطارق','الأعلى','الغاشية','الفجر','البلد','الشمس','الليل','الضحى','الشرح','التين','العلق','القدر','البينة','الزلزلة','العاديات','القارعة','التكاثر','العصر','الهمزة','الفيل','قريش','الماعون','الكوثر','الكافرون','النصر','المسد','الإخلاص','الفلق','الناس'];
  var audioState={surah:1,name:'الفاتحة',playing:false,buffering:false};
  var searchToken=0;
  var oldShowPage=showPage;
  var oldCalculatePrayers=calculatePrayers;

  function nativeBridge(){return window.AndroidBridge||null}
  function safeCall(name){
    var bridge=nativeBridge();if(!bridge||typeof bridge[name]!=='function')return false;
    try{var args=Array.prototype.slice.call(arguments,1);bridge[name].apply(bridge,args);return true}catch(ignore){return false}
  }
  function normalizeFast(value){
    return String(value||'').normalize('NFC')
      .replace(/[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]/g,'')
      .replace(/[أإآٱ]/g,'ا').replace(/ى/g,'ي').replace(/ة/g,'ه')
      .replace(/ؤ/g,'و').replace(/ئ/g,'ي').replace(/ـ/g,'')
      .replace(/[^\u0621-\u064A0-9 ]/g,' ').replace(/\s+/g,' ').trim().toLowerCase();
  }
  function searchWords(value){return normalizeFast(value).split(' ').filter(function(x){return x.length>0})}

  function removeDeadMushafSettings(){
    var card=document.querySelector('#page-settings .settings-card');if(!card)return;
    var ids=['mushafSwatches','fontRange','settingsTurnToggle','reduceMotionToggle','mushafFrameSwatches','readerBackdropSwatches','mushafSpacingRange'];
    for(var i=0;i<ids.length;i++){
      var node=document.getElementById(ids[i]);
      if(node){var setting=node.closest('.setting');if(setting)setting.remove()}
    }
    var settings=card.querySelectorAll('.setting');
    for(var s=0;s<settings.length;s++){
      var text=settings[s].textContent||'';
      if(/لون صفحات المصحف|لون ورق|شكل الإطار|زخرفة الإطار|خلفية خلف الصفحة|حجم خط المصحف|تباعد أسطر|السحب السلس|تقليل الحركة/.test(text))settings[s].remove();
    }
    localStorage.removeItem('mushaf');localStorage.removeItem('mushafFrame');localStorage.removeItem('readerBackdrop');localStorage.removeItem('mushafSpacing');
  }

  function installPrayerSetting(){
    var card=document.querySelector('#page-settings .settings-card');if(!card||document.getElementById('prayerAlertsToggle'))return;
    var method=document.getElementById('methodSelect');var anchor=method&&method.closest('.setting');
    var row=document.createElement('div');row.className='setting prayer-alert-setting';
    var enabled=localStorage.getItem('prayerAlerts')==='true';
    row.innerHTML='<label class="switch-row"><span><b>إشعارات الصلاة والأذان</b><small>تنبيه باسم الصلاة مع صوت أذان مختصر</small></span><input id="prayerAlertsToggle" type="checkbox" '+(enabled?'checked':'')+'></label>';
    if(anchor&&anchor.nextSibling)card.insertBefore(row,anchor.nextSibling);else card.appendChild(row);
    document.getElementById('prayerAlertsToggle').addEventListener('change',function(){
      var on=this.checked;localStorage.setItem('prayerAlerts',String(on));
      safeCall('setPrayerNotificationsEnabled',on);
      if(on){safeCall('requestNotificationPermission');scheduleNativePrayers();toast('تم تفعيل تنبيهات الصلاة')}else toast('تم إيقاف تنبيهات الصلاة');
    });
  }

  function prayerPayload(){
    if(!state.schedule)return [];
    var keys=['fajr','dhuhr','asr','maghrib','isha'],items=[];
    for(var i=0;i<keys.length;i++){
      var date=state.schedule[keys[i]];
      if(date&&date.getTime)items.push({key:keys[i],name:prayerNames[keys[i]],timestamp:date.getTime()});
    }
    return items;
  }
  function scheduleNativePrayers(){
    if(localStorage.getItem('prayerAlerts')!=='true')return;
    var items=prayerPayload();if(!items.length)return;
    safeCall('schedulePrayerNotifications',JSON.stringify(items));
  }
  calculatePrayers=function(){oldCalculatePrayers();setTimeout(scheduleNativePrayers,80)};

  function audioPageMarkup(){
    return '<section id="page-audio" class="page hidden audio-page">'+
      '<div class="section-head"><div><p class="eyebrow">تلاوة عبر الإنترنت</p><h2>ياسر الدوسري</h2></div><span class="pill">١١٤ سورة</span></div>'+
      '<div class="audio-notice">الصوت يُبث من الإنترنت حتى يبقى حجم التطبيق صغيرًا، بينما المصحف والنصوص تعمل دون إنترنت.</div>'+
      '<div class="search-box audio-search"><span>⌕</span><input id="audioSurahSearch" placeholder="ابحث باسم السورة..."></div>'+
      '<div id="audioSurahList" class="audio-surah-list"></div></section>';
  }
  function installAudioPage(){
    if(document.getElementById('page-audio'))return;
    var settings=document.getElementById('page-settings');
    if(settings)settings.insertAdjacentHTML('beforebegin',audioPageMarkup());
    titles.audio='الاستماع للقرآن';
    var grid=document.querySelector('#page-home .quick-grid');
    if(grid&&!document.getElementById('homeAudioButton'))grid.insertAdjacentHTML('beforeend','<button id="homeAudioButton" class="quick" onclick="showPage(\'audio\',true)"><span>🎧</span><b>الاستماع</b><small>ياسر الدوسري</small></button>');
    var drawer=document.querySelector('#drawer');
    if(drawer&&!document.getElementById('drawerAudioButton')){
      var button=document.createElement('button');button.id='drawerAudioButton';button.textContent='🎧 الاستماع للقرآن';button.onclick=function(){drawerGo('audio')};
      var settingButton=Array.prototype.slice.call(drawer.querySelectorAll('button')).filter(function(b){return (b.textContent||'').indexOf('الإعدادات')>=0})[0];
      drawer.insertBefore(button,settingButton||null);
    }
    var input=document.getElementById('audioSurahSearch');if(input)input.addEventListener('input',function(){renderAudioSurahs(this.value)});
    renderAudioSurahs('');
    installMiniPlayer();
  }
  function renderAudioSurahs(query){
    var box=document.getElementById('audioSurahList');if(!box)return;
    var q=normalizeFast(query),html='';
    for(var i=0;i<surahNames.length;i++){
      if(q&&normalizeFast(surahNames[i]).indexOf(q)<0)continue;
      html+='<button class="audio-surah-row '+(audioState.surah===i+1?'active':'')+'" onclick="playAudioSurah('+(i+1)+',\''+surahNames[i]+'\')"><span class="audio-number">'+arabicNumber(i+1)+'</span><span><b>سورة '+surahNames[i]+'</b><small>ياسر الدوسري</small></span><i>'+(audioState.surah===i+1&&audioState.playing?'❚❚':'▶')+'</i></button>';
    }
    box.innerHTML=html||'<div class="empty">لا توجد سورة بهذا الاسم.</div>';
  }
  function installMiniPlayer(){
    if(document.getElementById('audioMiniPlayer'))return;
    var el=document.createElement('div');el.id='audioMiniPlayer';el.className='audio-mini-player hidden';
    el.innerHTML='<button onclick="audioCommand(\'previous\')">⏮</button><button id="audioMainButton" class="audio-main" onclick="audioCommand(\'toggle\')">▶</button><button onclick="audioCommand(\'next\')">⏭</button><div class="audio-mini-info"><b id="audioMiniTitle">سورة الفاتحة</b><small>ياسر الدوسري</small></div><button onclick="audioCommand(\'stop\')">✕</button>';
    document.body.appendChild(el);
  }
  window.playAudioSurah=function(number,name){
    audioState.surah=Number(number)||1;audioState.name=name||surahNames[audioState.surah-1];audioState.buffering=true;
    updateAudioUi();
    if(!safeCall('playSurah',audioState.surah,audioState.name))toast('تشغيل الصوت متاح داخل تطبيق Android');
    else {safeCall('requestNotificationPermission');toast('جارٍ تجهيز التلاوة…')}
  };
  window.audioCommand=function(command){if(!safeCall('audioAction',command))toast('مشغل الصوت متاح داخل تطبيق Android')};
  window.onNativeAudioState=function(playing,surah,name,buffering){
    audioState.playing=!!playing;audioState.surah=Number(surah)||1;audioState.name=name||surahNames[audioState.surah-1];audioState.buffering=!!buffering;updateAudioUi();
  };
  function updateAudioUi(){
    var player=document.getElementById('audioMiniPlayer');if(!player)return;
    player.classList.remove('hidden');
    var title=document.getElementById('audioMiniTitle');if(title)title.textContent='سورة '+audioState.name;
    var button=document.getElementById('audioMainButton');if(button)button.textContent=audioState.buffering?'…':(audioState.playing?'❚❚':'▶');
    renderAudioSurahs(document.getElementById('audioSurahSearch')?document.getElementById('audioSurahSearch').value:'');
  }

  function scoreHadith(h,terms,phrase){
    if(!h._fastSearch)h._fastSearch=normalizeFast((h.text||'')+' '+(h.display||'')+' '+(h.narrator||'')+' '+(h.book||''));
    var text=h._fastSearch;if(!text)return 0;
    var score=text.indexOf(phrase)>=0?5000:0,words=text.split(' ');
    for(var t=0;t<terms.length;t++){
      var term=terms[t],best=0;
      for(var w=0;w<words.length;w++){
        var word=words[w];
        if(word===term){best=900;break}
        if(word.indexOf(term)===0||word.slice(-term.length)===term)best=Math.max(best,520);
      }
      if(!best)return 0;score+=best;
    }
    return score;
  }
  function nonBlockingHadithSearch(query){
    if(!state.hadith.length)return;
    var token=++searchToken,raw=String(query||'').trim(),normalized=normalizeFast(raw),terms=searchWords(raw),book=state.hadithBook;
    state.hadithSearchQuery=raw;
    var output=document.getElementById('hadithResults');
    if(!normalized){
      var first=[];for(var n=0;n<state.hadith.length&&first.length<36;n++){if(book==='all'||state.hadith[n].book===book)first.push({h:state.hadith[n],score:1})}
      state.hadithMatches=first;state.hadithVisible=12;renderHadithResults('');return;
    }
    if(normalized.length<3){
      state.hadithMatches=[];state.hadithVisible=12;
      output.innerHTML='<div class="empty card search-help">اكتب ثلاثة أحرف على الأقل حتى يبقى البحث سريعًا، مثل: صدق أو صلاة.</div>';
      var more=document.getElementById('loadMoreHadith');if(more)more.classList.add('hidden');return;
    }
    output.innerHTML='<div class="empty card search-loading">جارٍ البحث…</div>';
    var results=[],index=0;
    function chunk(){
      if(token!==searchToken)return;
      var end=Math.min(index+90,state.hadith.length);
      for(;index<end;index++){
        var h=state.hadith[index];if(book!=='all'&&h.book!==book)continue;
        var score=scoreHadith(h,terms,normalized);if(score)results.push({h:h,score:score});
      }
      if(index<state.hadith.length){setTimeout(chunk,0);return}
      if(token!==searchToken)return;
      results.sort(function(a,b){return b.score-a.score});
      state.hadithMatches=results.slice(0,160);state.hadithVisible=12;renderHadithResults(raw);
    }
    setTimeout(chunk,0);
  }
  runHadithSearch=nonBlockingHadithSearch;
  function installHadithInput(){
    var old=document.getElementById('hadithSearch');if(!old||old.dataset.fastSearch==='1')return;
    var input=old.cloneNode(true);input.dataset.fastSearch='1';old.parentNode.replaceChild(input,old);
    var timer=0;input.addEventListener('input',function(){var value=this.value;clearTimeout(timer);searchToken++;timer=setTimeout(function(){nonBlockingHadithSearch(value)},420)});
  }

  function installQuranInputGuard(){
    var old=document.getElementById('quranSearch');if(!old||old.dataset.fastGuard==='1')return;
    var input=old.cloneNode(true);input.dataset.fastGuard='1';old.parentNode.replaceChild(input,old);
    var timer=0;input.addEventListener('input',function(){var value=this.value;clearTimeout(timer);timer=setTimeout(function(){renderQuranSearch(value)},320)});
  }

  showPage=function(name,push){
    oldShowPage(name,push);
    document.body.classList.toggle('audio-visible',name==='audio');
    if(name==='audio')renderAudioSurahs(document.getElementById('audioSurahSearch')?document.getElementById('audioSurahSearch').value:'');
  };

  function init(){
    document.documentElement.dataset.realMushafImage='1';
    removeDeadMushafSettings();installPrayerSetting();installAudioPage();installHadithInput();installQuranInputGuard();
    var card=document.querySelector('#page-settings .settings-card');
    if(card)new MutationObserver(function(){removeDeadMushafSettings();installPrayerSetting()}).observe(card,{childList:true,subtree:true});
    var about=document.querySelector('#page-settings .setting:last-child .muted');
    if(about)about.textContent='الإصدار 4.6 — صفحات مصحف مصوّرة بزخرفتها داخل الصورة، بحث خفيف، تلاوة ياسر الدوسري عبر الإنترنت، وتنبيهات الصلاة.';
    setTimeout(function(){safeCall('audioAction','query');if(localStorage.getItem('prayerAlerts')==='true')scheduleNativePrayers()},700);
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
