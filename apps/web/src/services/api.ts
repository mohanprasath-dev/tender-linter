import {
  AuditDiffResponse,
  AuditResponse,
  AuditSummary,
  Finding,
  HealthData,
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
