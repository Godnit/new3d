(function(){
  'use strict';

  var oldShowPage=showPage;
  var oldSetFontSize=setFontSize;
  var oldRenderQibla=renderQibla;
  var reader={drag:null,animating:false};
  var compass={continuous:null,lastTarget:null};
  state.quranSearchQuery='';
  state.hadithSearchQuery='';

  function escRx(value){return String(value).replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}
  function normalizedMap(value){
    var source=String(value||''),plain='',map=[],lastSpace=false;
    var table={'أ':'ا','إ':'ا','آ':'ا','ٱ':'ا','ى':'ي','ة':'ه','ؤ':'و','ئ':'ي','ـ':' '};
    for(var i=0;i<source.length;i++){
      var ch=source[i];
      if(/[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]/.test(ch))continue;
      ch=table[ch]||ch;
      if(!/[\u0621-\u064A0-9 ]/.test(ch))ch=' ';
      if(ch===' '){if(lastSpace)continue;lastSpace=true}else lastSpace=false;
      plain+=ch.toLowerCase();map.push(i);
    }
    return {text:plain.trim(),map:map};
  }
  function tokens(query){return normalizeArabic(String(query||'').trim()).split(/\s+/).filter(function(x){return x.length>1})}
  function mergeRanges(ranges){
    ranges.sort(function(a,b){return a[0]-b[0]});var out=[];
    for(var i=0;i<ranges.length;i++){var last=out[out.length-1];if(last&&ranges[i][0]<=last[1])last[1]=Math.max(last[1],ranges[i][1]);else out.push(ranges[i])}
    return out;
  }
  function prefixMatch(text,query){
    var m=normalizedMap(text),ts=tokens(query),ranges=[],score=0;
    if(!ts.length)return {score:0,ranges:[]};
    for(var t=0;t<ts.length;t++){
      var token=ts[t],rx=new RegExp('(^|\\s)('+escRx(token)+'[\\u0621-\\u064A0-9]*)','g'),hit=false,found;
      while((found=rx.exec(m.text))){
        hit=true;
        var startN=found.index+found[1].length,endN=startN+found[2].length;
        var start=m.map[startN],end=m.map[Math.max(startN,endN-1)];
        if(start!=null&&end!=null)ranges.push([start,end+1]);
        score+=found[2]===token?1200:850;
        if(startN===0)score+=100;
        if(rx.lastIndex===found.index)rx.lastIndex++;
      }
      if(!hit)return {score:0,ranges:[]};
    }
    var phrase=normalizeArabic(query||'');
    if(phrase&&m.text.indexOf(phrase)>=0)score+=2400;
    return {score:score,ranges:mergeRanges(ranges)};
  }
  function highlightPrefix(text,query){
    var ranges=prefixMatch(text,query).ranges;if(!ranges.length)return escapeHtml(text);
    var html='',pos=0;
    for(var i=0;i<ranges.length;i++){
      html+=escapeHtml(text.slice(pos,ranges[i][0]));
      html+='<mark>'+escapeHtml(text.slice(ranges[i][0],ranges[i][1]))+'</mark>';
      pos=ranges[i][1];
    }
    return html+escapeHtml(text.slice(pos));
  }

  function rec(page){return state.mushafLayout[page-1]}
  function kind(line){return line.kind||line.k||'x'}
  function num(line){return line.line||line.n||0}
  function chapter(line){return line.chapter||line.c||1}
  function lineHtml(line){
    var k=kind(line),n=num(line);
    if(k==='s'||k==='surah'){
      var surah=state.quran[chapter(line)-1];
      return '<div class="mushaf-line surah-title-line" data-line="'+n+'"><span>سُورَةُ '+escapeHtml(surah?surah.name:'')+'</span></div>';
    }
    if(k==='b'||k==='basmala')return '<div class="mushaf-line basmala-line" data-line="'+n+'">بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ</div>';
    if(k==='q'||k==='quran')return '<div class="mushaf-line quran-line" data-line="'+n+'">'+escapeHtml(line.text||line.t||'')+'</div>';
    return '<div class="mushaf-line blank-line" data-line="'+n+'"></div>';
  }
  function names(record){
    return ((record&&(record.surahs||record.s))||[]).map(function(id){return state.quran[id-1]?state.quran[id-1].name:''}).filter(Boolean);
  }
  function classes(page,extra){
    var list=['mushaf-page','v5-mushaf-page',page%2?'page-on-right':'page-on-left'];
    if(page===1)list.push('mushaf-opening','mushaf-fatiha');
    if(page===2)list.push('mushaf-opening','mushaf-baqarah-opening');
    if(extra)list.push(extra);return list.join(' ');
  }
  function staticPage(page,extra){
    var record=rec(page);if(!record)return '';
    var pageNames=names(record),lines=record.lines||record.l||[];
    return '<article class="'+classes(page,extra)+'" data-page="'+page+'">'+
      '<header><span>'+escapeHtml(pageNames.length?pageNames.join(' • '):'المصحف الشريف')+'</span><span>الجزء '+arabicNumber(record.juz||record.j||1)+'</span></header>'+
      '<div class="page-text mushaf-lines lite-mushaf">'+lines.map(lineHtml).join('')+'</div>'+
      '<footer><span>☆</span><b>'+arabicNumber(page)+'</b><span>Aa</span></footer></article>';
  }
  function fitPage(page){
    if(!page)return;var box=page.querySelector('.page-text');if(!box||!box.clientWidth||!box.clientHeight)return;
    var opening=page.classList.contains('mushaf-opening'),rows=opening?8:15;
    var rowHeight=box.clientHeight/rows,requested=Math.max(18,Math.min(34,Number(localStorage.getItem('fontSize')||27)));
    var base=Math.min(requested,rowHeight*(opening?0.62:0.70));
    if(page.classList.contains('mushaf-fatiha'))base=Math.min(base,28);
    if(page.classList.contains('mushaf-baqarah-opening'))base=Math.min(base,26);
    base=Math.max(15,base);
    var q=box.querySelectorAll('.quran-line');
    for(var i=0;i<q.length;i++){q[i].style.fontSize=base+'px';q[i].style.wordSpacing='.02em'}
    var scale=1;
    for(var j=0;j<q.length;j++)scale=Math.min(scale,Math.max(.52,(q[j].clientWidth-8)/Math.max(1,q[j].scrollWidth)));
    var finalSize=Math.max(14,base*Math.min(1,scale)*.985);
    for(var z=0;z<q.length;z++)q[z].style.fontSize=finalSize+'px';
    var titles=box.querySelectorAll('.surah-title-line');for(var a=0;a<titles.length;a++)titles[a].style.fontSize=Math.max(16,finalSize*.72)+'px';
    var basmala=box.querySelectorAll('.basmala-line');for(var b=0;b<basmala.length;b++)basmala[b].style.fontSize=Math.max(18,finalSize*.92)+'px';
  }
  function renderCurrent(){
    var record=rec(state.currentPage);if(!record)return;
    var page=document.getElementById('mushafPage');if(!page)return;
    page.className=classes(state.currentPage,'');page.dataset.page=state.currentPage;
    document.getElementById('pageText').innerHTML=(record.lines||record.l||[]).map(lineHtml).join('');
    var pageNames=names(record);
    document.getElementById('pageSurah').textContent=pageNames.length?pageNames.join(' • '):'المصحف الشريف';
    document.getElementById('pageJuz').textContent='الجزء '+arabicNumber(record.juz||record.j||1);
    document.getElementById('readerTitle').textContent=pageNames.length?pageNames.join(' • '):'المصحف الشريف';
    document.getElementById('readerSubtitle').textContent='الصفحة '+arabicNumber(state.currentPage)+' من ٦٠٤';
    document.getElementById('pageNumber').textContent=arabicNumber(state.currentPage);
    document.getElementById('pageBookmark').textContent=isBookmarked('page',state.currentPage)?'★':'☆';
    var chip=document.getElementById('readerPageChip');if(chip)chip.textContent='الصفحة '+arabicNumber(state.currentPage)+' من ٦٠٤';
    page.style.transition='none';page.style.transform='translate3d(0,0,0)';
    requestAnimationFrame(function(){fitPage(page);setTimeout(function(){fitPage(page)},80)});
  }
  renderMushafPage=renderCurrent;

  function clearSides(){var stage=document.getElementById('mushafStage');if(!stage)return;stage.querySelectorAll('.mushaf-side-page').forEach(function(x){x.remove()})}
  function sidePages(){
    var stage=document.getElementById('mushafStage'),current=document.getElementById('mushafPage');if(!stage||!current)return null;
    clearSides();var prev=null,next=null;
    if(state.currentPage>1){var w=document.createElement('div');w.innerHTML=staticPage(state.currentPage-1,'mushaf-side-page mushaf-prev-page');prev=w.firstChild;stage.appendChild(prev);fitPage(prev)}
    if(state.currentPage<604){var w2=document.createElement('div');w2.innerHTML=staticPage(state.currentPage+1,'mushaf-side-page mushaf-next-page');next=w2.firstChild;stage.appendChild(next);fitPage(next)}
    place(0,current,prev,next,false);return {current:current,prev:prev,next:next};
  }
  function place(delta,current,prev,next,animate){
    var stage=document.getElementById('mushafStage'),width=Math.max(1,stage.clientWidth),tr=animate?'transform .22s cubic-bezier(.22,.72,.24,1)':'none';
    [current,prev,next].forEach(function(x){if(x)x.style.transition=tr});
    current.style.transform='translate3d('+delta+'px,0,0)';
    if(prev)prev.style.transform='translate3d('+(width+delta)+'px,0,0)';
    if(next)next.style.transform='translate3d('+(-width+delta)+'px,0,0)';
  }
  function save(page){
    state.currentPage=page;localStorage.setItem('lastPage',page);localStorage.setItem('lastRead',JSON.stringify({page:page}));
    renderCurrent();renderLastRead();clearSides();reader.animating=false;reader.drag=null;
  }
  function animateTo(page,direction,nodes){
    if(reader.animating)return;reader.animating=true;
    var width=Math.max(1,document.getElementById('mushafStage').clientWidth);
    requestAnimationFrame(function(){place(direction>0?width:-width,nodes.current,nodes.prev,nodes.next,true)});
    setTimeout(function(){save(page)},235);
  }
  turnTo=function(page,direction){
    if(page<1||page>604)return toast('هذه نهاية المصحف');if(reader.animating)return;
    var nodes=sidePages();if(!nodes){save(page);return}animateTo(page,direction>0?1:-1,nodes);
  };
  readerNext=function(){turnTo(state.currentPage+1,1)};
  readerPrev=function(){turnTo(state.currentPage-1,-1)};

  function bindStableReader(){
    var stage=document.getElementById('mushafStage');if(!stage||stage.dataset.stable2d)return;stage.dataset.stable2d='1';
    stage.addEventListener('pointerdown',function(e){
      if(reader.animating||e.target.closest('button'))return;
      var nodes=sidePages();if(!nodes)return;
      reader.drag={start:e.clientX,last:e.clientX,pointer:e.pointerId,width:Math.max(1,stage.clientWidth),nodes:nodes};
      try{stage.setPointerCapture(e.pointerId)}catch(ignore){}
    });
    stage.addEventListener('pointermove',function(e){
      var d=reader.drag;if(!d||d.pointer!==e.pointerId)return;d.last=e.clientX;
      var delta=e.clientX-d.start;if((delta>0&&state.currentPage>=604)||(delta<0&&state.currentPage<=1))delta*=.18;
      delta=Math.max(-d.width,Math.min(d.width,delta));place(delta,d.nodes.current,d.nodes.prev,d.nodes.next,false);e.preventDefault();
    },{passive:false});
    function end(){
      var d=reader.drag;if(!d)return;reader.drag=null;var delta=d.last-d.start,threshold=Math.min(92,d.width*.16);
      if(delta>threshold&&state.currentPage<604)return animateTo(state.currentPage+1,1,d.nodes);
      if(delta<-threshold&&state.currentPage>1)return animateTo(state.currentPage-1,-1,d.nodes);
      place(0,d.nodes.current,d.nodes.prev,d.nodes.next,true);setTimeout(function(){clearSides();reader.animating=false},235);
    }
    stage.addEventListener('pointerup',end);stage.addEventListener('pointercancel',end);stage.addEventListener('lostpointercapture',end);
  }
  function replaceReaderNode(){
    var old=document.getElementById('mushafPage');if(!old||old.dataset.cleanNode)return;
    var fresh=old.cloneNode(true);fresh.dataset.cleanNode='1';old.parentNode.replaceChild(fresh,old);
  }

  renderQuranSearch=function(query){
    if(!state.quran.length||state.currentQuranTab!=='surahs')return;
    state.quranSearchQuery=query||'';var box=document.getElementById('surahList'),q=String(query||'').trim(),rows=[];
    if(!q){for(var i=0;i<state.quran.length;i++)rows.push({type:'surah',score:0,s:state.quran[i]})}
    else{
      for(var s=0;s<state.quran.length;s++){
        var su=state.quran[s],nameHit=prefixMatch(su.name+' '+(su.transliteration||'')+' '+su.id,q);
        if(nameHit.score)rows.push({type:'surah',score:nameHit.score+3000,s:su});
        for(var v=0;v<su.verses.length;v++){var ay=su.verses[v],hit=prefixMatch(ay.text,q);if(hit.score)rows.push({type:'ayah',score:hit.score,s:su,a:ay})}
      }
      rows.sort(function(a,b){return b.score-a.score});rows=rows.slice(0,120);
    }
    box.innerHTML=rows.map(function(x){return x.type==='surah'?surahRow(x.s):ayahRow(x.s,x.a)}).join('')||'<div class="empty">لا توجد نتيجة تحتوي الكلمة أو كلمة تبدأ بها.</div>';
  };
  ayahRow=function(s,a){return '<button class="surah-row" onclick="openSurah('+s.id+','+a.id+')"><span class="number-badge">'+arabicNumber(a.id)+'</span><span class="surah-info"><strong>'+highlightPrefix(s.name,state.quranSearchQuery)+' — آية '+arabicNumber(a.id)+'</strong><small>'+highlightPrefix(a.text.substring(0,190),state.quranSearchQuery)+'</small></span></button>'};

  runHadithSearch=function(query){
    if(!state.hadith.length)return;state.hadithSearchQuery=query||'';
    var q=String(query||'').trim(),book=state.hadithBook,out=[];
    for(var i=0;i<state.hadith.length;i++){
      var h=state.hadith[i];if(book!=='all'&&h.book!==book)continue;
      var searchable=(h.display||'')+' '+(h.text||'')+' '+(h.narrator||'')+' '+(h.book||'');
      var hit=q?prefixMatch(searchable,q):{score:1};if(!q||hit.score)out.push({h:h,score:hit.score});
    }
    out.sort(function(a,b){return b.score-a.score});state.hadithMatches=out;state.hadithVisible=25;renderHadithResults(q);
  };
  function mainHadith(h){var x=h.display||'';return x.length>=45?x:(h.text||x)}
  renderHadithResults=function(query){
    var box=document.getElementById('hadithResults'),arr=state.hadithMatches.slice(0,state.hadithVisible),html='';
    html+='<div class="hadith-library-head"><strong>مكتبة الأحاديث</strong><span>'+arabicNumber(state.hadithMatches.length)+' نتيجة</span></div>';
    if(query)html+='<div class="smart-note">النتائج تحتوي الكلمة كاملة أو كلمة تبدأ بها، والتحديد لا يجزّئ الكلمة إلى حروف.</div>';
    for(var i=0;i<arr.length;i++){
      var h=arr[i].h,body=mainHadith(h),marked=isBookmarked('hadith',h.id);
      html+='<article class="hadith-card v5-hadith-card"><div class="hadith-book-chip">'+escapeHtml(h.book)+'</div><p class="hadith-text">'+highlightPrefix(body,state.hadithSearchQuery)+'</p><div class="hadith-meta"><span><b>الراوي:</b> '+escapeHtml(h.narrator||'الراوي مذكور في المصدر')+'</span><span><b>المصدر:</b> '+escapeHtml(h.book)+' — رقم '+arabicNumber(h.number||h.id)+'</span><span><b>حكم الحديث:</b> '+escapeHtml(h.grade||'راجع تخريج المصدر')+'</span></div><div class="hadith-actions"><button class="details-btn" onclick="toggleHadithFull(this)">عرض النص الكامل</button><button class="star-btn" onclick="toggleHadithBookmark('+h.id+',this)">'+(marked?'★':'☆')+'</button></div><div class="hadith-full hidden">'+escapeHtml(h.text||body)+'</div></article>';
    }
    box.innerHTML=html||'<div class="empty card">لا توجد نتائج مطابقة.</div>';
    var more=document.getElementById('loadMoreHadith');if(more)more.classList.toggle('hidden',state.hadithVisible>=state.hadithMatches.length);
  };
  window.toggleHadithFull=function(button){var full=button.closest('.hadith-card').querySelector('.hadith-full');full.classList.toggle('hidden');button.textContent=full.classList.contains('hidden')?'عرض النص الكامل':'إخفاء النص الكامل'};

  function angleDelta(from,to){return ((to-from+540)%360)-180}
  function compassUpdate(heading){
    var arrow=document.getElementById('qiblaArrow');if(!arrow)return;
    var target=(Number(state.qibla||0)-Number(heading||0)+360)%360;
    if(compass.continuous==null){compass.continuous=target;compass.lastTarget=target}
    else{
      var delta=angleDelta(compass.lastTarget,target);if(Math.abs(delta)>40)delta=Math.sign(delta)*40;
      compass.continuous+=delta*.30;compass.lastTarget=(compass.lastTarget+delta+360)%360;
    }
    arrow.style.transform='translate(-50%,-100%) rotate('+compass.continuous+'deg)';
    var status=document.getElementById('compassStatus');if(status)status.textContent='اتجاه الهاتف: '+arabicNumber(Math.round(heading))+'° • حرّك الهاتف بهدوء حتى يثبت السهم نحو الكعبة';
  }
  window.onNativeHeading=function(heading,accuracy){state.nativeHeading=Number(heading);state.compassAccuracy=Number(accuracy||0);compassUpdate(state.nativeHeading)};
  orientationHandler=function(e){
    if(state.nativeHeading!=null)return;var heading=null;
    if(typeof e.webkitCompassHeading==='number')heading=e.webkitCompassHeading;
    else if(e.alpha!=null){heading=360-e.alpha;var a=(screen.orientation&&screen.orientation.angle)||window.orientation||0;heading=(heading+Number(a)+360)%360}
    if(heading!=null)compassUpdate(heading);
  };
  renderQibla=function(){oldRenderQibla();compass.continuous=null;compass.lastTarget=null;if(state.nativeHeading!=null)compassUpdate(state.nativeHeading)};

  function redesignHome(){
    var page=document.getElementById('page-home');if(!page||page.dataset.redesigned)return;page.dataset.redesigned='1';
    var hero=page.querySelector('.hero');if(hero)hero.classList.add('v5-hero');
    var quick=page.querySelector('.quick-grid');if(quick)quick.classList.add('v5-dashboard');
    var next=page.querySelector('.hero-next');if(next)next.classList.add('v5-next-prayer');
    if(quick){
      quick.insertAdjacentHTML('beforeend','<button class="quick" onclick="showPage(\'qibla\',true)"><span>🧭</span><b>القبلة</b><small>اتجاه ثابت ودقيق</small></button><button class="quick" onclick="showPage(\'bookmarks\',true)"><span>♡</span><b>المفضلة</b><small>علاماتك المحفوظة</small></button><button class="quick" onclick="showPage(\'settings\',true)"><span>⚙</span><b>الإعدادات</b><small>تخصيص المصحف</small></button><button class="quick" onclick="showPage(\'quran\',true);setTimeout(function(){document.getElementById(\'quranSearch\').focus()},120)"><span>⌕</span><b>البحث</b><small>في القرآن والآيات</small></button><button class="quick" onclick="openMushafPage(Number(localStorage.getItem(\'lastPage\')||1))"><span>🔖</span><b>آخر قراءة</b><small>متابعة الصفحة</small></button>');
    }
  }

  showPage=function(name,push){
    oldShowPage(name,push);
    if(name==='reader')requestAnimationFrame(function(){renderCurrent();bindStableReader()});
    if(name==='qibla'){compass.continuous=null;compass.lastTarget=null;setTimeout(function(){if(state.nativeHeading!=null)compassUpdate(state.nativeHeading)},50)}
  };
  setFontSize=function(value){oldSetFontSize(value);if(state.page==='reader')requestAnimationFrame(function(){fitPage(document.getElementById('mushafPage'))})};

  window.addEventListener('resize',function(){if(state.page==='reader')fitPage(document.getElementById('mushafPage'))});
  document.addEventListener('DOMContentLoaded',function(){
    replaceReaderNode();bindStableReader();redesignHome();
    if(!localStorage.getItem('theme')){localStorage.setItem('theme','dark');document.documentElement.dataset.theme='dark'}
    var hint=document.querySelector('.gesture-hint');if(hint)hint.textContent='اسحب أفقيًا مثل معرض الصور؛ الصفحة المجاورة تبقى ظاهرة أثناء السحب.';
    var about=document.querySelector('#page-settings .setting:last-child .muted');if(about)about.textContent='الإصدار 4.1 — تصميم زمردي ذهبي، صفحات 2D سلسة، بحث دقيق، أحاديث كاملة، وقبلة مستقرة. يعمل دون إنترنت.';
  });
})();
