(() => {
  const upload = document.querySelector('#files');
  if (upload) upload.addEventListener('change', () => {
    const files = Array.from(upload.files || []);
    document.querySelector('#file-selection').textContent = files.length ? files.map(f => f.name).join(' · ') : 'No files selected';
  });
  document.querySelectorAll('[data-filter]').forEach(input => input.addEventListener('input', () => {
    const term = input.value.toLocaleLowerCase().trim();
    const items = Array.from(document.querySelectorAll('[data-filter-item="' + input.dataset.filter + '"]'));
    items.forEach(item => { item.hidden = !item.textContent.toLocaleLowerCase().includes(term); });
    const empty = document.querySelector('.filter-empty');
    if (empty) empty.hidden = !items.length || items.some(item => !item.hidden);
  }));
  document.querySelectorAll('form[data-async]').forEach(form => form.addEventListener('submit', async event => {
    event.preventDefault();
    if (form.dataset.busy === 'true') return;
    const button = event.submitter;
    if (button?.dataset.confirm && !window.confirm(button.dataset.confirm)) return;
    const message = form.querySelector('.form-message');
    const controls = Array.from(form.querySelectorAll('button'));
    const data = new FormData(form);
    if (button?.name) data.append(button.name, button.value);
    const oldText = button?.textContent;
    form.dataset.busy = 'true';
    form.setAttribute('aria-busy', 'true');
    controls.forEach(control => { control.disabled = true; });
    if (button) button.textContent = 'Working…';
    message.hidden = false;
    message.className = 'form-message loading';
    message.textContent = form.dataset.loading || 'Saving…';
    try {
      // A control named "action" shadows HTMLFormElement.action.
      const response = await fetch(form.getAttribute('action'), { method: 'POST', body: data, credentials: 'same-origin' });
      if (!response.ok) {
        let text = response.status === 401 ? 'Sign in through the office workspace, then try again.' : 'The request could not be completed. Please try again.';
        try { const body = await response.json(); if (typeof body.detail === 'string') text = body.detail; } catch (_) { /* Keep the readable fallback for non-JSON errors. */ }
        if (response.status === 503) text = 'Staff access is not configured. Set the staff credentials on the server before using the workspace.';
        throw new Error(text);
      }
      window.location.assign(response.url);
    } catch (error) {
      message.className = 'form-message error';
      message.textContent = error.message || 'Unable to reach the server. Your decision was not confirmed. Check the connection and try again.';
      message.setAttribute('role', 'alert');
      form.dataset.busy = 'false'; form.removeAttribute('aria-busy');
      controls.forEach(control => { control.disabled = false; });
      if (button) button.textContent = oldText;
    }
  }));
})();
(() => {
  // Review count next to the Review link. One request per page load, no polling.
  const count = document.querySelector('[data-review-count]');
  if (count) fetch('/api/activity', { credentials: 'same-origin', headers: { Accept: 'application/json' } })
    .then(response => response.ok ? response.json() : null)
    .then(body => {
      const waiting = body?.counts?.waiting || 0;
      if (!waiting) return;
      count.textContent = waiting > 99 ? '99+' : String(waiting);
      count.setAttribute('aria-label', waiting + ' waiting');
      count.hidden = false;
    })
    .catch(() => { /* The count is a hint; the Review page shows the real list. */ });
})();
