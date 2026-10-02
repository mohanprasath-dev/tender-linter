import React, { useEffect, useState } from 'react';

interface HealthData {
  status: string;
  app: string;
  environment: string;
  database: string;
}

interface VersionData {
  app: string;
  rule_set: string | null;
  model: string | null;
  prompt: string | null;
}

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [version, setVersion] = useState<VersionData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<string>('');

  const fetchStatus = async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const [healthRes, versionRes] = await Promise.all([
        fetch('/api/v1/health'),
        fetch('/api/v1/version'),
      ]);

      if (!healthRes.ok) {
        throw new Error(`Health check failed with HTTP ${healthRes.status}`);
      }
      if (!versionRes.ok) {
        throw new Error(`Version check failed with HTTP ${versionRes.status}`);
      }

      const healthData = (await healthRes.json()) as HealthData;
      const versionData = (await versionRes.json()) as VersionData;

      setHealth(healthData);
      setVersion(versionData);
      setLastChecked(new Date().toLocaleTimeString());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reach API server');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchStatus();
  }, []);

  return (
    <div>
      {/* Non-negotiable officer review banner */}
      <div className="banner" role="alert">
        <span className="banner-icon" aria-hidden="true">&#9888;</span>
        <span>This tool flags issues for the officer to review. It does not approve or reject a tender.</span>
      </div>

      <main className="container">
        <header className="header">
          <h1>Tender Linter</h1>
          <p>System Health and Service Status Dashboard</p>
        </header>

        {error && (
          <div className="card" style={{ marginBottom: '1.5rem', borderColor: 'var(--error)' }}>
            <div className="card-title">
              <span style={{ color: 'var(--error)' }}>Connection Notice</span>
              <span className="badge badge-error">Unreachable</span>
            </div>
            <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>
              Could not communicate with the API backend: {error}
            </p>
            <button
              type="button"
              className="refresh-button"
              onClick={() => void fetchStatus()}
              disabled={loading}
            >
              Retry Connection
            </button>
          </div>
        )}

        <div className="grid">
          {/* Service Health Card */}
          <div className="card">
            <div className="card-title">
              <span>API Gateway</span>
              {loading ? (
                <span className="badge badge-warning">Checking...</span>
              ) : health?.status === 'ok' ? (
                <span className="badge badge-success">Operational</span>
              ) : (
                <span className="badge badge-error">Offline</span>
              )}
            </div>
            <div className="stat-value">
              {loading ? 'Checking...' : health?.status === 'ok' ? 'Healthy' : 'Degraded'}
            </div>
            <div className="stat-desc">FastAPI Backend (Python 3.12, Pydantic v2)</div>

            <table className="info-table">
              <tbody>
                <tr>
                  <td className="label">Endpoint</td>
                  <td className="value">/api/v1/health</td>
                </tr>
                <tr>
                  <td className="label">Status</td>
                  <td className="value">{health?.status ?? 'Unknown'}</td>
                </tr>
                <tr>
                  <td className="label">Environment</td>
                  <td className="value">{health?.environment ?? 'Unknown'}</td>
                </tr>
                <tr>
                  <td className="label">Database</td>
                  <td className="value">{health?.database ?? 'Not connected'}</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Versions and Catalog Card */}
          <div className="card">
            <div className="card-title">
              <span>Registry Versions</span>
              <span className="badge badge-success">M0 Foundation</span>
            </div>
            <div className="stat-value">
              {version?.app ? `v${version.app}` : 'Loading...'}
            </div>
            <div className="stat-desc">System specification tracking</div>

            <table className="info-table">
              <tbody>
                <tr>
                  <td className="label">App Version</td>
                  <td className="value">{version?.app ?? '0.1.0'}</td>
                </tr>
                <tr>
                  <td className="label">Rule Set</td>
                  <td className="value">{version?.rule_set ?? 'None loaded'}</td>
                </tr>
                <tr>
                  <td className="label">Model ID</td>
                  <td className="value">{version?.model ?? 'null (M4 target)'}</td>
                </tr>
                <tr>
                  <td className="label">Prompt Version</td>
                  <td className="value">{version?.prompt ?? 'null (M4 target)'}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <button
            type="button"
            className="refresh-button"
            onClick={() => void fetchStatus()}
            disabled={loading}
          >
            {loading ? 'Refreshing...' : 'Refresh Status'}
          </button>
          {lastChecked && (
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
              Last checked: {lastChecked}
            </span>
          )}
        </div>
      </main>

      <footer className="footer">
        Tender Linter &bull; SIH 2026 Problem Statement SIH26108 &bull; Team OnFocus
      </footer>
    </div>
  );
};

export default App;
