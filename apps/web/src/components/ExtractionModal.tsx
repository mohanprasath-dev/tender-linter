import React, { useState } from 'react';
import { Clause } from '../types';

interface ExtractionModalProps {
  clause: Clause;
  auditId: string;
  onClose: () => void;
  onSave: (clauseId: string, updatedExtractions: {
    citations: Array<{
      raw: string;
      span: [number, number];
      is_number: string;
      part?: string | null;
      year?: number | null;
    }>;
    mentions_certification: boolean;
  }) => Promise<void>;
}

export const ExtractionModal: React.FC<ExtractionModalProps> = ({
  clause,
  onClose,
  onSave,
}) => {
  const [citations, setCitations] = useState(
    clause.extractions.citations.map((c) => ({
      raw: c.raw,
      span: c.span,
      is_number: c.is_number,
      part: c.part || '',
      year: c.year ? String(c.year) : '',
    }))
  );
  const [mentionsCert, setMentionsCert] = useState<boolean>(
    clause.extractions.mentions_certification
  );
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleCitationChange = (
    index: number,
    field: 'is_number' | 'part' | 'year' | 'raw',
    value: string
  ) => {
    setCitations((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], [field]: value };
      return copy;
    });
  };

  const handleAddCitation = () => {
    setCitations((prev) => [
      ...prev,
      { raw: 'IS ...', span: [0, 0], is_number: 'IS ', part: '', year: '' },
    ]);
  };

  const handleRemoveCitation = (index: number) => {
    setCitations((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      const payloadCitations = citations.map((c) => ({
        raw: c.raw,
        span: c.span,
        is_number: c.is_number.trim(),
        part: c.part.trim() || null,
        year: c.year ? parseInt(c.year, 10) : null,
      }));

      await onSave(clause.id, {
        citations: payloadCitations,
        mentions_certification: mentionsCert,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Re-evaluation failed');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true">
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3>Officer Extraction Editor</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              Edit extracted entities to test or correct deterministic rule evaluation.
            </p>
          </div>
          <button type="button" className="close-button" onClick={onClose} aria-label="Close modal">
            &times;
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="clause-preview-box">
              <span className="clause-label">{clause.id} Original Clause Text:</span>
              <p>&quot;{clause.text}&quot;</p>
            </div>

            {error && (
              <div className="notice-box notice-box-error">
                <span>{error}</span>
              </div>
            )}

            <div className="form-section">
              <div className="section-header-row">
                <h4>Extracted Indian Standards Citations</h4>
                <button
                  type="button"
                  className="button-small"
                  onClick={handleAddCitation}
                >
                  + Add Citation
                </button>
              </div>

              {citations.length === 0 ? (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                  No Indian Standards citations currently recorded for this clause.
                </p>
              ) : (
                citations.map((c, idx) => (
                  <div key={idx} className="citation-edit-row">
                    <div className="input-group">
                      <label htmlFor={`is-num-${idx}`}>Standard Number</label>
                      <input
                        id={`is-num-${idx}`}
                        type="text"
                        value={c.is_number}
                        onChange={(e) => handleCitationChange(idx, 'is_number', e.target.value)}
                        placeholder="e.g. IS/IEC 62368 Part 1"
                        required
                      />
                    </div>
                    <div className="input-group" style={{ maxWidth: '80px' }}>
                      <label htmlFor={`part-${idx}`}>Part</label>
                      <input
                        id={`part-${idx}`}
                        type="text"
                        value={c.part}
                        onChange={(e) => handleCitationChange(idx, 'part', e.target.value)}
                        placeholder="1"
                      />
                    </div>
                    <div className="input-group" style={{ maxWidth: '100px' }}>
                      <label htmlFor={`year-${idx}`}>Year</label>
                      <input
                        id={`year-${idx}`}
                        type="number"
                        value={c.year}
                        onChange={(e) => handleCitationChange(idx, 'year', e.target.value)}
                        placeholder="2023"
                      />
                    </div>
                    <button
                      type="button"
                      className="button-danger-small"
                      onClick={() => handleRemoveCitation(idx)}
                      title="Remove citation"
                    >
                      Delete
                    </button>
                  </div>
                ))
              )}
            </div>

            <div className="form-section">
              <h4>Mandatory Scheme Certification</h4>
              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={mentionsCert}
                  onChange={(e) => setMentionsCert(e.target.checked)}
                />
                <span>Mentions mandatory scheme registration (CRS, QCO, ISI mark, BIS order)</span>
              </label>
            </div>
          </div>

          <div className="modal-footer">
            <button
              type="button"
              className="button-secondary"
              onClick={onClose}
              disabled={saving}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="button-primary"
              disabled={saving}
            >
              {saving ? 'Re-evaluating...' : 'Re-evaluate Rules Instantly'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
