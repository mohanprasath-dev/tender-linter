export type Severity = 'ERROR' | 'WARNING' | 'INFO' | 'CANNOT_VERIFY';

export interface CitationItem {
  raw: string;
  span: [number, number];
  is_number: string;
  part?: string | null;
  section?: string | null;
  year?: number | null;
}

export interface ProductItem {
  text: string;
  span: [number, number];
  canonical_product_id?: string | null;
}

export interface Extractions {
  citations: CitationItem[];
  products: ProductItem[];
  mentions_certification: boolean;
  vague_phrases: unknown[];
}

export interface Clause {
  id: string;
  text: string;
  extractions: Extractions;
}

export interface FindingEvidence {
  url?: string | null;
  verified_on?: string | null;
  row_id?: number | null;
  instrument?: string | null;
  candidate?: string | null;
  term?: string | null;
  explanation?: string | null;
}

export interface Finding {
  id: string;
  rule_id: string;
  severity: Severity;
  clause_id: string;
  span: [number, number] | null;
  message_en: string;
  message_hi?: string | null;
  evidence?: FindingEvidence | null;
  decision?: 'ACCEPT' | 'DISMISS' | 'NOT_APPLICABLE' | null;
  decision_reason?: string | null;
  rule_set_version: string;
  model_version?: string | null;
  prompt_version?: string | null;
}

export interface AuditResponse {
  id: string;
  document_name?: string | null;
  status: string;
  language_hint: string;
  clauses: Clause[];
  findings: Finding[];
}

export interface MatrixCase {
  id: string;
  title: string;
  clause: string;
  expectedRules: string[];
  language: string;
  notes: string;
}

export interface HealthData {
  status: string;
  app: string;
  environment: string;
  database: string;
}

export interface VersionData {
  app: string;
  rule_set: string | null;
  model: string | null;
  prompt: string | null;
}

export interface AuditSummary {
  id: string;
  document_name?: string | null;
  created_at: string;
  created_by: string;
  status: string;
  language_hint: string;
  total_clauses: number;
  total_findings: number;
}

export interface ClauseDiffItem {
  id: string;
  old_text?: string;
  new_text?: string;
  text?: string;
}

export interface ClauseDiff {
  added: ClauseDiffItem[];
  removed: ClauseDiffItem[];
  modified: ClauseDiffItem[];
  unchanged: ClauseDiffItem[];
}

export interface AuditDiffResponse {
  draft_a_id: string;
  draft_b_id: string;
  added_findings: Finding[];
  resolved_findings: Finding[];
  retained_findings: Finding[];
  clause_diff: ClauseDiff;
  summary: {
    total_findings_draft_a: number;
    total_findings_draft_b: number;
    added_count: number;
    resolved_count: number;
    retained_count: number;
    clauses_added_count: number;
    clauses_modified_count: number;
    clauses_removed_count: number;
  };
}

export interface StandardRow {
  id: number;
  is_number: string;
  part?: string | null;
  section?: string | null;
  title: string;
  publication_year?: number | null;
  status: string;
  catalogue_url: string;
  verified_on: string;
  verified_by: string;
  second_checked_by?: string | null;
  evidence_ref: string;
}

export interface BulkImportReport {
  total_rows: number;
  imported_count: number;
  rejected_count: number;
  errors: Array<{ line: number; reason: string }>;
}

export interface VagueTerm {
  id: number;
  phrase: string;
  language: string;
  explanation: string;
}

export interface RuleItem {
  id: string;
  name: string;
  severity: Severity;
  fires_when: string;
  evidence: string;
  message_en: string;
  message_hi?: string | null;
}

export interface AuditLogRecord {
  id: number;
  timestamp: string;
  user_id?: number | null;
  action: string;
  table_name: string;
  record_id: number;
  old_values?: string | null;
  new_values?: string | null;
}


