/* terradoc v2 service worker: the site keeps working with a weak or no connection.
   - the shell (CSS, scripts, the two critical fonts, offline.html) is stored at install;
   - other files in assets/ (fonts, search index, pack): stored when first used, then served
     from the store (their names carry a hash, so they never change);
   - pages: from the network, with a copy kept (the last MAX_PAGES); from the copy when the
     network fails or is slower than TIMEOUT; offline.html for a page never opened;
   - photos (assets/img/), audio and anything else: never stored (cheap phones fill up).
   Several sites and previews share previews.terradoc.org, so every cache name carries this
   worker's scope, and a worker only ever deletes its own caches. A new version (new CSS,
   scripts, fonts, index or offline page) clears the old shell and the stored pages, whose
   CSS and scripts the new release no longer has.
   The build fills in VERSION, PRECACHE and OFFLINE. */
var VERSION = "1648ad322a";
var PRECACHE = ["assets/site.5a5b47f861.css", "assets/td.288f6304c8.js", "assets/fonts/td-text-400.95e022c145.woff2", "assets/fonts/td-ui-400.62b3f83d5c.woff2", "offline.html"];
var OFFLINE = "offline.html";
var PREFIX = 'td|' + self.registration.scope + '|';
var SHELL = PREFIX + 'shell-' + VERSION, PAGES = PREFIX + 'pages-' + VERSION;
var MAX_PAGES = 300, TIMEOUT = 4000;

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(SHELL).then(function (c) {
    return c.addAll(PRECACHE.map(function (p) { return new Request(p, { cache: 'reload' }); }));
  }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) {
      return k.indexOf(PREFIX) === 0 && k !== SHELL && k !== PAGES;
    }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

function trim(cache) {
  return cache.keys().then(function (keys) {
    if (keys.length > MAX_PAGES) return cache.delete(keys[0]).then(function () { return trim(cache); });
  });
}

function stored(req) {
  return caches.open(PAGES).then(function (c) { return c.match(req, { ignoreSearch: true }); });
}

self.addEventListener('fetch', function (e) {
  var req = e.request, url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin) return;
  if (url.href.indexOf(self.registration.scope) !== 0) return;
  var path = url.href.slice(self.registration.scope.length);
  if (/^assets\//.test(path) && !/^assets\/img\//.test(path)) {
    e.respondWith(caches.open(SHELL).then(function (c) {
      return c.match(req).then(function (hit) {
        return hit || fetch(req).then(function (res) {
          if (res.ok) c.put(req, res.clone());
          return res;
        });
      });
    }));
    return;
  }
  if (req.mode === 'navigate' || /\.html$/.test(url.pathname)) {
    var network = fetch(req).then(function (res) {
      if (res.ok) {
        var copy = res.clone();
        caches.open(PAGES).then(function (c) { return c.put(req, copy).then(function () { return trim(c); }); });
      }
      return res;
    });
    var slow = new Promise(function (resolve) {
      setTimeout(function () { stored(req).then(resolve); }, TIMEOUT);
    });
    e.respondWith(Promise.race([network, slow.then(function (hit) { return hit || network; })])
      .catch(function () {
        var offline = new URL(OFFLINE, self.registration.scope).href;
        return stored(req).then(function (hit) {
          if (hit) return hit;
          if (url.href === offline) return caches.match(offline, { cacheName: SHELL });
          return Response.redirect(offline, 302);  // its relative links work only at its own address
        });
      }));
  }
});
