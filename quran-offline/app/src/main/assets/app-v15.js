(function(){
  'use strict';

  /* v4.10 — stable offline audio, one-minute prayer alert test and true-north compass correction. */
  var previousAudioState=window.onNativeAudioState;
  var previousAudioCommand=window.audioCommand;
  var previousCalculatePrayers=window.calculatePrayers;
  var lastAudioError='';

  function bridgeCall(name){
    var bridge=window.AndroidBridge;
    if(!bridge||typeof bridge[name]!=='function')return false;
    try{bridge[name].apply(bridge,Array.prototype.slice.call(arguments,1));return true}catch(ignore){return false}
  }

  function miniPlayer(){return document.getElementById('audioMiniPlayer')}
  function hideAudioPlayer(){
    var player=miniPlayer();if(player)player.classList.add('hidden');
    var fill=document.getElementById('audioProgressFill');if(fill)fill.style.width='0%';
    var elapsed=document.getElementById('audioElapsed');if(elapsed)elapsed.textContent='٠:٠٠';
    var duration=document.getElementById('audioDuration');if(duration)duration.textContent='٠:٠٠';
  }

  window.audioCommand=function(command){
    if(command==='stop')hideAudioPlayer();
    if(typeof previousAudioCommand==='function')return previousAudioCommand(command);
  };

  window.onNativeAudioState=function(playing,surah,name,buffering,position,duration,active,error){
    if(typeof previousAudioState==='function')previousAudioState(playing,surah,name,buffering,position,duration);
    var isActive=active===undefined?(!!playing||!!buffering):!!active;
    if(!isActive)hideAudioPlayer();
    else {var player=miniPlayer();if(player)player.classList.remove('hidden')}
    var message=String(error||'').trim();
    if(message&&message!==lastAudioError){lastAudioError=message;if(typeof toast==='function')toast(message)}
    if(!message)lastAudioError='';
  };

  function syncCompassLocation(){
    if(!window.state||!state.coords)return;
    var lat=Number(state.coords.lat),lon=Number(state.coords.lon);
    if(Number.isFinite(lat)&&Number.isFinite(lon))bridgeCall('updateCompassLocation',lat,lon,0);
  }

  if(typeof previousCalculatePrayers==='function'){
    window.calculatePrayers=function(){
      var result=previousCalculatePrayers.apply(this,arguments);
      setTimeout(syncCompassLocation,80);
      return result;
    };
  }

  function installPrayerTest(){
    var card=document.querySelector('#page-settings .settings-card');
    if(!card||document.getElementById('prayerTestButton'))return;
    var toggle=document.getElementById('prayerAlertsToggle');
    var anchor=toggle&&toggle.closest('.setting');
    var row=document.createElement('div');row.className='setting prayer-test-setting';
    row.innerHTML='<div><b>اختبار إشعار الصلاة</b><small>يرسل إشعار العشاء التجريبي بعد دقيقة واحدة</small></div><button id="prayerTestButton" class="prayer-test-button" type="button">اختبار بعد دقيقة</button>';
    if(anchor&&anchor.nextSibling)card.insertBefore(row,anchor.nextSibling);else card.appendChild(row);
    document.getElementById('prayerTestButton').addEventListener('click',function(){
      localStorage.setItem('prayerAlerts','true');
      if(toggle)toggle.checked=true;
      bridgeCall('requestNotificationPermission');
      bridgeCall('setPrayerNotificationsEnabled',true);
      if(bridgeCall('testPrayerNotification',60000)){
        if(typeof toast==='function')toast('سيظهر إشعار اختبار العشاء بعد دقيقة');
      }else if(typeof toast==='function')toast('اختبار الإشعار متاح داخل تطبيق Android');
    });
  }

  function updateVersionText(){
    var about=document.querySelector('#page-settings .setting:last-child .muted');
    if(about)about.textContent='الإصدار 4.10 — مشغل صوت أكثر ثباتًا وجودة، إغلاق صحيح للمشغل، اختبار إشعارات الصلاة، وتصحيح القبلة إلى الشمال الحقيقي دون إنترنت.';
  }

  function init(){
    document.documentElement.dataset.audioFix='410';
    hideAudioPlayer();
    installPrayerTest();
    syncCompassLocation();
    updateVersionText();
    setTimeout(function(){bridgeCall('audioAction','query')},600);
    var card=document.querySelector('#page-settings .settings-card');
    if(card)new MutationObserver(function(){installPrayerTest()}).observe(card,{childList:true,subtree:true});
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
