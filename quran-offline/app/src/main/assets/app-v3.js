(function(){
  state.mushafLayout=[];
  var renderMushafPageV2=renderMushafPage;
  var setFontSizeV2=setFontSize;

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
      if(!text&&line.words){
        text=line.words.map(function(word){return word.t||word.c||''}).join(' ');
      }
      return '<div class="mushaf-line quran-line" data-line="'+number+'">'+escapeHtml(text)+'</div>';
    }
    return '<div class="mushaf-line blank-line" data-line="'+number+'"></div>';
  }

  function fitMushafLines(){
    var box=document.getElementById('pageText');
    if(!box)return;
    var base=Math.max(18,Math.min(42,Number(localStorage.getItem('fontSize')||29)));
    var lines=box.querySelectorAll('.quran-line');
    for(var i=0;i<lines.length;i++){
      var line=lines[i];
      line.style.fontSize=base+'px';
      var available=Math.max(1,line.clientWidth-2),needed=Math.max(1,line.scrollWidth);
      if(needed>available){line.style.fontSize=Math.max(14,base*(available/needed)*.975)+'px'}
    }
  }

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
    if(!rec||!lines){renderMushafPageV2();return}
    var pageText=document.getElementById('pageText');
    pageText.className='page-text mushaf-lines lite-mushaf';
    pageText.innerHTML=lines.map(lineMarkup).join('');
    var ids=rec.surahs||rec.s||[];
    var surahNames=ids.map(function(id){return state.quran[id-1]?state.quran[id-1].name:''}).filter(Boolean);
    document.getElementById('pageSurah').textContent=surahNames.length?surahNames.join(' • '):'المصحف الشريف';
    document.getElementById('pageJuz').textContent='الجزء '+arabicNumber(rec.juz||rec.j||1);
    document.getElementById('readerTitle').textContent='مصحف المدينة';
    document.getElementById('readerSubtitle').textContent='الصفحة '+arabicNumber(state.currentPage)+' من ٦٠٤';
    document.getElementById('pageNumber').textContent=arabicNumber(state.currentPage);
    document.getElementById('pageBookmark').textContent=isBookmarked('page',state.currentPage)?'★':'☆';
    document.getElementById('mushafPage').classList.toggle('short-mushaf-page',state.currentPage===1||state.currentPage===2);
    resetPageTransform();
    requestAnimationFrame(function(){fitMushafLines();setTimeout(fitMushafLines,80)});
  };

  setFontSize=function(value){
    setFontSizeV2(value);
    document.documentElement.style.setProperty('--qcf-base',value+'px');
    if(state.page==='reader')requestAnimationFrame(fitMushafLines);
  };

  window.addEventListener('resize',function(){if(state.page==='reader')fitMushafLines()});
})();
