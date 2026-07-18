(function(){
  'use strict';

  /* Rafiq Al-Huda v4.1 — stable 2D paging, exact-prefix search, complete hadith cards, and compass wrap smoothing. */
  state.readerDragging=false;
  state.readerAnimating=false;
  state.readerDrag=null;
  state.compassContinuous=null;
  state.compassLastTarget=null;
  state.quranSearchQuery='';
  state.hadithSearchQuery='';

  var previousShowPage=showPage;
  var previousSetFontSize=setFontSize;
  var previousRenderQibla=renderQibla;

  function normalizeMapped(value){
    var source=String(value||'');
    var plain='',map=[];
    var table={'أ':'ا','إ':'ا','آ':'ا','ٱ':'ا','ى':'ي','ة':'ه','ؤ':'و','ئ':'ي','ـ':' '};
    var lastSpace=false;
    for(var i=0;i<source.length;i++){
      var ch=source[i];
      if(/[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]/.test(ch))continue;
      ch=table[ch]||ch;
      if(!/[\u0621-\u064A0-9 ]/.test(ch))ch=' ';
      if(ch===' '){if(lastSpace)continue;lastSpace=true}else lastSpace=false;
      plain+=ch.toLowerCase();
      map.push(i);
    }
    return {text:plain.trim(),map:map};
  }

  function queryTokens(query){
    return normalizeArabic(String(query||'').trim()).split(/\s+/).filter(function(token){return token.length>1});
  }

  function termMatches(text,query){
    var mapped=normalizeMapped(text),tokens=queryTokens(query),matches=[];
    if(!tokens.length)return {score:0,matches:matches};
    var score=0;
    for(var t=0;t<tokens.length;t++){
      var token=tokens[t],rx=new RegExp('(^|\\s)('+escapeRegExp(token)+'[\\u0621-\\u064A0-9]*)','g'),hit=false,m;
      while((m=rx.exec(mapped.text))){
        hit=true;
        var normalizedStart=m.index+m[1].length;
        var normalizedEnd=normalizedStart+m[2].length;
        var start=mapped.map[normalizedStart],end=mapped.map[Math.max(normalizedStart,normalizedEnd-1)];
        if(start!=null&&end!=null)matches.push([start,end+1]);
        score+=m[2]===token?1200:850;
        if(normalizedStart===0)score+=120;
        if(rx.lastIndex===m.index)rx.lastIndex++;
      }
      if(!hit)return {score:0,matches:[]};
    }
    var phrase=normalizeArabic(query||'');
    if(phrase&&mapped.text.indexOf(phrase)>=0)score+=2500;
    return {score:score,matches:mergeRanges(matches)};
  }

  function escapeRegExp(value){return String(value).replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}
  function mergeRanges(ranges){
    ranges.sort(function(a,b){return a[0]-b[0]});var out=[];
    for(var i=0;i<ranges.length;i++){var last=out[out.length-1];if(last&&ranges[i][0]<=last[1])last[1]=Math.max(last[1],ranges[i][1]);else out.push(ranges[i])}
    return out;
  }
  function highlightExactPrefix(text,query){
    var found=termMatches(text,query),ranges=found.matches;
    if(!ranges.length)return escapeHtml(text);
    var html='',pos=0;
    for(var i=0;i<ranges.length;i++){
      html+=escapeHtml(text.slice(pos,ranges[i][0]));
      html+='<mark>'+escapeHtml(text.slice(ranges[i][0],ranges[i][1]))+'</mark>';
      pos=ranges[i][1];
    }
    return html+escapeHtml(text.slice(pos));
  }

  function pageRecord(page){return state.mushafLayout[page-1]}
  function lineKindV5(line){return line.kind||line.k||'x'}
  function lineNumberV5(line){return line.line||line.n||0}
  function lineChapterV5(line){return line.chapter||line.c||1}
  function lineMarkupV5(line){
    var kind=lineKindV5(line),number=lineNumberV5(line);
    if(kind==='s'||kind==='surah'){
      var surah=state.quran[lineChapterV5(line)-1];
      return '<div class="mushaf-line surah-title-line" data-line="'+number+'"><span>سُورَةُ '+escapeHtml(surah?surah.name:'')+'</span></div>';
    }
    if(kind==='b'||kind==='basmala')return '<div class="mushaf-line basmala-line" data-line="'+number+'">بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ</div>';
    if(kind==='q'||kind==='quran')return '<div class="mushaf-line quran-line" data-line="'+number+'">'+escapeHtml(line.text||line.t||'')+'</div>';
    return '<div class="mushaf-line blank-line" data-line="'+number+'"></div>';
  }

  function pageNames(rec){
    var ids=rec&&(rec.surahs||rec.s)||[];
    return ids.map(function(id){return state.quran[id-1]?state.quran[id-1].name:''}).filter(Boolean);
  }

  function pageClass(page){
    var list=['mushaf-page','v5-mushaf-page'];
    if(page===1)list.push('mushaf-opening','mushaf-fatiha');
    else if(page===2)list.push('mushaf-opening','mushaf-baqarah-opening');
    list.push(page%2?'page-on-right':'page-on-left');
    return list.join(' ');
  }

  function staticPageHtml(page,extraClass){
    var rec=pageRecord(page);if(!rec)return '';
    var lines=rec.lines||rec.l||[],names=pageNames(rec),juz=rec.juz||rec.j||1;
    return '<article class="'+pageClass(page)+' '+(extraClass||'')+'" data-page="'+page+'">'+
      '<header><span>'+escapeHtml(names.length?names.join(' • '):'المصحف الشريف')+'</span><span>الجزء '+arabicNumber(juz)+'</span></header>'+
      '<div class="page-text mushaf-lines lite-mushaf">'+lines.map(lineMarkupV5).join('')+'</div>'+
      '<footer><span>☆</span><b>'+arabicNumber(page)+'</b><span>Aa</span></footer>'+
      '</article>';
  }

  function renderCurrentPage(){
    var rec=pageRecord(state.currentPage),lines=rec&&(rec.lines||rec.l);if(!rec||!lines)return;
    var page=document.getElementById('mushafPage');if(!page)return;
    page.className=pageClass(state.currentPage);
    page.dataset.page=state.currentPage;
    document.getElementById('pageText').innerHTML=lines.map(lineMarkupV5).join('');
    var names=pageNames(rec);
    document.getElementById('pageSurah').textContent=names.length?names.join(' • '):'المصحف الشريف';
    document.getElementById('pageJuz').textContent='الجزء '+arabicNumber(rec.juz||rec.j||1);
    document.getElementById('readerTitle').textContent=names.length?names.join(' • '):'المصحف الشريف';
    document.getElementById('readerSubtitle').textContent='الصفحة '+arabicNumber(state.currentPage)+' من ٦٠٤';
    document.getElementById('pageNumber').textContent=arabicNumber(state.currentPage);
    document.getElementById('pageBookmark').textContent=isBookmarked('page',state.currentPage)?'★':'☆';
    var chip=document.getElementById('readerPageChip');if(chip)chip.textContent='الصفحة '+arabicNumber(state.currentPage)+' من ٦٠٤';
    requestAnimationFrame(function(){fitPageTypography(page);setTimeout(function(){fitPageTypography(page)},90)});
  }

  function fitPageTypography(page){
    if(!page)return;var box=page.querySelector('.page-text');if(!box||!box.clientWidth||!box.clientHeight)return;
    var lines=box.querySelectorAll('.quran-line'),availableRows=page.classList.contains('mushaf-opening')?8:15;
    var rowHeight=box.clientHeight/availableRows;
    var requested=Math.max(18,Math.min(34,Number(localStorage.getItem('fontSize')||27)));
    var base=Math.min(requested,rowHeight*(page.classList.contains('mushaf-opening')?.62:.70));
    if(page.classList.contains('mushaf-fatiha'))base=Math.min(base,28);
    if(page.classList.contains('mushaf-baqarah-opening'))base=Math.min(base,26);
    base=Math.max(15,base);
    for(var i=0;i<lines.length;i++){lines[i].style.fontSize=base+'px';lines[i].style.letterSpacing='0';lines[i].style.wordSpacing='.02em'}
    var scale=1;
    for(var j=0;j<lines.length;j++)scale=Math.min(scale,(lines[j].clientWidth-8)/Math.max(1,lines[j].scrollWidth));
    var finalSize=Math.max(14,base*Math.min(1,scale)*.985);
    for(var k=0;k<lines.length;k++)lines[k].style.fontSize=finalSize+'px';
    var title=box.querySelectorAll('.surah-title-line');for(var a=0;a<title.length;a++)title[a].style.fontSize=Math.max(16,finalSize*.72)+'px';
    var basmala=box.querySelectorAll('.basmala-line');for(var b=0;b<basmala.length;b++)basmala[b].style.fontSize=Math.max(18,finalSize*.92)+'px';
  }

  renderMushafPage=renderCurrentPage;

  function removeSidePages(){
    var stage=document.getElementById('mushafStage');if(!stage)return;
    var sides=stage.querySelectorAll('.mushaf-side-page');for(var i=0;i<sides.length;i++)sides[i].remove();
  }

  function ensureSidePages(){
    var stage=document.getElementById('mushafStage'),current=document.getElementById('mushafPage');if(!stage||!current)return null;
    removeSidePages();
    var prev=null,next=null;
    if(state.currentPage>1){var wrap=document.createElement('div');wrap.innerHTML=staticPageHtml(state.currentPage-1,'mushaf-side-page mushaf-prev-page');prev=wrap.firstChild;stage.appendChild(prev);fitPageTypography(prev)}
    if(state.currentPage<604){var wrap2=document.createElement('div');wrap2.innerHTML=staticPageHtml(state.currentPage+1,'mushaf-side-page mushaf-next-page');next=wrap2.firstChild;stage.appendChild(next);fitPageTypography(next)}
    setTransforms(0,current,prev,next,false);
    return {current:current,prev:prev,next:next};
  }

  function setTransforms(delta,current,prev,next,animate){
    var width=Math.max(1,document.getElementById('mushafStage').clientWidth);
    var transition=animate?'transform .22s cubic-bezier(.22,.72,.24,1)':'none';
    [current,prev,next].forEach(function(el){if(el)el.style.transition=transition});
    current.style.transform='translate3d('+delta+'px,0,0)';
    if(prev)prev.style.transform='translate3d('+(width+delta)+'px,0,0)';
    if(next)next.style.transform='translate3d('+(-width+delta)+'px,0,0)';
  }

  function commitPage(page){
    state.currentPage=page;
    localStorage.setItem('lastPage',page);
    localStorage.setItem('lastRead',JSON.stringify({page:page}));
    renderCurrentPage();renderLastRead();removeSidePages();
    var current=document.getElementById('mushafPage');if(current){current.style.transition='none';current.style.transform='translate3d(0,0,0)'}
    state.readerAnimating=false;state.readerDragging=false;state.readerDrag=null;
  }

  function animatePageChange(target,direction,nodes){
    if(state.readerAnimating)return;state.readerAnimating=true;
    var stage=document.getElementById('mushafStage'),width=Math.max(1,stage.clientWidth);
    var current=nodes.current,prev=nodes.prev,next=nodes.next;
    requestAnimationFrame(function(){
      if(direction>0)setTransforms(width,current,prev,next,true);
      else setTransforms(-width,current,prev,next,true);
    });
    setTimeout(function(){commitPage(target)},235);
  }

  turnTo=function(page,direction){
    if(page<1||page>604)return toast('هذه نهاية المصحف');
    if(state.readerAnimating)return;
    var nodes=ensureSidePages();if(!nodes){commitPage(page);return}
    animatePageChange(page,direction>0?1:-1,nodes);
  };
  readerNext=function(){turnTo(state.currentPage+1,1)};
  readerPrev=function(){turnTo(state.currentPage-1,-1)};

  bindPageGesture=function(){
    var stage=document.getElementById('mushafStage');if(!stage||stage.dataset.v5Bound)return;stage.dataset.v5Bound='1';
    stage.addEventListener('pointerdown',function(e){
      if(state.readerAnimating||e.target.closest('button'))return;
      var nodes=ensureSidePages();if(!nodes)return;
      state.readerDragging=true;
      state.readerDrag={start:e.clientX,last:e.clientX,pointer:e.pointerId,nodes:nodes,width:Math.max(1,stage.clientWidth)};
      try{stage.setPointerCapture(e.pointerId)}catch(ignore){}
    });
    stage.addEventListener('pointermove',function(e){
      var drag=state.readerDrag;if(!drag||drag.pointer!==e.pointerId)return;
      drag.last=e.clientX;var delta=e.clientX-drag.start;
      if((delta>0&&state.currentPage>=604)||(delta<0&&state.currentPage<=1))delta*=.18;
      delta=Math.max(-drag.width,Math.min(drag.width,delta));
      setTransforms(delta,drag.nodes.current,drag.nodes.prev,drag.nodes.next,false);
      e.preventDefault();
    },{passive:false});
    function finish(){
      var drag=state.readerDrag;if(!drag)return;
      var delta=drag.last-drag.start,threshold=Math.min(92,drag.width*.16);state.readerDrag=null;state.readerDragging=false;
      if(delta>threshold&&state.currentPage<604){animatePageChange(state.currentPage+1,1,drag.nodes);return}
      if(delta<-threshold&&state.currentPage>1){animatePageChange(state.currentPage-1,-1,drag.nodes);return}
      setTransforms(0,drag.nodes.current,drag.nodes.prev,drag.nodes.next,true);
      setTimeout(function(){removeSidePages();state.readerAnimating=false},235);
    }
    stage.addEventListener('pointerup',finish);stage.addEventListener('pointercancel',finish);stage.addEventListener('lostpointercapture',finish);
  };

  renderQuranSearch=function(query){
    if(!state.quran.length||state.currentQuranTab!=='surahs')return;
    state.quranSearchQuery=query||'';
    var box=document.getElementById('surahList'),q=String(query||'').trim(),rows=[];
    if(!q){for(var i=0;i<state.quran.length;i++)rows.push({type:'surah',score:0,s:state.quran[i]})}
    else{
      for(var s=0;s<state.quran.length;s++){
        var su=state.quran[s],nameMatch=termMatches(su.name+' '+(su.transliteration||'')+' '+su.id,q);
        if(nameMatch.score)rows.push({type:'surah',score:nameMatch.score+3000,s:su});
        for(var v=0;v<su.verses.length;v++){
          var ay=su.verses[v],hit=termMatches(ay.text,q);
          if(hit.score)rows.push({type:'ayah',score:hit.score,s:su,a:ay});
        }
      }
      rows.sort(function(a,b){return b.score-a.score});rows=rows.slice(0,120);
    }
    box.innerHTML=rows.map(function(item){return item.type==='surah'?surahRow(item.s):ayahRow(item.s,item.a)}).join('')||'<div class="empty">لا توجد نتيجة تبدأ بالكلمة المكتوبة.</div>';
  };
  ayahRow=function(s,a){return '<button class="surah-row" onclick="openSurah('+s.id+','+a.id+')"><span class="number-badge">'+arabicNumber(a.id)+'</span><span class="surah-info"><strong>'+highlightExactPrefix(s.name,state.quranSearchQuery)+' — آية '+arabicNumber(a.id)+'</strong><small>'+highlightExactPrefix(a.text.substring(0,190),state.quranSearchQuery)+'</small></span></button>'};

  runHadithSearch=function(query){
    if(!state.hadith.length)return;
    state.hadithSearchQuery=query||'';
    var q=String(query||'').trim(),book=state.hadithBook,matches=[];
    for(var i=0;i<state.hadith.length;i++){
      var h=state.hadith[i];if(book!=='all'&&h.book!==book)continue;
      var full=(h.display||h.text||'')+' '+(h.text||'')+' '+(h.narrator||'')+' '+(h.book||'');
      var hit=q?termMatches(full,q):{score:1};
      if(!q||hit.score)matches.push({h:h,score:hit.score});
    }
    matches.sort(function(a,b){return b.score-a.score});
    state.hadithMatches=matches;state.hadithVisible=25;renderHadithResults(q);
  };

  function hadithBody(h){return h.display&&h.display.length>22?h.display:h.text||''}
  function fullNarrator(h){return h.narrator||'الراوي مذكور في المصدر'}
  renderHadithResults=function(query){
    var box=document.getElementById('hadithResults'),list=state.hadithMatches.slice(0,state.hadithVisible),html='';
    html+='<div class="hadith-library-head"><strong>مكتبة الأحاديث</strong><span>'+arabicNumber(state.hadithMatches.length)+' نتيجة</span></div>';
    if(query)html+='<div class="smart-note">تظهر النتائج التي تحتوي كلمة البحث كاملة أو كلمة تبدأ بها.</div>';
    for(var i=0;i<list.length;i++){
      var h=list[i].h,marked=isBookmarked('hadith',h.id),body=hadithBody(h);
      html+='<article class="hadith-card v5-hadith-card">'+
        '<div class="hadith-book-chip">'+escapeHtml(h.book)+'</div>'+
        '<p class="hadith-text">'+highlightExactPrefix(body,state.hadithSearchQuery)+'</p>'+
        '<div class="hadith-meta">'+
          '<span><b>الراوي:</b> '+escapeHtml(fullNarrator(h))+'</span>'+
          '<span><b>المصدر:</b> '+escapeHtml(h.book)+' — رقم '+arabicNumber(h.number||h.id)+'</span>'+
          '<span><b>حكم الحديث:</b> '+escapeHtml(h.grade||'راجع تخريج المصدر')+'</span>'+
        '</div>'+
        '<div class="hadith-actions"><button class="details-btn" onclick="toggleHadithFull(this)">عرض النص الكامل</button><button class="star-btn" onclick="toggleHadithBookmark('+h.id+',this)">'+(marked?'★':'☆')+'</button></div>'+
        '<div class="hadith-full hidden">'+escapeHtml(h.text||body)+'</div>'+
      '</article>';
    }
    box.innerHTML=html||'<div class="empty card">لا توجد نتائج مطابقة.</div>';
    var more=document.getElementById('loadMoreHadith');if(more)more.classList.toggle('hidden',state.hadithVisible>=state.hadithMatches.length);
  };
  window.toggleHadithFull=function(button){var full=button.closest('.hadith-card').querySelector('.hadith-full');full.classList.toggle('hidden');button.textContent=full.classList.contains('hidden')?'عرض النص الكامل':'إخفاء النص الكامل'};

  function shortestDelta(from,to){return ((to-from+540)%360)-180}
  function updateCompassV5(heading){
    var arrow=document.getElementById('qiblaArrow');if(!arrow)return;
    var target=(Number(state.qibla||0)-Number(heading||0)+360)%360;
    if(state.compassContinuous==null){state.compassContinuous=target;state.compassLastTarget=target}
    else{
      var delta=shortestDelta(state.compassLastTarget,target);
      if(Math.abs(delta)>55)delta=Math.sign(delta)*55;
      state.compassContinuous+=delta*.34;
      state.compassLastTarget=(state.compassLastTarget+delta+360)%360;
    }
    arrow.style.transform='translate(-50%,-100%) rotate('+state.compassContinuous+'deg)';
    var status=document.getElementById('compassStatus');
    if(status)status.textContent='اتجاه الهاتف: '+arabicNumber(Math.round(heading))+'° • حرّك الهاتف بهدوء حتى يشير السهم إلى الكعبة';
  }
  window.onNativeHeading=function(heading,accuracy){state.nativeHeading=Number(heading);state.compassAccuracy=Number(accuracy||0);updateCompassV5(state.nativeHeading)};
  orientationHandler=function(e){
    if(state.nativeHeading!=null)return;var heading=null;
    if(typeof e.webkitCompassHeading==='number')heading=e.webkitCompassHeading;
    else if(e.alpha!=null){heading=360-e.alpha;var angle=(screen.orientation&&screen.orientation.angle)||window.orientation||0;heading=(heading+Number(angle)+360)%360}
    if(heading!=null)updateCompassV5(heading);
  };
  renderQibla=function(){previousRenderQibla();state.compassContinuous=null;state.compassLastTarget=null;if(state.nativeHeading!=null)updateCompassV5(state.nativeHeading)};

  function upgradeHome(){
    var page=document.getElementById('page-home');if(!page||page.dataset.v5)return;page.dataset.v5='1';
    var hero=page.querySelector('.hero');if(hero)hero.classList.add('v5-hero');
    var quick=page.querySelector('.quick-grid');if(quick)quick.classList.add('v5-dashboard');
    var prayer=page.querySelector('.hero-next');if(prayer)prayer.classList.add('v5-next-prayer');
  }

  showPage=function(name,push){
    previousShowPage(name,push);
    if(name==='reader')requestAnimationFrame(function(){renderCurrentPage();bindPageGesture()});
    if(name==='qibla'){state.compassContinuous=null;state.compassLastTarget=null;setTimeout(function(){if(state.nativeHeading!=null)updateCompassV5(state.nativeHeading)},40)}
  };
  setFontSize=function(value){previousSetFontSize(value);if(state.page==='reader')requestAnimationFrame(function(){fitPageTypography(document.getElementById('mushafPage'))})};

  window.addEventListener('resize',function(){if(state.page==='reader')fitPageTypography(document.getElementById('mushafPage'))});
  document.addEventListener('DOMContentLoaded',function(){
    upgradeHome();bindPageGesture();
    var hint=document.querySelector('.gesture-hint');if(hint)hint.textContent='اسحب الصفحة أفقيًا مثل معرض الصور؛ الصفحة المجاورة تبقى ظاهرة أثناء السحب.';
    var about=document.querySelector('#page-settings .setting:last-child .muted');if(about)about.textContent='الإصدار 4.1 — تصميم جديد، صفحات 2D سلسة، بحث دقيق، أحاديث كاملة، وقبلة مستقرة. يعمل دون إنترنت.';
  });
})();
