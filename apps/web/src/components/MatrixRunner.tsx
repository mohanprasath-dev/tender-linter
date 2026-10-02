import React, { useState } from 'react';
import { MATRIX_CASES } from '../data/matrixCases';
import { createAudit } from '../services/api';
import { MatrixCase } from '../types';

interface MatrixRunnerProps {
  onLoadClause: (clause: string, language: string) => void;
}

interface TestRunResult {
  detectedRules: string[];
  passed: boolean;
  loading: boolean;
  error?: string;
}

export const MatrixRunner: React.FC<MatrixRunnerProps> = ({ onLoadClause }) => {
  const [results, setResults] = useState<Record<string, TestRunResult>>({});
  const [runningAll, setRunningAll] = useState<boolean>(false);

  const runTestCase = async (testCase: MatrixCase): Promise<TestRunResult> => {
    try {
      const audit = await createAudit(testCase.clause, testCase.language);
      const detected = Array.from(
        new Set(audit.findings.map((f) => f.rule_id).filter((r) => r !== 'R14'))
      ).sort();

      const expected = [...testCase.expectedRules].sort();
      // Match check: expected rules must match detected rules
      const passed =
        expected.length === detected.length &&
        expected.every((r, idx) => r === detected[idx]);

      return {
        detectedRules: detected,
        passed,
        loading: false,
      };
    } catch (err) {
      return {
        detectedRules: [],
        passed: false,
        loading: false,
        error: err instanceof Error ? err.message : 'Execution error',
      };
    }
  };

  const handleRunSingle = async (testCase: MatrixCase) => {
    setResults((prev) => ({
      ...prev,
      [testCase.id]: { detectedRules: [], passed: false, loading: true },
    }));

    const result = await runTestCase(testCase);
    setResults((prev) => ({
      ...prev,
      [testCase.id]: result,
    }));
  };

  const handleRunAll = async () => {
    setRunningAll(true);
    const initialLoading: Record<string, TestRunResult> = {};
    MATRIX_CASES.forEach((c) => {
      initialLoading[c.id] = { detectedRules: [], passed: false, loading: true };
    });
    setResults(initialLoading);

    const newResults: Record<string, TestRunResult> = {};
    for (const testCase of MATRIX_CASES) {
      const res = await runTestCase(testCase);
      newResults[testCase.id] = res;
      setResults((prev) => ({ ...prev, [testCase.id]: res }));
    }

    setRunningAll(false);
  };

  const executedCount = Object.keys(results).filter((k) => !results[k].loading).length;
  const passedCount = Object.keys(results).filter(
    (k) => !results[k].loading && results[k].passed
  ).length;

  return (
    <div className="matrix-runner-container">
      <div className="card matrix-header-card">
        <div className="matrix-title-row">
          <div>
            <h2>Synthetic Test Matrix (T01 - T13)</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              Specification benchmark matrix defined in Section 16.7. Evaluates deterministic rule triggering over verified rows.
            </p>
          </div>
          <button
            type="button"
            className="button-primary"
            onClick={() => void handleRunAll()}
            disabled={runningAll}
          >
            {runningAll ? 'Evaluating Suite...' : 'Run All 13 Test Cases'}
          </button>
        </div>

        {executedCount > 0 && (
          <div className="matrix-summary-banner">
            <strong>Measured Score:</strong> {passedCount} of {executedCount} on test set synthetic-v1
            {passedCount === executedCount && executedCount === 13 && (
              <span className="badge badge-success" style={{ marginLeft: '1rem' }}>
                All 13 Cases Matched
              </span>
            )}
          </div>
        )}
      </div>

      <div className="matrix-table-card card">
        <div className="table-responsive">
          <table className="matrix-table">
            <thead>
              <tr>
                <th style={{ width: '60px' }}>ID</th>
                <th style={{ width: '220px' }}>Test Case</th>
                <th>Clause Specification Text</th>
                <th style={{ width: '130px' }}>Expected</th>
                <th style={{ width: '130px' }}>Observed</th>
                <th style={{ width: '90px' }}>Status</th>
                <th style={{ width: '160px' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {MATRIX_CASES.map((tc) => {
                const res = results[tc.id];

                return (
                  <tr key={tc.id}>
                    <td>
                      <span className="matrix-id-pill">{tc.id}</span>
                    </td>
                    <td>
                      <div className="matrix-case-title">{tc.title}</div>
                      <div className="matrix-case-notes">{tc.notes}</div>
                    </td>
                    <td className="matrix-clause-cell">
                      <p>&quot;{tc.clause}&quot;</p>
                      {tc.language !== 'en' && (
                        <span className="badge badge-neutral">Language: {tc.language}</span>
                      )}
                    </td>
                    <td>
                      {tc.expectedRules.length > 0 ? (
                        tc.expectedRules.map((r) => (
                          <span key={r} className="rule-badge-small">
                            {r}
                          </span>
                        ))
                      ) : (
                        <span className="badge badge-neutral">Clean (None)</span>
                      )}
                    </td>
                    <td>
                      {res?.loading ? (
                        <span className="loading-dots">Auditing...</span>
                      ) : res?.detectedRules ? (
                        res.detectedRules.length > 0 ? (
                          res.detectedRules.map((r) => (
                            <span key={r} className="rule-badge-small rule-badge-observed">
                              {r}
                            </span>
                          ))
                        ) : (
                          <span className="badge badge-neutral">None</span>
                        )
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>Not run</span>
                      )}
                    </td>
                    <td>
                      {res?.loading ? (
                        <span className="badge badge-warning">Testing</span>
                      ) : res?.passed ? (
                        <span className="badge badge-success">MATCH</span>
                      ) : res ? (
                        <span className="badge badge-error">DIFF</span>
                      ) : (
                        <span className="badge badge-neutral">Idle</span>
                      )}
                    </td>
                    <td>
                      <div className="matrix-action-cell">
                        <button
                          type="button"
                          className="button-small"
                          onClick={() => void handleRunSingle(tc)}
                          disabled={res?.loading || runningAll}
                        >
                          Run
                        </button>
                        <button
                          type="button"
                          className="button-link-small"
                          onClick={() => onLoadClause(tc.clause, tc.language)}
                        >
                          Inspect in Audit
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
