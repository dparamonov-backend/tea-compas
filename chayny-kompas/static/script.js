(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const json = id => JSON.parse($(id).textContent);

  /* mobile nav */
  const navToggle = $('.nav-toggle'), nav = $('.nav');
  const setNav = open => { nav.classList.toggle('open', open); navToggle.setAttribute('aria-expanded', String(open)); };
  navToggle.addEventListener('click', () => setNav(!nav.classList.contains('open')));
  $$('a', nav).forEach(a => a.addEventListener('click', () => setNav(false)));

  /* menu viewer */
  const base = window.STATIC_BASE || '/static/';
  const pages = json('#pagesData').map(p => base + p);
  const ceremonyPages = 9; // pages 1–9 are ceremonies, the rest is the food menu
  const viewer = $('#menuViewer'), img = $('#menuPage'), cur = $('#pageCurrent'), title = $('#viewerTitle');
  const dots = $$('.page-dot');
  let page = 0, lastFocus = null, touchX = 0;

  function show(n) {
    page = (n + pages.length) % pages.length;
    img.src = pages[page];
    img.alt = page < ceremonyPages ? `Страница ${page + 1} меню церемоний` : 'Меню блюд';
    cur.textContent = String(page + 1).padStart(2, '0');
    title.textContent = page < ceremonyPages ? 'Меню церемоний' : 'Меню блюд';
    dots.forEach((d, i) => d.classList.toggle('active', i === page));
  }
  function openViewer(n) {
    lastFocus = document.activeElement;
    show(n);
    viewer.classList.add('open'); viewer.setAttribute('aria-hidden', 'false');
    document.body.classList.add('viewer-open');
    $('.viewer-close').focus();
  }
  function closeViewer() {
    viewer.classList.remove('open'); viewer.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('viewer-open');
    if (lastFocus) lastFocus.focus();
  }
  $$('[data-open-menu]').forEach(b => b.addEventListener('click', () => openViewer(Number(b.dataset.openMenu) || 0)));
  $('.viewer-close').addEventListener('click', closeViewer);
  $('.viewer-arrow.prev').addEventListener('click', () => show(page - 1));
  $('.viewer-arrow.next').addEventListener('click', () => show(page + 1));
  dots.forEach(d => d.addEventListener('click', () => show(Number(d.dataset.page))));
  viewer.addEventListener('click', e => { if (e.target === viewer || e.target.classList.contains('viewer-stage') || e.target.classList.contains('viewer-page')) closeViewer(); });
  const stage = $('.viewer-stage');
  stage.addEventListener('touchstart', e => { touchX = e.changedTouches[0].screenX; }, { passive: true });
  stage.addEventListener('touchend', e => { const dx = e.changedTouches[0].screenX - touchX; if (Math.abs(dx) > 45) show(page + (dx < 0 ? 1 : -1)); }, { passive: true });
  document.addEventListener('keydown', e => {
    if (!viewer.classList.contains('open')) return;
    if (e.key === 'Escape') closeViewer();
    if (e.key === 'ArrowLeft') show(page - 1);
    if (e.key === 'ArrowRight') show(page + 1);
  });

  /* ceremony dialog */
  const dlg = $('#cerDialog'), cers = json('#cerData'), arts = json('#artData');
  let current = null;
  const fill = (sel, items, fn) => { $(sel).innerHTML = ''; items.forEach(i => { const li = document.createElement('li'); fn(li, i); $(sel).appendChild(li); }); };

  function openCeremony(id) {
    const c = cers.find(x => x.id === id); if (!c) return;
    current = c;
    $('#cerTitle').textContent = c.title;
    $('#cerTag').textContent = c.tagline;
    $('#cerPrice').textContent = `${c.price} ${c.per}`;
    $('#cerMeta').textContent = `${c.duration} · ${c.guests}`;
    $('#cerArt').innerHTML = arts[id] || '';
    $('#cerQuote').textContent = c.quote;
    fill('#cerTeas', c.teas, (li, t) => { const b = document.createElement('b'); b.textContent = t[0]; const s = document.createElement('span'); s.textContent = t[1]; li.append(b, s); });
    fill('#cerLearn', c.learn, (li, t) => { li.textContent = t; });
    fill('#cerFlow', c.flow, (li, t) => { li.textContent = t; });
    document.body.classList.add('dialog-open');
    dlg.showModal();
    dlg.scrollTop = 0;
  }
  $$('.cer-card').forEach(card => {
    card.addEventListener('click', () => openCeremony(card.dataset.cer));
    card.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openCeremony(card.dataset.cer); } });
  });
  $('.dialog-close').addEventListener('click', () => dlg.close());
  dlg.addEventListener('click', e => { if (e.target === dlg) dlg.close(); });
  dlg.addEventListener('close', () => document.body.classList.remove('dialog-open'));
  $('#cerForm').addEventListener('click', () => {
    const select = $('#ceremonySelect');
    if (current) select.value = current.title;
    dlg.close();
    $('#booking').scrollIntoView({ behavior: 'smooth' });
    setTimeout(() => $('input[name="name"]').focus({ preventScroll: true }), 600);
  });

  /* form: no past dates */
  const dateInput = $('input[name="preferred_date"]');
  if (dateInput) { const n = new Date(); dateInput.min = new Date(n - n.getTimezoneOffset() * 60000).toISOString().slice(0, 10); }
})();
