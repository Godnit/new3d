(function(){
  'use strict';

  /* Keep the page header tied to the surah that starts at the top of the page.
     When another surah begins mid-page, its own strip remains inside the page. */
  function fixPageHeaders(root){
    var pages=(root||document).querySelectorAll('.mushaf-page[data-page]');
    for(var i=0;i<pages.length;i++){
      var pageNumber=Number(pages[i].dataset.page||0);
      var record=state.mushafLayout&&state.mushafLayout[pageNumber-1];
      var ids=record&&(record.surahs||record.s)||[];
      var first=ids.length&&state.quran[ids[0]-1];
      var label=pages[i].querySelector('.meta-surah');
      if(label&&first){
        var expected='سورة '+first.name;
        if(label.textContent!==expected)label.textContent=expected;
      }
    }
  }

  function start(){
    var stage=document.getElementById('mushafStage');if(!stage)return;
    fixPageHeaders(stage);
    new MutationObserver(function(){fixPageHeaders(stage)}).observe(stage,{childList:true,subtree:true});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();
