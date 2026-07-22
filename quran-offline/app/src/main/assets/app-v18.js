(function(){
  'use strict';

  /* v4.15 final phone fixes: stable Qibla, one Mushaf style and locked drawer. */
  var previousToggleDrawer=window.toggleDrawer;
  var previousShowPage=window.showPage;

  function drawerIsOpen(){
    var drawer=document.getElementById('drawer');
    return !!(drawer&&drawer.classList.contains('open'));
  }

  function syncDrawerLock(open){
    document.documentElement.classList.toggle('drawer-open',!!open);
    document.body.classList.toggle('drawer-open',!!open);
  }

  window.toggleDrawer=function(open){
    if(typeof previousToggleDrawer==='function')previousToggleDrawer(open);
    syncDrawerLock(!!open);
  };

  function preventBackgroundTouch(event){
    if(!drawerIsOpen())return;
    var drawer=document.getElementById('drawer');
    if(drawer&&!drawer.contains(event.target))event.preventDefault();
  }

  function removeObsoleteAppearanceControls(){
    ['mushafImageStyleSetting','readerMushafStyleSetting','mushafFrameSwatches','readerBackdropSwatches'].forEach(function(id){
      var node=document.getElementById(id);if(node)node.remove();
    });
    var rows=document.querySelectorAll('#page-settings .setting');
    rows.forEach(function(row){
      var text=String(row.textContent||'');
      if(/نقشة وإطار صفحة المصحف|نسخة صفحات المصحف|شكل صفحات المصحف|كلاسيكي|هندسي|زخرفة نباتية|إطار بسيط|بدون إطار/.test(text))row.remove();
    });
  }

  function qiblaBearing(){
    if(typeof adhan!=='undefined'&&window.state&&state.coords){
      return adhan.Qibla(new adhan.Coordinates(Number(state.coords.lat),Number(state.coords.lon)));
    }
    return Number(window.state&&state.qibla||0);
  }

  function applyHeading(heading){
    var value=Number(heading);if(!Number.isFinite(value))return;
    var bearing=qiblaBearing();
    if(window.state){state.qibla=bearing;state.nativeHeading=value}
    var arrow=document.getElementById('qiblaArrow');
    if(arrow){
      arrow.classList.remove('waiting-heading');
      arrow.style.transform='translate(-50%,-100%) rotate('+((bearing-value+360)%360).toFixed(2)+'deg)';
    }
    var degrees=document.getElementById('qiblaDegrees');
    if(degrees)degrees.textContent=typeof arabicNumber==='function'?arabicNumber(Math.round(bearing)):Math.round(bearing);
  }

  window.onNativeHeading=function(heading,accuracy){
    if(window.state)state.compassAccuracy=Number(accuracy||0);
    applyHeading(heading);
  };

  function restoreSimpleQibla(){
    var card=document.querySelector('.qibla-card');if(!card)return;
    card.querySelectorAll('.compass-cardinals,.compass-status,.compass-reset-button').forEach(function(node){node.remove()});
    var button=card.querySelector('.primary-btn');
    if(button){button.textContent='تحديث الموقع';button.onclick=function(){if(typeof locateMe==='function')locateMe()}}
    var location=document.getElementById('qiblaLocation');
    if(location&&window.state&&state.coords)location.textContent='الموقع: '+(state.coords.name||'الموقع الحالي');
    var bearing=qiblaBearing();if(window.state)state.qibla=bearing;
    var degrees=document.getElementById('qiblaDegrees');
    if(degrees)degrees.textContent=typeof arabicNumber==='function'?arabicNumber(Math.round(bearing)):Math.round(bearing);
    if(window.state&&Number.isFinite(Number(state.nativeHeading)))applyHeading(state.nativeHeading);
  }

  window.renderQibla=restoreSimpleQibla;

  window.showPage=function(name,push){
    if(typeof previousShowPage==='function')previousShowPage(name,push);
    document.body.classList.toggle('audio-page-active',name==='audio');
    if(name==='qibla')setTimeout(restoreSimpleQibla,220);
    if(name==='settings')setTimeout(removeObsoleteAppearanceControls,40);
  };

  function init(){
    document.addEventListener('touchmove',preventBackgroundTouch,{passive:false});
    var drawer=document.getElementById('drawer');
    if(drawer){
      drawer.addEventListener('touchmove',function(event){event.stopPropagation()},{passive:true});
      new MutationObserver(function(){syncDrawerLock(drawer.classList.contains('open'))}).observe(drawer,{attributes:true,attributeFilter:['class']});
    }
    removeObsoleteAppearanceControls();
    restoreSimpleQibla();
    setTimeout(removeObsoleteAppearanceControls,500);
    setTimeout(removeObsoleteAppearanceControls,1200);
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
