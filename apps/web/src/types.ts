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
