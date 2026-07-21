(function(){
  'use strict';

  function applyClassicBlueDefaults(){
    if(!localStorage.getItem('classicBlueMushafV43')){
      localStorage.setItem('mushaf','white');
      localStorage.setItem('mushafFrame','blue');
      localStorage.setItem('readerBackdrop','light');
      localStorage.setItem('mushafSpacing','100');
      localStorage.setItem('classicBlueMushafV43','1');
    }
    var root=document.documentElement;
    root.dataset.mushaf=localStorage.getItem('mushaf')||'white';
    root.dataset.mushafFrame=localStorage.getItem('mushafFrame')||'blue';
    root.dataset.readerBackdrop=localStorage.getItem('readerBackdrop')||'light';
  }

  function tuneSettingsLabels(){
    var paper=document.getElementById('mushafSwatches');
    if(paper&&paper.previousElementSibling)paper.previousElementSibling.textContent='لون الورق داخل الإطار الأزرق';
    var frame=document.getElementById('mushafFrameSwatches');
    if(frame&&frame.previousElementSibling)frame.previousElementSibling.textContent='لون زخرفة الإطار التقليدي';
    var about=document.querySelector('#page-settings .setting:last-child .muted');
    if(about)about.textContent='الإصدار 4.3 — صفحة مصحف بيضاء بإطار أزرق مزخرف وشريط سورة مطابق للشكل الورقي، مع سحب 2D وبحث صحيح وأحاديث كاملة. يعمل دون إنترنت.';
  }

  function refreshReader(){
    if(typeof renderSwatches==='function')renderSwatches();
    if(typeof refreshCustomSettings==='function')refreshCustomSettings();
    if(typeof renderMushafPage==='function'&&window.state&&state.page==='reader')renderMushafPage();
  }

  function init(){
    applyClassicBlueDefaults();
    tuneSettingsLabels();
    setTimeout(function(){tuneSettingsLabels();refreshReader()},100);
    setTimeout(function(){tuneSettingsLabels();refreshReader()},900);
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
