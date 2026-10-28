(function () {
  'use strict';
  var cfg = window.CHOUCE_CONFIG || {};
  var dialog = document.getElementById('bookingDialog');
  var form = document.getElementById('bookingForm');
  var toast = document.getElementById('toast');
  var nav = document.getElementById('nav-links');
  var menu = document.querySelector('.menu-toggle');

  function notify(message) {
    if (!toast) return;
    toast.textContent = message;
    toast.hidden = false;
    clearTimeout(notify.timer);
    notify.timer = setTimeout(function () { toast.hidden = true; }, 4500);
  }

  var login = cfg.loginUrl || 'https://ioe.idky.tech/accounts/login/';
  document.querySelectorAll('[data-login]').forEach(function (link) {
    link.href = login;
  });
  ['companyName', 'icp', 'police'].forEach(function (key) {
    var el = document.querySelector('[data-cfg="' + key + '"]');
    if (el && cfg[key]) { el.textContent = cfg[key]; el.hidden = false; }
  });
  var police = document.querySelector('[data-cfg="police"]');
  if (police && cfg.policeCode) police.href = 'https://beian.mps.gov.cn/#/query/webSearch?code=' + encodeURIComponent(cfg.policeCode);

  if (menu && nav) {
    menu.addEventListener('click', function () {
      var open = menu.getAttribute('aria-expanded') !== 'true';
      menu.setAttribute('aria-expanded', String(open));
      nav.classList.toggle('open', open);
    });
    nav.querySelectorAll('a,button').forEach(function (item) {
      item.addEventListener('click', function () {
        nav.classList.remove('open');
        menu.setAttribute('aria-expanded', 'false');
      });
    });
  }

  document.querySelectorAll('[data-booking]').forEach(function (button) {
    button.addEventListener('click', function () {
      if (dialog && dialog.showModal) dialog.showModal();
      else location.href = 'product.html#contact';
    });
  });
  if (dialog && form) {
    var close = dialog.querySelector('.booking-close');
    if (close) close.addEventListener('click', function () { dialog.close(); });
    dialog.addEventListener('click', function (event) {
      if (event.target === dialog) dialog.close();
    });
    form.addEventListener('submit', async function (event) {
      event.preventDefault();
      var submit = form.querySelector('[type="submit"]');
      submit.disabled = true;
      try {
        var response = await fetch(cfg.bookingApiUrl || '/api/bookings/', {
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
        if (!response.ok) throw new Error(result.message || '预约提交失败，请稍后重试');
        form.reset();
        dialog.close();
        notify('预约已收到，我们会与你联系');
      } catch (error) {
        notify(error.message || '预约提交失败，请稍后重试');
      } finally {
        submit.disabled = false;
      }
    });
  }

  if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    document.documentElement.classList.add('js');
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08 });
    document.querySelectorAll('.reveal').forEach(function (el) { observer.observe(el); });
  }
})();
