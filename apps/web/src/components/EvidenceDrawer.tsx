import React from 'react';
import { FindingEvidence } from '../types';

interface EvidenceDrawerProps {
  evidence: FindingEvidence | null;
  ruleId: string;
  onClose: () => void;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({
  evidence,
  ruleId,
  onClose,
}) => {
  if (!evidence) {
    return null;
  }

  return (
    <div className="drawer-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="drawer-content" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div>
            <h3>Evidence Verification Drawer</h3>
            <span className="badge badge-info">Rule {ruleId} Reference</span>
          </div>
          <button type="button" className="close-button" onClick={onClose} aria-label="Close drawer">
            &times;
          </button>
        </div>

        <div className="drawer-body">
          <section className="drawer-section">
            <h4>Verified Provenance Metadata</h4>
            <dl className="provenance-list">
              <div className="provenance-item">
                <dt>Verified Date:</dt>
                <dd>{evidence.verified_on || 'Not recorded'}</dd>
              </div>
              {evidence.row_id && (
                <div className="provenance-item">
                  <dt>Data Row ID:</dt>
                  <dd>#{evidence.row_id}</dd>
                </div>
              )}
              {evidence.instrument && (
                <div className="provenance-item">
                  <dt>Statutory Instrument:</dt>
                  <dd>{evidence.instrument}</dd>
                </div>
              )}
              {evidence.candidate && (
                <div className="provenance-item">
                  <dt>Suggested Standard:</dt>
                  <dd><strong>{evidence.candidate}</strong></dd>
                </div>
              )}
              {evidence.term && (
                <div className="provenance-item">
                  <dt>Detected Phrase:</dt>
                  <dd>&quot;{evidence.term}&quot;</dd>
                </div>
              )}
              {evidence.explanation && (
                <div className="provenance-item">
                  <dt>Context Note:</dt>
                  <dd>{evidence.explanation}</dd>
                </div>
              )}
            </dl>
          </section>

          {evidence.url ? (
            <section className="drawer-section">
              <h4>Primary Source Link</h4>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '0.75rem' }}>
                Every non-abstain finding is source-linked to official Gazette notifications or the BIS catalogue.
              </p>
              <a
                href={evidence.url}
                target="_blank"
                rel="noopener noreferrer"
                className="external-link-button"
              >
                Open Official Source Record &#8599;
              </a>
            </section>
          ) : (
            <div className="notice-box">
              <span>Notice: This is an abstain or general requirement finding without an external catalog row.</span>
            </div>
          )}
        </div>

        <div className="drawer-footer">
          <button type="button" className="button-secondary" onClick={onClose}>
            Close Drawer
          </button>
        </div>
      </div>
    </div>
  );
};
