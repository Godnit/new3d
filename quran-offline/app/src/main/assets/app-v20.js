(function(){
  'use strict';

  function normalizeDegrees(value){value=Number(value)||0;return (value%360+360)%360}
  function qiblaBearing(latitude,longitude){
    var lat1=Number(latitude)*Math.PI/180,lat2=21.422487*Math.PI/180;
    var deltaLon=(39.826206-Number(longitude))*Math.PI/180;
    var y=Math.sin(deltaLon)*Math.cos(lat2);
    var x=Math.cos(lat1)*Math.sin(lat2)-Math.sin(lat1)*Math.cos(lat2)*Math.cos(deltaLon);
    return normalizeDegrees(Math.atan2(y,x)*180/Math.PI);
  }
  function arabic(value){return typeof arabicNumber==='function'?arabicNumber(value):String(value)}

  window.onNativeCompassLocation=function(latitude,longitude,altitude,accuracy){
    latitude=Number(latitude);longitude=Number(longitude);if(!Number.isFinite(latitude)||!Number.isFinite(longitude))return;
    if(window.state){
      state.coords={lat:latitude,lon:longitude,altitude:Number(altitude)||0,accuracy:Number(accuracy)||0,name:'موقعي الحالي'};
      state.qibla=qiblaBearing(latitude,longitude);
      try{localStorage.setItem('coords',JSON.stringify(state.coords))}catch(ignore){}
      var degrees=document.getElementById('qiblaDegrees');if(degrees)degrees.textContent=arabic(Math.round(state.qibla));
      var location=document.getElementById('qiblaLocation');if(location)location.textContent='الموقع: موقعي الحالي';
    }
  };

  function syncSeekPaint(){
    var range=document.getElementById('audioSeekRange');if(!range)return;
    var value=Math.max(0,Math.min(1000,Number(range.value)||0));
    range.style.setProperty('--seek-progress',(value/10)+'%');
  }
  function refreshLabels(){
    var about=document.querySelector('#page-settings .setting:last-child .muted');
    if(about)about.textContent='الإصدار 4.16 — مظهر فاتح وليلي فعلي، مصحف مصوّر مزخرف، الأجزاء ٢٦–٣٠ بصوت عادل ريان داخل التطبيق، وتنزيل اختياري لبقية السور.';
  }
  document.addEventListener('input',function(event){if(event.target&&event.target.id==='audioSeekRange')syncSeekPaint()},true);
  document.addEventListener('change',function(event){if(event.target&&event.target.id==='audioSeekRange')syncSeekPaint()},true);
  setInterval(syncSeekPaint,500);
  function init(){syncSeekPaint();refreshLabels();setTimeout(refreshLabels,900)}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
