import React from 'react';

interface HeaderProps {
  activeTab: 'workspace' | 'matrix' | 'curation' | 'health';
  onTabChange: (tab: 'workspace' | 'matrix' | 'curation' | 'health') => void;
  ruleSetVersion?: string | null;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onTabChange,
  ruleSetVersion = '0.1.0',
}) => {
  return (
    <header className="site-header">
      {/* Non-negotiable officer review banner */}
      <div className="banner" role="alert">
        <span className="banner-icon" aria-hidden="true">&#9888;</span>
        <span>This tool flags issues for the officer to review. It does not approve or reject a tender.</span>
      </div>

      <div className="nav-container">
        <div className="brand-section">
          <div className="brand-logo" aria-hidden="true">&#9670;</div>
          <div>
            <div className="brand-title">Tender Linter</div>
            <div className="brand-subtitle">Indian Standards Evidence Auditor</div>
          </div>
          {ruleSetVersion && (
            <span className="badge badge-neutral" title="Current Rule Set Version">
              Rules v{ruleSetVersion}
            </span>
          )}
          <span className="badge badge-success" title="Hindi Pipeline Verified: Supported on 32 test clauses">
            Hindi: Supported
          </span>
        </div>

        <nav className="tab-navigation" aria-label="Main Navigation">
          <button
            type="button"
            className={`tab-button ${activeTab === 'workspace' ? 'active' : ''}`}
            onClick={() => onTabChange('workspace')}
            aria-selected={activeTab === 'workspace'}
          >
            Audit Workspace
          </button>
          <button
            type="button"
            className={`tab-button ${activeTab === 'matrix' ? 'active' : ''}`}
            onClick={() => onTabChange('matrix')}
            aria-selected={activeTab === 'matrix'}
          >
            T01 - T13 Test Matrix
          </button>
          <button
            type="button"
            className={`tab-button ${activeTab === 'curation' ? 'active' : ''}`}
            onClick={() => onTabChange('curation')}
            aria-selected={activeTab === 'curation'}
          >
            Curation Console
          </button>
          <button
            type="button"
            className={`tab-button ${activeTab === 'health' ? 'active' : ''}`}
            onClick={() => onTabChange('health')}
            aria-selected={activeTab === 'health'}
          >
            System Status
          </button>
        </nav>
      </div>
    </header>
  );
};
