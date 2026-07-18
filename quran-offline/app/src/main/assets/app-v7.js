(function(){
  'use strict';

  /* Compatibility loader: index.html already loads this file synchronously.
     Insert the v4.2 stylesheet and script before DOMContentLoaded so the new
     reader, search, settings and hadith fixes become the active implementation. */
  document.write('<link rel="stylesheet" href="app-v8.css">');
  document.write('<script src="app-v8.js"><\/script>');
})();
