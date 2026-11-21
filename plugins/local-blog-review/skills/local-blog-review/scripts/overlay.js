// Commenting layer injected into the locally served site by server.mjs.
// Select text to comment, or Option-click a block (paragraph, table, figure) to comment on all of it.
(() => {
  if (window.__articleReview) return;
  window.__articleReview = true;

  const API = '/__review/api/comments';
  const root = () => document.querySelector('article') || document.querySelector('main') || document.body;
  const el = (tag, props = {}, ...children) => {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(props)) {
      if (key === 'class') node.className = value;
      else if (key === 'text') node.textContent = value;
      else if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
      else node.setAttribute(key, value);
    }
    node.append(...children.filter(child => child != null));
    return node;
  };
  const request = async (method, url, data) => {
    const response = await fetch(url, {
      method,
      headers: data ? { 'content-type': 'application/json' } : undefined,
      body: data ? JSON.stringify(data) : undefined,
    });
    if (!response.ok) throw new Error(`${method} ${url}: ${response.status}`);
    return response.json();
  };

  // ---- state ---------------------------------------------------------------
  let comments = [];
  let located = new Map(); // id -> [start, end] offsets in the article text, when found
  let storeFile = '';
  let panelOpen = false;
  let pending = null; // { start, end, kind } waiting for the composer
  let focusId = null;
  let lastPath = location.pathname;

  // ---- text index: every text node under the article, as one string --------
  function textIndex() {
    const walker = document.createTreeWalker(root(), NodeFilter.SHOW_TEXT);
    const nodes = [];
    let full = '';
    let node;
    while ((node = walker.nextNode())) {
      nodes.push({ node, start: full.length });
      full += node.nodeValue;
    }
    return { full, nodes };
  }
  function pointAt(index, offset) {
    const { nodes } = index;
    let lo = 0;
    let hi = nodes.length - 1;
    while (lo < hi) {
      const mid = (lo + hi + 1) >> 1;
      if (nodes[mid].start <= offset) lo = mid;
      else hi = mid - 1;
    }
    const hit = nodes[lo];
    return hit ? [hit.node, Math.min(offset - hit.start, hit.node.nodeValue.length)] : null;
  }
  function rangeAt(index, start, end) {
    const a = pointAt(index, start);
    const b = pointAt(index, end);
    if (!a || !b) return null;
    const range = document.createRange();
    range.setStart(...a);
    range.setEnd(...b);
    return range;
  }
  function offsetsOf(range) {
    const before = document.createRange();
    before.selectNodeContents(root());
    before.setEnd(range.startContainer, range.startOffset);
    const start = before.toString().length;
    return [start, start + range.toString().length];
  }
  // Find a comment's text again. Uses the text around it first, then the nearest match to where it was.
  function locate(comment, full) {
    if (!comment.quote) return null;
    const exact = full.indexOf(comment.prefix + comment.quote + comment.suffix);
    if (exact > -1) return [exact + comment.prefix.length, exact + comment.prefix.length + comment.quote.length];
    let best = -1;
    for (let at = full.indexOf(comment.quote); at > -1; at = full.indexOf(comment.quote, at + 1))
      if (best < 0 || Math.abs(at - comment.pos) < Math.abs(best - comment.pos)) best = at;
    return best < 0 ? null : [best, best + comment.quote.length];
  }
  function sectionOf(node) {
    let found = '';
    for (const heading of root().querySelectorAll('h1, h2, h3')) {
      // Headings inside a figure label the figure, not the section of the article it sits in.
      if (heading.closest('figure, [data-visualization-kind]')) continue;
      if (heading === node || heading.compareDocumentPosition(node) & Node.DOCUMENT_POSITION_FOLLOWING)
        found = heading.textContent.trim();
      else break;
    }
    return found;
  }

  // ---- interface (kept in a shadow root so site styles cannot reach it) ----
  const host = el('div', { id: 'article-review-host' });
  const shadow = host.attachShadow({ mode: 'open' });
  shadow.append(
    el('style', {
      text: `
      :host { all: initial; }
      * { box-sizing: border-box; font-family: ui-sans-serif, system-ui, -apple-system, sans-serif; }
      button { cursor: pointer; font: inherit; }
      .toggle { position: fixed; right: 16px; bottom: 16px; z-index: 2147483000; background: #ff570a; color: #fff;
        border: 0; border-radius: 999px; padding: 10px 16px; font-size: 14px; font-weight: 600; box-shadow: 0 4px 16px rgba(0,0,0,.4); }
      .panel { position: fixed; top: 0; right: 0; bottom: 0; width: min(380px, 92vw); z-index: 2147483001; background: #1b181f;
        color: #eee8e3; border-left: 1px solid #3a3441; display: flex; flex-direction: column; box-shadow: -8px 0 24px rgba(0,0,0,.35); }
      .panel[hidden] { display: none; }
      header { padding: 14px 16px; border-bottom: 1px solid #3a3441; display: flex; align-items: center; gap: 8px; }
      header h2 { margin: 0; font-size: 15px; font-weight: 600; flex: 1; }
      .hint { padding: 10px 16px; font-size: 12px; line-height: 1.5; color: #b9aebf; border-bottom: 1px solid #2c2731; }
      .list { flex: 1; overflow: auto; padding: 12px; display: flex; flex-direction: column; gap: 10px; }
      .empty { color: #b9aebf; font-size: 13px; padding: 12px 4px; }
      .card { border: 1px solid #3a3441; border-radius: 8px; padding: 10px 12px; background: #221e27; font-size: 13px; line-height: 1.45; }
      .card.done { opacity: .62; }
      .card.flash { outline: 2px solid #ff570a; }
      .meta { display: flex; gap: 6px; align-items: center; color: #b9aebf; font-size: 11px; margin-bottom: 6px; }
      .meta .section { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .chip { border-radius: 999px; padding: 1px 8px; font-size: 11px; background: #4a3a12; color: #ffd27a; }
      .chip.done { background: #173a2c; color: #8fe0b8; }
      .chip.lost { background: #4a1f25; color: #ff9aa5; }
      .quote { border-left: 3px solid #ffb300; padding: 2px 0 2px 8px; margin: 0 0 8px; color: #cfc6d3; cursor: pointer;
        display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
      .text { white-space: pre-wrap; overflow-wrap: anywhere; }
      .reply { margin-top: 8px; padding: 8px; border-radius: 6px; background: #17262b; color: #c7e9f0; white-space: pre-wrap; }
      .reply b { display: block; font-size: 11px; margin-bottom: 2px; color: #7fd1e0; }
      .actions { display: flex; gap: 6px; margin-top: 8px; }
      .actions button, .ghost { background: transparent; color: #cfc6d3; border: 1px solid #3a3441; border-radius: 6px; padding: 3px 9px; font-size: 12px; }
      .actions button:hover, .ghost:hover { background: #2c2731; }
      footer { padding: 10px 16px; border-top: 1px solid #3a3441; font-size: 11px; color: #9c91a3; overflow-wrap: anywhere; }
      textarea { width: 100%; min-height: 84px; resize: vertical; background: #141116; color: #eee8e3; border: 1px solid #4d424d;
        border-radius: 6px; padding: 8px; font-size: 13px; line-height: 1.45; }
      textarea:focus { outline: 2px solid #ff570a; outline-offset: 0; }
      .bubble { position: fixed; z-index: 2147483002; background: #ff570a; color: #fff; border: 0; border-radius: 6px;
        padding: 6px 10px; font-size: 13px; font-weight: 600; box-shadow: 0 4px 14px rgba(0,0,0,.45); }
      .composer { position: fixed; z-index: 2147483003; width: min(340px, 92vw); background: #1b181f; color: #eee8e3;
        border: 1px solid #4d424d; border-radius: 10px; padding: 12px; box-shadow: 0 10px 30px rgba(0,0,0,.5); font-size: 13px; }
      .composer .q { color: #b9aebf; margin-bottom: 8px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
      .row { display: flex; gap: 8px; justify-content: flex-end; margin-top: 8px; align-items: center; }
      .row small { flex: 1; color: #9c91a3; font-size: 11px; }
      .primary { background: #ff570a; color: #fff; border: 0; border-radius: 6px; padding: 6px 12px; font-size: 13px; font-weight: 600; }
      [hidden] { display: none !important; }`,
    })
  );
  const toggle = el('button', { class: 'toggle', onclick: () => setPanel(!panelOpen) });
  const list = el('div', { class: 'list' });
  const footer = el('footer');
  const panel = el(
    'aside',
    { class: 'panel', hidden: '', 'aria-label': 'Review comments' },
    el('header', {}, el('h2', { text: 'Review comments' }), el('button', { class: 'ghost', text: 'Close', onclick: () => setPanel(false) })),
    el('div', { class: 'hint', text: 'Select text in the article to comment on it. Option-click a paragraph, table or figure to comment on the whole block.' }),
    list,
    footer
  );
  const bubble = el('button', { class: 'bubble', hidden: '', text: 'Comment', onmousedown: event => event.preventDefault(), onclick: () => openComposer() });
  const composerQuote = el('div', { class: 'q' });
  const composerText = el('textarea', { placeholder: 'What should change here?' });
  const composer = el(
    'div',
    { class: 'composer', hidden: '' },
    composerQuote,
    composerText,
    el('div', { class: 'row' }, el('small', { text: '⌘ Enter to save · Esc to cancel' }), el('button', { class: 'ghost', text: 'Cancel', onclick: () => closeComposer() }), el('button', { class: 'primary', text: 'Save', onclick: () => saveComposer() }))
  );
  composerText.addEventListener('keydown', event => {
    if (event.key === 'Escape') closeComposer();
    if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) saveComposer();
  });
  shadow.append(toggle, panel, bubble, composer);
  document.head.append(
    el('style', {
      text: `::highlight(review-open){background-color:rgba(255,179,0,.34)}
             ::highlight(review-done){background-color:rgba(64,200,140,.18)}
             ::highlight(review-focus){background-color:rgba(255,87,10,.6)}`,
    })
  );
  const mount = () => {
    if (!host.isConnected) document.documentElement.append(host);
  };
  const inOverlay = event => event.composedPath().includes(host);

  function setPanel(open) {
    panelOpen = open;
    panel.hidden = !open;
    // On wide screens the article moves over, so the panel never covers the text being reviewed.
    document.documentElement.style.marginRight = open && innerWidth > 900 ? '380px' : '';
    render();
  }
  function place(node, rect) {
    node.hidden = false;
    const width = node.offsetWidth;
    const height = node.offsetHeight;
    const left = Math.max(8, Math.min(rect.right - width / 2, innerWidth - width - 8));
    const below = rect.bottom + 8;
    node.style.left = `${left}px`;
    node.style.top = `${below + height > innerHeight - 8 ? Math.max(8, rect.top - height - 8) : below}px`;
  }

  // ---- highlights and list -------------------------------------------------
  function refresh() {
    mount();
    const index = textIndex();
    located = new Map();
    const groups = { 'review-open': [], 'review-done': [], 'review-focus': [] };
    for (const comment of comments) {
      const span = locate(comment, index.full);
      if (!span) continue;
      located.set(comment.id, span);
      const range = rangeAt(index, ...span);
      if (range) groups[comment.id === focusId ? 'review-focus' : comment.status === 'done' ? 'review-done' : 'review-open'].push(range);
    }
    if (window.CSS?.highlights && window.Highlight)
      for (const [name, ranges] of Object.entries(groups)) {
        if (ranges.length) CSS.highlights.set(name, new Highlight(...ranges));
        else CSS.highlights.delete(name);
      }
    render();
  }
  function render() {
    const open = comments.filter(c => c.status !== 'done').length;
    toggle.textContent = comments.length ? `Comments · ${open} open` : 'Comments';
    toggle.hidden = panelOpen;
    footer.textContent = storeFile ? `Saved to ${storeFile}` : '';
    if (!panelOpen) return;
    const editing = list.querySelector('textarea');
    if (editing && shadow.activeElement === editing) return; // do not redraw under the cursor
    const ordered = [...comments].sort((a, b) => (located.get(a.id)?.[0] ?? a.pos) - (located.get(b.id)?.[0] ?? b.pos));
    list.replaceChildren(
      ...(ordered.length ? ordered.map(card) : [el('div', { class: 'empty', text: 'No comments on this page yet.' })])
    );
  }
  function card(comment) {
    const found = located.has(comment.id);
    const body = el('div', { class: 'text', text: comment.comment });
    const node = el(
      'div',
      { class: `card ${comment.status === 'done' ? 'done' : ''}`, 'data-id': comment.id },
      el(
        'div',
        { class: 'meta' },
        el('span', { class: 'section', text: comment.section || 'Article' }),
        found ? null : el('span', { class: 'chip lost', text: 'text changed' }),
        el('span', { class: `chip ${comment.status === 'done' ? 'done' : ''}`, text: comment.status === 'done' ? 'done' : 'open' })
      ),
      el('div', { class: 'quote', text: comment.quote || '(no text)', title: 'Show in article', onclick: () => reveal(comment.id) }),
      body,
      comment.reply ? el('div', { class: 'reply' }, el('b', { text: 'Claude' }), comment.reply) : null,
      el(
        'div',
        { class: 'actions' },
        el('button', { text: comment.status === 'done' ? 'Reopen' : 'Mark done', onclick: () => update(comment.id, { status: comment.status === 'done' ? 'open' : 'done' }) }),
        el('button', {
          text: 'Edit',
          onclick: () => {
            const box = el('textarea', {});
            box.value = comment.comment;
            const save = el('button', { class: 'primary', text: 'Save', onclick: () => update(comment.id, { comment: box.value }) });
            body.replaceWith(el('div', {}, box, el('div', { class: 'row' }, el('button', { class: 'ghost', text: 'Cancel', onclick: () => { box.blur(); render(); } }), save)));
            box.addEventListener('keydown', event => {
              if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) save.click();
            });
            box.focus();
          },
        }),
        el('button', { text: 'Delete', onclick: () => confirm('Delete this comment?') && remove(comment.id) })
      )
    );
    return node;
  }
  function reveal(id) {
    const span = located.get(id);
    if (!span) return;
    const range = rangeAt(textIndex(), ...span);
    const rect = range?.getBoundingClientRect();
    if (rect) scrollTo({ top: scrollY + rect.top - innerHeight / 3, behavior: 'smooth' });
    focusId = id;
    refresh();
    setTimeout(() => {
      if (focusId === id) focusId = null;
      refresh();
    }, 1800);
  }
  function showCard(id) {
    setPanel(true);
    const node = list.querySelector(`[data-id="${id}"]`);
    if (!node) return;
    node.scrollIntoView({ block: 'center', behavior: 'smooth' });
    node.classList.add('flash');
    setTimeout(() => node.classList.remove('flash'), 1500);
  }

  // ---- server calls --------------------------------------------------------
  async function pull() {
    try {
      const data = await request('GET', `${API}?path=${encodeURIComponent(location.pathname)}`);
      comments = data.comments;
      storeFile = data.file;
      refresh();
    } catch (error) {
      console.warn('[review]', error);
    }
  }
  async function update(id, change) {
    const saved = await request('PATCH', `${API}/${id}`, change);
    comments = comments.map(c => (c.id === id ? saved : c));
    list.querySelector('textarea')?.blur();
    refresh();
  }
  async function remove(id) {
    await request('DELETE', `${API}/${id}`);
    comments = comments.filter(c => c.id !== id);
    refresh();
  }

  // ---- composing -----------------------------------------------------------
  function closeComposer() {
    composer.hidden = true;
    bubble.hidden = true;
    pending = null;
    composerText.value = '';
  }
  function openComposer() {
    if (!pending) return;
    const index = textIndex();
    const range = rangeAt(index, pending.start, pending.end);
    composerQuote.textContent = index.full.slice(pending.start, pending.end).trim() || '(no text)';
    bubble.hidden = true;
    place(composer, range?.getBoundingClientRect() ?? { right: innerWidth / 2, bottom: innerHeight / 3, top: innerHeight / 3 });
    composerText.focus();
  }
  async function saveComposer() {
    const comment = composerText.value.trim();
    if (!comment || !pending) return;
    const { full } = textIndex();
    const { start, end, kind, node } = pending;
    const saved = await request('POST', API, {
      path: location.pathname,
      title: document.title,
      section: sectionOf(node),
      kind,
      quote: full.slice(start, end),
      prefix: full.slice(Math.max(0, start - 40), start),
      suffix: full.slice(end, end + 40),
      pos: start,
      comment,
    });
    comments.push(saved);
    closeComposer();
    getSelection()?.removeAllRanges();
    refresh();
    showCard(saved.id);
  }

  // ---- page events ---------------------------------------------------------
  function selectionSpan() {
    const selection = getSelection();
    if (!selection || selection.isCollapsed || !selection.rangeCount) return null;
    const range = selection.getRangeAt(0);
    if (!root().contains(range.commonAncestorContainer)) return null;
    const [start, end] = offsetsOf(range);
    if (end - start < 1 || !range.toString().trim()) return null;
    return { start, end: Math.min(end, start + 2000), kind: 'text', node: range.startContainer, rects: range.getClientRects() };
  }
  document.addEventListener('mouseup', event => {
    if (inOverlay(event)) return;
    setTimeout(() => {
      if (!composer.hidden) return;
      const span = selectionSpan();
      if (!span) {
        bubble.hidden = true;
        return;
      }
      pending = span;
      const rects = span.rects;
      place(bubble, rects[rects.length - 1] ?? { right: event.clientX, bottom: event.clientY, top: event.clientY });
    }, 0);
  });
  document.addEventListener(
    'click',
    event => {
      if (inOverlay(event)) return;
      // Option-click: comment on the whole block.
      if (event.altKey) {
        const block = event.target.closest?.('p, li, h1, h2, h3, h4, blockquote, table, figure, [data-visualization-kind]');
        if (!block || !root().contains(block)) return;
        event.preventDefault();
        event.stopPropagation();
        const range = document.createRange();
        range.selectNodeContents(block);
        const [start, end] = offsetsOf(range);
        pending = { start, end: Math.min(end, start + 300), kind: 'block', node: block };
        openComposer();
        return;
      }
      // A plain click on highlighted text opens its comment.
      if (!getSelection()?.isCollapsed) return;
      const caret = document.caretRangeFromPoint?.(event.clientX, event.clientY);
      if (!caret || !root().contains(caret.startContainer)) return;
      const [at] = offsetsOf(caret);
      const hit = comments.find(c => {
        const span = located.get(c.id);
        return span && at >= span[0] && at < span[1];
      });
      if (hit) showCard(hit.id);
    },
    true
  );
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !composer.hidden) closeComposer();
  });

  // The article re-renders (figures load late, edits hot-reload), so anchors are recomputed when it changes.
  let timer;
  const schedule = () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      if (location.pathname !== lastPath) {
        lastPath = location.pathname;
        closeComposer();
        pull();
      } else refresh();
    }, 400);
  };
  const start = () => {
    mount();
    new MutationObserver(records => {
      if (records.every(record => host.contains(record.target))) return;
      schedule();
    }).observe(document.body, { childList: true, subtree: true, characterData: true });
    addEventListener('popstate', schedule);
    // Picks up replies and status changes written to the file by Claude.
    setInterval(() => {
      if (document.visibilityState === 'visible' && composer.hidden && !list.querySelector('textarea')) pull();
    }, 5000);
    pull();
  };
  if (document.readyState === 'complete') setTimeout(start, 300);
  else addEventListener('load', () => setTimeout(start, 300));
})();
