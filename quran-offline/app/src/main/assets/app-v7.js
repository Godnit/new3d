(function(){
  'use strict';

  /* Compatibility loader: index.html already loads this file synchronously.
     Insert the current reader, search, settings and hadith implementation
     before DOMContentLoaded. */
  document.write('<link rel="stylesheet" href="app-v8.css">');
  document.write('<link rel="stylesheet" href="app-v10.css">');
  document.write('<script src="app-v8.js"><\/script>');
  document.write('<script src="app-v9.js"><\/script>');
  document.write('<script src="app-v10.js"><\/script>');
})();
