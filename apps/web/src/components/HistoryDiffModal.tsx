import React, { useEffect, useState } from 'react';
import { fetchAuditDiff, listAudits } from '../services/api';
import { AuditDiffResponse, AuditSummary } from '../types';

interface HistoryDiffModalProps {
  currentAuditId?: string;
  onClose: () => void;
}

export const HistoryDiffModal: React.FC<HistoryDiffModalProps> = ({
  currentAuditId,
  onClose,
}) => {
  const [audits, setAudits] = useState<AuditSummary[]>([]);
  const [loadingList, setLoadingList] = useState<boolean>(true);
  const [draftAId, setDraftAId] = useState<string>(currentAuditId || '');
  const [draftBId, setDraftBId] = useState<string>('');
  const [diffResult, setDiffResult] = useState<AuditDiffResponse | null>(null);
  const [loadingDiff, setLoadingDiff] = useState<boolean>(false);
  const [diffError, setDiffError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAuditList() {
      try {
        setLoadingList(true);
        const list = await listAudits(20);
        setAudits(list);
        if (list.length > 1 && !draftBId) {
          // If currentAuditId is set, default draftBId to the other audit
          const other = list.find((a) => a.id !== currentAuditId);
          if (other) {
            setDraftBId(other.id);
          }
        }
      } catch (err) {
        console.error('Failed to load audits for diff', err);
      } finally {
        setLoadingList(false);
      }
    }
    void loadAuditList();
  }, [currentAuditId]);

  const handleCompare = async () => {
    if (!draftAId || !draftBId) {
      setDiffError('Please select both Draft A and Draft B to compare.');
      return;
    }
    if (draftAId === draftBId) {
      setDiffError('Please select two distinct drafts to compare.');
      return;
    }

    setLoadingDiff(true);
    setDiffError(null);
    try {
      const res = await fetchAuditDiff(draftAId, draftBId);
      setDiffResult(res);
    } catch (err) {
      setDiffError(err instanceof Error ? err.message : 'Diff comparison failed');
    } finally {
      setLoadingDiff(false);
    }
  };

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="diff-modal-title"
    >
      <div
        className="modal-content"
        style={{ maxWidth: '900px', maxHeight: '85vh', overflowY: 'auto' }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '1rem',
          }}
        >
          <div>
            <h3 id="diff-modal-title" style={{ margin: 0, color: 'var(--text-main)' }}>
              Audit History & Version Diff
            </h3>
            <p style={{ margin: '4px 0 0', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              Compare two tender drafts to verify resolved issues and newly introduced defects.
            </p>
          </div>
          <button
            onClick={onClose}
            className="btn btn-secondary"
            aria-label="Close diff modal"
          >
            Close
          </button>
        </div>

        {/* Selection Bar */}
        <div
          style={{
            background: 'var(--bg-card)',
            padding: '1rem',
            borderRadius: '6px',
            border: '1px solid var(--border-color)',
            marginBottom: '1.25rem',
          }}
        >
          {loadingList ? (
            <p style={{ color: 'var(--text-muted)' }}>Loading previous audits...</p>
          ) : (
            <div
              style={{
                display: 'flex',
                gap: '1rem',
                flexWrap: 'wrap',
                alignItems: 'flex-end',
              }}
            >
              <div style={{ flex: 1, minWidth: '220px' }}>
                <label
                  htmlFor="draft-a-select"
                  style={{
                    display: 'block',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    marginBottom: '4px',
                    color: 'var(--text-muted)',
                  }}
                >
                  Baseline Draft (A):
                </label>
                <select
                  id="draft-a-select"
                  value={draftAId}
                  onChange={(e) => setDraftAId(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '6px 8px',
                    borderRadius: '4px',
                    border: '1px solid var(--border-color)',
                  }}
                >
                  <option value="">Select baseline draft</option>
                  {audits.map((a) => (
                    <option key={`a-${a.id}`} value={a.id}>
                      {a.document_name || a.id.slice(0, 8)} ({a.total_findings} issues,{' '}
                      {new Date(a.created_at).toLocaleDateString()})
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ flex: 1, minWidth: '220px' }}>
                <label
                  htmlFor="draft-b-select"
                  style={{
                    display: 'block',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    marginBottom: '4px',
                    color: 'var(--text-muted)',
                  }}
                >
                  Comparison Draft (B):
                </label>
                <select
                  id="draft-b-select"
                  value={draftBId}
                  onChange={(e) => setDraftBId(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '6px 8px',
                    borderRadius: '4px',
                    border: '1px solid var(--border-color)',
                  }}
                >
                  <option value="">Select comparison draft</option>
                  {audits.map((a) => (
                    <option key={`b-${a.id}`} value={a.id}>
                      {a.document_name || a.id.slice(0, 8)} ({a.total_findings} issues,{' '}
                      {new Date(a.created_at).toLocaleDateString()})
                    </option>
                  ))}
                </select>
              </div>

              <button
                onClick={handleCompare}
                disabled={loadingDiff || !draftAId || !draftBId || draftAId === draftBId}
                className="btn btn-primary"
              >
                {loadingDiff ? 'Comparing...' : 'Compare Drafts'}
              </button>
            </div>
          )}
          {diffError && (
            <p style={{ color: 'var(--color-error)', margin: '8px 0 0', fontSize: '0.85rem' }}>
              {diffError}
            </p>
          )}
        </div>

        {/* Diff Results View */}
        {diffResult && (
          <div>
            {/* Summary cards */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                gap: '0.75rem',
                marginBottom: '1.25rem',
              }}
            >
              <div
                style={{
                  background: '#f0fdf4',
                  border: '1px solid #86efac',
                  padding: '0.75rem',
                  borderRadius: '6px',
                }}
              >
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#166534' }}>
                  RESOLVED ISSUES
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#15803d' }}>
                  {diffResult.resolved_findings.length}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#166534' }}>
                  Fixed in comparison draft
                </div>
              </div>

              <div
                style={{
                  background: '#fef2f2',
                  border: '1px solid #fca5a5',
                  padding: '0.75rem',
                  borderRadius: '6px',
                }}
              >
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#991b1b' }}>
                  NEW ISSUES
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#b91c1c' }}>
                  {diffResult.added_findings.length}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#991b1b' }}>
                  Introduced in Draft B
                </div>
              </div>

              <div
                style={{
                  background: '#eff6ff',
                  border: '1px solid #93c5fd',
                  padding: '0.75rem',
                  borderRadius: '6px',
                }}
              >
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#1e40af' }}>
                  RETAINED ISSUES
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#1d4ed8' }}>
                  {diffResult.retained_findings.length}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#1e40af' }}>
                  Still present in both
                </div>
              </div>

              <div
                style={{
                  background: '#f8fafc',
                  border: '1px solid #cbd5e1',
                  padding: '0.75rem',
                  borderRadius: '6px',
                }}
              >
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#334155' }}>
                  CLAUSE EDITS
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a' }}>
                  {diffResult.clause_diff.modified.length}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#475569' }}>
                  Modified paragraphs
                </div>
              </div>
            </div>

            {/* Resolved Findings Details */}
            {diffResult.resolved_findings.length > 0 && (
              <div style={{ marginBottom: '1.25rem' }}>
                <h4 style={{ color: '#15803d', margin: '0 0 0.5rem', fontSize: '0.95rem' }}>
                  Resolved Findings (Fixed in Draft B)
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {diffResult.resolved_findings.map((f) => (
                    <div
                      key={`res-${f.id}`}
                      style={{
                        padding: '0.75rem',
                        background: '#f0fdf4',
                        border: '1px solid #bbf7d0',
                        borderRadius: '4px',
                      }}
                    >
                      <div style={{ fontWeight: 600, color: '#166534', fontSize: '0.85rem' }}>
                        Clause {f.clause_id}: {f.rule_id} ({f.severity})
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#14532d', marginTop: '2px' }}>
                        {f.message_en}
                      </div>
                      {f.evidence && f.evidence.url && (
                        <div style={{ fontSize: '0.75rem', color: '#15803d', marginTop: '4px' }}>
                          Evidence: {f.evidence.url} (Verified: {f.evidence.verified_on || 'N/A'})
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Added Findings Details */}
            {diffResult.added_findings.length > 0 && (
              <div style={{ marginBottom: '1.25rem' }}>
                <h4 style={{ color: '#b91c1c', margin: '0 0 0.5rem', fontSize: '0.95rem' }}>
                  New Findings Introduced in Draft B
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {diffResult.added_findings.map((f) => (
                    <div
                      key={`add-${f.id}`}
                      style={{
                        padding: '0.75rem',
                        background: '#fef2f2',
                        border: '1px solid #fecaca',
                        borderRadius: '4px',
                      }}
                    >
                      <div style={{ fontWeight: 600, color: '#991b1b', fontSize: '0.85rem' }}>
                        Clause {f.clause_id}: {f.rule_id} ({f.severity})
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#7f1d1d', marginTop: '2px' }}>
                        {f.message_en}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Modified Clauses Details */}
            {diffResult.clause_diff.modified.length > 0 && (
              <div>
                <h4 style={{ color: 'var(--text-main)', margin: '0 0 0.5rem', fontSize: '0.95rem' }}>
                  Modified Clauses Comparison
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {diffResult.clause_diff.modified.map((c) => (
                    <div
                      key={`cl-${c.id}`}
                      style={{
                        padding: '0.75rem',
                        border: '1px solid var(--border-color)',
                        borderRadius: '4px',
                        background: 'var(--bg-main)',
                      }}
                    >
                      <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '4px' }}>
                        Clause {c.id}
                      </div>
                      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                        <div style={{ flex: 1, minWidth: '220px' }}>
                          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#991b1b' }}>
                            Draft A (Previous):
                          </span>
                          <p
                            style={{
                              fontSize: '0.8rem',
                              margin: '2px 0 0',
                              color: 'var(--text-main)',
                              background: '#fee2e2',
                              padding: '6px',
                              borderRadius: '4px',
                            }}
                          >
                            {c.old_text}
                          </p>
                        </div>
                        <div style={{ flex: 1, minWidth: '220px' }}>
                          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#166534' }}>
                            Draft B (Updated):
                          </span>
                          <p
                            style={{
                              fontSize: '0.8rem',
                              margin: '2px 0 0',
                              color: 'var(--text-main)',
                              background: '#dcfce7',
                              padding: '6px',
                              borderRadius: '4px',
                            }}
                          >
                            {c.new_text}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
