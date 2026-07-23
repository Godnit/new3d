(function(){
  state.mushafLayout=[];
  state.turnBusy=false;
  state.featuredHadithOffset=0;

  var renderMushafPageV2=renderMushafPage;
  var setFontSizeV2=setFontSize;
  var showPageV2=showPage;

  function lineKind(line){return line.kind||line.k||'blank'}
  function lineNumber(line){return line.line||line.n||0}
  function lineChapter(line){return line.chapter||line.c||1}

  function lineMarkup(line){
    var kind=lineKind(line),number=lineNumber(line);
    if(kind==='surah'||kind==='s'){
      var surah=state.quran[lineChapter(line)-1];
      return '<div class="mushaf-line surah-title-line" data-line="'+number+'"><span>سُورَةُ '+escapeHtml(surah?surah.name:'')+'</span></div>';
    }
    if(kind==='basmala'||kind==='b'){
      return '<div class="mushaf-line basmala-line" data-line="'+number+'">بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ</div>';
    }
    if(kind==='quran'||kind==='q'){
      var text=line.text||line.t||'';
      if(!text&&line.words){text=line.words.map(function(word){return word.t||word.c||''}).join(' ')}
      return '<div class="mushaf-line quran-line" data-line="'+number+'">'+escapeHtml(text)+'</div>';
    }
    return '<div class="mushaf-line blank-line" data-line="'+number+'"></div>';
  }

  function fitMushafLines(){
    var box=document.getElementById('pageText');
    if(!box||!box.clientWidth||!box.clientHeight)return;
    var page=document.getElementById('mushafPage');
    var opening=page&&page.classList.contains('opening-mushaf-page');
    var base=Math.max(18,Math.min(42,Number(localStorage.getItem('fontSize')||29)));
    var visible=Math.max(1,box.querySelectorAll('.mushaf-line:not(.blank-line)').length);
    var rowCount=opening?visible:15;
    var rowHeight=Math.max(1,box.clientHeight/rowCount);
    var target=Math.min(opening?56:42,opening?Math.max(base+7,rowHeight*.58):Math.max(base,rowHeight*.70));
    var lines=box.querySelectorAll('.quran-line');
    for(var i=0;i<lines.length;i++){
      var line=lines[i];
      line.style.fontSize=target+'px';
      line.style.transform='none';
      var available=Math.max(1,line.clientWidth-4),needed=Math.max(1,line.scrollWidth);
      if(needed>available){line.style.fontSize=Math.max(14,target*(available/needed)*.978)+'px'}
    }
  }

  function ensureReaderChrome(){
    var reader=document.getElementById('page-reader');
    if(!reader||document.getElementById('readerFloatingChrome'))return;
    var chrome=document.createElement('div');
    chrome.id='readerFloatingChrome';
    chrome.className='reader-floating-chrome';
    chrome.innerHTML='<button class="reader-float-btn reader-menu-float" aria-label="القائمة الجانبية" onclick="toggleDrawer(true)">☰</button><div id="readerPageChip" class="reader-page-chip">الصفحة ١</div><button class="reader-float-btn reader-settings-float" aria-label="إعدادات المصحف" onclick="showReaderSettings()">Aa</button>';
    reader.appendChild(chrome);
    var next=document.createElement('button');
    next.className='reader-edge reader-edge-next';
    next.setAttribute('aria-label','الصفحة التالية');
    next.setAttribute('onclick','readerNext()');
    next.textContent='›';
    var prev=document.createElement('button');
    prev.className='reader-edge reader-edge-prev';
    prev.setAttribute('aria-label','الصفحة السابقة');
    prev.setAttribute('onclick','readerPrev()');
    prev.textContent='‹';
    reader.appendChild(next);reader.appendChild(prev);
  }

  function updateReaderChrome(){
    var chip=document.getElementById('readerPageChip');
    if(chip)chip.textContent='الصفحة '+arabicNumber(state.currentPage)+' من ٦٠٤';
  }

  showPage=function(name,push){
    showPageV2(name,push);
    document.body.classList.toggle('reader-mode',name==='reader');
    if(name==='reader'){
      window.scrollTo(0,0);
      ensureReaderChrome();
      updateReaderChrome();
      requestAnimationFrame(function(){fitMushafLines();setTimeout(fitMushafLines,90)});
    }
  };

  buildPageMap=function(){
    state.pageByAyah={};
    for(var p=0;p<state.pages.length;p++){
      var page=state.pages[p],items=page.verses||page.pages||page.v||[];
      for(var i=0;i<items.length;i++){
        var item=items[i];
        if(Array.isArray(item))state.pageByAyah[item[0]+':'+item[1]]=p+1;
        else state.pageByAyah[item.chapter+':'+item.verse]=p+1;
      }
    }
  };

  loadData=function(){
    Promise.all([
      fetch('quran.json').then(checkJson),
      fetch('quran_pages.json').then(checkJson),
      fetch('quran_mushaf.json').then(checkJson),
      fetch('hadith.json').then(checkJson)
    ]).then(function(all){
      state.quran=all[0];state.pages=all[1];state.mushafLayout=all[2];state.hadith=all[3];
      buildPageMap();renderQuranTab();runHadithSearch('');renderLastRead();
      document.getElementById('hadithCount').textContent=arabicNumber(state.hadith.length)+' حديث';
    }).catch(function(error){
      console.error(error);toast('تعذر تحميل بعض البيانات المضمّنة');
      document.getElementById('surahList').innerHTML='<div class="empty">تعذر تحميل بيانات المصحف.</div>';
    });
  };

  renderMushafPage=function(){
    var rec=state.mushafLayout[state.currentPage-1];
    var lines=rec&&(rec.lines||rec.l);
    if(!rec||!lines){renderMushafPageV2();updateReaderChrome();return}
    var opening=state.currentPage===1||state.currentPage===2;
    var shown=opening?lines.filter(function(line){return lineKind(line)!=='blank'}):lines;
    var pageText=document.getElementById('pageText');
    pageText.className='page-text mushaf-lines lite-mushaf';
    pageText.style.setProperty('--visible-lines',String(Math.max(1,shown.length)));
    pageText.innerHTML=shown.map(lineMarkup).join('');
    var ids=rec.surahs||rec.s||[];
    var surahNames=ids.map(function(id){return state.quran[id-1]?state.quran[id-1].name:''}).filter(Boolean);
    document.getElementById('pageSurah').textContent=surahNames.length?surahNames.join(' • '):'المصحف الشريف';
    document.getElementById('pageJuz').textContent='الجزء '+arabicNumber(rec.juz||rec.j||1);
    document.getElementById('readerTitle').textContent='مصحف المدينة';
    document.getElementById('readerSubtitle').textContent='الصفحة '+arabicNumber(state.currentPage)+' من ٦٠٤';
    document.getElementById('pageNumber').textContent=arabicNumber(state.currentPage);
    document.getElementById('pageBookmark').textContent=isBookmarked('page',state.currentPage)?'★':'☆';
    var mushaf=document.getElementById('mushafPage');
    mushaf.classList.toggle('opening-mushaf-page',opening);
    mushaf.classList.toggle('page-on-right',state.currentPage%2===1);
    mushaf.classList.toggle('page-on-left',state.currentPage%2===0);
    resetPageTransform();updateReaderChrome();
    requestAnimationFrame(function(){fitMushafLines();setTimeout(fitMushafLines,90)});
  };

  function savePage(page){
    state.currentPage=page;
    localStorage.setItem('lastPage',page);
    localStorage.setItem('lastRead',JSON.stringify({page:page}));
    renderMushafPage();renderLastRead();
  }

  readerNext=function(){turnTo(state.currentPage+1,1)};
  readerPrev=function(){turnTo(state.currentPage-1,-1)};

  turnTo=function(page,direction){
    if(page<1||page>604)return toast('هذه نهاية المصحف');
    if(state.turnBusy)return;
    var el=document.getElementById('mushafPage'),stage=document.getElementById('mushafStage');
    var enabled=localStorage.getItem('pageTurn')!=='false'&&localStorage.getItem('reduceMotion')!=='true';
    if(!enabled||!el||!stage){savePage(page);return}
    var ghost=el.cloneNode(true);
    ghost.removeAttribute('id');
    var ids=ghost.querySelectorAll('[id]');for(var i=0;i<ids.length;i++)ids[i].removeAttribute('id');
    ghost.classList.remove('dragging','snap-back');
    ghost.classList.add('page-turn-copy',direction>0?'turn-to-right':'turn-to-left');
    ghost.style.transform=el.style.transform||'translate3d(0,0,0) rotateY(0deg)';
    stage.appendChild(ghost);
    state.turnBusy=true;
    el.classList.remove('dragging','snap-back');
    el.style.transform='none';
    savePage(page);
    ghost.getBoundingClientRect();
    requestAnimationFrame(function(){ghost.classList.add('page-turn-go')});
    setTimeout(function(){if(ghost.parentNode)ghost.parentNode.removeChild(ghost);state.turnBusy=false},390);
  };

  bindPageGesture=function(){
    var el=document.getElementById('mushafPage');
    if(!el)return;
    el.addEventListener('pointerdown',function(e){
      if(state.turnBusy||localStorage.getItem('pageTurn')==='false'||e.target.closest('button'))return;
      state.drag={x:e.clientX,last:e.clientX,width:Math.max(1,el.getBoundingClientRect().width),pointer:e.pointerId};
      try{el.setPointerCapture(e.pointerId)}catch(ignore){}
      el.classList.remove('snap-back');el.classList.add('dragging');
    });
    el.addEventListener('pointermove',function(e){
      if(!state.drag||state.drag.pointer!==e.pointerId)return;
      state.drag.last=e.clientX;
      var d=e.clientX-state.drag.x;
      if((d>0&&state.currentPage>=604)||(d<0&&state.currentPage<=1))d*=.18;
      var max=state.drag.width*.62;d=Math.max(-max,Math.min(max,d));
      var p=d/state.drag.width;
      el.style.transformOrigin=d>0?'right center':'left center';
      el.style.transform='translate3d('+(d*.46)+'px,0,0) rotateY('+(-p*18)+'deg) scale(.997)';
      var curl=el.querySelector('.page-curl');
      if(curl){curl.style.opacity=Math.min(.52,Math.abs(p)*1.2);curl.style.width=(Math.abs(p)*32)+'%';curl.style.right=d>0?'0':'auto';curl.style.left=d>0?'auto':'0'}
      e.preventDefault();
    },{passive:false});
    function finish(e){
      if(!state.drag)return;
      var d=state.drag.last-state.drag.x,threshold=state.drag.width*.13;
      state.drag=null;el.classList.remove('dragging');
      if(Math.abs(d)>threshold){
        var nextPage=state.currentPage+(d>0?1:-1);
        if(nextPage>=1&&nextPage<=604){turnTo(nextPage,d>0?1:-1);return}
      }
      el.classList.add('snap-back');resetPageTransform();
      setTimeout(function(){el.classList.remove('snap-back')},260);
    }
    el.addEventListener('pointerup',finish);
    el.addEventListener('pointercancel',finish);
    el.addEventListener('lostpointercapture',function(){if(state.drag)finish({})});
  };

  resetPageTransform=function(){
    var el=document.getElementById('mushafPage');if(!el)return;
    el.style.transform='none';el.style.transformOrigin='center center';
    var c=el.querySelector('.page-curl');if(c){c.style.opacity=0;c.style.width=0;c.style.left='auto';c.style.right='0'}
  };

  setFontSize=function(value){
    setFontSizeV2(value);
    document.documentElement.style.setProperty('--qcf-base',value+'px');
    if(state.page==='reader')requestAnimationFrame(fitMushafLines);
  };

  function featuredHadith(){
    var source=state.hadithMatches&&state.hadithMatches.length?state.hadithMatches.map(function(x){return x.h}):state.hadith;
    if(!source.length)return null;
    var day=Math.floor(Date.now()/86400000);
    return source[(day+state.featuredHadithOffset)%source.length];
  }

  function featuredMarkup(x){
    if(!x)return'';
    var marked=isBookmarked('hadith',x.id);
    return '<section class="hadith-featured"><div class="hadith-featured-head"><span>حديث اليوم</span><small>'+escapeHtml(x.book||'السنة النبوية')+'</small></div><p>'+escapeHtml(x.text)+'</p><div class="hadith-featured-meta">'+escapeHtml(x.narrator||'')+(x.grade?' • '+escapeHtml(x.grade):'')+'</div><div class="hadith-featured-actions"><button onclick="nextFeaturedHadith()">حديث آخر</button><button onclick="toggleFeaturedHadith('+x.id+',this)">'+(marked?'★ محفوظ':'☆ حفظ')+'</button></div></section>';
  }

  nextFeaturedHadith=function(){state.featuredHadithOffset++;renderHadithResults(normalizeArabic(document.getElementById('hadithSearch').value||''))};
  toggleFeaturedHadith=function(id,btn){
    var h=null;for(var i=0;i<state.hadith.length;i++)if(state.hadith[i].id===id){h=state.hadith[i];break}
    if(!h)return;toggleBookmark('hadith',id,{id:id,title:'حديث من '+h.book,text:h.text,book:h.book,number:h.number});
    btn.textContent=isBookmarked('hadith',id)?'★ محفوظ':'☆ حفظ';
  };

  renderHadithResults=function(q){
    var box=document.getElementById('hadithResults'),arr=state.hadithMatches.slice(0,state.hadithVisible),h=featuredMarkup(featuredHadith());
    h+='<div class="hadith-library-head"><strong>مكتبة الأحاديث</strong><span>'+arabicNumber(state.hadithMatches.length)+' نتيجة</span></div>';
    if(q&&arr.length)h+='<div class="smart-note">النتائج مرتبة حسب أقرب تطابق في النص والراوي والكتاب.</div>';
    for(var i=0;i<arr.length;i++){
      var x=arr[i].h,marked=isBookmarked('hadith',x.id);
      h+='<article class="hadith-card"><p class="hadith-text">'+escapeHtml(x.text)+'</p><div class="hadith-meta"><span><b>الراوي أو أول السند:</b> '+escapeHtml(x.narrator||'غير مفصول في المصدر')+'</span><span><b>المصدر:</b> '+escapeHtml(x.book)+' — رقم '+arabicNumber(x.number||x.id)+'</span><span><b>الحكم:</b> '+escapeHtml(x.grade||'راجع تخريج المصدر')+'</span></div><div class="hadith-actions"><span class="pill">'+escapeHtml(x.book)+'</span><button class="star-btn" onclick="toggleHadithBookmark('+x.id+',this)">'+(marked?'★':'☆')+'</button></div></article>';
    }
    box.innerHTML=h||'<div class="empty card">لا توجد نتائج. جرّب كلمة أقصر أو معنى قريبًا.</div>';
    document.getElementById('loadMoreHadith').classList.toggle('hidden',state.hadithVisible>=state.hadithMatches.length);
  };

  window.addEventListener('resize',function(){if(state.page==='reader')fitMushafLines()});
  document.addEventListener('DOMContentLoaded',function(){ensureReaderChrome()});
})();