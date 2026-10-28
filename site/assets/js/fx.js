/* 筹策官网特效层（2026-10-28）：滚动进度 / 首屏金尘粒子+极光 / 截图带视差倾斜。
   只做展示增强，不碰业务逻辑；支持 prefers-reduced-motion 与触屏自动降级。 */
(function () {
  'use strict';
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* 顶部滚动进度条 */
  var bar = document.createElement('div');
  bar.id = 'fx-progress';
  document.body.appendChild(bar);
  var ticking = false;
  function setProgress() {
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    bar.style.transform = 'scaleX(' + (max > 0 ? (h.scrollTop || document.body.scrollTop) / max : 0) + ')';
    ticking = false;
  }
  window.addEventListener('scroll', function () {
    if (!ticking) { ticking = true; requestAnimationFrame(setProgress); }
  }, { passive: true });
  setProgress();

  if (reduce) return;

  /* 首屏极光 + 金尘粒子 */
  var hero = document.querySelector('.hero');
  if (hero) {
    var aurora = document.createElement('div');
    aurora.className = 'fx-aurora';
    aurora.setAttribute('aria-hidden', 'true');
    hero.insertBefore(aurora, hero.firstChild);

    var canvas = document.createElement('canvas');
    canvas.className = 'fx-particles';
    canvas.setAttribute('aria-hidden', 'true');
    hero.appendChild(canvas);
    var ctx = canvas.getContext('2d');
    var W = 0, H = 0, parts = [], raf = null;
    function resize() {
      var r = hero.getBoundingClientRect();
      var dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      W = r.width; H = r.height;
      canvas.width = W * dpr; canvas.height = H * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      var n = Math.round(Math.min(70, Math.max(26, W * H / 26000)));
      parts = [];
      for (var i = 0; i < n; i++) {
        parts.push({
          x: Math.random() * W, y: Math.random() * H,
          r: 0.8 + Math.random() * 1.9,
          s: 0.12 + Math.random() * 0.4,
          ph: Math.random() * Math.PI * 2,
          sw: 0.2 + Math.random() * 0.7,
          a: 0.25 + Math.random() * 0.5
        });
      }
    }
    function tick(t) {
      ctx.clearRect(0, 0, W, H);
      for (var i = 0; i < parts.length; i++) {
        var p = parts[i];
        p.y -= p.s;
        p.x += Math.sin(t / 1600 + p.ph) * p.sw * 0.3;
        if (p.y < -4) { p.y = H + 4; p.x = Math.random() * W; }
        var tw = 0.65 + 0.35 * Math.sin(t / 900 + p.ph * 3);
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(232,200,126,' + (p.a * tw).toFixed(3) + ')';
        ctx.fill();
      }
      raf = requestAnimationFrame(tick);
    }
    resize();
    window.addEventListener('resize', resize);
    raf = requestAnimationFrame(tick);
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) { if (raf) cancelAnimationFrame(raf); raf = null; }
      else if (!raf) raf = requestAnimationFrame(tick);
    });
  }

  /* 视差倾斜：首屏卡片组与界面大图（仅精细指针设备） */
  if (window.matchMedia && window.matchMedia('(pointer: fine)').matches) {
    function tilt(el, max) {
      if (!el) return;
      el.addEventListener('mousemove', function (e) {
        var r = el.getBoundingClientRect();
        var dx = (e.clientX - r.left) / r.width - 0.5;
        var dy = (e.clientY - r.top) / r.height - 0.5;
        el.style.transform = 'perspective(1200px) rotateY(' + (dx * max).toFixed(2) + 'deg) rotateX(' + (-dy * max).toFixed(2) + 'deg)';
      });
      el.addEventListener('mouseleave', function () { el.style.transform = ''; });
    }
    tilt(document.querySelector('.hero .cards'), 2.2);
    tilt(document.querySelector('.tour .stage'), 1.6);
  }
})();
