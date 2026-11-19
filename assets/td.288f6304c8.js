/* terradoc v2: small enhancements; every page works without this file. */
(function () {
  'use strict';
  // Phone menu: Esc and a click outside close it, focus goes back to the button.
  var menu = document.querySelector('.td-menu');
  if (menu) {
    var summary = menu.querySelector('summary');
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && menu.open) { menu.open = false; summary.focus(); }
    });
    document.addEventListener('click', function (e) {
      if (menu.open && !menu.contains(e.target)) menu.open = false;
    });
  }
  // Offline: the service worker sits at the site root (data-root on <html>).
  if ('serviceWorker' in navigator && location.protocol === 'https:') {
    var root = document.documentElement.getAttribute('data-root') || '';
    if (root.charAt(0) !== '/' && !/^https?:/.test(root)) {
      navigator.serviceWorker.register(root + 'sw.js').catch(function () {});
    }
  }
  // List filter (animals, plants, articles, references): hides the items that do not
  // match. Reads ?search= / ?q= and ?category= (links from v1 pages); category chips set
  // ?category= in place. Without script the lists are complete and the chips stay hidden.
  function fold(s) {
    return String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
      .replace(/[\u2019'\u02bc`\u00b4\u2018]/g, '').replace(/\s+/g, ' ').trim();
  }
  var params = new URLSearchParams(location.search);
  Array.prototype.forEach.call(document.querySelectorAll('[data-td-filter]'), function (box) {
    var list = document.getElementById(box.getAttribute('data-td-filter'));
    if (!list) return;
    var input = box.querySelector('input'), status = box.querySelector('[role="status"]');
    var T = JSON.parse(box.getAttribute('data-td-strings') || '{}');
    var items = Array.prototype.map.call(list.querySelectorAll('[data-td-item]'), function (li) {
      var cats = li.getAttribute('data-td-categories');
      return { el: li, text: fold(li.textContent), cats: cats ? cats.split('|') : [] };
    });
    var groups = list.querySelectorAll('[data-td-group]');
    var chips = document.querySelector('[data-td-chips="' + list.id + '"]');
    // Only lists with category chips (the encyclopedia) read ?category=; v1's fauna page
    // used it for its own groups, which the v2 list does not filter by.
    var category = chips ? params.get('category') || '' : '';
    function apply() {
      var q = fold(input.value), shown = 0;
      items.forEach(function (it) {
        var ok = (!q || it.text.indexOf(q) >= 0) && (!category || it.cats.some(function (c) {
          return c === category || c.indexOf(category + '/') === 0;
        }));
        it.el.hidden = !ok;
        if (ok) shown++;
      });
      Array.prototype.forEach.call(groups, function (g) { g.hidden = !g.querySelector('[data-td-item]:not([hidden])'); });
      if (chips) Array.prototype.forEach.call(chips.querySelectorAll('[data-td-category]'), function (a) {
        if (a.getAttribute('data-td-category') === category) a.setAttribute('aria-current', 'true');
        else a.removeAttribute('aria-current');
      });
      status.textContent = !(q || category) ? '' : shown ? (T.count || '').replace('{n}', shown).replace('{total}', items.length) : T.none || '';
    }
    box.hidden = false;
    if (chips) {
      chips.hidden = false;
      chips.addEventListener('click', function (e) {
        var a = e.target.closest && e.target.closest('[data-td-category]');
        if (!a) return;
        e.preventDefault();
        category = a.getAttribute('data-td-category');
        var url = new URL(location.href);
        if (category) url.searchParams.set('category', category); else url.searchParams.delete('category');
        history.replaceState(null, '', url);
        apply();
      });
    }
    input.value = params.get('search') || params.get('q') || '';
    input.addEventListener('input', apply);
    if (input.value || category) apply();
  });
  // Remember the language chosen with the switch (read by the site root page).
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('[data-td-locale]');
    if (a) { try { localStorage.setItem('td-locale', a.getAttribute('data-td-locale')); } catch (err) {} }
  });
})();
