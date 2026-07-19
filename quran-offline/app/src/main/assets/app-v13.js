(function(){
  'use strict';

  /* v4.7 — full offline Yasser Al-Dosari recitation. */
  var previousAudioState=window.onNativeAudioState;

  function formatTime(milliseconds){
    var seconds=Math.max(0,Math.floor((Number(milliseconds)||0)/1000));
    var minutes=Math.floor(seconds/60),remaining=seconds%60;
    return arabicNumber(minutes)+':'+arabicNumber(String(remaining).padStart(2,'0'));
  }

  function installProgress(){
    var player=document.getElementById('audioMiniPlayer');
    if(!player||document.getElementById('audioProgress'))return;
    var progress=document.createElement('div');
    progress.className='offline-audio-progress';
    progress.innerHTML='<div class="offline-audio-track"><span id="audioProgressFill"></span></div><div class="offline-audio-times"><small id="audioElapsed">٠:٠٠</small><small id="audioDuration">٠:٠٠</small></div>';
    player.appendChild(progress);
  }

  function updateProgress(position,duration){
    installProgress();
    var total=Math.max(0,Number(duration)||0),current=Math.max(0,Number(position)||0);
    var fill=document.getElementById('audioProgressFill');
    if(fill)fill.style.width=(total?Math.min(100,current*100/total):0)+'%';
    var elapsed=document.getElementById('audioElapsed');if(elapsed)elapsed.textContent=formatTime(current);
    var durationNode=document.getElementById('audioDuration');if(durationNode)durationNode.textContent=formatTime(total);
  }

  window.onNativeAudioState=function(playing,surah,name,buffering,position,duration){
    if(typeof previousAudioState==='function')previousAudioState(playing,surah,name,buffering);
    updateProgress(position,duration);
    var badge=document.getElementById('offlineAudioBadge');
    if(badge)badge.textContent=buffering?'جارٍ تجهيز السورة':(playing?'يعمل دون إنترنت':'جاهز دون إنترنت');
  };

  function convertAudioPageToOffline(){
    var page=document.getElementById('page-audio');if(!page)return;
    var eyebrow=page.querySelector('.eyebrow');if(eyebrow)eyebrow.textContent='تلاوة كاملة دون إنترنت';
    var title=page.querySelector('h2');if(title)title.textContent='ياسر الدوسري';
    var pill=page.querySelector('.pill');if(pill){pill.id='offlineAudioBadge';pill.textContent='١١٤ سورة مضمّنة'}
    var notice=page.querySelector('.audio-notice');
    if(notice)notice.innerHTML='<b>التلاوة محمّلة داخل التطبيق.</b> شغّل أي سورة دون إنترنت، ويستمر الصوت عند قفل الشاشة أو فتح تطبيق آخر.';
    var rows=page.querySelectorAll('.audio-surah-row small');
    for(var i=0;i<rows.length;i++)rows[i].textContent='ياسر الدوسري — دون إنترنت';
    installProgress();
  }

  function refreshOfflineLabels(){
    convertAudioPageToOffline();
    var home=document.getElementById('homeAudioButton');
    if(home){var small=home.querySelector('small');if(small)small.textContent='ياسر الدوسري — دون إنترنت'}
    var about=document.querySelector('#page-settings .setting:last-child .muted');
    if(about)about.textContent='الإصدار 4.7 — المصحف المصوّر كاملًا، تلاوة ياسر الدوسري للسور الـ١١٤ دون إنترنت، مشغل خلفي، أحاديث مختارة وتنبيهات الصلاة.';
    var hero=document.querySelector('#page-home .hero p:not(.eyebrow)');
    if(hero)hero.textContent='مصحف المدينة المصوّر وتلاوة ياسر الدوسري كاملة، الأذكار والحديث والصلاة والقبلة — دون إنترنت.';
  }

  function init(){
    document.documentElement.dataset.offlineAudio='1';
    refreshOfflineLabels();
    new MutationObserver(refreshOfflineLabels).observe(document.body,{childList:true,subtree:true});
    setTimeout(function(){if(window.AndroidBridge)try{window.AndroidBridge.audioAction('query')}catch(ignore){}},500);
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
