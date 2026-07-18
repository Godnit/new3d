(function(){
  state.galleryBusy=false;
  state.adhkarIndex=0;
  state.quranSearchQuery='';
  state.hadithSearchQuery='';
  state.nativeHeading=null;
  state.compassAccuracy=0;

  var showPagePrevious=showPage;
  var setFontSizePrevious=setFontSize;

  function splitAdhkar(){
    var output=[];
    for(var i=0;i<adhkarData.length;i++){
      var d=adhkarData[i];
      if(d.id==='m2'){
        output.push(
          {id:'m2a',cat:'الصباح',title:'سورة الإخلاص',text:'قُلْ هُوَ اللَّهُ أَحَدٌ، اللَّهُ الصَّمَدُ، لَمْ يَلِدْ وَلَمْ يُولَدْ، وَلَمْ يَكُنْ لَهُ كُفُوًا أَحَدٌ',target:3,source:'تقال ثلاث مرات صباحًا ومساءً'},
          {id:'m2b',cat:'الصباح',title:'سورة الفلق',text:'قُلْ أَعُوذُ بِرَبِّ الْفَلَقِ، مِنْ شَرِّ مَا خَلَقَ، وَمِنْ شَرِّ غَاسِقٍ إِذَا وَقَبَ، وَمِنْ شَرِّ النَّفَّاثَاتِ فِي الْعُقَدِ، وَمِنْ شَرِّ حَاسِدٍ إِذَا حَسَدَ',target:3,source:'تقال ثلاث مرات صباحًا ومساءً'},
          {id:'m2c',cat:'الصباح',title:'سورة الناس',text:'قُلْ أَعُوذُ بِرَبِّ النَّاسِ، مَلِكِ النَّاسِ، إِلَهِ النَّاسِ، مِنْ شَرِّ الْوَسْوَاسِ الْخَنَّاسِ، الَّذِي يُوَسْوِسُ فِي صُدُورِ النَّاسِ، مِنَ الْجِنَّةِ وَالنَّاسِ',target:3,source:'تقال ثلاث مرات صباحًا ومساءً'}
        );
      }else if(d.id==='p3'){
        output.push(
          {id:'p3a',cat:'بعد الصلاة',title:'التسبيح',text:'سُبْحَانَ اللَّهِ',target:33,source:'صحيح مسلم'},
          {id:'p3b',cat:'بعد الصلاة',title:'التحميد',text:'الْحَمْدُ لِلَّهِ',target:33,source:'صحيح مسلم'},
          {id:'p3c',cat:'بعد الصلاة',title:'التكبير',text:'اللَّهُ أَكْبَرُ',target:33,source:'صحيح مسلم'}
        );
      }else if(d.id==='s3'){
        output.push(
          {id:'s3a',cat:'النوم',title:'تسبيح فاطمة',text:'سُبْحَانَ اللَّهِ',target:33,source:'صحيح البخاري ومسلم'},
          {id:'s3b',cat:'النوم',title:'تحميد فاطمة',text:'الْحَمْدُ لِلَّهِ',target:33,source:'صحيح البخاري ومسلم'},
          {id:'s3c',cat:'النوم',title:'تكبير فاطمة',text:'اللَّهُ أَكْبَرُ',target:34,source:'صحيح البخاري ومسلم'}
        );
      }else output.push(d);
    }
    adhkarData=output;
  }
  splitAdhkar();

  function lineKind(line){return line.kind||line.k||'blank'}
  function lineNumber(line){return line.line||line.n||0}
  function lineChapter(line){return line.chapter||line.c||1}
  function lineMarkup(line){
    var kind=lineKind(line),number=lineNumber(line);
    if(kind==='surah'||kind==='s'){
      var surah=state.quran[lineChapter(line)-1];
      return '<div class="mushaf-line surah-title-line" data-line="'+number+'"><span>سُورَةُ '+escapeHtml(surah?surah.name:'')+'</span></div>';
    }
    if(kind==='basmala'||kind==='b')return '<div class="mushaf-line basmala-line" data-line="'+number+'">بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ</div>';
    if(kind==='quran'||kind==='q'){
      var text=line.text||line.t||'';
      if(!text&&line.words)text=line.words.map(function(word){return word.t||word.c||''}).join(' ');
      return '<div class="mushaf-line quran-line" data-line="'+number+'">'+escapeHtml(text)+'</div>';
    }
    return '<div class="mushaf-line blank-line" data-line="'+number+'"></div>';
  }

  function fitUniformMushaf(){
    var box=document.getElementById('pageText');
    if(!box||!box.clientWidth||!box.clientHeight)return;
    var requested=Math.max(18,Math.min(38,Number(localStorage.getItem('fontSize')||29)));
    var rowHeight=box.clientHeight/15;
    var target=Math.min(requested,rowHeight*.72);
    if(state.currentPage<=2)target=Math.min(requested+1,rowHeight*.68);
    target=Math.max(15,target);
    var lines=box.querySelectorAll('.quran-line');
    for(var i=0;i<lines.length;i++){lines[i].style.fontSize=target+'px';lines[i].style.transform='none'}
    var scale=1;
    for(var j=0;j<lines.length;j++){
      var available=Math.max(1,lines[j].clientWidth-4),needed=Math.max(1,lines[j].scrollWidth);
      scale=Math.min(scale,available/needed);
    }
    var finalSize=Math.max(13,target*Math.min(1,scale)*.975);
    for(var k=0;k<lines.length;k++)lines[k].style.fontSize=finalSize+'px';
    var basmala=box.querySelectorAll('.basmala-line');
    for(var b=0;b<basmala.length;b++)basmala[b].style.fontSize=Math.max(18,finalSize*.92)+'px';
    var titles=box.querySelectorAll('.surah-title-line');
    for(var t=0;t<titles.length;t++)titles[t].style.fontSize=Math.max(16,finalSize*.70)+'px';
  }

  renderMushafPage=function(){
    var rec=state.mushafLayout[state.currentPage-1],lines=rec&&(rec.lines||rec.l);
    if(!rec||!lines)return;
    var pageText=document.getElementById('pageText');
    pageText.className='page-text mushaf-lines lite-mushaf';
    pageText.innerHTML=lines.map(lineMarkup).join('');
    var ids=rec.surahs||rec.s||[];
    var names=ids.map(function(id){return state.quran[id-1]?state.quran[id-1].name:''}).filter(Boolean);
    document.getElementById('pageSurah').textContent=names.length?names.join(' • '):'المصحف الشريف';
    document.getElementById('pageJuz').textContent='الجزء '+arabicNumber(rec.juz||rec.j||1);
    document.getElementById('readerTitle').textContent='مصحف المدينة';
    document.getElementById('readerSubtitle').textContent='الصفحة '+arabicNumber(state.currentPage)+' من ٦٠٤';
    document.getElementById('pageNumber').textContent=arabicNumber(state.currentPage);
    document.getElementById('pageBookmark').textContent=isBookmarked('page',state.currentPage)?'★':'☆';
    var page=document.getElementById('mushafPage');
    page.classList.toggle('opening-mushaf-page',state.currentPage<=2);
    page.classList.toggle('page-on-right',state.currentPage%2===1);
    page.classList.toggle('page-on-left',state.currentPage%2===0);
    page.style.transition='none';page.style.transform='translate3d(0,0,0)';
    var chip=document.getElementById('readerPageChip');if(chip)chip.textContent='الصفحة '+arabicNumber(state.currentPage)+' من ٦٠٤';
    requestAnimationFrame(function(){fitUniformMushaf();setTimeout(fitUniformMushaf,80);setTimeout(fitUniformMushaf,180)});
  };

  function savePage(page){
    state.currentPage=page;
    localStorage.setItem('lastPage',page);
    localStorage.setItem('lastRead',JSON.stringify({page:page}));
    renderMushafPage();renderLastRead();
  }

  function removeIds(root){var nodes=root.querySelectorAll('[id]');for(var i=0;i<nodes.length;i++)nodes[i].removeAttribute('id')}

  turnTo=function(page,direction){
    if(page<1||page>604)return toast('هذه نهاية المصحف');
    if(state.galleryBusy)return;
    var stage=document.getElementById('mushafStage'),el=document.getElementById('mushafPage');
    if(!stage||!el){savePage(page);return}
    state.galleryBusy=true;
    var startTransform=el.style.transform||'translate3d(0,0,0)';
    var ghost=el.cloneNode(true);removeIds(ghost);ghost.classList.add('gallery-page-copy');ghost.style.transform=startTransform;ghost.style.transition='none';stage.appendChild(ghost);
    var incomingStart=direction>0?'-104%':'104%';
    savePage(page);
    el.style.transition='none';el.style.transform='translate3d('+incomingStart+',0,0)';
    el.getBoundingClientRect();ghost.getBoundingClientRect();
    requestAnimationFrame(function(){
      var easing='transform .26s cubic-bezier(.22,.72,.24,1),opacity .24s ease';
      ghost.style.transition=easing;el.style.transition=easing;
      ghost.style.transform='translate3d('+(direction>0?'104%':'-104%')+',0,0)';ghost.style.opacity='.30';
      el.style.transform='translate3d(0,0,0)';
    });
    setTimeout(function(){if(ghost.parentNode)ghost.parentNode.removeChild(ghost);el.style.transition='none';el.style.transform='translate3d(0,0,0)';state.galleryBusy=false;fitUniformMushaf()},300);
  };
  readerNext=function(){turnTo(state.currentPage+1,1)};
  readerPrev=function(){turnTo(state.currentPage-1,-1)};

  bindPageGesture=function(){
    var el=document.getElementById('mushafPage');if(!el)return;
    var drag=null;
    el.addEventListener('pointerdown',function(e){
      if(state.galleryBusy||e.target.closest('button'))return;
      drag={x:e.clientX,last:e.clientX,width:Math.max(1,el.getBoundingClientRect().width),pointer:e.pointerId};
      try{el.setPointerCapture(e.pointerId)}catch(ignore){}
      el.style.transition='none';
    });
    el.addEventListener('pointermove',function(e){
      if(!drag||drag.pointer!==e.pointerId)return;
      drag.last=e.clientX;var d=e.clientX-drag.x;
      if((d>0&&state.currentPage>=604)||(d<0&&state.currentPage<=1))d*=.18;
      d=Math.max(-drag.width*.72,Math.min(drag.width*.72,d));
      el.style.transform='translate3d('+d+'px,0,0)';e.preventDefault();
    },{passive:false});
    function finish(){
      if(!drag)return;var d=drag.last-drag.x,threshold=drag.width*.12;drag=null;
      if(Math.abs(d)>threshold){var page=state.currentPage+(d>0?1:-1);if(page>=1&&page<=604){turnTo(page,d>0?1:-1);return}}
      el.style.transition='transform .22s cubic-bezier(.22,.72,.24,1)';el.style.transform='translate3d(0,0,0)';setTimeout(function(){el.style.transition='none'},230);
    }
    el.addEventListener('pointerup',finish);el.addEventListener('pointercancel',finish);el.addEventListener('lostpointercapture',finish);
  };

  showPage=function(name,push){
    showPagePrevious(name,push);
    if(name==='reader')requestAnimationFrame(function(){fitUniformMushaf();setTimeout(fitUniformMushaf,130)});
    if(name==='qibla'){renderQibla();ensureCompassStatus()}
  };
  setFontSize=function(value){setFontSizePrevious(value);if(state.page==='reader')requestAnimationFrame(function(){fitUniformMushaf();setTimeout(fitUniformMushaf,100)})};

  function normalizeWithMap(text){
    var out='',map=[],lastSpace=false,table={'أ':'ا','إ':'ا','آ':'ا','ٱ':'ا','ى':'ي','ة':'ه','ؤ':'و','ئ':'ي','ـ':' '};
    text=String(text||'');
    for(var i=0;i<text.length;i++){
      var c=text[i];if(/[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]/.test(c))continue;
      c=table[c]||c;if(!/[\u0621-\u064A0-9 ]/.test(c))c=' ';
      if(c===' '){if(lastSpace)continue;lastSpace=true}else lastSpace=false;
      out+=c.toLowerCase();map.push(i);
    }
    return {text:out.trim(),map:map};
  }
  function highlightText(text,query){
    var q=normalizeArabic(query||''),tokens=q.split(' ').filter(function(x){return x.length>1});
    if(!tokens.length)return escapeHtml(text);
    var mapped=normalizeWithMap(text),ranges=[];
    for(var i=0;i<tokens.length;i++){
      var from=0,idx;
      while((idx=mapped.text.indexOf(tokens[i],from))>=0){
        var start=mapped.map[idx],end=mapped.map[Math.min(mapped.map.length-1,idx+tokens[i].length-1)]+1;
        if(start!=null&&end!=null)ranges.push([start,end]);from=idx+tokens[i].length;
      }
    }
    if(!ranges.length)return escapeHtml(text);
    ranges.sort(function(a,b){return a[0]-b[0]});var merged=[];
    for(var r=0;r<ranges.length;r++){var last=merged[merged.length-1];if(last&&ranges[r][0]<=last[1])last[1]=Math.max(last[1],ranges[r][1]);else merged.push(ranges[r])}
    var html='',pos=0;for(var m=0;m<merged.length;m++){html+=escapeHtml(text.slice(pos,merged[m][0]));html+='<mark>'+escapeHtml(text.slice(merged[m][0],merged[m][1]))+'</mark>';pos=merged[m][1]}return html+escapeHtml(text.slice(pos));
  }
  function exactScore(query,text){
    if(!query)return 1;var pos=text.indexOf(query);if(pos>=0)return 3000-Math.min(500,pos);
    var tokens=query.split(' ').filter(function(x){return x.length>1}),found=0;
    for(var i=0;i<tokens.length;i++)if(text.indexOf(tokens[i])>=0)found++;
    if(found===tokens.length&&found)return 1800+found*20;
    if(found)return 700+found*80;
    return fuzzyScore(query,text);
  }

  renderQuranSearch=function(query){
    if(!state.quran.length||state.currentQuranTab!=='surahs')return;
    state.quranSearchQuery=query||'';var box=document.getElementById('surahList'),q=normalizeArabic(String(query||'').trim()),rows=[];
    if(!q){for(var i=0;i<state.quran.length;i++)rows.push({type:'surah',score:0,s:state.quran[i]})}
    else{
      for(var s=0;s<state.quran.length;s++){
        var su=state.quran[s],name=normalizeArabic(su.name+' '+(su.transliteration||'')+' '+su.id),ns=exactScore(q,name);
        if(ns>0)rows.push({type:'surah',score:ns+1000,s:su});
        for(var v=0;v<su.verses.length;v++){
          var ay=su.verses[v],score=exactScore(q,normalizeArabic(ay.text));if(score>=700)rows.push({type:'ayah',score:score,s:su,a:ay});
        }
      }
      rows.sort(function(a,b){return b.score-a.score});rows=rows.slice(0,100);
    }
    var html='';for(var r=0;r<rows.length;r++){var item=rows[r];html+=item.type==='surah'?surahRow(item.s):ayahRow(item.s,item.a)}
    box.innerHTML=html||'<div class="empty">لا توجد نتيجة مطابقة. جرّب كلمة أقصر أو صيغة قريبة.</div>';
  };
  ayahRow=function(s,a){return '<button class="surah-row" onclick="openSurah('+s.id+','+a.id+')"><span class="number-badge">'+arabicNumber(a.id)+'</span><span class="surah-info"><strong>'+highlightText(s.name,state.quranSearchQuery)+' — آية '+arabicNumber(a.id)+'</strong><small>'+highlightText(a.text.substring(0,150),state.quranSearchQuery)+'</small></span></button>'};

  runHadithSearch=function(query){
    if(!state.hadith.length)return;state.hadithSearchQuery=query||'';
    var q=normalizeArabic(String(query||'').trim()),book=state.hadithBook,m=[];
    for(var i=0;i<state.hadith.length;i++){
      var h=state.hadith[i];if(book!=='all'&&h.book!==book)continue;
      var searchable=normalizeArabic((h.display||'')+' '+h.text+' '+h.narrator+' '+h.book),score=exactScore(q,searchable);
      if(!q||score>0)m.push({h:h,score:score});
    }
    m.sort(function(a,b){return b.score-a.score});state.hadithMatches=m;state.hadithVisible=20;renderHadithResults(q);
  };
  function conciseNarrator(x){return x.narrator||'لم يُفصل اسم الراوي في المصدر'}
  function featuredHadithV4(){var src=state.hadithMatches.length?state.hadithMatches.map(function(x){return x.h}):state.hadith;if(!src.length)return null;return src[Math.floor(Date.now()/86400000)%src.length]}
  renderHadithResults=function(q){
    var box=document.getElementById('hadithResults'),arr=state.hadithMatches.slice(0,state.hadithVisible),feature=featuredHadithV4(),html='';
    if(feature)html+='<section class="hadith-featured"><div class="hadith-featured-head"><span>حديث اليوم</span><small>'+escapeHtml(feature.book)+'</small></div><p>'+highlightText(feature.display||feature.text,state.hadithSearchQuery)+'</p><div class="hadith-featured-meta"><b>الراوي:</b> '+escapeHtml(conciseNarrator(feature))+'<br><b>الحكم:</b> '+escapeHtml(feature.grade||'راجع تخريج المصدر')+'</div></section>';
    html+='<div class="hadith-library-head"><strong>مكتبة الأحاديث</strong><span>'+arabicNumber(state.hadithMatches.length)+' نتيجة</span></div>';
    if(q&&arr.length)html+='<div class="smart-note">أظهرت النتائج المطابقة للكلمة أولًا، ثم النتائج القريبة في المعنى والكتابة.</div>';
    for(var i=0;i<arr.length;i++){
      var x=arr[i].h,marked=isBookmarked('hadith',x.id);
      html+='<article class="hadith-card"><p class="hadith-text">'+highlightText(x.display||x.text,state.hadithSearchQuery)+'</p><div class="hadith-meta"><span><b>الراوي:</b> '+escapeHtml(conciseNarrator(x))+'</span><span><b>المصدر:</b> '+escapeHtml(x.book)+' — رقم '+arabicNumber(x.number||x.id)+'</span><span><b>حكم الحديث:</b> '+escapeHtml(x.grade||'راجع تخريج المصدر')+'</span></div><div class="hadith-actions"><span class="pill">'+escapeHtml(x.book)+'</span><button class="star-btn" onclick="toggleHadithBookmark('+x.id+',this)">'+(marked?'★':'☆')+'</button></div></article>';
    }
    box.innerHTML=html||'<div class="empty card">لا توجد نتائج. جرّب كلمة أقصر أو معنى قريبًا.</div>';
    document.getElementById('loadMoreHadith').classList.toggle('hidden',state.hadithVisible>=state.hadithMatches.length);
  };

  function categoryItems(){return adhkarData.filter(function(d){return d.cat===adhkarCategory})}
  setAdhkarCategory=function(c){adhkarCategory=c;state.adhkarIndex=0;renderAdhkarCategories();renderAdhkar()};
  renderAdhkar=function(){
    var items=categoryItems(),box=document.getElementById('adhkarList');if(!items.length){box.innerHTML='<div class="empty card">لا توجد أذكار في هذا القسم.</div>';return}
    state.adhkarIndex=Math.max(0,Math.min(state.adhkarIndex,items.length-1));
    var d=items[state.adhkarIndex],n=Math.min(d.target,dhikrCounters[d.id]||0),done=n>=d.target,percent=Math.round(n/d.target*100);
    var dots='';for(var i=0;i<items.length;i++)dots+='<span class="'+(i===state.adhkarIndex?'active ':'')+((dhikrCounters[items[i].id]||0)>=items[i].target?'done':'')+'"></span>';
    box.innerHTML='<div class="adhkar-page-shell"><div class="adhkar-page-progress"><b>'+escapeHtml(adhkarCategory)+'</b><small>'+arabicNumber(state.adhkarIndex+1)+' من '+arabicNumber(items.length)+'</small></div><article class="adhkar-page-card"><span class="pill">'+escapeHtml(d.title)+'</span><p>'+escapeHtml(d.text)+'</p><div class="dhikr-source">'+escapeHtml(d.source)+'</div><div class="adhkar-count-status"><strong>'+arabicNumber(n)+'</strong><span>من '+arabicNumber(d.target)+'</span></div><div class="progress"><span style="width:'+percent+'%"></span></div><button class="adhkar-read-btn '+(done?'complete':'')+'" onclick="incrementDhikr(\''+d.id+'\')">'+(done?'تمت القراءة ✓':(d.target===1?'قرأت':'اضغط للعد'))+'</button></article><div class="adhkar-dots">'+dots+'</div><div class="adhkar-nav"><button onclick="prevDhikr()" '+(state.adhkarIndex===0?'disabled':'')+'>السابق</button><button onclick="nextDhikr()" '+(!done||state.adhkarIndex===items.length-1?'disabled':'')+'>'+(state.adhkarIndex===items.length-1?'اكتمل القسم':'التالي')+'</button></div></div>';
  };
  incrementDhikr=function(id){var d=getDhikr(id);if((dhikrCounters[id]||0)<d.target)dhikrCounters[id]=(dhikrCounters[id]||0)+1;localStorage.setItem('dhikrCounters',JSON.stringify(dhikrCounters));renderAdhkar();if(dhikrCounters[id]===d.target)toast('أحسنت، اكتمل هذا الذكر ويمكنك الانتقال للتالي')};
  nextDhikr=function(){var items=categoryItems(),d=items[state.adhkarIndex];if(!d)return;if((dhikrCounters[d.id]||0)<d.target)return toast('أكمل قراءة الذكر أولًا');if(state.adhkarIndex<items.length-1){state.adhkarIndex++;animateDhikr(1)}};
  prevDhikr=function(){if(state.adhkarIndex>0){state.adhkarIndex--;animateDhikr(-1)}};
  function animateDhikr(direction){var box=document.getElementById('adhkarList');box.classList.add(direction>0?'adhkar-slide-next':'adhkar-slide-prev');setTimeout(function(){renderAdhkar();box.classList.remove('adhkar-slide-next','adhkar-slide-prev')},130)}
  function bindAdhkarSwipe(){
    var box=document.getElementById('adhkarList');if(!box||box.dataset.swipeBound)return;box.dataset.swipeBound='1';var drag=null;
    box.addEventListener('pointerdown',function(e){if(e.target.closest('button'))return;drag={x:e.clientX,last:e.clientX,pointer:e.pointerId};try{box.setPointerCapture(e.pointerId)}catch(ignore){}});
    box.addEventListener('pointermove',function(e){if(drag&&drag.pointer===e.pointerId)drag.last=e.clientX});
    function end(){if(!drag)return;var d=drag.last-drag.x;drag=null;if(Math.abs(d)>55){if(d>0)nextDhikr();else prevDhikr()}}
    box.addEventListener('pointerup',end);box.addEventListener('pointercancel',end);
  }

  var framePresets=[['classic','كلاسيكي'],['geometric','هندسي'],['floral','زخرفة نباتية'],['simple','إطار بسيط'],['none','بدون إطار']];
  setMushafFrame=function(id){localStorage.setItem('mushafFrame',id);document.documentElement.dataset.frame=id;renderFrameOptions();toast('تم تغيير إطار المصحف')};
  function renderFrameOptions(){var box=document.getElementById('mushafFrameOptions');if(!box)return;var active=localStorage.getItem('mushafFrame')||'classic';box.innerHTML=framePresets.map(function(x){return '<button class="frame-choice '+(x[0]===active?'active':'')+'" onclick="setMushafFrame(\''+x[0]+'\')"><span class="frame-preview frame-'+x[0]+'"></span><b>'+x[1]+'</b></button>'}).join('')}
  function setupSettings(){
    document.documentElement.dataset.frame=localStorage.getItem('mushafFrame')||'classic';
    var settings=document.querySelector('#page-settings .settings-card');
    if(settings&&!document.getElementById('mushafFrameOptions')){
      var node=document.createElement('div');node.className='setting';node.innerHTML='<label>نقشة وإطار صفحة المصحف</label><div id="mushafFrameOptions" class="frame-options"></div>';
      var fontSetting=document.getElementById('fontRange');fontSetting=fontSetting&&fontSetting.closest('.setting');settings.insertBefore(node,fontSetting||settings.firstChild);renderFrameOptions();
    }
    var turnLabels=document.querySelectorAll('#pageTurnToggle,#settingsTurnToggle');for(var i=0;i<turnLabels.length;i++){var row=turnLabels[i].closest('.switch-row');if(row&&row.querySelector('span'))row.querySelector('span').textContent='السحب السلس بين الصفحات'}
    var hint=document.querySelector('.gesture-hint');if(hint)hint.textContent='اسحب الصفحة يمينًا للصفحة التالية، ويسارًا للصفحة السابقة.';
    var edges=document.querySelectorAll('.reader-edge');for(var e=0;e<edges.length;e++)edges[e].remove();
  }

  function ensureCompassStatus(){
    var card=document.querySelector('.qibla-card');if(!card||document.getElementById('compassStatus'))return;
    var p=document.createElement('p');p.id='compassStatus';p.className='compass-status';p.textContent='حرّك الهاتف على شكل الرقم ٨ لمعايرة البوصلة.';card.insertBefore(p,card.querySelector('.primary-btn'));
  }
  function updateCompassArrow(heading){
    var arrow=document.getElementById('qiblaArrow');if(!arrow)return;var rot=(Number(state.qibla||0)-Number(heading||0)+360)%360;arrow.style.transform='translate(-50%,-100%) rotate('+rot+'deg)';
    var status=document.getElementById('compassStatus');if(status)status.textContent='اتجاه الهاتف: '+arabicNumber(Math.round(heading))+'° • اتبع السهم نحو القبلة';
  }
  window.onNativeHeading=function(heading,accuracy){state.nativeHeading=Number(heading);state.compassAccuracy=Number(accuracy||0);updateCompassArrow(state.nativeHeading)};
  renderQibla=function(){
    if(typeof adhan!=='undefined'){var c=new adhan.Coordinates(state.coords.lat,state.coords.lon);state.qibla=adhan.Qibla(c)}
    var degrees=document.getElementById('qiblaDegrees');if(degrees)degrees.textContent=Math.round(state.qibla||0);
    ensureCompassStatus();if(state.nativeHeading!=null)updateCompassArrow(state.nativeHeading);else updateCompassArrow(0);
  };
  orientationHandler=function(e){
    if(state.nativeHeading!=null)return;var heading=null;
    if(typeof e.webkitCompassHeading==='number')heading=e.webkitCompassHeading;
    else if(e.alpha!=null){heading=360-e.alpha;var angle=(screen.orientation&&screen.orientation.angle)||window.orientation||0;heading=(heading+Number(angle)+360)%360}
    if(heading!=null)updateCompassArrow(heading);
  };

  var clearDataPrevious=clearAppData;
  clearAppData=function(){localStorage.removeItem('mushafFrame');clearDataPrevious()};

  window.addEventListener('resize',function(){if(state.page==='reader')fitUniformMushaf()});
  document.addEventListener('DOMContentLoaded',function(){setupSettings();bindAdhkarSwipe();ensureCompassStatus();setTimeout(function(){var edges=document.querySelectorAll('.reader-edge');for(var i=0;i<edges.length;i++)edges[i].remove()},30)});
})();
