/* terradoc v2 dictionary: search as you type, the on-screen keyboard, and the way back from
   a word to the list it was opened from. The letter lists and word pages work without it. */
(function (global) {
  'use strict';

  /* ---- Search, without the page (tests/test_v2_dictionary.py runs this part in node). ---- */
  function makeSearch(folds) {
    var keys = Object.keys(folds || {}).sort(function (a, b) { return b.length - a.length; });
    var re = keys.length ? new RegExp(keys.map(function (k) {
      return k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }).join('|'), 'g') : null;
    // Accents, case and apostrophes never matter.
    function fold(s) {
      return String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
        .replace(/[’'ʼ`´‘]/g, '').replace(/\s+/g, ' ').trim();
    }
    // Words of the language: also the site's folds (r = l, ...) and no leading hyphen (-ka).
    function vfold(s) {
      s = fold(s).replace(/^-+/, '');
      return re ? s.replace(re, function (m) { return folds[m]; }) : s;
    }
    function escapeRe(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
    function slug(s) {
      return String(s || '').normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase()
        .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
    }
    function prepare(d) {
      return d.rows.map(function (r, i) {
        var sl = r.length > 7 ? r[7] : slug(r[1]);
        var g = fold(r[3]);
        return { id: r[0], entry: r[1], homonym: r[2], gloss: r[3], audio: r[6], order: i,
                 file: r[0] + (sl ? '-' + sl : '') + '.html',
                 hw: vfold(r[1]), g: g,
                 senses: g.split(/\s*[,;.]\s*/).filter(Boolean),
                 x: fold(r[4] + ' ' + r[5]) };
      });
    }
    // Lower is better: the word itself, the start of a word, a gloss that is the query,
    // the query as a word in a gloss, then inside words, then IPA and scientific names.
    function score(r, q, v, gw, hs) {
      if (v && r.hw === v) return 0;
      if (v && r.hw.indexOf(v) === 0) return 1;
      if (r.senses.indexOf(q) >= 0) return 2;
      if (gw.test(r.g)) return 3;
      if (v && hs.test(r.hw)) return 4;
      if (v && r.hw.indexOf(v) > 0) return 5;
      if (r.g.indexOf(q) >= 0) return 6;
      if (r.x.indexOf(q) >= 0) return 7;
      return -1;
    }
    function search(rows, raw) {
      var q = fold(raw), v = vfold(raw);
      if (!q) return [];
      var gw = new RegExp('(^|[^a-z0-9])' + escapeRe(q) + '($|[^a-z0-9])');
      var hs = new RegExp('[\\s-]' + escapeRe(v));
      var hits = [];
      for (var i = 0; i < rows.length; i++) {
        var s = score(rows[i], q, v, gw, hs);
        if (s >= 0) hits.push([s, rows[i]]);
      }
      hits.sort(function (a, b) { return a[0] - b[0] || a[1].order - b[1].order; });
      return hits.map(function (h) { return h[1]; });
    }
    return { fold: fold, vfold: vfold, slug: slug, prepare: prepare, search: search };
  }
  global.TDSearch = makeSearch;

  var doc = global.document;
  if (!doc || !doc.querySelector) return;
  var input = doc.getElementById('td-q');

  // On-screen keyboard: types the language's letters at the cursor.
  var kb = doc.querySelector('.td-keyboard');
  if (kb && input) {
    kb.hidden = false;
    kb.addEventListener('click', function (e) {
      var b = e.target.closest && e.target.closest('.td-key');
      if (!b) return;
      var k = b.getAttribute('data-key'), s = input.selectionStart, t = input.selectionEnd;
      if (s == null) { s = t = input.value.length; }
      input.value = input.value.slice(0, s) + k + input.value.slice(t);
      input.focus();
      input.setSelectionRange(s + k.length, s + k.length);
      input.dispatchEvent(new Event('input', { bubbles: true }));
    });
  }

  // From a word opened from search results, "back" returns to those results.
  var back = doc.querySelector('[data-td-back]');
  var article = doc.querySelector('[data-entry]');
  if (back && article && doc.referrer) {
    try {
      var ref = new URL(doc.referrer);
      if (ref.origin === location.origin && /\/dictionary\/index\.html$/.test(ref.pathname) && ref.search) {
        back.href = ref.pathname + ref.search + '#e-' + article.getAttribute('data-entry');
      }
    } catch (err) { /* keep the letter list */ }
  }

  var box = doc.querySelector('.td-dict[data-index]');
  if (!box || !input) return;
  var T = JSON.parse(box.getAttribute('data-strings') || '{}');
  var engine = makeSearch(JSON.parse(box.getAttribute('data-folds') || '{}'));
  var LANG = box.getAttribute('data-lang') || '';
  var LOCALE = box.getAttribute('data-locale') || 'pt';
  var status = doc.getElementById('td-status');
  var results = doc.getElementById('td-results');
  var MAX = 100, GLOSS = 160;
  var rows = null, loading = null;

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; });
  }
  function fmt(s, vars) { return String(s || '').replace(/\{(\w+)\}/g, function (_, k) { return vars[k]; }); }
  function say(text) { if (status) status.textContent = text; }
  function clip(s) { return s.length <= GLOSS ? s : s.slice(0, GLOSS - 1).replace(/\s+\S*$/, '') + '…'; }

  function load() {
    if (rows) return Promise.resolve(rows);
    if (loading) return loading;
    say(T.ui_dict_loading);
    loading = fetch(box.getAttribute('data-index')).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    }).then(function (d) {
      rows = engine.prepare(d);
      say('');
      return rows;
    }).catch(function (err) {
      loading = null;
      say(T.ui_dict_failed);
      var b = doc.createElement('button');
      b.type = 'button'; b.className = 'td-button td-button--quiet'; b.textContent = T.ui_retry;
      b.addEventListener('click', function () { b.remove(); load().then(function () { run(); }, function () {}); });
      if (status) { status.appendChild(doc.createTextNode(' ')); status.appendChild(b); }
      throw err;
    });
    return loading;
  }

  function render(list, raw) {
    if (!list.length) { results.innerHTML = ''; say(fmt(T.ui_dict_none, { q: raw })); return; }
    var n = list.length.toLocaleString(LOCALE);
    say(fmt(list.length === 1 ? T.ui_dict_results_one : T.ui_dict_results, { n: n, q: raw })
        + (list.length > MAX ? ' ' + fmt(T.ui_dict_more, { shown: MAX }) : ''));
    var lang = LANG ? ' lang="' + esc(LANG) + '"' : '';
    var glossLang = LOCALE.indexOf('pt') === 0 ? '' : ' lang="pt-BR"';
    results.innerHTML = '<ol class="td-words">' + list.slice(0, MAX).map(function (r) {
      return '<li><a id="e-' + esc(r.id) + '" href="' + encodeURI(r.file) + '"><span class="td-word"><span class="td-hw"' + lang + '>'
        + esc(r.entry) + '</span>' + (r.homonym ? '<sup class="td-homonym">' + esc(r.homonym) + '</sup>' : '') + '</span></a>'
        + (r.audio ? ' <span class="td-has-audio" aria-hidden="true">♪</span><span class="td-sr">' + esc(T.ui_has_audio) + '</span>' : '')
        + ' <span class="td-words__gloss"' + glossLang + '>' + esc(clip(r.gloss)) + '</span></li>';
    }).join('') + '</ol>';
  }

  var timer = null;
  function run(focusId) {
    var raw = input.value.trim();
    var url = new URL(location.href);
    if (raw) url.searchParams.set('q', raw); else url.searchParams.delete('q');
    if (!focusId) url.hash = '';
    history.replaceState(null, '', url);
    var hint = doc.getElementById('td-hint');
    if (hint) hint.hidden = !!raw;
    if (!engine.fold(raw)) { results.innerHTML = ''; say(''); return; }
    load().then(function (all) {
      if (input.value.trim() !== raw) return; // typed on meanwhile
      render(engine.search(all, raw), raw);
      var a = focusId && doc.getElementById(focusId);
      if (a) { a.scrollIntoView({ block: 'center' }); a.focus(); }
    }, function () {});
  }

  input.addEventListener('focus', function () { load().catch(function () {}); }, { once: true });
  input.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(run, 120); });
  input.form.addEventListener('submit', function (e) { e.preventDefault(); clearTimeout(timer); run(); });

  var q0 = new URLSearchParams(location.search).get('q');
  if (q0) {
    input.value = q0;
    run(/^#e-\d+$/.test(location.hash) ? location.hash.slice(1) : null);
  }
})(typeof self !== 'undefined' ? self : this);
