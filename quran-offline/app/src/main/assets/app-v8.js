(function(){
  'use strict';

  /* Rafiq Al-Huda 4.2 — real Mushaf arrangement, edge-to-edge 2D gallery paging,
     whole-word Arabic search, complete hadith cards, and page-only appearance settings. */

  var earlyStage=document.getElementById('mushafStage');
  if(earlyStage)earlyStage.dataset.stable2d='v8';

  var gallery={drag:null,animating:false,bound:false,duration:255};
  var previousShowPage=showPage;
  var previousSetFontSize=setFontSize;

  var paperPresets={
    cream:{paper:'#fffaf0',ink:'#24211d'},
    white:{paper:'#ffffff',ink:'#171918'},
    parchment:{paper:'#f3e0b9',ink:'#302519'},
    night:{paper:'#10231e',ink:'#f3ead7'},
    green:{paper:'#eaf3e7',ink:'#17352c'}
  };
  var framePresets={
    blue:{color:'#245f83',soft:'#d7e8f2',name:'أزرق المصحف'},
    gold:{color:'#aa7a2f',soft:'#f1e1bd',name:'ذهبي'},
    green:{color:'#39745f',soft:'#d7e9e0',name:'أخضر'},
    gray:{color:'#676f70',soft:'#e1e5e4',name:'رمادي'},
    none:{color:'transparent',soft:'transparent',name:'بدون إطار'}
  };
  var backdropPresets={
    light:{color:'#eef1ee',name:'فاتحة'},
    gray:{color:'#d9dfdc',name:'رمادية'},
    sepia:{color:'#dfd5c3',name:'دافئة'},
    dark:{color:'#071c17',name:'داكنة'}
  };

  function clamp(value,min,max){return Math.max(min,Math.min(max,value))}
  function pageRecord(page){return state.mushafLayout&&state.mushafLayout[page-1]}
  function lineKind(line){return line.kind||line.k||'x'}
  function lineNumber(line){return line.line||line.n||0}
  function lineChapter(line){return line.chapter||line.c||1}
  function pageSurahNames(record){
    return ((record&&(record.surahs||record.s))||[]).map(function(id){
      return state.quran[id-1]?state.quran[id-1].name:'';
    }).filter(Boolean);
  }
  function pageClasses(page,extra){
    var classes=['mushaf-page','mushaf-gallery-page',page%2?'page-on-right':'page-on-left'];
    if(page===1)classes.push('mushaf-opening','mushaf-fatiha');
    if(page===2)classes.push('mushaf-opening','mushaf-baqarah-opening');
    if(extra)classes.push(extra);
    return classes.join(' ');
  }
  function lineMarkup(line){
    var kind=lineKind(line),number=lineNumber(line);
    if(kind==='s'||kind==='surah'){
      var surah=state.quran[lineChapter(line)-1];
      return '<div class="mushaf-line surah-title-line" data-line="'+number+'"><span class="surah-strip"><i></i><b>سُورَةُ '+escapeHtml(surah?surah.name:'')+'</b><i></i></span></div>';
    }
    if(kind==='b'||kind==='basmala'){
      return '<div class="mushaf-line basmala-line" data-line="'+number+'">بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ</div>';
    }
    if(kind==='q'||kind==='quran'){
      return '<div class="mushaf-line quran-line" data-line="'+number+'"><span>'+escapeHtml(line.text||line.t||'')+'</span></div>';
    }
    return '<div class="mushaf-line blank-line" data-line="'+number+'"></div>';
  }
  function pageInnerMarkup(page,interactive){
    var record=pageRecord(page);
    if(!record)return '<div class="empty">تعذر تحميل الصفحة.</div>';
    var names=pageSurahNames(record),lines=record.lines||record.l||[];
    var last=names.length?names[names.length-1]:'المصحف الشريف';
    var header='<header class="mushaf-page-meta"><span class="meta-surah">سورة '+escapeHtml(last)+'</span><span class="meta-juz">الجزء '+arabicNumber(record.juz||record.j||1)+'</span></header>';
    var text='<div class="page-text mushaf-lines authentic-mushaf-lines">'+lines.map(lineMarkup).join('')+'</div>';
    var bookmark=interactive?'<button id="pageBookmark" onclick="togglePageBookmark()">'+(isBookmarked('page',page)?'★':'☆')+'</button>':'<span>☆</span>';
    var footer='<footer class="mushaf-page-footer">'+bookmark+'<b'+(interactive?' id="pageNumber"':'')+'>'+arabicNumber(page)+'</b>'+(interactive?'<button onclick="showReaderSettings()">Aa</button>':'<span>Aa</span>')+'</footer>';
    return header+text+footer;
  }
  function renderInto(element,page,interactive){
    if(!element)return;
    element.className=pageClasses(page,element.classList.contains('mushaf-side-page')?'mushaf-side-page':'');
    element.dataset.page=String(page);
    element.innerHTML=pageInnerMarkup(page,interactive);
    requestAnimationFrame(function(){fitAuthenticPage(element)});
  }
  function staticPage(page,extra){
    var article=document.createElement('article');
    article.className=pageClasses(page,'mushaf-side-page '+(extra||''));
    article.dataset.page=String(page);
    article.innerHTML=pageInnerMarkup(page,false);
    return article;
  }
  function renderCurrentPage(){
    var page=document.getElementById('mushafPage'),record=pageRecord(state.currentPage);
    if(!page||!record)return;
    renderInto(page,state.currentPage,true);
    var names=pageSurahNames(record),title=names.length?names.join(' • '):'المصحف الشريف';
    var titleNode=document.getElementById('readerTitle');if(titleNode)titleNode.textContent=title;
    var subtitle=document.getElementById('readerSubtitle');if(subtitle)subtitle.textContent='الصفحة '+arabicNumber(state.currentPage)+' من ٦٠٤';
    var chip=document.getElementById('readerPageChip');if(chip)chip.textContent='الصفحة '+arabicNumber(state.currentPage)+' من ٦٠٤';
    localStorage.setItem('lastPage',String(state.currentPage));
    localStorage.setItem('lastRead',JSON.stringify({page:state.currentPage}));
    page.style.transition='none';
    page.style.transform='translate3d(0,0,0)';
  }
  renderMushafPage=renderCurrentPage;

  function fitAuthenticPage(page){
    if(!page)return;
    var box=page.querySelector('.authentic-mushaf-lines');
    if(!box||!box.clientWidth||!box.clientHeight)return;
    var spacing=clamp(Number(localStorage.getItem('mushafSpacing')||100),86,116)/100;
    var rowHeight=box.clientHeight/15;
    var requested=clamp(Number(localStorage.getItem('fontSize')||27),20,38);
    var base=clamp(Math.min(requested,rowHeight*.69/spacing),15,32);
    var lines=box.querySelectorAll('.quran-line span');
    for(var i=0;i<lines.length;i++){
      var line=lines[i];
      line.style.fontSize=base+'px';
      line.style.transform='none';
      line.style.wordSpacing='.025em';
      var available=Math.max(1,line.parentElement.clientWidth-4);
      var width=Math.max(1,line.scrollWidth);
      if(width>available){
        var ratio=clamp(available/width,.76,1);
        if(ratio>.86)line.style.transform='scaleX('+ratio+')';
        else line.style.fontSize=Math.max(13,base*ratio*.98)+'px';
      }
    }
    var titleSize=clamp(base*.66,14,21);
    var titles=box.querySelectorAll('.surah-title-line b');
    for(var t=0;t<titles.length;t++)titles[t].style.fontSize=titleSize+'px';
    var basmala=box.querySelectorAll('.basmala-line');
    for(var b=0;b<basmala.length;b++)basmala[b].style.fontSize=clamp(base*.88,17,27)+'px';
  }

  function stageWidth(){var stage=document.getElementById('mushafStage');return Math.max(1,stage?stage.clientWidth:window.innerWidth)}
  function clearSidePages(){
    var stage=document.getElementById('mushafStage');if(!stage)return;
    var sides=stage.querySelectorAll('.mushaf-side-page');for(var i=0;i<sides.length;i++)sides[i].remove();
  }
  function preparePages(){
    var stage=document.getElementById('mushafStage'),current=document.getElementById('mushafPage');
    if(!stage||!current)return null;
    clearSidePages();
    var next=null,previous=null;
    if(state.currentPage<604){next=staticPage(state.currentPage+1,'mushaf-next-page');stage.appendChild(next);fitAuthenticPage(next)}
    if(state.currentPage>1){previous=staticPage(state.currentPage-1,'mushaf-prev-page');stage.appendChild(previous);fitAuthenticPage(previous)}
    var nodes={current:current,next:next,previous:previous,width:stageWidth()};
    positionPages(0,nodes,false);
    return nodes;
  }
  function positionPages(delta,nodes,animate){
    if(!nodes)return;
    var transition=animate?'transform '+gallery.duration+'ms cubic-bezier(.22,.72,.24,1)':'none';
    [nodes.current,nodes.next,nodes.previous].forEach(function(page){if(page)page.style.transition=transition});
    nodes.current.style.transform='translate3d('+delta+'px,0,0)';
    if(nodes.next)nodes.next.style.transform='translate3d('+(-nodes.width+delta)+'px,0,0)';
    if(nodes.previous)nodes.previous.style.transform='translate3d('+(nodes.width+delta)+'px,0,0)';
  }
  function finishPageChange(page){
    state.currentPage=clamp(page,1,604);
    renderCurrentPage();
    renderLastRead();
    clearSidePages();
    gallery.drag=null;gallery.animating=false;
  }
  function animateTo(page,direction,nodes){
    if(gallery.animating||page<1||page>604)return;
    gallery.animating=true;
    var target=direction>0?nodes.width:-nodes.width;
    requestAnimationFrame(function(){positionPages(target,nodes,true)});
    setTimeout(function(){finishPageChange(page)},gallery.duration+25);
  }
  function jumpTo(page){
    page=Number(page);
    if(page<1||page>604)return toast('هذه نهاية المصحف');
    if(gallery.animating||page===state.currentPage)return;
    var nodes=preparePages();
    if(!nodes){state.currentPage=page;renderCurrentPage();return}
    if(page===state.currentPage+1)return animateTo(page,1,nodes);
    if(page===state.currentPage-1)return animateTo(page,-1,nodes);
    finishPageChange(page);
  }
  turnTo=function(page){jumpTo(page)};
  readerNext=function(){jumpTo(state.currentPage+1)};
  readerPrev=function(){jumpTo(state.currentPage-1)};

  function bindGalleryReader(){
    var stage=document.getElementById('mushafStage');if(!stage||gallery.bound)return;
    gallery.bound=true;stage.dataset.stable2d='v8';
    stage.addEventListener('pointerdown',function(event){
      if(gallery.animating||event.target.closest('button'))return;
      var nodes=preparePages();if(!nodes)return;
      gallery.drag={pointer:event.pointerId,startX:event.clientX,lastX:event.clientX,startTime:performance.now(),nodes:nodes};
      try{stage.setPointerCapture(event.pointerId)}catch(ignore){}
    });
    stage.addEventListener('pointermove',function(event){
      var drag=gallery.drag;if(!drag||drag.pointer!==event.pointerId)return;
      drag.lastX=event.clientX;
      var delta=drag.lastX-drag.startX;
      if((delta>0&&!drag.nodes.next)||(delta<0&&!drag.nodes.previous))delta*=.18;
      delta=clamp(delta,-drag.nodes.width,drag.nodes.width);
      positionPages(delta,drag.nodes,false);
      event.preventDefault();
    },{passive:false});
    function endDrag(){
      var drag=gallery.drag;if(!drag)return;
      gallery.drag=null;
      var delta=drag.lastX-drag.startX;
      var elapsed=Math.max(16,performance.now()-drag.startTime);
      var velocity=Math.abs(delta)/elapsed;
      var threshold=Math.min(96,drag.nodes.width*.17);
      var commit=Math.abs(delta)>threshold||(Math.abs(delta)>34&&velocity>.38);
      if(commit&&delta>0&&drag.nodes.next)return animateTo(state.currentPage+1,1,drag.nodes);
      if(commit&&delta<0&&drag.nodes.previous)return animateTo(state.currentPage-1,-1,drag.nodes);
      positionPages(0,drag.nodes,true);
      setTimeout(function(){clearSidePages();gallery.animating=false},gallery.duration+20);
    }
    stage.addEventListener('pointerup',endDrag);
    stage.addEventListener('pointercancel',endDrag);
    stage.addEventListener('lostpointercapture',endDrag);
  }

  function normalizeArabicWord(value){
    return String(value||'').normalize('NFC')
      .replace(/[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]/g,'')
      .replace(/[أإآٱ]/g,'ا').replace(/ى/g,'ي').replace(/ة/g,'ه')
      .replace(/ؤ/g,'و').replace(/ئ/g,'ي').replace(/ـ/g,'')
      .replace(/[^\u0621-\u064A0-9]/g,'').toLowerCase();
  }
  function queryTerms(query){
    return String(query||'').trim().split(/\s+/).map(normalizeArabicWord).filter(Boolean);
  }
  function wordSpans(text){
    var source=String(text||''),regex=/[\u0600-\u06FF]+|[0-9]+/g,match,words=[];
    while((match=regex.exec(source))){
      var normalized=normalizeArabicWord(match[0]);
      if(normalized)words.push({raw:match[0],norm:normalized,start:match.index,end:match.index+match[0].length});
    }
    return words;
  }
  function wordMatch(word,term){
    if(word===term)return 4;
    if(word.indexOf(term)===0)return 3;
    if(word.length>term.length&&word.slice(-term.length)===term)return 2;
    return 0;
  }
  function mergeRanges(ranges){
    ranges.sort(function(a,b){return a[0]-b[0]});var merged=[];
    for(var i=0;i<ranges.length;i++){
      var last=merged[merged.length-1];
      if(last&&ranges[i][0]<=last[1])last[1]=Math.max(last[1],ranges[i][1]);
      else merged.push(ranges[i]);
    }
    return merged;
  }
  function exactWordSearch(text,query){
    var terms=queryTerms(query),words=wordSpans(text),score=0,ranges=[];
    if(!terms.length)return {score:0,ranges:[]};
    for(var t=0;t<terms.length;t++){
      var term=terms[t],best=0,found=[];
      for(var w=0;w<words.length;w++){
        var rank=wordMatch(words[w].norm,term);
        if(rank){best=Math.max(best,rank);found.push(words[w])}
      }
      if(!best)return {score:0,ranges:[]};
      score+=best===4?1500:best===3?1050:850;
      for(var f=0;f<found.length;f++)ranges.push([found[f].start,found[f].end]);
    }
    var normalizedText=words.map(function(word){return word.norm}).join(' ');
    var normalizedQuery=terms.join(' ');
    if(normalizedText.indexOf(normalizedQuery)>=0)score+=2600;
    return {score:score,ranges:mergeRanges(ranges)};
  }
  function highlightedWords(text,query){
    var ranges=exactWordSearch(text,query).ranges;if(!ranges.length)return escapeHtml(text);
    var html='',position=0;
    for(var i=0;i<ranges.length;i++){
      html+=escapeHtml(text.slice(position,ranges[i][0]));
      html+='<mark>'+escapeHtml(text.slice(ranges[i][0],ranges[i][1]))+'</mark>';
      position=ranges[i][1];
    }
    return html+escapeHtml(text.slice(position));
  }
  function queryTooBroad(query){
    var terms=queryTerms(query),common={ال:1,في:1,من:1,عن:1,ما:1,لا:1,يا:1,او:1};
    return terms.length===1&&(terms[0].length<2||common[terms[0]]);
  }

  renderQuranSearch=function(query){
    if(!state.quran.length||state.currentQuranTab!=='surahs')return;
    state.quranSearchQuery=query||'';
    var box=document.getElementById('surahList'),raw=String(query||'').trim(),rows=[];
    if(!raw){
      for(var i=0;i<state.quran.length;i++)rows.push({type:'surah',score:0,s:state.quran[i]});
    }else if(queryTooBroad(raw)){
      box.innerHTML='<div class="empty search-help">اكتب كلمة أوضح من حرفين، مثل: الصلاة أو الصدق.</div>';return;
    }else{
      for(var s=0;s<state.quran.length;s++){
        var surah=state.quran[s];
        var nameHit=exactWordSearch(surah.name+' '+(surah.transliteration||'')+' '+surah.id,raw);
        if(nameHit.score)rows.push({type:'surah',score:nameHit.score+3500,s:surah});
        for(var v=0;v<surah.verses.length;v++){
          var ayah=surah.verses[v],hit=exactWordSearch(ayah.text,raw);
          if(hit.score)rows.push({type:'ayah',score:hit.score,s:surah,a:ayah});
        }
      }
      rows.sort(function(a,b){return b.score-a.score});rows=rows.slice(0,100);
    }
    box.innerHTML=rows.map(function(item){
      if(item.type==='surah')return surahRow(item.s);
      return '<button class="surah-row ayah-search-row" onclick="openSurah('+item.s.id+','+item.a.id+')"><span class="number-badge">'+arabicNumber(item.a.id)+'</span><span class="surah-info"><strong>'+escapeHtml(item.s.name)+' — الآية '+arabicNumber(item.a.id)+'</strong><small>'+highlightedWords(item.a.text,state.quranSearchQuery)+'</small></span></button>';
    }).join('')||'<div class="empty search-help">لا توجد آية أو سورة تطابق الكلمة بهذه الصيغة.</div>';
  };

  runHadithSearch=function(query){
    if(!state.hadith.length)return;
    state.hadithSearchQuery=query||'';
    var raw=String(query||'').trim(),book=state.hadithBook,results=[];
    if(raw&&queryTooBroad(raw)){
      state.hadithMatches=[];state.hadithVisible=12;
      document.getElementById('hadithResults').innerHTML='<div class="empty card search-help">اكتب كلمة أوضح، مثل: الصلاة أو الصدق.</div>';
      document.getElementById('loadMoreHadith').classList.add('hidden');return;
    }
    for(var i=0;i<state.hadith.length;i++){
      var hadith=state.hadith[i];if(book!=='all'&&hadith.book!==book)continue;
      var searchable=(hadith.text||'')+' '+(hadith.narrator||'')+' '+(hadith.book||'');
      var result=raw?exactWordSearch(searchable,raw):{score:1,ranges:[]};
      if(!raw||result.score)results.push({h:hadith,score:result.score});
    }
    results.sort(function(a,b){return b.score-a.score});
    state.hadithMatches=results;state.hadithVisible=12;renderHadithResults(raw);
  };
  renderHadithResults=function(query){
    var box=document.getElementById('hadithResults'),items=state.hadithMatches.slice(0,state.hadithVisible),html='';
    html+='<div class="hadith-library-head"><strong>مكتبة الأحاديث</strong><span>'+arabicNumber(state.hadithMatches.length)+' نتيجة</span></div>';
    if(query)html+='<div class="smart-note">يُعرض الحديث فقط عند وجود الكلمة نفسها، أو كلمة تبدأ بها أو تنتهي بها. ويُحدد كامل اللفظ المطابق، لا حروف متفرقة.</div>';
    for(var i=0;i<items.length;i++){
      var h=items[i].h,marked=isBookmarked('hadith',h.id),full=h.text||h.display||'';
      html+='<article class="hadith-card complete-hadith-card"><div class="hadith-card-top"><span class="hadith-book-chip">'+escapeHtml(h.book)+'</span><button class="star-btn" onclick="toggleHadithBookmark('+h.id+',this)">'+(marked?'★':'☆')+'</button></div><p class="hadith-text">'+highlightedWords(full,state.hadithSearchQuery)+'</p><div class="hadith-meta"><span><b>الراوي:</b> '+escapeHtml(h.narrator||'مذكور في نص الحديث')+'</span><span><b>المصدر:</b> '+escapeHtml(h.book)+' — رقم '+arabicNumber(h.number||h.id)+'</span><span><b>الحكم:</b> '+escapeHtml(h.grade||'راجع تخريج المصدر')+'</span></div></article>';
    }
    box.innerHTML=html||'<div class="empty card">لا توجد نتائج مطابقة للكلمة.</div>';
    var more=document.getElementById('loadMoreHadith');if(more)more.classList.toggle('hidden',state.hadithVisible>=state.hadithMatches.length);
  };
  loadMoreHadith=function(){state.hadithVisible+=12;renderHadithResults(state.hadithSearchQuery||'')};

  function applyReaderAppearance(){
    var paperId=localStorage.getItem('mushaf')||'cream';
    var frameId=localStorage.getItem('mushafFrame')||'blue';
    var backdropId=localStorage.getItem('readerBackdrop')||'light';
    var paper=paperPresets[paperId]||paperPresets.cream;
    var frame=framePresets[frameId]||framePresets.blue;
    var backdrop=backdropPresets[backdropId]||backdropPresets.light;
    var root=document.documentElement;
    root.dataset.mushaf=paperId;root.dataset.mushafFrame=frameId;root.dataset.readerBackdrop=backdropId;
    root.style.setProperty('--mushaf-paper-v8',paper.paper);
    root.style.setProperty('--mushaf-ink-v8',paper.ink);
    root.style.setProperty('--mushaf-frame-v8',frame.color);
    root.style.setProperty('--mushaf-frame-soft-v8',frame.soft);
    root.style.setProperty('--reader-backdrop-v8',backdrop.color);
    root.style.setProperty('--mushaf-spacing-v8',String(clamp(Number(localStorage.getItem('mushafSpacing')||100),86,116)/100));
  }
  setMushaf=function(id){
    if(!paperPresets[id])id='cream';
    localStorage.setItem('mushaf',id);applyReaderAppearance();renderSwatches();refreshCustomSettings();
    if(state.page==='reader')requestAnimationFrame(renderCurrentPage);
    toast('تم تغيير لون ورق الصفحة داخل الإطار');
  };
  window.setMushafFrame=function(id){
    if(!framePresets[id])id='blue';
    localStorage.setItem('mushafFrame',id);applyReaderAppearance();refreshCustomSettings();
    toast('تم تغيير إطار الصفحة وشريط السورة');
  };
  window.setReaderBackdrop=function(id){
    if(!backdropPresets[id])id='light';
    localStorage.setItem('readerBackdrop',id);applyReaderAppearance();refreshCustomSettings();
    toast('تم تغيير الخلفية خلف الصفحة');
  };
  window.setMushafSpacing=function(value){
    value=clamp(Number(value)||100,86,116);
    localStorage.setItem('mushafSpacing',String(value));applyReaderAppearance();
    var label=document.getElementById('mushafSpacingValue');if(label)label.textContent=arabicNumber(value)+'٪';
    if(state.page==='reader')requestAnimationFrame(function(){fitAuthenticPage(document.getElementById('mushafPage'))});
  };
  function swatchButtons(map,active,handler){
    return Object.keys(map).map(function(id){
      var item=map[id],background=item.color==='transparent'?'linear-gradient(135deg,#fff 45%,#c44 46% 54%,#fff 55%)':item.color;
      return '<button class="swatch '+(id===active?'active':'')+'" aria-label="'+item.name+'" title="'+item.name+'" style="background:'+background+'" onclick="'+handler+'(\''+id+'\')"></button>';
    }).join('');
  }
  function installCustomSettings(){
    var settings=document.querySelector('#page-settings .settings-card');if(!settings||document.getElementById('mushafFrameSwatches'))return;
    var paper=document.getElementById('mushafSwatches');
    if(paper&&paper.previousElementSibling)paper.previousElementSibling.textContent='لون ورق الصفحة داخل الإطار';
    var anchor=paper?paper.closest('.setting'):settings.querySelector('.setting:nth-child(3)');
    var block=document.createElement('div');
    block.className='setting mushaf-advanced-setting';
    block.innerHTML='<label>لون الإطار وشريط اسم السورة</label><div id="mushafFrameSwatches" class="swatches"></div><label>الخلفية التي تظهر خلف الصفحة</label><div id="readerBackdropSwatches" class="swatches"></div><label>تباعد أسطر الصفحة: <span id="mushafSpacingValue"></span></label><input id="mushafSpacingRange" type="range" min="86" max="116" value="100" oninput="setMushafSpacing(this.value)"><small class="muted">هذه الخيارات منفصلة: لون الورق يغيّر داخل الصفحة، والإطار يغيّر حدودها وشريط السورة، والخلفية تغيّر المساحة خلف الصفحة فقط.</small>';
    if(anchor&&anchor.nextSibling)settings.insertBefore(block,anchor.nextSibling);else settings.appendChild(block);
    var turnRows=settings.querySelectorAll('.switch-row');
    for(var i=0;i<turnRows.length;i++){
      if(turnRows[i].textContent.indexOf('السحب السلس')>=0)turnRows[i].closest('.setting').style.display='none';
    }
    refreshCustomSettings();
  }
  function refreshCustomSettings(){
    var frame=document.getElementById('mushafFrameSwatches');if(frame)frame.innerHTML=swatchButtons(framePresets,localStorage.getItem('mushafFrame')||'blue','setMushafFrame');
    var backdrop=document.getElementById('readerBackdropSwatches');if(backdrop)backdrop.innerHTML=swatchButtons(backdropPresets,localStorage.getItem('readerBackdrop')||'light','setReaderBackdrop');
    var range=document.getElementById('mushafSpacingRange'),value=clamp(Number(localStorage.getItem('mushafSpacing')||100),86,116);
    if(range)range.value=String(value);
    var label=document.getElementById('mushafSpacingValue');if(label)label.textContent=arabicNumber(value)+'٪';
  }

  setFontSize=function(value){
    previousSetFontSize(value);
    if(state.page==='reader')requestAnimationFrame(function(){fitAuthenticPage(document.getElementById('mushafPage'))});
  };
  showPage=function(name,push){
    previousShowPage(name,push);
    if(name==='reader')requestAnimationFrame(function(){renderCurrentPage();bindGalleryReader()});
    if(name==='hadith')setTimeout(function(){var input=document.getElementById('hadithSearch');if(input&&!input.value)runHadithSearch('')},0);
  };

  function initV8(){
    applyReaderAppearance();installCustomSettings();bindGalleryReader();renderCurrentPage();
    var hint=document.querySelector('.gesture-hint');if(hint)hint.textContent='اسحب الصفحة يمينًا أو يسارًا مثل الصور؛ الصفحات متصلة بلا طي أو دوران.';
    var about=document.querySelector('#page-settings .setting:last-child .muted');
    if(about)about.textContent='الإصدار 4.2 — تخطيط مصحف بصفحة كاملة وشريط سورة، سحب 2D متصل، بحث كلمة صحيح، وأحاديث كاملة. يعمل دون إنترنت.';
    window.addEventListener('resize',function(){if(state.page==='reader')requestAnimationFrame(renderCurrentPage)});
  }
  document.addEventListener('DOMContentLoaded',initV8);
})();
