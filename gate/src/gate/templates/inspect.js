(() => {
  const initial = JSON.parse(document.getElementById('inspection-data').textContent);
  const byId = id => document.getElementById('ix-' + id);
  const node = (tag, text, className) => {
    const item = document.createElement(tag);
    if (text !== undefined) item.textContent = text;
    if (className) item.className = className;
    return item;
  };
  const external = (title, url, className) => {
    try {
      const parsed = new URL(url);
      if (parsed.protocol !== 'https:' || parsed.username || parsed.password) return node('span', title, className);
      const item = node('a', title, className);
      item.href = parsed.href; item.target = '_blank'; item.rel = 'noopener noreferrer';
      return item;
    } catch (_) { return node('span', title, className); }
  };
  const labels = {public:'Published', approved:'Reviewer approved', cleaned:'Published, cleaned', hold:'Needs review', withheld:'Kept internal'};
  let number = 1, total = initial.page.total, timer, controller, stopped = false;
  let latest = initial, lastRender = '', sensoRunning = false;
  const image = (side, available, digest, empty, copy = side === 'before' ? 'original' : 'cleaned') => {
    const img = byId(side), message = byId(side + '-message');
    if (!available) {
      img.hidden = true; img.removeAttribute('src'); delete img.dataset.key;
      message.textContent = empty; message.hidden = false; return;
    }
    const key = copy + ':' + number + ':' + digest;
    if (img.dataset.key === key) return;
    img.dataset.key = key; img.hidden = true; message.hidden = false;
    message.textContent = 'Loading page…';
    img.onload = () => { img.hidden = false; message.hidden = true; };
    img.onerror = () => {
      img.hidden = true; delete img.dataset.key;
      message.textContent = 'Preview unavailable. Use Open PDF or Refresh to retry.'; message.hidden = false;
    };
    img.src = '/internal/preview/' + initial.id + '/' + number + '?copy=' + copy + '&v=' + encodeURIComponent(digest);
  };
  function render(data) {
    latest = data; total = data.page.total;
    byId('page').textContent = 'Page ' + number + ' of ' + total;
    byId('previous').disabled = number <= 1; byId('next').disabled = number >= total;
    const signature = JSON.stringify(data);
    if (signature === lastRender) return;
    lastRender = signature;
    byId('state').textContent = data.processing ? 'Processing · original stays internal' : !data.current ? 'Recheck required · public access paused' : labels[data.decision] || 'Not cleared';
    const publicLink = byId('public'); publicLink.hidden = !data.published;
    publicLink.href = '/public/file/' + data.id;
    byId('live-dot').classList.toggle('running', data.processing);
    byId('after-label').textContent = data.has_cleaned ? data.published ? 'Published copy' : 'Cleaned preview · internal' : data.published ? 'Published original' : 'Cleaned copy';
    byId('clean-link').hidden = !(data.has_cleaned || data.published);
    byId('clean-link').href = data.has_cleaned ? '/internal/clean/' + data.id : '/public/file/' + data.id;
    for (const side of ['before', 'after']) byId(side + '-paper').style.aspectRatio = data.page.width + '/' + data.page.height;
    image('before', true, data.original_digest, 'Original unavailable');
    image('after', data.page.cleaned_page || (!data.has_cleaned && data.published), data.cleaned_digest || data.original_digest,
          data.processing ? 'Agents are preparing the result. The original stays internal.' : data.has_cleaned ? 'No corresponding page in the cleaned copy.' : 'No cleaned copy was produced. The original stays internal.', data.has_cleaned ? 'cleaned' : 'original');
    byId('overlay').replaceChildren(...data.page.regions.map(rect => {
      const region = node('span', undefined, 'ix-region');
      ['left','top','width','height'].forEach((field, index) => region.style[field] = (rect[index] * 100) + '%');
      return region;
    }));
    byId('overlay').hidden = !byId('highlight').checked;
    byId('comparison-note').textContent = data.has_cleaned
      ? data.page.regions.length + ' changed text lines on this page. Overlay compares extracted words; images and annotations are not covered.'
      : data.published ? 'The original was published unchanged.' : 'A cleaned preview appears only when a copy exists.';
    byId('removal-count').textContent = data.manifest.length ? data.manifest.length + ' total' : '';
    byId('manifest').replaceChildren(...(data.manifest.length ? data.manifest.map(change => {
      const item = node('li'); item.append(node('span', change.category), node('small', change.masked + ' · p.' + change.page)); return item;
    }) : [node('li', data.processing ? 'Awaiting removal manifest' : 'No removals recorded')]));
    byId('steps').replaceChildren(...data.steps.map(step => {
      const states = new Set(['waiting','running','done','skipped','error']);
      const state = states.has(step.status) ? step.status : 'waiting';
      const item = node('li', undefined, 'ix-step ' + state), detail = node('span', step.name);
      detail.append(node('small', step.agent));
      const duration = Number.isFinite(step.duration_ms) ? (step.duration_ms / 1000).toFixed(1) + 's' : '';
      item.append(detail, node('span', state + (duration ? ' · ' + duration : ''))); return item;
    }));
    byId('no-trace').hidden = data.trace_available;
    byId('verdict').textContent = data.review ? 'Reviewer ' + data.review + (data.processing ? ' · checks still running' : '') : 'No reviewer verdict recorded';
    byId('policies').replaceChildren(...(data.policies.length ? data.policies.map(policy => {
      const item = node('p', policy.title, 'ix-policy'); item.append(node('small', policy.source)); return item;
    }) : [node('p', 'No finding-linked guidelines recorded.', 'ix-empty')]));
    renderSenso(data);
    byId('sources').replaceChildren(...data.sources.map(source => {
      const item = external(source.title + ' ↗', source.url, 'ix-source');
      item.append(node('small', source.locator)); return item;
    }));
  }
  function renderSenso(data) {
    const receipt = data.citation, state = data.senso || {};
    byId('senso-run').disabled = sensoRunning || !state.configured || !data.policies.length;
    byId('senso-run').textContent = sensoRunning ? 'Looking up…' : receipt?.status === 'cited' ? 'Run again' : 'Run lookup';
    byId('senso-connection').textContent = !state.configured ? 'Not connected on this server.'
      : state.ready ? 'Reviewed guideline pack · synced' : 'Server key configured · pack is verified during lookup';
    byId('senso-query-label').textContent = receipt?.query && receipt.status === 'cited' ? 'Query sent to Senso' : 'Next lookup query';
    byId('senso-query').textContent = receipt?.query || state.query || 'No finding-linked query for this document.';
    if (!sensoRunning) {
      byId('senso-state').className = 'ix-search-state';
      byId('senso-state').textContent = receipt?.status === 'cited'
        ? receipt.passages + (receipt.passages === 1 ? ' passage' : ' passages') + ' retrieved · ' + receipt.latency_ms + ' ms'
        : receipt?.reason || (data.policies.length ? 'No lookup recorded.' : 'No finding-linked guideline for this document.');
    }
    const content = byId('senso');
    if (receipt?.status !== 'cited') {
      content.replaceChildren(node('strong', 'No provider citation'), node('p', 'Local guidelines remain available in the Guidelines tab.'));
      return;
    }
    const passages = receipt.context_passages?.length ? receipt.context_passages : [{text:receipt.excerpt}];
    content.replaceChildren(...passages.map((passage, index) => {
      const block = node('article', undefined, 'ix-passage');
      block.append(node('strong', 'Passage ' + (index + 1)), node('p', passage.text));
      if (passage.version_id) block.append(node('p', 'Version ' + passage.version_id, 'ix-passage-version'));
      return block;
    }));
    const details = node('details', undefined, 'ix-receipt');
    details.append(node('summary', 'Retrieval receipt'));
    for (const [label, value] of [['Content',receipt.content_id],['Version',receipt.version_id],
      ['Guideline digest',receipt.guideline_digest],['Retrieved',receipt.retrieved_at ? new Date(receipt.retrieved_at * 1000).toLocaleString('en') : 'Not retained']]) {
      details.append(node('p', label + ': ' + value));
    }
    content.append(details);
  }
  async function lookupSenso() {
    if (byId('senso-run').disabled) return;
    sensoRunning = true; renderSenso(latest);
    byId('senso').setAttribute('aria-busy', 'true');
    byId('senso-state').className = 'ix-search-state';
    byId('senso-state').textContent = 'Verifying the guideline pack and retrieving cited passages…';
    try {
      const response = await fetch('/api/inspect/' + initial.id + '/senso', {
        method:'POST', credentials:'same-origin', cache:'no-store', headers:{Accept:'application/json'},
        signal:AbortSignal.timeout(90000),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.citation?.reason || data.detail || 'Senso lookup unavailable. Retry Run lookup.');
      if (data.citation?.status !== 'cited' || !data.senso) throw new Error('Senso returned no citation. Retry Run lookup.');
      sensoRunning = false;
      latest = {...latest, citation:data.citation, senso:data.senso};
      lastRender = ''; render(latest);
    } catch (error) {
      byId('senso-state').textContent = error.name === 'TimeoutError' ? 'Lookup timed out. Retry Run lookup.' : error.message;
      byId('senso-state').className = 'ix-search-state error';
    } finally {
      sensoRunning = false; byId('senso').setAttribute('aria-busy', 'false');
      byId('senso-run').disabled = !latest.senso?.configured || !latest.policies.length;
      byId('senso-run').textContent = latest.citation?.status === 'cited' ? 'Run again' : 'Run lookup';
    }
  }
  async function load() {
    controller?.abort(); controller = new AbortController();
    const request = controller, page = number;
    const timeout = setTimeout(() => request.abort(), 10000);
    byId('refresh').disabled = true;
    try {
      const response = await fetch('/api/inspect/' + initial.id + '?page=' + page, {credentials:'same-origin', cache:'no-store', signal:request.signal});
      if (!response.ok) throw new Error(response.status === 401 ? 'Session expired. Reload to sign in.' : 'Document could not be refreshed. Try Refresh.');
      const data = await response.json();
      if (request !== controller || page !== number) return;
      if (!data.page || !Array.isArray(data.steps)) throw new Error('Document response was incomplete. Try Refresh.');
      render(data); byId('error').hidden = true;
    } catch (error) {
      if (request !== controller) return;
      byId('error').textContent = error.name === 'AbortError' ? 'Refresh timed out. Try Refresh.' : error.message;
      byId('error').hidden = false;
    } finally {
      clearTimeout(timeout);
      if (request === controller) byId('refresh').disabled = false;
    }
  }
  async function poll() {
    if (stopped) return;
    if (!document.hidden) await load();
    timer = setTimeout(poll, latest.processing ? 2000 : 10000);
  }
  byId('previous').addEventListener('click', () => { if (number > 1) { number--; void load(); } });
  byId('next').addEventListener('click', () => { if (number < total) { number++; void load(); } });
  byId('refresh').addEventListener('click', () => { lastRender = ''; void load(); });
  byId('highlight').addEventListener('change', () => { byId('overlay').hidden = !byId('highlight').checked; });
  function renderResearch(data, fresh = false) {
    byId('query').textContent = data.query;
    byId('leads').replaceChildren(...data.leads.map(lead => {
      const item = node('article', undefined, 'ix-lead');
      item.append(external(lead.title + ' ↗', lead.url));
      const date = new Date(lead.published_at);
      item.append(node('p', lead.publisher + ' · ' + (Number.isNaN(date.valueOf()) ? 'Date unavailable' : date.toLocaleDateString('en', {month:'short',day:'numeric',year:'numeric'}))));
      const action = node('a', 'Review source →', 'ix-propose'); action.href = '/learning?lead=' + encodeURIComponent(lead.id) + '#source-form';
      item.append(action); return item;
    }));
    byId('search-state').textContent = (fresh ? 'Found ' : 'Saved: ') + data.leads.length + ' reporting leads. No rules changed.';
    byId('search-state').className = 'ix-search-state';
  }
  async function research(search = false) {
    const button = byId('search'); if (button.disabled) return;
    button.disabled = true; byId('leads').setAttribute('aria-busy', 'true');
    byId('search-state').textContent = search ? 'Searching Google News…' : 'Loading saved reporting…';
    byId('search-state').className = 'ix-search-state';
    try {
      const response = await fetch(search ? '/learning/discover' : '/api/research', {
        method: search ? 'POST' : 'GET', credentials:'same-origin', cache:'no-store',
        headers:{Accept:'application/json'}, signal:AbortSignal.timeout(20000),
      });
      if (!response.ok) throw new Error(response.status === 401 ? 'Session expired. Reload to sign in.' : 'Reporting search unavailable. Saved results are unchanged; retry Search reporting.');
      const data = await response.json();
      if (!Array.isArray(data.leads) || typeof data.query !== 'string') throw new Error('Reporting response was incomplete. Retry Search reporting.');
      renderResearch(data, search);
    } catch (error) {
      byId('search-state').textContent = error.name === 'TimeoutError' ? 'Search timed out. Retry Search reporting.' : error.message;
      byId('search-state').className = 'ix-search-state error';
    } finally { button.disabled = false; byId('leads').setAttribute('aria-busy', 'false'); }
  }
  const tabs = Array.from(document.querySelectorAll('[data-ix-tab]'));
  function selectTab(tab, focus = false) {
    for (const candidate of tabs) {
      const selected = candidate === tab;
      candidate.setAttribute('aria-selected', String(selected)); candidate.tabIndex = selected ? 0 : -1;
      byId('panel-' + candidate.dataset.ixTab).hidden = !selected;
    }
    if (focus) tab.focus();
  }
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => selectTab(tab));
    tab.addEventListener('keydown', event => {
      const direction = event.key === 'ArrowRight' ? 1 : event.key === 'ArrowLeft' ? -1 : 0;
      if (direction || event.key === 'Home' || event.key === 'End') {
        event.preventDefault();
        selectTab(tabs[event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (index + direction + tabs.length) % tabs.length], true);
      }
    });
  });
  function selectLinkedTab() {
    const linkedTab = tabs.find(tab => '#' + tab.dataset.ixTab === location.hash);
    if (linkedTab) selectTab(linkedTab);
  }
  selectLinkedTab(); window.addEventListener('hashchange', selectLinkedTab);
  byId('search').addEventListener('click', () => void research(true));
  byId('senso-run').addEventListener('click', () => void lookupSenso());
  window.addEventListener('pagehide', () => { stopped = true; clearTimeout(timer); controller?.abort(); });
  render(initial); void research(); timer = setTimeout(poll, 2000);
})();
