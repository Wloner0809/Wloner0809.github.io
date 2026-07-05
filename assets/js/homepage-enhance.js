// Homepage enhancements: theme toggle, total citations, scrollspy, scroll-reveal.
(function () {
  'use strict';

  var GS_JSON = 'https://raw.githubusercontent.com/Wloner0809/Wloner0809.github.io/main/google_scholar_crawler/results/gs_data.json';

  // ---- #5 Dark mode manual toggle ----
  function currentTheme() {
    var attr = document.documentElement.getAttribute('data-theme');
    if (attr === 'dark' || attr === 'light') return attr;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem('theme', theme); } catch (e) {}
  }
  function initThemeToggle() {
    var btn = document.getElementById('theme-toggle');
    if (!btn) return;
    btn.addEventListener('click', function () {
      applyTheme(currentTheme() === 'dark' ? 'light' : 'dark');
    });
  }

  // ---- #7 Total citations badge ----
  function initTotalCitations() {
    var el = document.getElementById('total-citations-count');
    if (!el || typeof jQuery === 'undefined') return;
    jQuery.getJSON(GS_JSON, function (data) {
      if (data && typeof data.citedby !== 'undefined') {
        el.textContent = data.citedby;
      } else {
        el.textContent = 'N/A';
      }
    }).fail(function () { el.textContent = 'N/A'; });
  }

  // ---- #2 Scrollspy: highlight active section in sidebar nav ----
  function initScrollSpy() {
    var links = Array.prototype.slice.call(document.querySelectorAll('.site-nav a.normal'));
    if (!links.length || !('IntersectionObserver' in window)) return;
    var map = {};
    links.forEach(function (a) {
      var href = a.getAttribute('href') || '';
      var hash = href.indexOf('#') >= 0 ? href.slice(href.indexOf('#') + 1) : '';
      if (hash) map[hash] = a;
    });
    var targets = Object.keys(map)
      .map(function (id) { return document.getElementById(id); })
      .filter(Boolean);
    if (!targets.length) return;

    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          links.forEach(function (a) { a.classList.remove('active'); });
          var active = map[entry.target.id];
          if (active) active.classList.add('active');
        }
      });
    }, { rootMargin: '-45% 0px -50% 0px', threshold: 0 });
    targets.forEach(function (t) { spy.observe(t); });
  }

  // ---- #1 Scroll-reveal entrance animations ----
  function initScrollReveal() {
    var items = Array.prototype.slice.call(document.querySelectorAll('.reveal'));
    if (!items.length) return;
    if (!('IntersectionObserver' in window)) {
      items.forEach(function (el) { el.classList.add('reveal-visible'); });
      return;
    }
    var obs = new IntersectionObserver(function (entries, o) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('reveal-visible');
          o.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });
    items.forEach(function (el) { obs.observe(el); });
  }

  function init() {
    initThemeToggle();
    initTotalCitations();
    initScrollSpy();
    initScrollReveal();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
