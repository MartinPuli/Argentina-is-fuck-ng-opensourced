(() => {
  const form = document.querySelector('[data-pdf-intake]');
  if (!form) return;
  const input = form.querySelector('input[type=file]');
  const message = form.querySelector('[data-intake-message]');
  const selection = form.querySelector('[data-intake-files]');
  const retry = form.querySelector('[data-intake-retry]');
  let files = [];
  let busy = false;
  let depth = 0;
  const showError = text => {
    message.hidden = false;
    message.className = 'form-message error';
    message.setAttribute('role', 'alert');
    message.textContent = text;
  };
  async function submit(selected) {
    if (busy || !selected.length) return;
    files = Array.from(selected);
    selection.textContent = files.map(file => file.name).join(' · ');
    retry.hidden = true;
    if (files.length > 8 || files.some(file => !/\.pdf$/i.test(file.name) || !file.size)) {
      showError('Choose 1 to 8 non-empty PDF files.'); return;
    }
    if (files.some(file => file.size > 10 * 1024 * 1024) || files.reduce((n, file) => n + file.size, 0) > 25 * 1024 * 1024) {
      showError('Use PDFs under 10 MB each and 25 MB in total.'); return;
    }
    busy = true;
    input.disabled = true;
    form.setAttribute('aria-busy', 'true');
    message.hidden = false;
    message.className = 'form-message loading';
    message.setAttribute('role', 'status');
    message.textContent = 'Uploading PDFs…';
    const data = new FormData();
    files.forEach(file => data.append('files', file));
    try {
      const response = await fetch(form.getAttribute('action'), {
        method: 'POST', body: data, credentials: 'same-origin', headers: {Accept: 'application/json'},
      });
      if (!response.ok) {
        let text = response.status === 401 ? 'Session expired. Reload to sign in.' : 'Upload failed. Your files were not accepted.';
        try { const body = await response.json(); if (typeof body.detail === 'string') text = body.detail; } catch (_) {}
        throw new Error(text);
      }
      const body = await response.json();
      if (response.status !== 202 || body.location !== '/live') throw new Error('Upload could not be confirmed. Check Activity before retrying.');
      message.textContent = 'Files accepted. Opening analysis…';
      window.location.assign('/live');
    } catch (error) {
      showError(error.message || 'Connection lost. Check Activity before retrying to avoid uploading twice.');
      retry.hidden = false;
      busy = false;
      input.disabled = false;
      form.removeAttribute('aria-busy');
    }
  }
  input.addEventListener('change', () => submit(input.files));
  form.addEventListener('submit', event => { event.preventDefault(); submit(input.files); });
  retry.addEventListener('click', () => submit(files));
  const hasFiles = event => Array.from(event.dataTransfer?.types || []).includes('Files');
  document.addEventListener('dragenter', event => {
    if (!hasFiles(event)) return;
    event.preventDefault(); depth++;
    if (!busy) document.documentElement.classList.add('pdf-drag');
  });
  document.addEventListener('dragover', event => {
    if (hasFiles(event)) { event.preventDefault(); event.dataTransfer.dropEffect = busy ? 'none' : 'copy'; }
  });
  document.addEventListener('dragleave', event => {
    if (!hasFiles(event)) return;
    depth = Math.max(0, depth - 1);
    if (!depth) document.documentElement.classList.remove('pdf-drag');
  });
  document.addEventListener('drop', event => {
    if (!hasFiles(event)) return;
    event.preventDefault(); depth = 0; document.documentElement.classList.remove('pdf-drag');
    if (!busy) submit(event.dataTransfer.files);
  });
  window.addEventListener('dragend', () => { depth = 0; document.documentElement.classList.remove('pdf-drag'); });
})();
