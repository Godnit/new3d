(function(){
  'use strict';

  var displayedQiblaAngle=null;
  var audioDownloadStates={};
  var wrappedShowPage=window.showPage;

  function normalizeDegrees(value){value=Number(value)||0;return (value%360+360)%360}
  function shortestDelta(from,to){return ((to-from+540)%360)-180}
  function resolvedTheme(preference){
    if(preference==='system')return window.matchMedia&&window.matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light';
    return preference==='dark'||preference==='sepia'?preference:'light';
  }
  function applyAppearance417(){
    var preference=localStorage.getItem('theme')||'system';
    var theme=resolvedTheme(preference);
    var accent=localStorage.getItem('accent')||'emerald';
    document.documentElement.dataset.theme=theme;
    document.documentElement.dataset.themePreference=preference;
    document.documentElement.dataset.accent=accent;
    document.documentElement.dataset.uiReady='1';
    if(document.body){document.body.dataset.theme=theme;document.body.dataset.accent=accent}
    var select=document.getElementById('themeSelect');if(select&&select.value!==preference)select.value=preference;
    var meta=document.querySelector('meta[name="theme-color"]');
    if(meta)meta.content=theme==='dark'?'#031f19':(theme==='sepia'?'#5b4a31':'#f3f5f2');
  }

  window.setTheme=function(value){
    value=['system','light','dark','sepia'].indexOf(value)>=0?value:'system';
    localStorage.setItem('theme',value);applyAppearance417();
    if(typeof toast==='function')toast('تم تغيير المظهر');
  };
  window.cycleTheme=function(){
    var current=resolvedTheme(localStorage.getItem('theme')||'system');
    window.setTheme(current==='dark'?'light':'dark');
  };
  window.setAccent=function(id){
    if(['emerald','teal','indigo','burgundy','sand'].indexOf(id)<0)id='emerald';
    localStorage.setItem('accent',id);applyAppearance417();
    if(typeof renderSwatches==='function')renderSwatches();
    if(typeof toast==='function')toast('تم تغيير لون التطبيق');
  };

  /* Keep the arrow angle continuous across 359° -> 0° so CSS never performs a full turn. */
  window.onNativeHeading=function(heading,accuracy){
    heading=Number(heading);if(!Number.isFinite(heading))return;
    var qibla=window.state&&Number.isFinite(Number(state.qibla))?normalizeDegrees(state.qibla):0;
    var target=normalizeDegrees(qibla-normalizeDegrees(heading));
    if(displayedQiblaAngle===null)displayedQiblaAngle=target;
    else displayedQiblaAngle+=shortestDelta(normalizeDegrees(displayedQiblaAngle),target);
    var arrow=document.getElementById('qiblaArrow');
    if(arrow){arrow.classList.remove('waiting-heading');arrow.style.transform='translate(-50%,-100%) rotate('+displayedQiblaAngle.toFixed(2)+'deg)'}
    var status=document.getElementById('qiblaSensorStatus');
    if(status){var level=Number(accuracy);status.textContent=level<=0?'حرّك الهاتف على شكل ٨ لمعايرة البوصلة':(level===1?'دقة البوصلة منخفضة — ابتعد عن الحديد والمغناطيس':'اتجاه القبلة جاهز')}
  };

  function markAudioReady(){
    var body=document.body,box=document.getElementById('audioSurahList');if(!body||!box)return;
    if(box.querySelector('.v416-row')){body.classList.add('v417-audio-ready');return}
    body.classList.remove('v417-audio-ready');
    var attempts=0,timer=setInterval(function(){
      attempts++;if(box.querySelector('.v416-row')){body.classList.add('v417-audio-ready');clearInterval(timer)}
      else if(attempts>30){body.classList.add('v417-audio-ready');clearInterval(timer)}
    },35);
  }

  window.showPage=function(name,push){
    if(name==='audio'&&document.body)document.body.classList.remove('v417-audio-ready');
    if(typeof wrappedShowPage==='function')wrappedShowPage(name,push);
    applyAppearance417();
    if(name==='audio')setTimeout(markAudioReady,20);
    if(name==='qibla')displayedQiblaAngle=null;
  };

  function updateDownloadRow(number,status,progress,error){
    var row=document.querySelector('#audioSurahList [data-surah="'+number+'"]');if(!row)return;
    var action=row.querySelector('.audio-row-action,.audio-local-badge,.v416-download-progress');
    if(status==='downloading'||status==='queued'){
      var label=status==='queued'?'انتظار':Math.max(0,Math.min(99,Number(progress)||0))+'٪';
      if(action){action.className='v416-download-progress';action.textContent=label}
    }else if(status==='error'){
      if(action){action.className='audio-row-action download';action.textContent='متابعة التحميل'}
      if(error&&typeof toast==='function')toast(error);
    }
  }

  /* Do not invoke the legacy download callback: it rebuilt the whole list in old colors. */
  window.onNativeAudioDownloadState=function(number,status,progress,bytes,total,error){
    number=Number(number)||0;status=String(status||'');
    if(number)audioDownloadStates[number]={status:status,progress:Number(progress)||0,bytes:Number(bytes)||0,total:Number(total)||0};
    updateDownloadRow(number,status,progress,error);
    if(status==='completed'){
      delete audioDownloadStates[number];
      if(typeof toast==='function')toast('اكتمل تنزيل السورة');
      setTimeout(function(){if(window.state&&state.page==='audio')window.showPage('audio',false)},120);
    }else if(status==='error')delete audioDownloadStates[number];
  };

  function removeMisleadingPageColorControls(){
    var photographed=document.getElementById('mushafSwatches');
    if(photographed){var row=photographed.closest?photographed.closest('.setting'):null;if(row)row.remove();else photographed.remove()}
    var reader=document.getElementById('readerSwatches');if(reader)reader.remove();
  }

  function init(){
    applyAppearance417();removeMisleadingPageColorControls();
    if(window.matchMedia){
      var media=window.matchMedia('(prefers-color-scheme: dark)');
      var changed=function(){if((localStorage.getItem('theme')||'system')==='system')applyAppearance417()};
      if(media.addEventListener)media.addEventListener('change',changed);
    }
    if(window.state&&state.page==='audio')markAudioReady();
    setTimeout(function(){applyAppearance417();removeMisleadingPageColorControls()},250);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
