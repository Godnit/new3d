(function(){
  'use strict';

  /* v4.14 — first five Juz offline, verified per-Surah downloads, one compact real-image Mushaf. */
  var names=['الفاتحة','البقرة','آل عمران','النساء','المائدة','الأنعام','الأعراف','الأنفال','التوبة','يونس','هود','يوسف','الرعد','إبراهيم','الحجر','النحل','الإسراء','الكهف','مريم','طه','الأنبياء','الحج','المؤمنون','النور','الفرقان','الشعراء','النمل','القصص','العنكبوت','الروم','لقمان','السجدة','الأحزاب','سبأ','فاطر','يس','الصافات','ص','الزمر','غافر','فصلت','الشورى','الزخرف','الدخان','الجاثية','الأحقاف','محمد','الفتح','الحجرات','ق','الذاريات','الطور','النجم','القمر','الرحمن','الواقعة','الحديد','المجادلة','الحشر','الممتحنة','الصف','الجمعة','المنافقون','التغابن','الطلاق','التحريم','الملك','القلم','الحاقة','المعارج','نوح','الجن','المزمل','المدثر','القيامة','الإنسان','المرسلات','النبأ','النازعات','عبس','التكوير','الانفطار','المطففين','الانشقاق','البروج','الطارق','الأعلى','الغاشية','الفجر','البلد','الشمس','الليل','الضحى','الشرح','التين','العلق','القدر','البينة','الزلزلة','العاديات','القارعة','التكاثر','العصر','الهمزة','الفيل','قريش','الماعون','الكوثر','الكافرون','النصر','المسد','الإخلاص','الفلق','الناس'];
  var originalPlay=window.playAudioSurah;
  var previousAudioState=window.onNativeAudioState;
  var availability={items:[]};
  var downloadStates={};
  var rendering=false;
  var scheduled=false;
  var oldShowPage=window.showPage;

  function bridge(){return window.AndroidBridge||null}
  function normalize(value){return String(value||'').normalize('NFC').replace(/[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]/g,'').replace(/[أإآٱ]/g,'ا').replace(/ى/g,'ي').replace(/ة/g,'ه').replace(/ـ/g,'').replace(/[^\u0621-\u064A0-9 ]/g,' ').replace(/\s+/g,' ').trim()}
  function item(number){return availability.items&&availability.items[number-1]||{surah:number,builtIn:number<=4,available:number<=4,downloaded:false,bytes:0}}
  function sizeLabel(bytes){
    bytes=Number(bytes||0);if(!bytes)return '';
    if(bytes<1048576)return Math.max(1,Math.round(bytes/1024))+' ك.ب';
    return (bytes/1048576).toFixed(bytes>10485760?0:1)+' م.ب';
  }
  function escapeHtml(value){return String(value||'').replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}

  function refreshAvailability(){
    var nativeBridge=bridge();
    if(nativeBridge&&typeof nativeBridge.getAudioAvailabilityJson==='function'){
      try{
        var parsed=JSON.parse(nativeBridge.getAudioAvailabilityJson()||'{}');
        if(parsed&&Array.isArray(parsed.items))availability=parsed;
      }catch(ignore){}
    }else{
      availability.items=names.map(function(_,index){return {surah:index+1,builtIn:index<4,available:index<4,downloaded:false,bytes:0}});
    }
    scheduleRender();
  }

  function scheduleRender(){
    if(scheduled)return;scheduled=true;
    setTimeout(function(){scheduled=false;renderList()},20);
  }

  function actionMarkup(number,data,state){
    if(state&&state.status==='downloading')return '<button type="button" class="audio-row-action progress" disabled>'+Math.max(0,Math.min(99,state.progress||0))+'٪</button>';
    if(state&&state.status==='queued')return '<button type="button" class="audio-row-action progress" disabled>انتظار</button>';
    if(data.builtIn)return '<span class="audio-local-badge">داخل التطبيق</span>';
    if(data.downloaded)return '<button type="button" class="audio-row-action delete" data-action="delete" data-surah="'+number+'">حذف</button>';
    return '<button type="button" class="audio-row-action download" data-action="download" data-surah="'+number+'">تحميل'+(data.bytes?' · '+sizeLabel(data.bytes):'')+'</button>';
  }

  function renderList(){
    var box=document.getElementById('audioSurahList');if(!box||rendering)return;
    rendering=true;
    var queryNode=document.getElementById('audioSurahSearch');
    var query=normalize(queryNode?queryNode.value:'');
    var html='';
    for(var index=0;index<names.length;index++){
      var number=index+1,name=names[index];
      if(query&&normalize(name).indexOf(query)<0)continue;
      var data=item(number),state=downloadStates[number];
      var available=!!(data.available||data.builtIn||data.downloaded||(state&&state.status==='completed'));
      var subtitle=data.builtIn?'عادل ريان — يعمل فورًا دون إنترنت':(data.downloaded?'عادل ريان — محملة على الهاتف':'عادل ريان — تحتاج تنزيلًا مرة واحدة');
      html+='<div class="compact-audio-row '+(available?'available':'missing')+'" data-surah="'+number+'">'+
        '<button type="button" class="audio-row-main" data-action="'+(available?'play':'download')+'" data-surah="'+number+'" data-name="'+escapeHtml(name)+'">'+
        '<span class="audio-number">'+(typeof arabicNumber==='function'?arabicNumber(number):number)+'</span><span class="audio-row-copy"><b>سورة '+escapeHtml(name)+'</b><small>'+subtitle+'</small></span><i>'+(available?'▶':'↓')+'</i></button>'+actionMarkup(number,data,state)+'</div>';
    }
    box.innerHTML=html||'<div class="empty">لا توجد سورة بهذا الاسم.</div>';
    if(box.dataset.compactBound!=='1'){
      box.dataset.compactBound='1';
      box.addEventListener('click',function(event){
        var control=event.target.closest('[data-action]');if(!control)return;
        var number=Number(control.dataset.surah||0),action=control.dataset.action,name=control.dataset.name||names[number-1];
        if(action==='play')playAvailable(number,name);
        else if(action==='download')download(number);
        else if(action==='delete')removeDownload(number);
      });
    }
    rendering=false;
  }

  function playAvailable(number,name){
    var data=item(number);
    if(!(data.available||data.builtIn||data.downloaded))return download(number);
    if(typeof originalPlay==='function')originalPlay(number,name||names[number-1]);
  }

  function download(number){
    var nativeBridge=bridge();
    if(!nativeBridge||typeof nativeBridge.downloadSurahAudio!=='function')return toast('التنزيل متاح داخل تطبيق Android فقط');
    try{
      downloadStates[number]={status:'queued',progress:0};scheduleRender();
      if(typeof nativeBridge.requestNotificationPermission==='function')nativeBridge.requestNotificationPermission();
      nativeBridge.downloadSurahAudio(number);
      toast('بدأ تنزيل سورة '+names[number-1]);
    }catch(error){delete downloadStates[number];scheduleRender();toast('تعذر بدء التنزيل')}
  }

  function removeDownload(number){
    var nativeBridge=bridge();if(!nativeBridge||typeof nativeBridge.deleteSurahAudio!=='function')return;
    if(!confirm('حذف تلاوة سورة '+names[number-1]+' من الهاتف؟'))return;
    try{nativeBridge.deleteSurahAudio(number)}catch(ignore){}
  }

  window.playAudioSurah=function(number,name){
    number=Number(number)||1;var data=item(number);
    if(data.available||data.builtIn||data.downloaded)return playAvailable(number,name);
    download(number);
  };

  window.onNativeAudioState=function(){
    if(typeof previousAudioState==='function')previousAudioState.apply(this,arguments);
    scheduleRender();
  };

  window.onNativeAudioDownloadState=function(number,status,progress,bytes,total,error){
    number=Number(number)||0;if(!number)return;
    downloadStates[number]={status:String(status||''),progress:Number(progress||0),bytes:Number(bytes||0),total:Number(total||0)};
    if(status==='completed'){
      delete downloadStates[number];toast('اكتمل تنزيل سورة '+names[number-1]+' وأصبحت تعمل دون إنترنت');refreshAvailability();
    }else if(status==='deleted'){
      delete downloadStates[number];toast('تم حذف ملف السورة');refreshAvailability();
    }else if(status==='error'){
      delete downloadStates[number];toast(error||'فشل التنزيل. تحقق من الإنترنت');refreshAvailability();
    }else scheduleRender();
  };

  function compactLabels(){
    localStorage.setItem('mushafImageStyle','blue');
    document.documentElement.dataset.mushafImageStyle='blue';
    var notice=document.querySelector('#page-audio .audio-notice');
    if(notice)notice.innerHTML='<b>الأجزاء الخمسة الأولى جاهزة داخل التطبيق.</b> وُضعت سور الفاتحة والبقرة وآل عمران والنساء كاملة حتى لا تنقطع السورة. بقية السور تُحمّل مرة واحدة ثم تعمل دون إنترنت.';
    var eyebrow=document.querySelector('#page-audio .eyebrow');if(eyebrow)eyebrow.textContent='استماع وتنزيل اختياري';
    var home=document.querySelector('#homeAudioButton small');if(home)home.textContent='أول خمسة أجزاء دون إنترنت';
    var setting=document.getElementById('mushafImageStyleSetting');
    if(setting)setting.innerHTML='<label>شكل صفحات المصحف</label><select class="select" disabled><option>مصحف مزخرف مضغوط</option></select><small>صفحات حقيقية جاهزة، مضغوطة بصيغة WebP للحفاظ على وضوح الحروف وتقليل الحجم.</small>';
    var readerSetting=document.getElementById('readerMushafStyleSetting');
    if(readerSetting)readerSetting.innerHTML='<span>شكل الصفحة</span><select class="select" disabled><option>مصحف مزخرف مضغوط</option></select>';
    var about=document.querySelector('#page-settings .setting:last-child .muted');
    if(about)about.textContent='الإصدار 4.14 — مصحف مصوّر مضغوط، الأجزاء الخمسة الأولى بصوت عادل ريان داخل التطبيق، وتنزيل اختياري لبقية السور.';
  }

  function bind(){
    var search=document.getElementById('audioSurahSearch');
    if(search&&!search.dataset.compactBound){search.dataset.compactBound='1';search.addEventListener('input',scheduleRender)}
    compactLabels();refreshAvailability();
  }

  window.showPage=function(name,push){
    oldShowPage(name,push);
    if(name==='audio')setTimeout(bind,30);
    if(name==='reader'&&typeof window.refreshMushafImages==='function')setTimeout(window.refreshMushafImages,30);
  };

  function init(){setTimeout(bind,200);setTimeout(compactLabels,700)}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
