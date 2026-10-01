/* GO(A)LF — drawer nav, language switch, scroll reveal, progress bar */
(function () {
  'use strict';

  var body = document.body;
  var btn = document.getElementById('navBtn');
  var panel = document.getElementById('navPanel');
  var head = document.getElementById('head');
  var bar = document.getElementById('bar');
  var langBox = document.getElementById('lang');

  /* ---------- language ---------- */
  var STORE = 'goalf-lang';
  var TITLES = { en: 'GO(A)LF — Park(ing) Day', ko: 'GO(A)LF — 파킹데이' };
  var nodes = document.querySelectorAll('[data-ko]');

  // keep the English markup as authored, so switching back is lossless
  nodes.forEach(function (el) {
    el.setAttribute('data-en', el.innerHTML.trim());
  });

  function setLang(lang) {
    var ko = lang === 'ko';
    document.documentElement.lang = ko ? 'ko' : 'en';
    nodes.forEach(function (el) {
      el.innerHTML = el.getAttribute(ko ? 'data-ko' : 'data-en');
    });
    document.title = TITLES[ko ? 'ko' : 'en'];
    langBox.querySelectorAll('button').forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.dataset.lang === lang));
    });
    try { localStorage.setItem(STORE, lang); } catch (e) {}
  }

  var saved = null;
  try { saved = localStorage.getItem(STORE); } catch (e) {}
  setLang(saved || (/^ko\b/i.test(navigator.language || '') ? 'ko' : 'en'));

  langBox.addEventListener('click', function (e) {
    var b = e.target.closest('button[data-lang]');
    if (b) setLang(b.dataset.lang);
  });

  /* ---------- drawer ---------- */
  function setNav(open) {
    body.classList.toggle('nav-open', open);
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  }

  btn.addEventListener('click', function () {
    setNav(!body.classList.contains('nav-open'));
  });

  panel.addEventListener('click', function (e) {
    if (e.target.closest('a')) setNav(false);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') setNav(false);
  });

  /* ---------- header state + reading progress ---------- */
  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      var y = window.scrollY || document.documentElement.scrollTop;
      head.classList.toggle('is-stuck', y > 8);

      var max = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.width = (max > 0 ? (y / max) * 100 : 0) + '%';
      ticking = false;
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------- scroll reveal ---------- */
  var items = document.querySelectorAll('.rv');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          en.target.classList.add('in');
          io.unobserve(en.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

    items.forEach(function (el) { io.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.add('in'); });
  }
})();
