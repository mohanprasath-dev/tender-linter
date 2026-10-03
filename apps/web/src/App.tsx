import React, { useState } from 'react';
import { AuditWorkspace } from './components/AuditWorkspace';
import { CurationConsole } from './components/CurationConsole';
import { Header } from './components/Header';
import { MatrixRunner } from './components/MatrixRunner';
import { SystemHealth } from './components/SystemHealth';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'workspace' | 'matrix' | 'curation' | 'health'>('workspace');
  const [workspaceClause, setWorkspaceClause] = useState<string>('');
  const [workspaceLanguage, setWorkspaceLanguage] = useState<string>('en');

  const handleLoadClause = (clause: string, language: string) => {
    setWorkspaceClause(clause);
    setWorkspaceLanguage(language);
    setActiveTab('workspace');
  };

  return (
    <div className="app-shell">
      <Header
        activeTab={activeTab}
        onTabChange={setActiveTab}
        ruleSetVersion="0.1.0"
      />

      <main className="main-content">
        {activeTab === 'workspace' && (
          <AuditWorkspace
            key={workspaceClause}
            initialClause={workspaceClause}
            initialLanguage={workspaceLanguage}
          />
        )}

        {activeTab === 'matrix' && (
          <MatrixRunner onLoadClause={handleLoadClause} />
        )}

        {activeTab === 'curation' && <CurationConsole />}

        {activeTab === 'health' && <SystemHealth />}
      </main>

      <footer className="site-footer">
        <div className="footer-inner">
          <span>Problem Statement SIH26108 | Team OnFocus (Team ID 176283)</span>
          <span>Deterministic Evidence-Linked Procurement Standards Auditor</span>
        </div>
      </footer>
    </div>
  );
};
