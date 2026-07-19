(function(){
  'use strict';

  /* v4.6: real Madani Mushaf page images with the ornament baked into each image. */
  var reader={stage:null,current:null,previous:null,next:null,drag:null,animating:false,duration:220};
  var compass={heading:null,target:null,display:null,raf:0,lastTime:0};
  var oldShowPage=showPage;
  var oldRenderQibla=renderQibla;

  function clamp(value,min,max){return Math.max(min,Math.min(max,value))}
  function pad3(value){return String(value).padStart(3,'0')}
  function pageSource(page){return 'mushaf-pages/page'+pad3(page)+'.webp'}
  function pageAlt(page){return 'صفحة '+arabicNumber(page)+' من المصحف الشريف'}

  function buildStage(){
    var old=document.getElementById('mushafStage');
    if(!old)return null;
    if(old.dataset.imageReader==='1')return old;
    var stage=document.createElement('div');
    stage.id='mushafStage';
    stage.className='mushaf-stage image-mushaf-stage';
    stage.dataset.imageReader='1';
    stage.innerHTML='<div class="image-page-layer image-prev-layer"><img draggable="false" alt=""></div><div class="image-page-layer image-current-layer"><img draggable="false" alt=""></div><div class="image-page-layer image-next-layer"><img draggable="false" alt=""></div><div class="image-loading">جارٍ فتح صفحة المصحف…</div>';
    old.parentNode.replaceChild(stage,old);
    reader.stage=stage;
    reader.previous=stage.querySelector('.image-prev-layer');
    reader.current=stage.querySelector('.image-current-layer');
    reader.next=stage.querySelector('.image-next-layer');
    bindReader(stage);
    return stage;
  }

  function setImage(layer,page){
    if(!layer)return;
    var img=layer.querySelector('img');
    if(page<1||page>604){layer.classList.add('empty-image-page');img.removeAttribute('src');img.alt='';return}
    layer.classList.remove('empty-image-page');
    img.alt=pageAlt(page);
    img.dataset.page=String(page);
    img.src=pageSource(page);
  }

  function place(delta,animate){
    var stage=reader.stage||buildStage();if(!stage)return;
    var width=Math.max(1,stage.clientWidth);
    var transition=animate?'transform '+reader.duration+'ms cubic-bezier(.22,.72,.24,1)':'none';
    [reader.current,reader.previous,reader.next].forEach(function(layer){if(layer)layer.style.transition=transition});
    reader.current.style.transform='translate3d('+delta+'px,0,0)';
    reader.next.style.transform='translate3d('+(-width+delta)+'px,0,0)';
    reader.previous.style.transform='translate3d('+(width+delta)+'px,0,0)';
  }

  function renderImages(){
    var stage=buildStage();if(!stage)return;
    setImage(reader.current,state.currentPage);
    setImage(reader.previous,state.currentPage-1);
    setImage(reader.next,state.currentPage+1);
    place(0,false);
    var chip=document.getElementById('readerPageChip');if(chip)chip.textContent='الصفحة '+arabicNumber(state.currentPage)+' من ٦٠٤';
    var title=document.getElementById('readerTitle');if(title)title.textContent='المصحف الشريف';
    var subtitle=document.getElementById('readerSubtitle');if(subtitle)subtitle.textContent='الصفحة '+arabicNumber(state.currentPage)+' من ٦٠٤';
    localStorage.setItem('lastPage',String(state.currentPage));
    localStorage.setItem('lastRead',JSON.stringify({page:state.currentPage}));
    var loading=stage.querySelector('.image-loading');
    var image=reader.current.querySelector('img');
    if(loading){loading.classList.remove('hidden');image.onload=function(){loading.classList.add('hidden')};image.onerror=function(){loading.textContent='تعذر تحميل صورة الصفحة'};if(image.complete&&image.naturalWidth)loading.classList.add('hidden')}
    preload(state.currentPage+2);preload(state.currentPage-2);
  }
  function preload(page){if(page<1||page>604)return;var image=new Image();image.src=pageSource(page)}

  function commit(page){
    state.currentPage=clamp(page,1,604);reader.drag=null;reader.animating=false;renderImages();if(typeof renderLastRead==='function')renderLastRead();
  }
  function animateTo(page,direction){
    if(reader.animating||page<1||page>604)return;
    reader.animating=true;
    var width=Math.max(1,(reader.stage||buildStage()).clientWidth);
    requestAnimationFrame(function(){place(direction>0?width:-width,true)});
    setTimeout(function(){commit(page)},reader.duration+25);
  }
  function go(page){
    page=Number(page);if(page<1||page>604){toast('هذه نهاية المصحف');return}
    if(page===state.currentPage+1)return animateTo(page,1);
    if(page===state.currentPage-1)return animateTo(page,-1);
    commit(page);
  }

  function bindReader(stage){
    stage.addEventListener('pointerdown',function(event){
      if(reader.animating)return;
      reader.drag={pointer:event.pointerId,start:event.clientX,last:event.clientX,startTime:performance.now(),width:Math.max(1,stage.clientWidth)};
      try{stage.setPointerCapture(event.pointerId)}catch(ignore){}
    });
    stage.addEventListener('pointermove',function(event){
      var drag=reader.drag;if(!drag||drag.pointer!==event.pointerId)return;
      drag.last=event.clientX;
      var delta=clamp(drag.last-drag.start,-drag.width,drag.width);
      if((delta>0&&state.currentPage===604)||(delta<0&&state.currentPage===1))delta*=.16;
      place(delta,false);event.preventDefault();
    },{passive:false});
    function end(){
      var drag=reader.drag;if(!drag)return;reader.drag=null;
      var delta=drag.last-drag.start,elapsed=Math.max(16,performance.now()-drag.startTime),velocity=Math.abs(delta)/elapsed;
      var accept=Math.abs(delta)>Math.min(105,drag.width*.18)||(Math.abs(delta)>38&&velocity>.42);
      if(accept&&delta>0&&state.currentPage<604)return animateTo(state.currentPage+1,1);
      if(accept&&delta<0&&state.currentPage>1)return animateTo(state.currentPage-1,-1);
      place(0,true);setTimeout(function(){reader.animating=false},reader.duration+20);
    }
    stage.addEventListener('pointerup',end);stage.addEventListener('pointercancel',end);stage.addEventListener('lostpointercapture',end);
  }

  renderMushafPage=renderImages;
  turnTo=function(page){go(page)};
  readerNext=function(){go(state.currentPage+1)};
  readerPrev=function(){go(state.currentPage-1)};

  function shortest(from,to){return ((to-from+540)%360)-180}
  function circularSmooth(previous,next,alpha){
    if(previous==null)return next;
    var p=previous*Math.PI/180,n=next*Math.PI/180;
    var x=(1-alpha)*Math.cos(p)+alpha*Math.cos(n),y=(1-alpha)*Math.sin(p)+alpha*Math.sin(n);
    return (Math.atan2(y,x)*180/Math.PI+360)%360;
  }
  function compassFrame(){
    var arrow=document.getElementById('qiblaArrow');
    if(!arrow||compass.target==null){compass.raf=0;return}
    if(compass.display==null)compass.display=compass.target;
    var delta=shortest(compass.display,compass.target);
    compass.display+=clamp(delta,-8,8)*.18;
    arrow.style.transform='translate(-50%,-100%) rotate('+compass.display+'deg)';
    if(Math.abs(delta)>.15)compass.raf=requestAnimationFrame(compassFrame);else compass.raf=0;
  }
  function updateCompass(rawHeading,accuracy){
    var heading=Number(rawHeading);if(!Number.isFinite(heading))return;
    compass.heading=circularSmooth(compass.heading,(heading+360)%360,.12);
    var desired=(Number(state.qibla||0)-compass.heading+360)%360;
    compass.target=compass.target==null?desired:(compass.target+shortest(compass.target,desired)+360)%360;
    if(!compass.raf)compass.raf=requestAnimationFrame(compassFrame);
    var status=document.getElementById('compassStatus');
    if(status){if(Number(accuracy)<=0)status.textContent='حرّك الهاتف على شكل رقم ٨ لمعايرة البوصلة';else status.textContent='اتجاه الهاتف: '+arabicNumber(Math.round(compass.heading))+'°'}
  }
  window.onNativeHeading=function(heading,accuracy){state.nativeHeading=Number(heading);state.compassAccuracy=Number(accuracy||0);updateCompass(heading,accuracy)};
  renderQibla=function(){oldRenderQibla();compass.heading=null;compass.target=null;compass.display=null;if(state.nativeHeading!=null)updateCompass(state.nativeHeading,state.compassAccuracy)};

  function refreshHome(){
    var page=document.getElementById('page-home');if(!page)return;
    page.classList.add('official-home');
    var hero=page.querySelector('.hero');if(hero&&hero.querySelector('p:not(.eyebrow)'))hero.querySelector('p:not(.eyebrow)').textContent='مصحف المدينة المصوّر، الأذكار، الحديث، الصلاة والقبلة — دون إنترنت.';
  }

  showPage=function(name,push){
    oldShowPage(name,push);
    if(name==='reader')requestAnimationFrame(renderImages);
    if(name==='qibla'){compass.heading=null;compass.target=null;compass.display=null;setTimeout(function(){if(state.nativeHeading!=null)updateCompass(state.nativeHeading,state.compassAccuracy)},80)}
  };

  function init(){
    buildStage();refreshHome();
    var hint=document.querySelector('.gesture-hint');if(hint)hint.textContent='اسحب الصفحة أفقيًا مثل معرض الصور.';
    if(state.page==='reader')renderImages();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
