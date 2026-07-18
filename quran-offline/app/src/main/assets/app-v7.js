(function(){
  'use strict';

  function escapeRegex(value){return String(value).replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}
  function normalizedWithMap(value){
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
    var start=0,end=plain.length;
    while(start<end&&plain[start]===' ')start++;
    while(end>start&&plain[end-1]===' ')end--;
    return {text:plain.slice(start,end),map:map.slice(start,end)};
  }
  function terms(query){return normalizeArabic(String(query||'').trim()).split(/\s+/).filter(function(x){return x.length>1})}
  function merge(ranges){
    ranges.sort(function(a,b){return a[0]-b[0]});var output=[];
    for(var i=0;i<ranges.length;i++){var last=output[output.length-1];if(last&&ranges[i][0]<=last[1])last[1]=Math.max(last[1],ranges[i][1]);else output.push(ranges[i])}
    return output;
  }
  function searchHit(text,query){
    var mapped=normalizedWithMap(text),queryTerms=terms(query),ranges=[],score=0;
    if(!queryTerms.length)return {score:0,ranges:[]};
    for(var t=0;t<queryTerms.length;t++){
      var term=queryTerms[t];
      var rx=new RegExp('(^|\\s)([\\u0621-\\u064A0-9]*'+escapeRegex(term)+'[\\u0621-\\u064A0-9]*)','g');
      var found,matched=false;
      while((found=rx.exec(mapped.text))){
        matched=true;
        var word=found[2],wordStart=found.index+found[1].length,inside=word.indexOf(term);
        var startN=wordStart+inside,endN=startN+term.length;
        var start=mapped.map[startN],end=mapped.map[Math.max(startN,endN-1)];
        if(start!=null&&end!=null)ranges.push([start,end+1]);
        if(word===term)score+=1400;
        else if(word.indexOf(term)===0)score+=1050;
        else if(word.endsWith(term))score+=980;
        else score+=850;
        if(rx.lastIndex===found.index)rx.lastIndex++;
      }
      if(!matched)return {score:0,ranges:[]};
    }
    var phrase=normalizeArabic(query||'');
    if(phrase&&mapped.text.indexOf(phrase)>=0)score+=2600;
    return {score:score,ranges:merge(ranges)};
  }
  function highlighted(text,query){
    var ranges=searchHit(text,query).ranges;if(!ranges.length)return escapeHtml(text);
    var html='',position=0;
    for(var i=0;i<ranges.length;i++){
      html+=escapeHtml(text.slice(position,ranges[i][0]));
      html+='<mark>'+escapeHtml(text.slice(ranges[i][0],ranges[i][1]))+'</mark>';
      position=ranges[i][1];
    }
    return html+escapeHtml(text.slice(position));
  }

  renderQuranSearch=function(query){
    if(!state.quran.length||state.currentQuranTab!=='surahs')return;
    state.quranSearchQuery=query||'';
    var box=document.getElementById('surahList'),q=String(query||'').trim(),rows=[];
    if(!q){for(var i=0;i<state.quran.length;i++)rows.push({type:'surah',score:0,s:state.quran[i]})}
    else{
      for(var s=0;s<state.quran.length;s++){
        var surah=state.quran[s],nameResult=searchHit(surah.name+' '+(surah.transliteration||'')+' '+surah.id,q);
        if(nameResult.score)rows.push({type:'surah',score:nameResult.score+3200,s:surah});
        for(var v=0;v<surah.verses.length;v++){
          var ayah=surah.verses[v],result=searchHit(ayah.text,q);
          if(result.score)rows.push({type:'ayah',score:result.score,s:surah,a:ayah});
        }
      }
      rows.sort(function(a,b){return b.score-a.score});rows=rows.slice(0,120);
    }
    box.innerHTML=rows.map(function(item){return item.type==='surah'?surahRow(item.s):ayahRow(item.s,item.a)}).join('')||'<div class="empty">لا توجد نتيجة تحتوي الكلمة المكتوبة.</div>';
  };
  ayahRow=function(surah,ayah){return '<button class="surah-row" onclick="openSurah('+surah.id+','+ayah.id+')"><span class="number-badge">'+arabicNumber(ayah.id)+'</span><span class="surah-info"><strong>'+highlighted(surah.name,state.quranSearchQuery)+' — آية '+arabicNumber(ayah.id)+'</strong><small>'+highlighted(ayah.text.substring(0,200),state.quranSearchQuery)+'</small></span></button>'};

  runHadithSearch=function(query){
    if(!state.hadith.length)return;
    state.hadithSearchQuery=query||'';
    var q=String(query||'').trim(),book=state.hadithBook,results=[];
    for(var i=0;i<state.hadith.length;i++){
      var hadith=state.hadith[i];if(book!=='all'&&hadith.book!==book)continue;
      var searchable=(hadith.display||'')+' '+(hadith.text||'')+' '+(hadith.narrator||'')+' '+(hadith.book||'');
      var result=q?searchHit(searchable,q):{score:1};
      if(!q||result.score)results.push({h:hadith,score:result.score});
    }
    results.sort(function(a,b){return b.score-a.score});
    state.hadithMatches=results;state.hadithVisible=25;renderHadithResults(q);
  };
  function visibleText(hadith){var shortText=hadith.display||'';return shortText.length>=45?shortText:(hadith.text||shortText)}
  renderHadithResults=function(query){
    var box=document.getElementById('hadithResults'),items=state.hadithMatches.slice(0,state.hadithVisible),html='';
    html+='<div class="hadith-library-head"><strong>مكتبة الأحاديث</strong><span>'+arabicNumber(state.hadithMatches.length)+' نتيجة</span></div>';
    if(query)html+='<div class="smart-note">تظهر الكلمة نفسها، أو كلمة تحتويها في بدايتها أو نهايتها، ويُحدد الجزء المكتوب كاملًا.</div>';
    for(var i=0;i<items.length;i++){
      var h=items[i].h,body=visibleText(h),marked=isBookmarked('hadith',h.id);
      html+='<article class="hadith-card v5-hadith-card"><div class="hadith-book-chip">'+escapeHtml(h.book)+'</div><p class="hadith-text">'+highlighted(body,state.hadithSearchQuery)+'</p><div class="hadith-meta"><span><b>الراوي:</b> '+escapeHtml(h.narrator||'الراوي مذكور في المصدر')+'</span><span><b>المصدر:</b> '+escapeHtml(h.book)+' — رقم '+arabicNumber(h.number||h.id)+'</span><span><b>حكم الحديث:</b> '+escapeHtml(h.grade||'راجع تخريج المصدر')+'</span></div><div class="hadith-actions"><button class="details-btn" onclick="toggleHadithFull(this)">عرض النص الكامل</button><button class="star-btn" onclick="toggleHadithBookmark('+h.id+',this)">'+(marked?'★':'☆')+'</button></div><div class="hadith-full hidden">'+highlighted(h.text||body,state.hadithSearchQuery)+'</div></article>';
    }
    box.innerHTML=html||'<div class="empty card">لا توجد نتائج مطابقة.</div>';
    var more=document.getElementById('loadMoreHadith');if(more)more.classList.toggle('hidden',state.hadithVisible>=state.hadithMatches.length);
  };
})();
