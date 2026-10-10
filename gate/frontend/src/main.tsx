import { useCallback, useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Button, Chip, SearchField, Spinner } from '@heroui/react';
import './workspace.css';

type Document = { id: number; purchase_id: number; filename: string; office: string; procedure: string; decision: string; current: boolean; created_at: number };
type Workspace = { counts: { total: number; published: number; review: number; blocked: number; stale: number }; files: Document[] };
type Filter = 'all' | 'review' | 'private' | 'published' | 'stale';
const filters: [Filter, string][] = [['all', 'All'], ['review', 'Review'], ['private', 'Private'], ['published', 'Published'], ['stale', 'Recheck']];
const dateFormat = new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
const available = (file: Document) => file.current && ['public', 'approved', 'cleaned'].includes(file.decision);
function status(file: Document) {
  if (!file.current) return { text: 'Recheck', tone: 'recheck' };
  if (file.decision === 'hold') return { text: 'Review', tone: 'review' };
  if (available(file)) return { text: file.decision === 'cleaned' ? 'Published, cleaned' : 'Published', tone: 'published' };
  return { text: 'Private', tone: 'private' };
}
function initialWorkspace(): Workspace | null {
  try { const value = JSON.parse(document.getElementById('workspace-data')?.textContent ?? 'null'); return value && Array.isArray(value.files) && value.counts ? value : null; } catch { return null; }
}
function WorkspaceApp() {
  const [data, setData] = useState<Workspace | null>(initialWorkspace);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<Filter>('all');
  const [query, setQuery] = useState('');
  const [sort, setSort] = useState('newest');
  const load = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    try {
      const response = await fetch('/api/workspace', { credentials: 'same-origin', cache: 'no-store', signal: signal ?? AbortSignal.timeout(10000) });
      if (!response.ok) throw new Error(response.status === 401 ? 'Session expired. Reload to sign in.' : 'Documents could not be loaded.');
      const payload = await response.json();
      if (!Array.isArray(payload.files) || !payload.counts) throw new Error('Documents could not be loaded.');
      setData(payload); setError('');
    } catch (err) {
      if (!(err instanceof DOMException && err.name === 'AbortError')) setError(err instanceof Error ? err.message : 'Connection unavailable.');
    } finally { setLoading(false); }
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(new DOMException('Request timed out.', 'TimeoutError')), 10000);
    void load(controller.signal);
    return () => { window.clearTimeout(timeout); controller.abort(); };
  }, [load]);
  useEffect(() => {
    const refresh = () => { void load(); };
    window.addEventListener('gate:workspace-changed', refresh);
    return () => window.removeEventListener('gate:workspace-changed', refresh);
  }, [load]);
  const documents = useMemo(() => {
    const term = query.trim().toLocaleLowerCase();
    const rows = (data?.files ?? []).filter(file =>
      (filter === 'all' || (filter === 'review' && file.decision === 'hold') || (filter === 'private' && file.decision === 'withheld') || (filter === 'published' && available(file)) || (filter === 'stale' && !file.current)) &&
      (!term || `${file.filename} ${file.office} ${file.procedure}`.toLocaleLowerCase().includes(term))
    );
    return [...rows].sort((a, b) => sort === 'name' ? a.filename.localeCompare(b.filename) : sort === 'oldest' ? a.created_at - b.created_at : b.created_at - a.created_at);
  }, [data, filter, query, sort]);
  return <section className="hero-workspace" aria-label="Document workspace">
    <header className="workspace-heading"><h1>Documents</h1><div className="workspace-actions"><Button size="sm" onPress={() => window.location.assign('/office')}>Upload PDF</Button></div></header>
    <div className="workspace-totals" aria-label="Document totals">{[
      ['Total', data?.counts.total], ['Review', data?.counts.review], ['Private', data?.counts.blocked], ['Published', data?.counts.published]
    ].map(([label, value]) => <div key={label}><span>{label}</span><strong>{value ?? '—'}</strong></div>)}</div>
    <div className="workspace-toolbar"><div className="workspace-filters" role="group" aria-label="Filter documents">{filters.map(([id, label]) => <Button key={id} size="sm" variant="ghost" aria-pressed={filter === id} className={filter === id ? 'filter-selected' : ''} onPress={() => setFilter(id)}>{label}{id === 'stale' && !!data?.counts.stale && <span className="filter-count">{data.counts.stale}</span>}</Button>)}</div><div className="workspace-search"><SearchField aria-label="Search documents" value={query} onChange={setQuery} variant="secondary"><SearchField.Group><SearchField.SearchIcon /><SearchField.Input placeholder="Search files or offices" /><SearchField.ClearButton /></SearchField.Group></SearchField></div></div>
    {error && <div className="workspace-error" role="alert"><span>{error}</span><Button size="sm" variant="secondary" isDisabled={loading} onPress={() => { void load(); }}>Retry</Button></div>}
    <div className="workspace-table-wrap" aria-busy={loading}><table className="workspace-table"><thead><tr><th scope="col">Document</th><th scope="col">Status</th><th scope="col" className="workspace-office">Office</th><th scope="col" className="workspace-date">Added</th><th scope="col" className="workspace-row-action"><span className="sr-only">Action</span></th></tr></thead><tbody>
      {!data && loading ? <tr><td colSpan={5}><div className="workspace-empty" role="status"><Spinner size="sm" /><span>Loading documents</span></div></td></tr> : documents.length ? documents.map(file => { const state = status(file); return <tr key={file.id}><td><a className="workspace-file" href={`/inspect/${file.id}`}>{file.filename}</a><span className="workspace-reference">{file.procedure}</span></td><td><Chip size="sm" variant="soft" className={`workspace-chip tone-${state.tone}`}>{state.text}</Chip></td><td className="workspace-office">{file.office.replace(/^UGL /, '')}</td><td className="workspace-date">{dateFormat.format(new Date(file.created_at * 1000))}</td><td className="workspace-row-action"><a href={file.current ? `/inspect/${file.id}` : '/learning'}>{file.current ? 'Open' : 'Recheck'}<span aria-hidden="true">↗</span><span className="sr-only"> {file.filename}</span></a></td></tr>; }) : <tr><td colSpan={5}><div className="workspace-empty"><span>{data?.counts.total ? 'No matching documents' : 'No documents yet'}</span>{data?.counts.total ? <Button variant="secondary" size="sm" onPress={() => { setQuery(''); setFilter('all'); }}>Clear filters</Button> : <Button size="sm" onPress={() => window.location.assign('/office')}>Upload PDF</Button>}</div></td></tr>}
    </tbody></table></div>
    <footer className="workspace-footer"><span>{data ? `${documents.length} shown · ${data.counts.total} total${data.counts.total > data.files.length ? ' · latest 100 loaded' : ''}` : '—'}</span><div><label htmlFor="workspace-sort" className="sr-only">Sort documents</label><select id="workspace-sort" value={sort} onChange={event => setSort(event.target.value)}><option value="newest">Newest first</option><option value="oldest">Oldest first</option><option value="name">File name</option></select><Button variant="ghost" size="sm" isDisabled={loading} onPress={() => { void load(); }}>{loading ? 'Refreshing…' : 'Refresh'}</Button></div></footer>
  </section>;
}
const root = document.getElementById('document-workspace');
if (root) createRoot(root).render(<WorkspaceApp />);
