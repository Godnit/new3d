(function(){
  'use strict';

  /* v4.13 — Adel Rayan, precomposed full-page Mushaf images and verified live Qibla heading. */
  var RECITER='عادل ريان';
  var STYLE_KEY='mushafImageStyle';
  var styleNames={blue:'مصحف مزخرف أزرق',gold:'مصحف مزخرف ذهبي',plain:'الصفحة الأصلية'};
  var compass={target:null,display:null,raf:0,accuracy:0,lastHeadingAt:0,heading:null,tilt:0};
  var previousAudioState=window.onNativeAudioState;
  var previousShowPage=window.showPage;

  function clamp(value,min,max){return Math.max(min,Math.min(max,value))}
  function shortest(from,to){return ((to-from+540)%360)-180}
  function currentStyle(){var value=localStorage.getItem(STYLE_KEY)||'blue';return styleNames[value]?value:'blue'}
  function bridgeCall(name){
    var bridge=window.AndroidBridge;if(!bridge||typeof bridge[name]!=='function')return false;
    try{bridge[name].apply(bridge,Array.prototype.slice.call(arguments,1));return true}catch(ignore){return false}
  }
  function replaceText(root,from,to){
    if(!root)return;
    var walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT),node;
    while((node=walker.nextNode()))if(node.nodeValue&&node.nodeValue.indexOf(from)>=0)node.nodeValue=node.nodeValue.split(from).join(to);
  }

  function applyMushafStyle(){
    var style=currentStyle();
    document.documentElement.dataset.mushafImageStyle=style;
    delete document.documentElement.dataset.originalMushaf;
    var obsolete=document.querySelectorAll('.real-mushaf-border,.mushaf-theme-frame');
    for(var i=0;i<obsolete.length;i++)obsolete[i].remove();
    var controls=document.querySelectorAll('[data-mushaf-style-select]');
    for(var c=0;c<controls.length;c++)controls[c].value=style;
  }

  window.setMushafImageStyle=function(style){
    if(!styleNames[style])style='blue';
    localStorage.setItem(STYLE_KEY,style);
    applyMushafStyle();
    if(typeof window.refreshMushafImages==='function')window.refreshMushafImages();
    if(typeof toast==='function')toast('تم اختيار '+styleNames[style]);
  };

  function styleSelectMarkup(){
    var style=currentStyle();
    return '<select class="select mushaf-style-select" data-mushaf-style-select onchange="setMushafImageStyle(this.value)">'+
      '<option value="blue" '+(style==='blue'?'selected':'')+'>مصحف مزخرف أزرق</option>'+
      '<option value="gold" '+(style==='gold'?'selected':'')+'>مصحف مزخرف ذهبي</option>'+
      '<option value="plain" '+(style==='plain'?'selected':'')+'>الصفحة الأصلية</option></select>';
  }

  function installStyleControls(){
    var card=document.querySelector('#page-settings .settings-card');
    if(card&&!document.getElementById('mushafImageStyleSetting')){
      var row=document.createElement('div');row.id='mushafImageStyleSetting';row.className='setting mushaf-image-style-setting';
      row.innerHTML='<label>نسخة صفحات المصحف</label>'+styleSelectMarkup()+'<small>كل اختيار يستخدم صور صفحات كاملة جاهزة؛ النص والزخرفة داخل الصورة نفسها.</small>';
      var method=document.getElementById('methodSelect');var anchor=method&&method.closest('.setting');
      card.insertBefore(row,anchor||card.firstChild);
    }
    var sheet=document.getElementById('readerSettings');
    if(sheet&&!document.getElementById('readerMushafStyleSetting')){
      var box=document.createElement('label');box.id='readerMushafStyleSetting';box.className='reader-mushaf-style-setting';
      box.innerHTML='<span>نسخة الصفحة</span>'+styleSelectMarkup();
      var swatches=document.getElementById('readerSwatches');
      if(swatches)sheet.insertBefore(box,swatches);else sheet.appendChild(box);
    }
  }

  function refreshReciterLabels(){
    replaceText(document.body,'ياسر الدوسري',RECITER);
    var title=document.querySelector('#page-audio h2');if(title)title.textContent=RECITER;
    var home=document.querySelector('#homeAudioButton small');if(home)home.textContent=RECITER+' — دون إنترنت';
    var rows=document.querySelectorAll('#audioSurahList .audio-surah-row small');
    for(var i=0;i<rows.length;i++)rows[i].textContent=RECITER+' — دون إنترنت';
    var mini=document.querySelector('.audio-mini-info small');if(mini)mini.textContent=RECITER;
    var about=document.querySelector('#page-settings .setting:last-child .muted');
    if(about)about.textContent='الإصدار 4.13 — تلاوة عادل ريان كاملة دون إنترنت، صفحات مصحف مزخرفة جاهزة، وتصحيح البوصلة والموقع.';
  }

  window.onNativeAudioState=function(){
    if(typeof previousAudioState==='function')previousAudioState.apply(this,arguments);
    refreshReciterLabels();
  };

  function qiblaBearing(latitude,longitude){
    var lat1=Number(latitude)*Math.PI/180;
    var lon1=Number(longitude)*Math.PI/180;
    var lat2=21.422487*Math.PI/180;
    var lon2=39.826206*Math.PI/180;
    var delta=lon2-lon1;
    var y=Math.sin(delta)*Math.cos(lat2);
    var x=Math.cos(lat1)*Math.sin(lat2)-Math.sin(lat1)*Math.cos(lat2)*Math.cos(delta);
    return (Math.atan2(y,x)*180/Math.PI+360)%360;
  }

  function ensureCompassUi(){
    var card=document.querySelector('.qibla-card');if(!card)return;
    var compassNode=card.querySelector('.compass');
    if(compassNode&&!compassNode.querySelector('.compass-cardinals')){
      compassNode.insertAdjacentHTML('beforeend','<div class="compass-cardinals"><b class="north">شمال</b><b class="east">شرق</b><b class="south">جنوب</b><b class="west">غرب</b></div>');
    }
    if(!document.getElementById('compassStatus')){
      var p=document.createElement('p');p.id='compassStatus';p.className='compass-status';p.textContent='جارٍ انتظار قراءة حقيقية من حساس البوصلة…';
      var button=card.querySelector('.primary-btn');card.insertBefore(p,button||null);
    }
    var mainButton=card.querySelector('.primary-btn');
    if(mainButton){mainButton.textContent='تحديث الموقع والبوصلة';mainButton.onclick=function(){refreshCompass(true)}}
    if(!document.getElementById('compassResetButton')){
      var reset=document.createElement('button');reset.id='compassResetButton';reset.type='button';reset.className='soft-btn compass-reset-button';reset.textContent='إعادة معايرة السهم';
      reset.onclick=function(){compass.target=null;compass.display=null;compass.heading=null;refreshCompass(true)};
      card.appendChild(reset);
    }
  }

  function setCompassWaiting(message){
    var arrow=document.getElementById('qiblaArrow');if(arrow)arrow.classList.add('waiting-heading');
    var status=document.getElementById('compassStatus');if(status)status.textContent=message||'جارٍ انتظار قراءة حقيقية من حساس البوصلة…';
  }

  function compassFrame(){
    var arrow=document.getElementById('qiblaArrow');
    if(!arrow||compass.target==null){compass.raf=0;return}
    if(compass.display==null)compass.display=compass.target;
    var delta=shortest(compass.display,compass.target);
    compass.display=(compass.display+clamp(delta,-45,45)*0.62+360)%360;
    arrow.style.transform='translate(-50%,-100%) rotate('+compass.display.toFixed(2)+'deg)';
    arrow.classList.remove('waiting-heading');
    if(Math.abs(delta)>0.15)compass.raf=requestAnimationFrame(compassFrame);else compass.raf=0;
  }

  function updateHeading(rawHeading,accuracy,tilt){
    var heading=Number(rawHeading);if(!Number.isFinite(heading))return;
    compass.heading=(heading+360)%360;
    compass.accuracy=Number(accuracy||0);
    compass.tilt=Math.abs(Number(tilt||0));
    compass.lastHeadingAt=Date.now();
    var qibla=Number(state.qibla);
    if(!Number.isFinite(qibla))return;
    compass.target=(qibla-compass.heading+360)%360;
    if(!compass.raf)compass.raf=requestAnimationFrame(compassFrame);
    var status=document.getElementById('compassStatus');
    if(status){
      if(compass.tilt>68)status.textContent='اجعل الهاتف أفقيًا ثم وجّه أعلاه؛ ميل الهاتف الآن كبير.';
      else if(compass.accuracy<=0)status.textContent='دقة الحساس منخفضة: أبعد الهاتف عن الحديد وحرّكه على شكل الرقم ٨.';
      else status.textContent='اتجاه الهاتف '+arabicNumber(Math.round(compass.heading))+'° — عندما يشير السهم للأعلى فأنت باتجاه القبلة.';
    }
  }

  window.onNativeHeading=function(heading,accuracy,tilt){
    state.nativeHeading=Number(heading);state.compassAccuracy=Number(accuracy||0);
    updateHeading(heading,accuracy,tilt);
  };

  function refreshCompass(requestNative){
    ensureCompassUi();
    if(state.coords){
      state.qibla=qiblaBearing(state.coords.lat,state.coords.lon);
      var degrees=document.getElementById('qiblaDegrees');
      if(degrees)degrees.textContent=arabicNumber(Math.round(state.qibla));
      var location=document.getElementById('qiblaLocation');
      if(location)location.textContent='الموقع: '+(state.coords.name||'الموقع الحالي');
      bridgeCall('updateCompassLocation',Number(state.coords.lat),Number(state.coords.lon),0);
    }
    compass.target=null;compass.display=null;
    if(requestNative)bridgeCall('requestCompassRefresh');
    if(state.nativeHeading!=null&&Date.now()-compass.lastHeadingAt<2500)updateHeading(state.nativeHeading,state.compassAccuracy,compass.tilt);
    else setCompassWaiting('حرّك الهاتف قليلًا وانتظر قراءة الحساس، ثم ضعه أفقيًا بعيدًا عن المعادن.');
    setTimeout(function(){
      if(Date.now()-compass.lastHeadingAt>2500)setCompassWaiting('لم تصل قراءة موثوقة من الحساس. اضغط تحديث الموقع والبوصلة وحرّك الهاتف على شكل الرقم ٨.');
    },2800);
  }

  window.renderQibla=function(){refreshCompass(false)};

  window.showPage=function(name,push){
    previousShowPage(name,push);
    if(name==='reader')setTimeout(function(){applyMushafStyle();if(typeof window.refreshMushafImages==='function')window.refreshMushafImages()},20);
    if(name==='qibla')setTimeout(function(){refreshCompass(true)},140);
  };

  function init(){
    document.documentElement.dataset.reader='adel-rayan-v413';
    installStyleControls();applyMushafStyle();refreshReciterLabels();ensureCompassUi();
    var settings=document.getElementById('page-settings');
    if(settings)new MutationObserver(function(){installStyleControls();refreshReciterLabels()}).observe(settings,{childList:true,subtree:true});
    setTimeout(function(){applyMushafStyle();refreshReciterLabels();if(state.page==='qibla')refreshCompass(true)},300);
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();