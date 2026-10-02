import React, { useState } from 'react';
import { MATRIX_CASES } from '../data/matrixCases';
import {
  createAudit,
  editClauseExtractions,
  fetchReport,
  recordFindingDecision,
} from '../services/api';
import { AuditResponse, Clause, FindingEvidence, Severity } from '../types';
import { EvidenceDrawer } from './EvidenceDrawer';
import { ExtractionModal } from './ExtractionModal';

interface AuditWorkspaceProps {
  initialClause?: string;
  initialLanguage?: string;
}

export const AuditWorkspace: React.FC<AuditWorkspaceProps> = ({
  initialClause = '',
  initialLanguage = 'en',
}) => {
  const [inputText, setInputText] = useState<string>(
    initialClause || MATRIX_CASES[0].clause
  );
  const [languageHint, setLanguageHint] = useState<string>(initialLanguage);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [audit, setAudit] = useState<AuditResponse | null>(null);
  const [selectedClauseId, setSelectedClauseId] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');

  // Drawer and Modal states
  const [activeEvidence, setActiveEvidence] = useState<{
    evidence: FindingEvidence | null;
    ruleId: string;
  } | null>(null);
  const [editingClause, setEditingClause] = useState<Clause | null>(null);

  // Dismiss reason prompt modal/state
  const [dismissFindingId, setDismissFindingId] = useState<string | null>(null);
  const [dismissReason, setDismissReason] = useState<string>('');

  const handleRunAudit = async (textToAudit?: string, lang?: string) => {
    const text = textToAudit !== undefined ? textToAudit : inputText;
    const currentLang = lang !== undefined ? lang : languageHint;

    if (!text.trim()) {
      setError('Please enter specification text to audit.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await createAudit(text, currentLang);
      setAudit(res);
      if (res.clauses.length > 0) {
        setSelectedClauseId(res.clauses[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Audit execution failed');
    } finally {
      setLoading(false);
    }
  };

  const handlePresetSelect = (clauseText: string, lang = 'en') => {
    setInputText(clauseText);
    setLanguageHint(lang);
    void handleRunAudit(clauseText, lang);
  };

  const handleDecision = async (
    findingId: string,
    decision: 'ACCEPT' | 'DISMISS' | 'NOT_APPLICABLE',
    reason?: string
  ) => {
    if (!audit) return;
    try {
      await recordFindingDecision(audit.id, findingId, decision, reason);
      // Update finding locally
      setAudit((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          findings: prev.findings.map((f) =>
            f.id === findingId
              ? { ...f, decision, decision_reason: reason || null }
              : f
          ),
        };
      });
      setDismissFindingId(null);
      setDismissReason('');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to record decision');
    }
  };

  const handleSaveExtractions = async (
    clauseId: string,
    updated: {
      citations: Array<{
        raw: string;
        span: [number, number];
        is_number: string;
        part?: string | null;
        year?: number | null;
      }>;
      mentions_certification: boolean;
    }
  ) => {
    if (!audit) return;
    const updatedAudit = await editClauseExtractions(audit.id, clauseId, updated);
    setAudit(updatedAudit);
  };

  const handleExport = async (format: 'json' | 'csv') => {
    if (!audit) return;
    try {
      const rep = await fetchReport(audit.id, format);
      const filename = `tender_linter_audit_${audit.id}.${format}`;
      let blob: Blob;

      if (format === 'csv' && rep.text) {
        blob = new Blob([rep.text], { type: 'text/csv;charset=utf-8;' });
      } else {
        blob = new Blob([JSON.stringify(rep.json, null, 2)], {
          type: 'application/json',
        });
      }

      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Export failed');
    }
  };

  const filteredFindings = audit
    ? audit.findings.filter((f) => {
        if (severityFilter !== 'ALL' && f.severity !== severityFilter) {
          return false;
        }
        if (selectedClauseId && f.clause_id !== selectedClauseId) {
          return false;
        }
        return true;
      })
    : [];

  const getSeverityBadgeClass = (sev: Severity) => {
    switch (sev) {
      case 'ERROR':
        return 'badge-error';
      case 'WARNING':
        return 'badge-warning';
      case 'INFO':
        return 'badge-info';
      case 'CANNOT_VERIFY':
        return 'badge-cannot-verify';
      default:
        return 'badge-neutral';
    }
  };

  return (
    <div className="workspace-container">
      {/* Input section */}
      <section className="input-card card" aria-label="Tender specification input">
        <div className="input-header-row">
          <div>
            <h2>Tender Specification Auditor</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              Paste tender clauses or pick a verified benchmark specification below.
            </p>
          </div>
          <div className="language-selector">
            <label htmlFor="lang-select">Language:</label>
            <select
              id="lang-select"
              value={languageHint}
              onChange={(e) => setLanguageHint(e.target.value)}
              aria-label="Language selection"
            >
              <option value="en">English</option>
              <option value="hi">Hindi (हिन्दी)</option>
            </select>
          </div>
        </div>

        {/* Quick sample buttons for T01 - T13 */}
        <div className="preset-row" aria-label="Benchmark presets">
          <span className="preset-label">Quick Samples:</span>
          <button
            type="button"
            className="preset-chip"
            onClick={() => handlePresetSelect(MATRIX_CASES[0].clause, 'en')}
          >
            T01: Laptops (IS 13252)
          </button>
          <button
            type="button"
            className="preset-chip"
            onClick={() => handlePresetSelect(MATRIX_CASES[1].clause, 'en')}
          >
            T02: Laptops (IS/IEC 62368)
          </button>
          <button
            type="button"
            className="preset-chip"
            onClick={() => handlePresetSelect(MATRIX_CASES[3].clause, 'en')}
          >
            T04: Microwave (IS 302)
          </button>
          <button
            type="button"
            className="preset-chip"
            onClick={() => handlePresetSelect(MATRIX_CASES[5].clause, 'en')}
          >
            T06: Vague Term
          </button>
          <button
            type="button"
            className="preset-chip"
            onClick={() => handlePresetSelect(MATRIX_CASES[9].clause, 'en')}
          >
            T10: Typo (IS 13253)
          </button>
          <button
            type="button"
            className="preset-chip"
            onClick={() => handlePresetSelect(MATRIX_CASES[11].clause, 'hi')}
          >
            T12: Hindi Clause
          </button>
          <button
            type="button"
            className="preset-chip"
            onClick={() => handlePresetSelect(MATRIX_CASES[12].clause, 'en')}
          >
            T13: Compliant Clause
          </button>
        </div>

        <textarea
          className="spec-textarea"
          rows={3}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Paste tender specification text here..."
          aria-label="Tender specification text"
        />

        <div className="action-row">
          <button
            type="button"
            className="button-primary"
            onClick={() => void handleRunAudit()}
            disabled={loading}
          >
            {loading ? 'Auditing Specification...' : 'Audit Specification'}
          </button>
          {error && <span className="error-text">{error}</span>}
        </div>
      </section>

      {/* Main Audit Results Split View */}
      {audit && (
        <div className="audit-results-grid">
          {/* Left Column: Clauses and Span Highlights */}
          <div className="clauses-column">
            <div className="column-header">
              <h3>Specification Clauses ({audit.clauses.length})</h3>
              <span className="subtext">Select a clause to inspect extractions</span>
            </div>

            <div className="clauses-list" role="region" aria-label="Clauses list">
              {audit.clauses.map((clause) => {
                const isSelected = selectedClauseId === clause.id;
                const findingsForClause = audit.findings.filter(
                  (f) => f.clause_id === clause.id
                );

                return (
                  <div
                    key={clause.id}
                    className={`clause-card ${isSelected ? 'selected' : ''}`}
                    onClick={() => setSelectedClauseId(clause.id)}
                  >
                    <div className="clause-card-header">
                      <span className="clause-id-badge">{clause.id}</span>
                      <div className="clause-badges">
                        {findingsForClause.length > 0 ? (
                          <span className="badge badge-warning">
                            {findingsForClause.length} Finding{findingsForClause.length > 1 ? 's' : ''}
                          </span>
                        ) : (
                          <span className="badge badge-success">No Issues</span>
                        )}
                        <button
                          type="button"
                          className="button-link-small"
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditingClause(clause);
                          }}
                        >
                          Edit Extractions
                        </button>
                      </div>
                    </div>

                    <div className="clause-text-display">
                      <p>{clause.text}</p>
                    </div>

                    {/* Extracted summary bar */}
                    <div className="clause-meta-row">
                      <span>
                        Citations: {clause.extractions.citations.length > 0
                          ? clause.extractions.citations.map((c) => c.is_number).join(', ')
                          : 'None'}
                      </span>
                      <span>
                        CRS Mention: {clause.extractions.mentions_certification ? 'Yes' : 'No'}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Finding Cards Grouped by Severity */}
          <div className="findings-column">
            <div className="column-header">
              <div className="findings-header-title">
                <h3>Line-Level Findings ({filteredFindings.length})</h3>
                {selectedClauseId && (
                  <button
                    type="button"
                    className="button-link-small"
                    onClick={() => setSelectedClauseId(null)}
                  >
                    Show all clauses
                  </button>
                )}
              </div>

              {/* Severity filter pills */}
              <div className="filter-pills" role="toolbar" aria-label="Severity filter">
                {['ALL', 'ERROR', 'WARNING', 'INFO', 'CANNOT_VERIFY'].map((sev) => (
                  <button
                    key={sev}
                    type="button"
                    className={`filter-pill ${severityFilter === sev ? 'active' : ''}`}
                    onClick={() => setSeverityFilter(sev)}
                  >
                    {sev}
                  </button>
                ))}
              </div>
            </div>

            <div className="findings-list" role="region" aria-label="Findings list">
              {filteredFindings.length === 0 ? (
                <div className="empty-findings-box card">
                  <span className="empty-icon">&#10003;</span>
                  <h4>No Findings for Selected Filter</h4>
                  <p style={{ color: 'var(--text-muted)' }}>
                    No defects detected in this section matching your active filter.
                  </p>
                </div>
              ) : (
                filteredFindings.map((finding) => (
                  <article key={finding.id} className="finding-card card">
                    <div className="finding-card-header">
                      <div className="finding-badges">
                        <span className="rule-badge">{finding.rule_id}</span>
                        <span className={`badge ${getSeverityBadgeClass(finding.severity)}`}>
                          {finding.severity}
                        </span>
                        <span className="clause-ref-badge">{finding.clause_id}</span>
                      </div>

                      {finding.decision ? (
                        <span
                          className={`badge ${
                            finding.decision === 'ACCEPT'
                              ? 'badge-success'
                              : 'badge-neutral'
                          }`}
                        >
                          {finding.decision}
                        </span>
                      ) : (
                        <span className="badge badge-pending">Officer Review Pending</span>
                      )}
                    </div>

                    <div className="finding-body">
                      <p className="finding-message-en">{finding.message_en}</p>
                      {finding.message_hi && (
                        <p className="finding-message-hi">{finding.message_hi}</p>
                      )}

                      {finding.decision_reason && (
                        <div className="decision-note">
                          <strong>Officer Note:</strong> {finding.decision_reason}
                        </div>
                      )}

                      {/* Evidence Summary line */}
                      <div className="finding-evidence-summary">
                        <span>
                          Verified On: {finding.evidence?.verified_on || 'Dataset record'}
                        </span>
                        {finding.evidence && (
                          <button
                            type="button"
                            className="evidence-drawer-toggle"
                            onClick={() =>
                              setActiveEvidence({
                                evidence: finding.evidence || null,
                                ruleId: finding.rule_id,
                              })
                            }
                          >
                            View Evidence &amp; Source &#8599;
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Officer Action Bar */}
                    <div className="finding-actions">
                      <span className="action-label">Officer Action:</span>
                      <button
                        type="button"
                        className={`action-button action-accept ${
                          finding.decision === 'ACCEPT' ? 'active' : ''
                        }`}
                        onClick={() => handleDecision(finding.id, 'ACCEPT')}
                      >
                        Accept
                      </button>
                      <button
                        type="button"
                        className={`action-button action-dismiss ${
                          finding.decision === 'DISMISS' ? 'active' : ''
                        }`}
                        onClick={() => {
                          setDismissFindingId(finding.id);
                          setDismissReason(finding.decision_reason || '');
                        }}
                      >
                        Dismiss with Reason
                      </button>
                      <button
                        type="button"
                        className={`action-button action-na ${
                          finding.decision === 'NOT_APPLICABLE' ? 'active' : ''
                        }`}
                        onClick={() => handleDecision(finding.id, 'NOT_APPLICABLE')}
                      >
                        Not Applicable
                      </button>
                    </div>
                  </article>
                ))
              )}
            </div>

            {/* Export Toolbar */}
            <div className="export-toolbar">
              <span className="export-title">Export Audit Report:</span>
              <button
                type="button"
                className="button-secondary-small"
                onClick={() => void handleExport('json')}
              >
                Download JSON Report
              </button>
              <button
                type="button"
                className="button-secondary-small"
                onClick={() => void handleExport('csv')}
              >
                Download CSV Report
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Evidence Drawer */}
      {activeEvidence && (
        <EvidenceDrawer
          evidence={activeEvidence.evidence}
          ruleId={activeEvidence.ruleId}
          onClose={() => setActiveEvidence(null)}
        />
      )}

      {/* Extraction Editor Modal */}
      {editingClause && audit && (
        <ExtractionModal
          clause={editingClause}
          auditId={audit.id}
          onClose={() => setEditingClause(null)}
          onSave={handleSaveExtractions}
        />
      )}

      {/* Inline Dismiss Reason Modal */}
      {dismissFindingId && (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="modal-content" style={{ maxWidth: '480px' }}>
            <div className="modal-header">
              <h3>Dismiss Finding with Reason</h3>
              <button
                type="button"
                className="close-button"
                onClick={() => setDismissFindingId(null)}
              >
                &times;
              </button>
            </div>
            <div className="modal-body">
              <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                Please record the justification for dismissing this flagged issue.
              </p>
              <textarea
                className="spec-textarea"
                rows={3}
                value={dismissReason}
                onChange={(e) => setDismissReason(e.target.value)}
                placeholder="e.g. Standard verified in state tender exemption or tender uses custom spec."
                required
              />
            </div>
            <div className="modal-footer">
              <button
                type="button"
                className="button-secondary"
                onClick={() => setDismissFindingId(null)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="button-primary"
                onClick={() =>
                  handleDecision(dismissFindingId, 'DISMISS', dismissReason)
                }
                disabled={!dismissReason.trim()}
              >
                Confirm Dismissal
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
