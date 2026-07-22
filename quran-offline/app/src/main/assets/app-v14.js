(function(){
  'use strict';

  /* v4.13 — selected hadiths and cleanup of obsolete runtime Mushaf overlays. */
  var selectedHadiths=[];
  var selectedIndex=0;
  var hadithPolls=0;

  function escapeHtml(value){
    return String(value||'').replace(/[&<>"']/g,function(character){
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character];
    });
  }

  function normalized(value){
    return String(value||'').normalize('NFC')
      .replace(/[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]/g,'')
      .replace(/[أإآٱ]/g,'ا').replace(/ى/g,'ي').replace(/ة/g,'ه')
      .replace(/ؤ/g,'و').replace(/ئ/g,'ي').replace(/ـ/g,'')
      .replace(/[^\u0621-\u064A0-9 ]/g,' ').replace(/\s+/g,' ').trim();
  }

  function conciseHadith(item){
    var text=String(item.display||item.text||'').trim();
    if(text.length>430)text=text.slice(0,427).replace(/\s+\S*$/,'')+'…';
    return text;
  }

  function findHadithByPhrase(phrase){
    if(!window.state||!Array.isArray(state.hadith))return null;
    var wanted=normalized(phrase);
    for(var i=0;i<state.hadith.length;i++){
      var item=state.hadith[i];
      var searchable=normalized((item.text||'')+' '+(item.display||''));
      if(searchable.indexOf(wanted)>=0)return item;
    }
    return null;
  }

  function collectSelectedHadiths(){
    if(!window.state||!Array.isArray(state.hadith)||!state.hadith.length)return false;
    var phrases=['عليكم بالصدق','انما الاعمال بالنيات','من كان يومن بالله واليوم الاخر','المسلم من سلم المسلمون','احب الاعمال الى الله','لا يومن احدكم حتى يحب لاخيه','الراحمون يرحمهم الرحمن'];
    var seen={};
    selectedHadiths=[];
    for(var i=0;i<phrases.length;i++){
      var item=findHadithByPhrase(phrases[i]);
      if(item){
        var key=String(item.id||item.book+'-'+item.number);
        if(!seen[key]){seen[key]=true;selectedHadiths.push(item)}
      }
    }
    if(selectedHadiths.length<4){
      for(var j=0;j<state.hadith.length&&selectedHadiths.length<7;j++){
        var candidate=state.hadith[j];
        var candidateText=conciseHadith(candidate);
        var candidateKey=String(candidate.id||candidate.book+'-'+candidate.number);
        if(candidateText.length>=70&&candidateText.length<=430&&!seen[candidateKey]){
          seen[candidateKey]=true;selectedHadiths.push(candidate);
        }
      }
    }
    var day=Math.floor(Date.now()/86400000);
    selectedIndex=selectedHadiths.length?day%selectedHadiths.length:0;
    return selectedHadiths.length>0;
  }

  function installHadithSection(){
    var home=document.getElementById('page-home');
    if(!home||document.getElementById('homeSelectedHadith'))return;
    var section=document.createElement('section');
    section.id='homeSelectedHadith';
    section.className='home-hadith-section';
    section.innerHTML='<div class="home-hadith-head"><div><p class="eyebrow">من السنة النبوية</p><h2>حديث مختار</h2></div><button type="button" class="home-hadith-next" onclick="nextSelectedHadith()" aria-label="حديث آخر">↻</button></div><article class="home-hadith-card"><p id="homeHadithText">جارٍ تجهيز الحديث المختار…</p><div class="home-hadith-meta"><span id="homeHadithSource"></span><button type="button" onclick="openSelectedHadithLibrary()">فتح مكتبة الحديث</button></div></article>';
    var quick=home.querySelector('.quick-grid');
    if(quick&&quick.nextSibling)home.insertBefore(section,quick.nextSibling);else home.appendChild(section);
  }

  function renderSelectedHadith(){
    installHadithSection();
    var textNode=document.getElementById('homeHadithText');
    var sourceNode=document.getElementById('homeHadithSource');
    if(!textNode||!sourceNode)return;
    if(!selectedHadiths.length){
      textNode.textContent='يعمل قسم الحديث كاملًا دون إنترنت، وسيظهر الحديث المختار بعد اكتمال تحميل البيانات المحلية.';
      sourceNode.textContent='رفيق الهدى';
      return;
    }
    var item=selectedHadiths[selectedIndex%selectedHadiths.length];
    textNode.innerHTML=escapeHtml(conciseHadith(item));
    var source=item.book||'السنة النبوية';
    if(item.number)source+=' — رقم '+arabicNumber(item.number);
    sourceNode.textContent=source;
  }

  window.nextSelectedHadith=function(){
    if(!selectedHadiths.length){collectSelectedHadiths()}
    if(selectedHadiths.length){selectedIndex=(selectedIndex+1)%selectedHadiths.length;renderSelectedHadith()}
  };

  window.openSelectedHadithLibrary=function(){
    if(typeof showPage==='function')showPage('hadith',true);
  };

  function removeAddedMushafFrames(){
    delete document.documentElement.dataset.originalMushaf;
    var frames=document.querySelectorAll('.real-mushaf-border,.mushaf-theme-frame,.page-curl');
    for(var i=0;i<frames.length;i++)frames[i].remove();
  }

  function improvePrayerSetting(){
    var toggle=document.getElementById('prayerAlertsToggle');
    if(!toggle||toggle.dataset.finalPrayerSetting==='1')return;
    toggle.dataset.finalPrayerSetting='1';
    var row=toggle.closest('.setting');
    var small=row&&row.querySelector('small');
    if(small)small.textContent='تنبيه باسم الصلاة مع أذان مختصر. على بعض الهواتف قد يتأخر التنبيه قليلًا عند تقييد البطارية.';
  }

  function refreshFinalLabels(){
    removeAddedMushafFrames();
    improvePrayerSetting();
    var about=document.querySelector('#page-settings .setting:last-child .muted');
    if(about)about.textContent='الإصدار 4.8 — مصحف المدينة المصوّر كاملًا دون إطار مضاف، تلاوة ياسر الدوسري للسور الـ١١٤ دون إنترنت، تشغيل في الخلفية، تحكم من الإشعار، أحاديث مختارة وتنبيهات الصلاة.';
    var notice=document.querySelector('#page-audio .audio-notice');
    if(notice)notice.innerHTML='<b>التلاوة كاملة داخل التطبيق.</b> جودة صوت متوازنة مع حجم مناسب، وتستمر عند قفل الشاشة أو استخدام تطبيق آخر.';
  }

  function waitForHadiths(){
    installHadithSection();
    if(collectSelectedHadiths()){renderSelectedHadith();return}
    hadithPolls++;
    if(hadithPolls<60)setTimeout(waitForHadiths,500);
  }

  function init(){
    installHadithSection();
    refreshFinalLabels();
    waitForHadiths();
    var stage=document.getElementById('mushafStage');
    if(stage)new MutationObserver(removeAddedMushafFrames).observe(stage,{childList:true,subtree:true});
    var settings=document.getElementById('page-settings');
    if(settings)new MutationObserver(improvePrayerSetting).observe(settings,{childList:true,subtree:true});
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();