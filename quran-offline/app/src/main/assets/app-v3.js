(function(){
  state.mushafLayout=[];
  state.pageFonts={};
  var renderMushafPageV2=renderMushafPage;
  var setFontSizeV2=setFontSize;

  function pad3(number){return String(number).padStart(3,'0')}
  function pageFontName(page){return 'QCF_Page_'+pad3(page)}

  function ensurePageFont(page){
    if(state.pageFonts[page])return state.pageFonts[page];
    var family=pageFontName(page),url='fonts/qcf-v2/p'+page+'.woff2';
    if(typeof FontFace==='function'){
      var face=new FontFace(family,"url('"+url+"') format('woff2')",{display:'block'});
      state.pageFonts[page]=face.load().then(function(loaded){document.fonts.add(loaded);return family}).catch(function(){delete state.pageFonts[page];return null});
    }else{
      var style=document.createElement('style');
      style.textContent="@font-face{font-family:'"+family+"';src:url('"+url+"') format('woff2');font-display:block}";
      document.head.appendChild(style);
      state.pageFonts[page]=Promise.resolve(family);
    }
    return state.pageFonts[page];
  }

  function lineMarkup(line){
    if(line.kind==='surah'){
      var surah=state.quran[(line.chapter||1)-1];
      return '<div class="mushaf-line surah-title-line" data-line="'+line.line+'"><span>سُورَةُ '+escapeHtml(surah?surah.name:'')+'</span></div>';
    }
    if(line.kind==='basmala'){
      return '<div class="mushaf-line basmala-line" data-line="'+line.line+'">بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ</div>';
    }
    if(line.kind==='quran'){
      var words=(line.words||[]).map(function(word){
        var value=word.c||word.t||'';
        return '<span class="qcf-word '+(word.k==='end'?'ayah-end':'')+'" data-verse="'+escapeHtml(word.v||'')+'" title="'+escapeHtml(word.t||'')+'">'+escapeHtml(value)+'</span>';
      }).join(' ');
      return '<div class="mushaf-line quran-line" data-line="'+line.line+'">'+words+'</div>';
    }
    return '<div class="mushaf-line blank-line" data-line="'+line.line+'"></div>';
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
      if(needed>available){line.style.fontSize=Math.max(15,base*(available/needed)*.985)+'px'}
    }
  }

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
    if(!rec||!rec.lines){renderMushafPageV2();return}
    var pageText=document.getElementById('pageText');
    pageText.className='page-text mushaf-lines';
    pageText.classList.remove('qcf-ready');
    pageText.innerHTML=rec.lines.map(lineMarkup).join('');
    var surahNames=(rec.surahs||[]).map(function(id){return state.quran[id-1]?state.quran[id-1].name:''}).filter(Boolean);
    document.getElementById('pageSurah').textContent=surahNames.length?surahNames.join(' • '):'المصحف الشريف';
    document.getElementById('pageJuz').textContent='الجزء '+arabicNumber(rec.juz||1);
    document.getElementById('readerTitle').textContent='مصحف المدينة';
    document.getElementById('readerSubtitle').textContent='الصفحة '+arabicNumber(state.currentPage)+' من ٦٠٤';
    document.getElementById('pageNumber').textContent=arabicNumber(state.currentPage);
    document.getElementById('pageBookmark').textContent=isBookmarked('page',state.currentPage)?'★':'☆';
    document.getElementById('mushafPage').classList.toggle('short-mushaf-page',state.currentPage===1||state.currentPage===2);
    resetPageTransform();
    ensurePageFont(state.currentPage).then(function(family){
      if(family){pageText.style.setProperty('--page-qcf-font',"'"+family+"'");pageText.classList.add('qcf-ready')}
      requestAnimationFrame(function(){fitMushafLines();setTimeout(fitMushafLines,80)});
    });
  };

  setFontSize=function(value){
    setFontSizeV2(value);
    document.documentElement.style.setProperty('--qcf-base',value+'px');
    if(state.page==='reader')requestAnimationFrame(fitMushafLines);
  };

  window.addEventListener('resize',function(){if(state.page==='reader')fitMushafLines()});
})();
