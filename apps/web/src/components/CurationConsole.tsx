import React, { useEffect, useState } from 'react';
import {
  bulkImportCsv,
  createStandardRow,
  createVagueTerm,
  deleteVagueTerm,
  fetchAuditLogs,
  fetchRulesCatalog,
  fetchStaleRows,
  fetchUnverifiedQueue,
  fetchVagueTerms,
  reverifyStandardRow,
  verifyStandardRow,
} from '../services/api';
import {
  AuditLogRecord,
  BulkImportReport,
  RuleItem,
  StandardRow,
  VagueTerm,
} from '../types';

type CurationTab = 'queue' | 'add' | 'import' | 'stale' | 'rules' | 'logs';

export const CurationConsole: React.FC = () => {
  const [activeTab, setActiveTab] = useState<CurationTab>('queue');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Verification Queue
  const [unverifiedRows, setUnverifiedRows] = useState<StandardRow[]>([]);

  // Add Standard Row Form
  const [newIsNumber, setNewIsNumber] = useState('');
  const [newTitle, setNewTitle] = useState('');
  const [newYear, setNewYear] = useState('');
  const [newStatus, setNewStatus] = useState('Active');
  const [newCatalogueUrl, setNewCatalogueUrl] = useState('');
  const [newEvidenceRef, setNewEvidenceRef] = useState('');
  const [workingNote, setWorkingNote] = useState('');

  // Bulk Import
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importReport, setImportReport] = useState<BulkImportReport | null>(null);

  // Stale Rows
  const [staleRows, setStaleRows] = useState<StandardRow[]>([]);
  const [reverifyEvidence, setReverifyEvidence] = useState<{ [id: number]: string }>({});

  // Vague Terms & Rules
  const [vagueTerms, setVagueTerms] = useState<VagueTerm[]>([]);
  const [rulesCatalog, setRulesCatalog] = useState<RuleItem[]>([]);
  const [newVaguePhrase, setNewVaguePhrase] = useState('');
  const [newVagueLang, setNewVagueLang] = useState('en');
  const [newVagueExp, setNewVagueExp] = useState('');

  // Audit Logs
  const [auditLogs, setAuditLogs] = useState<AuditLogRecord[]>([]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      if (activeTab === 'queue') {
        const rows = await fetchUnverifiedQueue();
        setUnverifiedRows(rows);
      } else if (activeTab === 'stale') {
        const rows = await fetchStaleRows(180);
        setStaleRows(rows);
      } else if (activeTab === 'rules') {
        const [terms, rules] = await Promise.all([
          fetchVagueTerms(),
          fetchRulesCatalog(),
        ]);
        setVagueTerms(terms);
        setRulesCatalog(rules);
      } else if (activeTab === 'logs') {
        const logs = await fetchAuditLogs(100);
        setAuditLogs(logs);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load curation data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadData();
  }, [activeTab]);

  const handleVerifyRow = async (id: number) => {
    setError(null);
    try {
      await verifyStandardRow(id);
      setSuccessMsg(`Standard #${id} signed off by independent second verifier.`);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Verification failed');
    }
  };

  const handleReverifyRow = async (id: number) => {
    const evidence = reverifyEvidence[id] || 'Reaffirmed via BIS Gazette portal';
    setError(null);
    try {
      await reverifyStandardRow(id, evidence);
      setSuccessMsg(`Standard #${id} re-verified successfully.`);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Re-verification failed');
    }
  };

  const handleCreateRow = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (!newCatalogueUrl.startsWith('https://')) {
      setError('Catalogue URL must begin with https://');
      return;
    }
    if (!newEvidenceRef.trim()) {
      setError('Evidence reference is mandatory');
      return;
    }

    try {
      const created = await createStandardRow({
        is_number: newIsNumber.trim(),
        title: newTitle.trim(),
        publication_year: newYear ? parseInt(newYear, 10) : null,
        status: newStatus,
        catalogue_url: newCatalogueUrl.trim(),
        evidence_ref: newEvidenceRef.trim(),
      });
      setSuccessMsg(
        `Standard ${created.is_number} created and queued for second-person verification.`
      );
      setNewIsNumber('');
      setNewTitle('');
      setNewYear('');
      setNewCatalogueUrl('');
      setNewEvidenceRef('');
      setWorkingNote('');
      setActiveTab('queue');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Creation failed');
    }
  };

  const handleBulkImport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!importFile) {
      setError('Please select a CSV file to import.');
      return;
    }
    setError(null);
    setSuccessMsg(null);
    try {
      const rep = await bulkImportCsv(importFile);
      setImportReport(rep);
      setSuccessMsg(
        `Import completed: ${rep.imported_count} imported, ${rep.rejected_count} rejected.`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bulk import failed');
    }
  };

  const handleCreateVague = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newVaguePhrase.trim() || !newVagueExp.trim()) return;
    try {
      await createVagueTerm({
        phrase: newVaguePhrase.trim(),
        language: newVagueLang,
        explanation: newVagueExp.trim(),
      });
      setSuccessMsg(`Vague term '${newVaguePhrase}' added.`);
      setNewVaguePhrase('');
      setNewVagueExp('');
      const updated = await fetchVagueTerms();
      setVagueTerms(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add vague term');
    }
  };

  const handleDeleteVague = async (id: number) => {
    try {
      await deleteVagueTerm(id);
      setVagueTerms((prev) => prev.filter((t) => t.id !== id));
      setSuccessMsg('Vague term removed.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete term');
    }
  };

  return (
    <div className="workspace-container">
      {/* Header Banner */}
      <section className="input-card card" style={{ marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2>Data Curation & Quality Console</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', margin: '4px 0 0' }}>
              Maintain verified Indian Standards catalogue rows, enforce two-person verification, and audit provenance.
            </p>
          </div>
          <button onClick={loadData} className="btn btn-secondary" style={{ fontSize: '0.85rem' }}>
            Refresh
          </button>
        </div>

        {/* Sub-tabs navigation */}
        <div className="filter-pills" style={{ marginTop: '1rem' }}>
          <button
            type="button"
            className={`filter-pill ${activeTab === 'queue' ? 'active' : ''}`}
            onClick={() => setActiveTab('queue')}
          >
            Verification Queue {unverifiedRows.length > 0 && `(${unverifiedRows.length})`}
          </button>
          <button
            type="button"
            className={`filter-pill ${activeTab === 'add' ? 'active' : ''}`}
            onClick={() => setActiveTab('add')}
          >
            New Row Editor
          </button>
          <button
            type="button"
            className={`filter-pill ${activeTab === 'import' ? 'active' : ''}`}
            onClick={() => setActiveTab('import')}
          >
            Bulk CSV Import
          </button>
          <button
            type="button"
            className={`filter-pill ${activeTab === 'stale' ? 'active' : ''}`}
            onClick={() => setActiveTab('stale')}
          >
            Staleness Dashboard
          </button>
          <button
            type="button"
            className={`filter-pill ${activeTab === 'rules' ? 'active' : ''}`}
            onClick={() => setActiveTab('rules')}
          >
            Rules & Vague Terms
          </button>
          <button
            type="button"
            className={`filter-pill ${activeTab === 'logs' ? 'active' : ''}`}
            onClick={() => setActiveTab('logs')}
          >
            Audit Log Trail
          </button>
        </div>
      </section>

      {/* Alerts */}
      {error && (
        <div
          style={{
            background: '#fee2e2',
            border: '1px solid #f87171',
            color: '#b91c1c',
            padding: '0.75rem 1rem',
            borderRadius: '6px',
            marginBottom: '1rem',
            fontSize: '0.875rem',
          }}
        >
          {error}
        </div>
      )}
      {successMsg && (
        <div
          style={{
            background: '#dcfce7',
            border: '1px solid #4ade80',
            color: '#15803d',
            padding: '0.75rem 1rem',
            borderRadius: '6px',
            marginBottom: '1rem',
            fontSize: '0.875rem',
          }}
        >
          {successMsg}
        </div>
      )}

      {/* Tab: Verification Queue */}
      {activeTab === 'queue' && (
        <section className="card">
          <div style={{ marginBottom: '1rem' }}>
            <h3>Two-Person Verification Queue</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              Every standard row must be verified by a distinct second checker before it enters production evaluations.
            </p>
          </div>

          {loading ? (
            <p style={{ color: 'var(--text-muted)' }}>Loading queue...</p>
          ) : unverifiedRows.length === 0 ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              No rows currently awaiting second verification sign-off.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {unverifiedRows.map((row) => (
                <div
                  key={row.id}
                  style={{
                    padding: '1rem',
                    border: '1px solid var(--border-color)',
                    borderRadius: '6px',
                    background: 'var(--bg-main)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: '1rem',
                  }}
                >
                  <div style={{ flex: 1, minWidth: '280px' }}>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <span style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--text-main)' }}>
                        {row.is_number}
                      </span>
                      <span className="badge badge-warning">Awaiting 2nd Check</span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        Curated by: <b>{row.verified_by}</b> on {row.verified_on}
                      </span>
                    </div>
                    <p style={{ margin: '4px 0', fontSize: '0.875rem', color: 'var(--text-main)' }}>
                      {row.title}
                    </p>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      Source URL:{' '}
                      <a href={row.catalogue_url} target="_blank" rel="noreferrer" style={{ color: '#2563eb' }}>
                        {row.catalogue_url}
                      </a>{' '}
                      | Evidence Ref: {row.evidence_ref}
                    </div>
                  </div>

                  <button
                    onClick={() => void handleVerifyRow(row.id)}
                    className="btn btn-primary"
                    style={{ fontSize: '0.85rem' }}
                  >
                    Sign Off (2nd Checker)
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* Tab: New Row Editor */}
      {activeTab === 'add' && (
        <section className="card">
          <div style={{ marginBottom: '1rem' }}>
            <h3>Curate New Indian Standard Row</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              Save is blocked without verified source URL and evidence. Working notes are kept locally and never exported.
            </p>
          </div>

          <form onSubmit={(e) => void handleCreateRow(e)}>
            <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
              {/* Left Column: Row metadata */}
              <div style={{ flex: 1, minWidth: '300px', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div>
                  <label style={{ display: 'block', fontWeight: 600, fontSize: '0.85rem', marginBottom: '4px' }}>
                    Standard Number (IS Number)*:
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. IS 269 or IS/IEC 62368 Part 1"
                    value={newIsNumber}
                    onChange={(e) => setNewIsNumber(e.target.value)}
                    style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid var(--border-color)' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontWeight: 600, fontSize: '0.85rem', marginBottom: '4px' }}>
                    Standard Title*:
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Ordinary Portland cement specifications"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid var(--border-color)' }}
                  />
                </div>

                <div style={{ display: 'flex', gap: '1rem' }}>
                  <div style={{ flex: 1 }}>
                    <label style={{ display: 'block', fontWeight: 600, fontSize: '0.85rem', marginBottom: '4px' }}>
                      Publication Year:
                    </label>
                    <input
                      type="number"
                      placeholder="e.g. 2015"
                      value={newYear}
                      onChange={(e) => setNewYear(e.target.value)}
                      style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid var(--border-color)' }}
                    />
                  </div>
                  <div style={{ flex: 1 }}>
                    <label style={{ display: 'block', fontWeight: 600, fontSize: '0.85rem', marginBottom: '4px' }}>
                      Status:
                    </label>
                    <select
                      value={newStatus}
                      onChange={(e) => setNewStatus(e.target.value)}
                      style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid var(--border-color)' }}
                    >
                      <option value="Active">Active</option>
                      <option value="Withdrawn">Withdrawn</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontWeight: 600, fontSize: '0.85rem', marginBottom: '4px' }}>
                    Official Catalogue URL (https://)*:
                  </label>
                  <input
                    type="url"
                    required
                    placeholder="https://standardsbis.bsbedge.com/record/..."
                    value={newCatalogueUrl}
                    onChange={(e) => setNewCatalogueUrl(e.target.value)}
                    style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid var(--border-color)' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontWeight: 600, fontSize: '0.85rem', marginBottom: '4px' }}>
                    Evidence Reference*:
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Gazette S.O. 123(E) or BIS portal record verification"
                    value={newEvidenceRef}
                    onChange={(e) => setNewEvidenceRef(e.target.value)}
                    style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid var(--border-color)' }}
                  />
                </div>

                <button type="submit" className="btn btn-primary" style={{ marginTop: '0.5rem' }}>
                  Save & Queue for 2nd Check
                </button>
              </div>

              {/* Right Column: Side-by-side working note */}
              <div style={{ flex: 1, minWidth: '300px' }}>
                <label style={{ display: 'block', fontWeight: 600, fontSize: '0.85rem', marginBottom: '4px' }}>
                  Side-by-Side Official Source Text (Private Working Note):
                </label>
                <textarea
                  rows={14}
                  value={workingNote}
                  onChange={(e) => setWorkingNote(e.target.value)}
                  placeholder="Paste excerpt from official gazette or standards portal here as verification evidence. Stays client-side as working reference and is never exported."
                  style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid var(--border-color)', fontFamily: 'monospace', fontSize: '0.85rem' }}
                />
              </div>
            </div>
          </form>
        </section>
      )}

      {/* Tab: Bulk CSV Import */}
      {activeTab === 'import' && (
        <section className="card">
          <div style={{ marginBottom: '1rem' }}>
            <h3>Bulk Curated Standards Import</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              Upload team-curated CSV. Rows missing verified URLs or labelled UNVERIFIED will be rejected in the validation report.
            </p>
          </div>

          <form onSubmit={(e) => void handleBulkImport(e)} style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                style={{ padding: '6px' }}
              />
              <button type="submit" className="btn btn-primary" disabled={!importFile}>
                Upload & Validate CSV
              </button>
            </div>
          </form>

          {importReport && (
            <div>
              <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
                <span className="badge badge-neutral">Total: {importReport.total_rows}</span>
                <span className="badge badge-success">Imported: {importReport.imported_count}</span>
                <span className="badge badge-error">Rejected: {importReport.rejected_count}</span>
              </div>

              {importReport.errors.length > 0 && (
                <div style={{ border: '1px solid #fca5a5', borderRadius: '6px', overflow: 'hidden' }}>
                  <div style={{ background: '#fef2f2', padding: '8px 12px', fontWeight: 600, color: '#991b1b', fontSize: '0.85rem' }}>
                    Validation Rejections ({importReport.errors.length})
                  </div>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                    <thead>
                      <tr style={{ background: 'var(--bg-main)', borderBottom: '1px solid var(--border-color)' }}>
                        <th style={{ padding: '6px 12px', textAlign: 'left' }}>Line #</th>
                        <th style={{ padding: '6px 12px', textAlign: 'left' }}>Rejection Reason</th>
                      </tr>
                    </thead>
                    <tbody>
                      {importReport.errors.map((err, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid var(--border-color)' }}>
                          <td style={{ padding: '6px 12px' }}>{err.line}</td>
                          <td style={{ padding: '6px 12px', color: '#b91c1c' }}>{err.reason}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </section>
      )}

      {/* Tab: Staleness Dashboard */}
      {activeTab === 'stale' && (
        <section className="card">
          <div style={{ marginBottom: '1rem' }}>
            <h3>Staleness Dashboard (&gt; 180 Days)</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              Standard entries older than 180 days require re-verification against primary BIS Gazette reaffirmations.
            </p>
          </div>

          {loading ? (
            <p style={{ color: 'var(--text-muted)' }}>Loading stale records...</p>
          ) : staleRows.length === 0 ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#15803d' }}>
              All standard records in the database are currently fresh within 180 days.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {staleRows.map((row) => (
                <div
                  key={row.id}
                  style={{
                    padding: '1rem',
                    border: '1px solid var(--border-color)',
                    borderRadius: '6px',
                    background: 'var(--bg-main)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: '1rem',
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>{row.is_number}</span>
                      <span className="badge badge-warning">Stale</span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        Last verified: {row.verified_on || 'Never'} by {row.verified_by}
                      </span>
                    </div>
                    <p style={{ margin: '4px 0', fontSize: '0.85rem' }}>{row.title}</p>
                  </div>

                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <input
                      type="text"
                      placeholder="New Gazette / Verification ref"
                      value={reverifyEvidence[row.id] || ''}
                      onChange={(e) =>
                        setReverifyEvidence({
                          ...reverifyEvidence,
                          [row.id]: e.target.value,
                        })
                      }
                      style={{ padding: '6px 8px', borderRadius: '4px', border: '1px solid var(--border-color)', fontSize: '0.8rem', width: '220px' }}
                    />
                    <button
                      onClick={() => void handleReverifyRow(row.id)}
                      className="btn btn-secondary"
                      style={{ fontSize: '0.85rem' }}
                    >
                      Re-verify Today
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* Tab: Rules & Vague Terms */}
      {activeTab === 'rules' && (
        <section className="card">
          <div style={{ marginBottom: '1.5rem' }}>
            <h3>Curated Vague Terms (Defect Rule R09)</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              Phrases that imply standards without citing an exact number, triggering ambiguity warnings.
            </p>

            <form onSubmit={(e) => void handleCreateVague(e)} style={{ display: 'flex', gap: '8px', margin: '1rem 0', flexWrap: 'wrap' }}>
              <input
                type="text"
                required
                placeholder="Vague phrase (e.g. as per standard)"
                value={newVaguePhrase}
                onChange={(e) => setNewVaguePhrase(e.target.value)}
                style={{ flex: 1, minWidth: '180px', padding: '6px 8px', borderRadius: '4px', border: '1px solid var(--border-color)' }}
              />
              <select
                value={newVagueLang}
                onChange={(e) => setNewVagueLang(e.target.value)}
                style={{ padding: '6px 8px', borderRadius: '4px', border: '1px solid var(--border-color)' }}
              >
                <option value="en">English</option>
                <option value="hi">Hindi</option>
              </select>
              <input
                type="text"
                required
                placeholder="Explanation for officer"
                value={newVagueExp}
                onChange={(e) => setNewVagueExp(e.target.value)}
                style={{ flex: 2, minWidth: '220px', padding: '6px 8px', borderRadius: '4px', border: '1px solid var(--border-color)' }}
              />
              <button type="submit" className="btn btn-primary" style={{ fontSize: '0.85rem' }}>
                Add Phrase
              </button>
            </form>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {vagueTerms.map((vt) => (
                <div
                  key={vt.id}
                  style={{
                    padding: '6px 12px',
                    borderRadius: '4px',
                    border: '1px solid var(--border-color)',
                    background: 'var(--bg-main)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '0.85rem',
                  }}
                >
                  <span>
                    <b>{vt.phrase}</b> ({vt.language})
                  </span>
                  <button
                    onClick={() => void handleDeleteVague(vt.id)}
                    style={{ border: 'none', background: 'none', color: '#b91c1c', cursor: 'pointer', fontWeight: 'bold' }}
                    title="Delete vague term"
                  >
                    &times;
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h3>Deterministic Rules Catalogue ({rulesCatalog.length})</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '1rem' }}>
              Rules loaded deterministically from rules.yaml. Every verdict is traceable to verified database rows.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {rulesCatalog.map((r) => (
                <div
                  key={r.id}
                  style={{
                    padding: '0.75rem',
                    border: '1px solid var(--border-color)',
                    borderRadius: '4px',
                    background: 'var(--bg-main)',
                  }}
                >
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span style={{ fontWeight: 700 }}>{r.id}: {r.name}</span>
                    <span className="badge badge-neutral">{r.severity}</span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    <b>Trigger condition:</b> {r.fires_when}
                  </div>
                  <div style={{ fontSize: '0.8rem', marginTop: '2px' }}>
                    <b>Message:</b> {r.message_en}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Tab: Audit Log Trail */}
      {activeTab === 'logs' && (
        <section className="card">
          <div style={{ marginBottom: '1rem' }}>
            <h3>Append-Only Curation Audit Log</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              Cryptographically traceable record of all row creations, updates, and verifier sign-offs.
            </p>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ background: 'var(--bg-main)', borderBottom: '1px solid var(--border-color)' }}>
                  <th style={{ padding: '8px', textAlign: 'left' }}>Timestamp (UTC)</th>
                  <th style={{ padding: '8px', textAlign: 'left' }}>Action</th>
                  <th style={{ padding: '8px', textAlign: 'left' }}>Table</th>
                  <th style={{ padding: '8px', textAlign: 'left' }}>Record ID</th>
                  <th style={{ padding: '8px', textAlign: 'left' }}>Details</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.map((log) => (
                  <tr key={log.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '8px', whiteSpace: 'nowrap' }}>{log.timestamp}</td>
                    <td style={{ padding: '8px' }}>
                      <span className="badge badge-neutral">{log.action}</span>
                    </td>
                    <td style={{ padding: '8px' }}>{log.table_name}</td>
                    <td style={{ padding: '8px' }}>{log.record_id}</td>
                    <td style={{ padding: '8px', fontFamily: 'monospace', fontSize: '0.75rem', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {log.new_values || log.old_values || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
};
