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
    var hint = document.querySelector('.lb__hint');
    if (hint) hint.textContent = ko ? '탭하면 확대' : 'tap image to zoom';
    try { localStorage.setItem(STORE, lang); } catch (e) {}
  }

  window.__goalfRelang = null;
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

  /* ---------- tap any figure to enlarge ---------- */
  var lb = document.createElement('div');
  lb.className = 'lb';
  lb.setAttribute('role','dialog');
  lb.setAttribute('aria-modal','true');
  lb.hidden = false;
  lb.innerHTML =
    '<div class="lb__bar"><span class="lb__cap"></span>' +
    '<button type="button" class="lb__x" aria-label="Close">\u2715</button></div>' +
    '<div class="lb__scroll"><img alt=""></div>' +
    '<p class="lb__hint" data-ko="탭하면 확대">tap image to zoom</p>';
  document.body.appendChild(lb);

  var lbImg = lb.querySelector('img');
  var lbCap = lb.querySelector('.lb__cap');
  var lbScroll = lb.querySelector('.lb__scroll');
  var lastFocus = null;

  document.querySelectorAll('figure.poster, figure.shot').forEach(function (fig) {
    var img = fig.querySelector('img');
    if (!img) return;
    fig.classList.add('zoomable');
    fig.tabIndex = 0;
    fig.setAttribute('role','button');
    fig.addEventListener('click', function () { openLb(fig, img); });
    fig.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openLb(fig, img); }
    });
  });

  function openLb(fig, img) {
    lastFocus = fig;
    lbImg.src = img.currentSrc || img.src;
    lbImg.alt = img.alt || '';
    var cap = fig.querySelector('figcaption');
    lbCap.textContent = cap ? cap.textContent.trim() : (img.alt || '');
    lb.classList.remove('is-zoomed');
    lb.classList.add('open');
    body.classList.add('lb-open');
    lbScroll.scrollTop = 0; lbScroll.scrollLeft = 0;
    lb.querySelector('.lb__x').focus();
  }

  function closeLb() {
    lb.classList.remove('open','is-zoomed');
    body.classList.remove('lb-open');
    if (lastFocus) lastFocus.focus();
  }

  lbImg.addEventListener('click', function (e) {
    e.stopPropagation();
    var z = lb.classList.toggle('is-zoomed');
    if (z) {
      lbScroll.scrollLeft = (lbScroll.scrollWidth - lbScroll.clientWidth) / 2;
      lbScroll.scrollTop = 0;
    }
  });
  lb.addEventListener('click', closeLb);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && lb.classList.contains('open')) closeLb();
  });

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
