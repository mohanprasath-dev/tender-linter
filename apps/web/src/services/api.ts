import {
  AuditDiffResponse,
  AuditLogRecord,
  AuditResponse,
  AuditSummary,
  BulkImportReport,
  Finding,
  HealthData,
  RuleItem,
  StandardRow,
  VagueTerm,
  VersionData,
} from '../types';

let cachedToken: string | null = null;

export async function ensureAuthToken(): Promise<string> {
  if (cachedToken) {
    return cachedToken;
  }

  const stored = localStorage.getItem('tender_linter_token');
  if (stored) {
    cachedToken = stored;
    return stored;
  }

  try {
    const resp = await fetch('/api/v1/auth/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: 'officer1',
        password: 'hashed_reviewer_password',
      }),
    });

    if (resp.ok) {
      const data = (await resp.json()) as { access_token: string };
      cachedToken = data.access_token;
      localStorage.setItem('tender_linter_token', data.access_token);
      return data.access_token;
    }
  } catch (err) {
    console.warn('Auto authentication fallback error:', err);
  }

  return '';
}

async function authHeaders(): Promise<HeadersInit> {
  const token = await ensureAuthToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export async function createAudit(text: string, languageHint = 'en'): Promise<AuditResponse> {
  const headers = await authHeaders();
  const resp = await fetch('/api/v1/audits', {
    method: 'POST',
    headers,
    body: JSON.stringify({
      text,
      language_hint: languageHint,
    }),
  });

  if (!resp.ok) {
    const errorText = await resp.text();
    throw new Error(`Audit creation failed (${resp.status}): ${errorText}`);
  }

  return (await resp.json()) as AuditResponse;
}

export async function getAudit(auditId: string): Promise<AuditResponse> {
  const headers = await authHeaders();
  const resp = await fetch(`/api/v1/audits/${encodeURIComponent(auditId)}`, {
    headers,
  });

  if (!resp.ok) {
    throw new Error(`Failed to fetch audit (${resp.status})`);
  }

  return (await resp.json()) as AuditResponse;
}

export async function recordFindingDecision(
  auditId: string,
  findingId: string,
  decision: 'ACCEPT' | 'DISMISS' | 'NOT_APPLICABLE',
  reason?: string
): Promise<Finding> {
  const headers = await authHeaders();
  const resp = await fetch(
    `/api/v1/audits/${encodeURIComponent(auditId)}/findings/${encodeURIComponent(findingId)}/decision`,
    {
      method: 'POST',
      headers,
      body: JSON.stringify({
        decision,
        reason: reason || null,
      }),
    }
  );

  if (!resp.ok) {
    throw new Error(`Failed to record decision (${resp.status})`);
  }

  return (await resp.json()) as Finding;
}

export async function editClauseExtractions(
  auditId: string,
  clauseId: string,
  editPayload: {
    citations?: unknown[];
    mentions_certification?: boolean;
    mapped_product?: unknown;
  }
): Promise<AuditResponse> {
  const headers = await authHeaders();
  const resp = await fetch(
    `/api/v1/audits/${encodeURIComponent(auditId)}/extractions/${encodeURIComponent(clauseId)}`,
    {
      method: 'POST',
      headers,
      body: JSON.stringify(editPayload),
    }
  );

  if (!resp.ok) {
    throw new Error(`Extraction re-evaluation failed (${resp.status})`);
  }

  return (await resp.json()) as AuditResponse;
}

export async function downloadReport(
  auditId: string,
  format: 'pdf' | 'docx' | 'csv' | 'json'
): Promise<void> {
  const headers = await authHeaders();
  const resp = await fetch(
    `/api/v1/audits/${encodeURIComponent(auditId)}/report?format=${format}`,
    {
      headers,
    }
  );

  if (!resp.ok) {
    throw new Error(`Report download failed (${resp.status})`);
  }

  const blob = await resp.blob();
  const disposition = resp.headers.get('content-disposition');
  let filename = `tender_audit_${auditId.slice(0, 8)}.${format}`;
  if (disposition && disposition.includes('filename=')) {
    const match = disposition.match(/filename="?([^"]+)"?/);
    if (match && match[1]) {
      filename = match[1];
    }
  }

  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export async function listAudits(limit = 20): Promise<AuditSummary[]> {
  const headers = await authHeaders();
  const resp = await fetch(`/api/v1/audits?limit=${limit}`, {
    headers,
  });

  if (!resp.ok) {
    throw new Error(`Failed to list audits (${resp.status})`);
  }

  return (await resp.json()) as AuditSummary[];
}

export async function fetchAuditDiff(
  draftAId: string,
  draftBId: string
): Promise<AuditDiffResponse> {
  const headers = await authHeaders();
  const resp = await fetch(
    `/api/v1/audits/${encodeURIComponent(draftAId)}/diff/${encodeURIComponent(draftBId)}`,
    {
      headers,
    }
  );

  if (!resp.ok) {
    throw new Error(`Failed to fetch audit diff (${resp.status})`);
  }

  return (await resp.json()) as AuditDiffResponse;
}

export async function fetchReport(
  auditId: string,
  format: 'json' | 'csv'
): Promise<{ text?: string; json?: unknown }> {
  const headers = await authHeaders();
  const resp = await fetch(
    `/api/v1/audits/${encodeURIComponent(auditId)}/report?format=${format}`,
    {
      headers,
    }
  );

  if (!resp.ok) {
    throw new Error(`Report export failed (${resp.status})`);
  }

  if (format === 'csv') {
    const text = await resp.text();
    return { text };
  } else {
    const json = await resp.json();
    return { json };
  }
}


export async function fetchHealth(): Promise<HealthData> {
  const resp = await fetch('/api/v1/health');
  if (!resp.ok) {
    throw new Error(`Health status check failed: HTTP ${resp.status}`);
  }
  return (await resp.json()) as HealthData;
}

export async function fetchVersion(): Promise<VersionData> {
  const resp = await fetch('/api/v1/version');
  if (!resp.ok) {
    throw new Error(`Version check failed: HTTP ${resp.status}`);
  }
  return (await resp.json()) as VersionData;
}

export async function fetchUnverifiedQueue(): Promise<StandardRow[]> {
  const headers = await authHeaders();
  const resp = await fetch('/api/v1/admin/queue/unverified', { headers });
  if (!resp.ok) {
    throw new Error(`Failed to fetch unverified queue (${resp.status})`);
  }
  return (await resp.json()) as StandardRow[];
}

export async function verifyStandardRow(rowId: number): Promise<StandardRow> {
  const headers = await authHeaders();
  const resp = await fetch(`/api/v1/admin/rows/${rowId}/verify`, {
    method: 'POST',
    headers,
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to verify standard (${resp.status})`);
  }
  return (await resp.json()) as StandardRow;
}

export async function fetchStaleRows(staleDays = 180): Promise<StandardRow[]> {
  const headers = await authHeaders();
  const resp = await fetch(`/api/v1/admin/stale?stale_days=${staleDays}`, { headers });
  if (!resp.ok) {
    throw new Error(`Failed to fetch stale standards (${resp.status})`);
  }
  return (await resp.json()) as StandardRow[];
}

export async function reverifyStandardRow(
  rowId: number,
  evidenceRef: string
): Promise<StandardRow> {
  const headers = await authHeaders();
  const resp = await fetch(`/api/v1/admin/rows/${rowId}/re-verify`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ evidence_ref: evidenceRef }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to re-verify standard (${resp.status})`);
  }
  return (await resp.json()) as StandardRow;
}

export async function createStandardRow(row: {
  is_number: string;
  part?: string | null;
  section?: string | null;
  title: string;
  publication_year?: number | null;
  status: string;
  catalogue_url: string;
  evidence_ref: string;
}): Promise<StandardRow> {
  const headers = await authHeaders();
  const resp = await fetch('/api/v1/admin/rows', {
    method: 'POST',
    headers,
    body: JSON.stringify(row),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to create standard row (${resp.status})`);
  }
  return (await resp.json()) as StandardRow;
}

export async function bulkImportCsv(file: File): Promise<BulkImportReport> {
  const token = await ensureAuthToken();
  const formData = new FormData();
  formData.append('file', file);

  const resp = await fetch('/api/v1/admin/import-csv', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `CSV Import failed (${resp.status})`);
  }
  return (await resp.json()) as BulkImportReport;
}

export async function fetchVagueTerms(): Promise<VagueTerm[]> {
  const headers = await authHeaders();
  const resp = await fetch('/api/v1/admin/vague-terms', { headers });
  if (!resp.ok) {
    throw new Error(`Failed to fetch vague terms (${resp.status})`);
  }
  return (await resp.json()) as VagueTerm[];
}

export async function createVagueTerm(term: {
  phrase: string;
  language: string;
  explanation: string;
}): Promise<VagueTerm> {
  const headers = await authHeaders();
  const resp = await fetch('/api/v1/admin/vague-terms', {
    method: 'POST',
    headers,
    body: JSON.stringify(term),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to create vague term (${resp.status})`);
  }
  return (await resp.json()) as VagueTerm;
}

export async function deleteVagueTerm(termId: number): Promise<void> {
  const headers = await authHeaders();
  const resp = await fetch(`/api/v1/admin/vague-terms/${termId}`, {
    method: 'DELETE',
    headers,
  });
  if (!resp.ok) {
    throw new Error(`Failed to delete vague term (${resp.status})`);
  }
}

export async function fetchRulesCatalog(): Promise<RuleItem[]> {
  const headers = await authHeaders();
  const resp = await fetch('/api/v1/admin/rules', { headers });
  if (!resp.ok) {
    throw new Error(`Failed to fetch rules catalog (${resp.status})`);
  }
  return (await resp.json()) as RuleItem[];
}

export async function fetchAuditLogs(limit = 100): Promise<AuditLogRecord[]> {
  const headers = await authHeaders();
  const resp = await fetch(`/api/v1/admin/audit-logs?limit=${limit}`, { headers });
  if (!resp.ok) {
    throw new Error(`Failed to fetch audit logs (${resp.status})`);
  }
  return (await resp.json()) as AuditLogRecord[];
}

