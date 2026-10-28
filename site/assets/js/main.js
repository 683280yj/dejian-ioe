/* 筹策官网 v1.0 · 2026-10-28 */
(function () {
  'use strict';
  var doc = document;
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var cfg = window.CHOUCE_CONFIG || {};
  function $(s, r) { return (r || doc).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || doc).querySelectorAll(s)); }
  function val(k) { return (cfg[k] || '').toString().trim(); }

  /* ---------- 轻提示 ---------- */
  var tt;
  function toast(msg) {
    var t = $('#toast'); if (!t) return;
    t.textContent = msg; t.hidden = false;
    requestAnimationFrame(function () { t.classList.add('on'); });
    clearTimeout(tt);
    tt = setTimeout(function () { t.classList.remove('on'); setTimeout(function () { t.hidden = true; }, 300); }, 3200);
  }

  /* ---------- 站点配置：联系方式、登录、备案 ---------- */
  (function applyConfig() {
    // 「登录系统」：填了 loginUrl 就直接打开系统登录页；没填则滚到预约区并提示
    var loginUrl = val('loginUrl');
    $$('[data-login]').forEach(function (a) {
      if (loginUrl) { a.href = loginUrl; a.target = '_blank'; a.rel = 'noopener'; }
      else a.addEventListener('click', function () { toast('系统账号由筹策开通，请联系筹策顾问'); });
    });

    var name = $('[data-cfg="companyName"]');
    if (name && val('companyName')) { name.textContent = val('companyName'); name.hidden = false; }

    var icp = $('[data-cfg="icp"]');
    if (icp && val('icp')) { icp.textContent = val('icp'); icp.hidden = false; }

    var police = $('[data-cfg="police"]');
    if (police && val('police')) {
      police.textContent = val('police');
      if (val('policeCode')) police.href = 'https://beian.mps.gov.cn/#/query/webSearch?code=' + encodeURIComponent(val('policeCode'));
      police.hidden = false;
    }

    var book = $('#bookBtn'), lines = $('#clines'), html = '';
    var phone = val('phone'), email = val('email'), url = val('bookingUrl');
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) email = '';
    var tel = phone.replace(/[^\d+]/g, '');
    if (url) { book.href = url; if (/^https?:/i.test(url)) { book.target = '_blank'; book.rel = 'noopener'; } }
    else if (email) book.href = 'mailto:' + email + '?subject=' + encodeURIComponent('预约产品讲解');
    else if (phone) book.href = 'tel:' + tel;
    else book.href = '#contact';
    function esc(s) { return s.replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); }
    if (phone) html += '<li><span>电话</span><a href="tel:' + esc(tel) + '">' + esc(phone) + '</a></li>';
    if (email) html += '<li><span>邮箱</span><a href="mailto:' + esc(email) + '">' + esc(email) + '</a></li>';
    if (html) { lines.innerHTML = html; lines.hidden = false; }
    else if (!url) { var pd = $('#cpending'); if (pd) pd.hidden = false; }
    // 首屏和导航的「预约产品讲解」统一指向问策板块
  })();

  /* ---------- 预约：由访客确认后通过自己的邮箱发送 ---------- */
  (function bookingDialog() {
    var dialog = $('#bookingDialog'), form = $('#bookingForm');
    if (!dialog || !form || !dialog.showModal) return;
    var email = val('email');
    var hasEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    var bookingUrl = val('bookingUrl');
    var bookingApiUrl = val('bookingApiUrl');
    var phone = val('phone').replace(/[^\d+]/g, '');
    $$('a[href="#contact"]:not([data-login]), #bookBtn').forEach(function (a) {
      if (bookingUrl) {
        a.href = bookingUrl;
        if (/^https?:/i.test(bookingUrl)) { a.target = '_blank'; a.rel = 'noopener'; }
      } else if (bookingApiUrl || hasEmail) {
        a.addEventListener('click', function (e) { e.preventDefault(); dialog.showModal(); });
      } else if (phone) {
        a.href = 'tel:' + phone;
      } else {
        a.addEventListener('click', function (e) {
          e.preventDefault();
          toast('预约联系方式暂未配置，请稍后再试');
        });
      }
    });
    $('#bookingClose').addEventListener('click', function () { dialog.close(); });
    form.addEventListener('submit', async function (e) {
      e.preventDefault();
      if (bookingApiUrl) {
        var submit = form.querySelector('button[type="submit"]');
        submit.disabled = true;
        try {
          var response = await fetch(bookingApiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              phone: form.elements.phone.value.trim(),
              category: form.elements.category.value.trim(),
              consent: form.elements.consent.checked,
              website: form.elements.website.value
            })
          });
          var result = await response.json();
          if (!response.ok) throw new Error(result.message || '暂时无法提交');
          form.reset();
          dialog.close();
          toast('预约已收到，我们会与你联系');
        } catch (err) {
          toast(err.message || '暂时无法提交，请稍后重试');
        } finally {
          submit.disabled = false;
        }
        return;
      }
      var email = val('email');
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        toast('预约邮箱尚未配置为有效地址，请稍后联系筹策顾问');
        return;
      }
      var subject = encodeURIComponent('筹策产品讲解预约');
      var body = encodeURIComponent('联系电话：' + form.elements.phone.value.trim() + '\n经营品类：' + form.elements.category.value.trim());
      window.location.href = 'mailto:' + email + '?subject=' + subject + '&body=' + body;
      dialog.close();
    });
  })();

  /* ---------- 顶栏 ---------- */
  var top = $('#top'), btn = $('.menu-btn');
  function onScroll() { top.classList.toggle('scrolled', window.scrollY > 40); }
  window.addEventListener('scroll', onScroll, { passive: true }); onScroll();
  btn.addEventListener('click', function () {
    var open = !top.classList.contains('open');
    top.classList.toggle('open', open);
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    btn.setAttribute('aria-label', open ? '关闭导航' : '打开导航');
  });
  $$('#nav a').forEach(function (a) {
    a.addEventListener('click', function () { top.classList.remove('open'); btn.setAttribute('aria-expanded', 'false'); });
  });

  /* ---------- 页脚撕纸边 ---------- */
  (function torn() {
    var p = $('#tornPath'); if (!p) return;
    var d = 'M0 40 L0 22', x = 0, seed = 7;
    function rnd() { seed = (seed * 9301 + 49297) % 233280; return seed / 233280; }
    while (x < 1440) { x += 10 + rnd() * 22; d += ' L' + Math.min(x, 1440).toFixed(1) + ' ' + (8 + rnd() * 26).toFixed(1); }
    p.setAttribute('d', d + ' L1440 40 Z');
  })();

  /* ---------- 滚动字带 ---------- */
  (function marquee() {
    var w = ['采购', '库存', '盘点', '批发开单', '供应商对账', '补货测算', '库存预警'], m = '';
    for (var k = 0; k < 2; k++) w.forEach(function (x, i) { m += '<span class="' + (i % 2 ? 'o' : '') + '">' + x + '</span><em>◆</em>'; });
    $('#mq').innerHTML = m + m;
  })();

  /* ---------- 数字计数 ---------- */
  function count(el) {
    var n = +el.getAttribute('data-n');
    if (reduce || !window.requestAnimationFrame) { el.textContent = n; return; }
    var s = performance.now();
    (function f(now) {
      var p = Math.min((now - s) / 1400, 1);
      el.textContent = Math.round(n * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(f); else el.textContent = n;
    })(s);
  }

  /* ---------- 进场动画 ---------- */
  var rv = $$('.rv'), counters = $$('.al [data-n]');
  if (reduce || !('IntersectionObserver' in window)) {
    rv.forEach(function (e) { e.classList.add('rv-in'); });
  } else {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        show(e.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    counters.forEach(function (e) { e.textContent = '0'; });
    // 首屏内的元素直接显示；其余交给观察器
    var vh = window.innerHeight || 800;
    rv.forEach(function (e) {
      if (e.getBoundingClientRect().top < vh) show(e); else io.observe(e);
    });
    // 兜底：观察器没触发（截图、打印、旧内核）也不会留下空白
    function showAll() { rv.forEach(function (e) { if (!e.classList.contains('rv-in')) { e.classList.add('shown'); show(e); } }); }
    setTimeout(showAll, 4000);
    window.addEventListener('beforeprint', showAll);
  }
  function show(e) {
    if (e.classList.contains('rv-in')) return;
    e.classList.add('rv-in');
    $$('[data-n]', e).forEach(count);
    if (io) io.unobserve(e);
  }

  /* ---------- 问策背景视频：进入视野才加载 ---------- */
  (function video() {
    var v = $('.cbg');
    var connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    if (!v || reduce || (connection && (connection.saveData || /(^|-)2g$/.test(connection.effectiveType))) || !('IntersectionObserver' in window)) return;
    var vio = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) {
          if (!v.src) { v.src = v.getAttribute('data-src'); }
          var pr = v.play(); if (pr && pr.catch) pr.catch(function () {});
        } else if (v.src) { v.pause(); }
      });
    }, { rootMargin: '200px 0px' });
    vio.observe(v);
  })();

  /* ---------- 真实界面：标签切换（支持方向键） ---------- */
  (function tabs() {
    var tabs = $$('.tabs [role="tab"]'); if (!tabs.length) return;
    function sel(i, focus) {
      tabs.forEach(function (t, k) {
        var on = k === i, pn = doc.getElementById(t.getAttribute('aria-controls'));
        t.setAttribute('aria-selected', on ? 'true' : 'false');
        t.tabIndex = on ? 0 : -1;
        pn.hidden = !on; pn.classList.toggle('on', on);
      });
      if (focus) tabs[i].focus();
      tabs[i].scrollIntoView && tabs[i].parentNode.scrollWidth > tabs[i].parentNode.clientWidth &&
        tabs[i].parentNode.scrollTo({ left: tabs[i].offsetLeft - 20, behavior: reduce ? 'auto' : 'smooth' });
    }
    tabs.forEach(function (t, i) {
      t.addEventListener('click', function () { sel(i); });
      t.addEventListener('keydown', function (e) {
        var n = e.key === 'ArrowRight' ? i + 1 : e.key === 'ArrowLeft' ? i - 1 : e.key === 'Home' ? 0 : e.key === 'End' ? tabs.length - 1 : null;
        if (n === null) return; e.preventDefault(); sel((n + tabs.length) % tabs.length, true);
      });
    });
  })();

  /* ---------- 流程条：逐步点亮 ---------- */
  (function wf() {
    var steps = $$('#wf li'); if (!steps.length) return;
    if (reduce) { steps.forEach(function (e) { e.classList.add('on'); }); return; }
    var i = -1, timer;
    function tick() { i = (i + 1) % (steps.length + 2); steps.forEach(function (e, k) { e.classList.toggle('on', k <= i); e.classList.toggle('cur', k === i); }); }
    if (!('IntersectionObserver' in window)) { steps.forEach(function (e) { e.classList.add('on'); }); return; }
    new IntersectionObserver(function (es) {
      es.forEach(function (e) { clearInterval(timer); if (e.isIntersecting) { tick(); timer = setInterval(tick, 900); } });
    }, { threshold: 0.3 }).observe($('#wf'));
  })();

  if (reduce) return; // 以下均为首屏动效

  /* ---------- 首屏标题：逐字浮现 + 后半句轮换 ---------- */
  var h = $('#hero-title'), l1 = $('.l1', h), l2 = $('.l2', h);
  var heads = [['每一箱货，', '都算过再进'], ['每一条建议，', '都写明依据'], ['每一张采购单，', '都等人确认']];
  function split(el, text, delay) {
    el.textContent = '';
    Array.prototype.forEach.call(text, function (c) {
      var s = doc.createElement('span'); s.className = 'ch in'; s.textContent = c;
      s.style.animationDelay = (delay += 0.07).toFixed(2) + 's'; el.appendChild(s);
    });
    return delay;
  }
  split(l2, heads[0][1], split(l1, heads[0][0], 0.3) + 0.05);
  var hi = 0;
  setTimeout(function () {
    setInterval(function () {
      hi = (hi + 1) % heads.length;
      h.classList.add('swap');
      setTimeout(function () {
        l1.textContent = heads[hi][0]; l2.textContent = heads[hi][1];
        h.setAttribute('aria-label', heads[hi][0] + heads[hi][1]);
        h.classList.remove('swap');
      }, 460);
    }, 3400);
  }, 1800);

  /* ---------- 补货测算卡：逐步展开 ---------- */
  var cl = $$('#calc li'), dr = $('#draft');
  function run() {
    cl.forEach(function (e) { e.classList.remove('on'); }); dr.classList.remove('on');
    cl.forEach(function (e, i) { setTimeout(function () { e.classList.add('on'); }, 600 * i); });
    setTimeout(function () { dr.classList.add('on'); }, 600 * cl.length + 200);
  }
  setTimeout(function () { run(); setInterval(run, 7000); }, 2400);

  /* ---------- 预警卡轮换 ---------- */
  var wn = $$('#warn li'), wi = 0;
  setInterval(function () { wn[wi].classList.remove('on'); wi = (wi + 1) % wn.length; wn[wi].classList.add('on'); }, 2200);

  /* ---------- 首屏数字条 ---------- */
  var hs = $$('.stats [data-n]');
  hs.forEach(function (e) { e.textContent = '0'; });
  setTimeout(function () { hs.forEach(count); }, 2700);
})();
