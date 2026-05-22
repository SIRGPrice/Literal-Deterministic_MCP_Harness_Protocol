export type ActionDefinition = {
  description?: string;
  verbs?: string[];
  confirmation_required?: boolean;
};

export type ParameterDefinition = {
  description?: string;
  values?: string[];
  range?: [number, number];
  required?: boolean;
};

export type CapabilityDefinition = {
  description?: string;
  kind?: string;
  aliases?: string[];
  actions: string[];
  parameters?: Record<string, ParameterDefinition>;
  state?: Record<string, unknown>;
};

export type GroupDefinition = {
  description?: string;
  members: string[];
  aliases?: string[];
  actions: string[];
};

export type ScenarioStep = {
  target: string;
  action: string;
  parameters?: Record<string, unknown>;
  description?: string;
};

export type ScenarioDefinition = {
  description?: string;
  aliases?: string[];
  steps: ScenarioStep[];
};

export type Catalog = {
  name?: string;
  version?: string;
  actions: Record<string, ActionDefinition>;
  capabilities: Record<string, CapabilityDefinition>;
  groups?: Record<string, GroupDefinition>;
  scenarios?: Record<string, ScenarioDefinition>;
  policies?: Policy;
};

export type Rule = {
  target?: string;
  action?: string;
  reason?: string;
};

export type Policy = {
  fuzzy_cutoff?: number;
  inspect_verbs?: string[];
  scenario_verbs?: string[];
  synonyms?: Record<string, string[]>;
  confirmations?: Rule[];
  deny?: Rule[];
};

export type DecisionTrace = {
  id: string;
  created_at: number;
  route: string;
  input_text?: string;
  target?: string;
  action?: string;
  parameters?: Record<string, unknown>;
  outcome?: string;
  latency_ms?: number;
  errors?: string[];
  requires_confirmation?: boolean;
  matches?: Array<{
    field: string;
    requested: string;
    resolved?: string | null;
    score: number;
    method: string;
    suggestions?: string[];
  }>;
};

export type IntegrationSnippets = Record<'mcp_stdio' | 'python_sdk' | 'http', string>;

export type SimulateResponse = {
  ok: boolean;
  route?: string;
  message?: string;
  target?: string;
  action?: string;
  parameters?: Record<string, unknown>;
  result?: unknown;
  trace?: DecisionTrace;
  steps?: SimulateResponse[];
};
