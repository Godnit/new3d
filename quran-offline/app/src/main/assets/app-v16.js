(function(){
  'use strict';

  /* v4.12 — Adel Rayan labels, responsive Qibla compass and selectable full-page Mushaf frames. */
  var RECITER='عادل ريان';
  var STYLE_KEY='mushafImageStyle';
  var styleNames={blue:'مزخرف أزرق',gold:'ذهبي هندسي',plain:'الصفحة الأصلية'};
  var compass={target:null,display:null,raf:0,accuracy:0};
  var previousAudioState=window.onNativeAudioState;

  function clamp(value,min,max){return Math.max(min,Math.min(max,value))}
  function shortest(from,to){return ((to-from+540)%360)-180}
  function currentStyle(){var value=localStorage.getItem(STYLE_KEY)||'blue';return styleNames[value]?value:'blue'}
  function replaceText(root,from,to){
    if(!root)return;
    var walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT),node;
    while((node=walker.nextNode()))if(node.nodeValue&&node.nodeValue.indexOf(from)>=0)node.nodeValue=node.nodeValue.split(from).join(to);
  }

  function frameSource(style){
    if(style==='blue')return 'mushaf-blue-frame.svg';
    if(style==='gold')return 'mushaf-gold-frame.svg';
    return '';
  }

  function applyMushafStyle(){
    var style=currentStyle();
    document.documentElement.dataset.mushafImageStyle=style;
    var shells=document.querySelectorAll('.mushaf-image-shell');
    for(var i=0;i<shells.length;i++){
      var shell=shells[i];
      shell.dataset.mushafStyle=style;
      var frame=shell.querySelector('.mushaf-theme-frame');
      if(!frame){frame=document.createElement('img');frame.className='mushaf-theme-frame';frame.draggable=false;frame.alt='';shell.appendChild(frame)}
      var source=frameSource(style);
      if(source){frame.src=source;frame.classList.remove('hidden')}else{frame.removeAttribute('src');frame.classList.add('hidden')}
    }
    var controls=document.querySelectorAll('[data-mushaf-style-select]');
    for(var c=0;c<controls.length;c++)controls[c].value=style;
  }

  window.setMushafImageStyle=function(style){
    if(!styleNames[style])style='blue';
    localStorage.setItem(STYLE_KEY,style);
    applyMushafStyle();
    if(typeof toast==='function')toast('تم اختيار '+styleNames[style]);
  };

  function styleSelectMarkup(){
    var style=currentStyle();
    return '<select class="select mushaf-style-select" data-mushaf-style-select onchange="setMushafImageStyle(this.value)">'+
      '<option value="blue" '+(style==='blue'?'selected':'')+'>مزخرف أزرق</option>'+
      '<option value="gold" '+(style==='gold'?'selected':'')+'>ذهبي هندسي</option>'+
      '<option value="plain" '+(style==='plain'?'selected':'')+'>الصفحة الأصلية بلا إطار</option></select>';
  }

  function installStyleControls(){
    var card=document.querySelector('#page-settings .settings-card');
    if(card&&!document.getElementById('mushafImageStyleSetting')){
      var row=document.createElement('div');row.id='mushafImageStyleSetting';row.className='setting mushaf-image-style-setting';
      row.innerHTML='<label>شكل صفحات المصحف</label>'+styleSelectMarkup()+'<small>يغيّر الزخرفة فقط، مع إبقاء نص الصفحة الأصلي كاملًا.</small>';
      var method=document.getElementById('methodSelect');var anchor=method&&method.closest('.setting');
      card.insertBefore(row,anchor||card.firstChild);
    }
    var sheet=document.getElementById('readerSettings');
    if(sheet&&!document.getElementById('readerMushafStyleSetting')){
      var box=document.createElement('label');box.id='readerMushafStyleSetting';box.className='reader-mushaf-style-setting';
      box.innerHTML='<span>شكل الصفحة</span>'+styleSelectMarkup();
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
    if(about)about.textContent='الإصدار 4.12 — تلاوة عادل ريان كاملة دون إنترنت، صفحات مصحف كاملة بثلاثة أشكال، وقبلة أسرع مع الشمال الحقيقي.';
  }

  window.onNativeAudioState=function(){
    if(typeof previousAudioState==='function')previousAudioState.apply(this,arguments);
    refreshReciterLabels();
  };

  function ensureCompassUi(){
    var card=document.querySelector('.qibla-card');if(!card)return;
    var compassNode=card.querySelector('.compass');
    if(compassNode&&!compassNode.querySelector('.compass-cardinals')){
      compassNode.insertAdjacentHTML('beforeend','<div class="compass-cardinals"><b class="north">ش</b><b class="east">ق</b><b class="south">ج</b><b class="west">غ</b></div>');
    }
    if(!document.getElementById('compassStatus')){
      var p=document.createElement('p');p.id='compassStatus';p.className='compass-status';p.textContent='ضع الهاتف أفقيًا وحرّكه على شكل الرقم ٨ للمعايرة.';
      var button=card.querySelector('.primary-btn');card.insertBefore(p,button||null);
    }
    if(!document.getElementById('compassResetButton')){
      var reset=document.createElement('button');reset.id='compassResetButton';reset.type='button';reset.className='soft-btn compass-reset-button';reset.textContent='إعادة ضبط حركة البوصلة';
      reset.onclick=function(){compass.target=null;compass.display=null;if(typeof toast==='function')toast('تمت إعادة ضبط حركة البوصلة')};
      card.appendChild(reset);
    }
  }

  function compassFrame(){
    var arrow=document.getElementById('qiblaArrow');
    if(!arrow||compass.target==null){compass.raf=0;return}
    if(compass.display==null)compass.display=compass.target;
    var delta=shortest(compass.display,compass.target);
    compass.display=(compass.display+clamp(delta,-24,24)*0.48+360)%360;
    arrow.style.transform='translate(-50%,-100%) rotate('+compass.display.toFixed(2)+'deg)';
    if(Math.abs(delta)>0.2)compass.raf=requestAnimationFrame(compassFrame);else compass.raf=0;
  }

  function updateHeading(rawHeading,accuracy){
    var heading=Number(rawHeading);if(!Number.isFinite(heading))return;
    ensureCompassUi();
    compass.accuracy=Number(accuracy||0);
    var qibla=Number(state.qibla||0);
    var desired=(qibla-heading+360)%360;
    compass.target=compass.target==null?desired:(compass.target+shortest(compass.target,desired)+360)%360;
    if(!compass.raf)compass.raf=requestAnimationFrame(compassFrame);
    var status=document.getElementById('compassStatus');
    if(status){
      if(compass.accuracy<=0)status.textContent='دقة البوصلة منخفضة: أبعد الهاتف عن المعادن وحرّكه على شكل الرقم ٨.';
      else status.textContent='اتجاه الهاتف '+arabicNumber(Math.round(heading))+'° — اتبع رأس السهم إلى القبلة.';
    }
  }

  window.onNativeHeading=function(heading,accuracy){
    state.nativeHeading=Number(heading);state.compassAccuracy=Number(accuracy||0);updateHeading(heading,accuracy);
  };

  window.renderQibla=function(){
    if(typeof adhan!=='undefined'&&state.coords){
      var coordinates=new adhan.Coordinates(Number(state.coords.lat),Number(state.coords.lon));
      state.qibla=adhan.Qibla(coordinates);
    }
    var degrees=document.getElementById('qiblaDegrees');if(degrees)degrees.textContent=arabicNumber(Math.round(Number(state.qibla||0)));
    ensureCompassUi();compass.target=null;compass.display=null;
    if(state.nativeHeading!=null)updateHeading(state.nativeHeading,state.compassAccuracy);else updateHeading(0,0);
  };

  function init(){
    document.documentElement.dataset.reader='adel-rayan';
    installStyleControls();applyMushafStyle();refreshReciterLabels();ensureCompassUi();
    var stage=document.getElementById('mushafStage');
    if(stage)new MutationObserver(function(){applyMushafStyle()}).observe(stage,{childList:true,subtree:true});
    var settings=document.getElementById('page-settings');
    if(settings)new MutationObserver(function(){installStyleControls();refreshReciterLabels()}).observe(settings,{childList:true,subtree:true});
    setTimeout(function(){applyMushafStyle();refreshReciterLabels();if(state.page==='qibla')renderQibla()},250);
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
