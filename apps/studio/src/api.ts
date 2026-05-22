import type { Catalog, IntegrationSnippets, Policy, SimulateResponse, DecisionTrace } from './types';

const fallbackCatalog: Catalog = {
  name: 'Smart Office Agent Harness',
  version: '0.1.0',
  actions: {
    turn_on: { description: 'Enable a controllable capability.', verbs: ['turn on', 'enable', 'activate'] },
    turn_off: { description: 'Disable a controllable capability.', verbs: ['turn off', 'disable', 'stop'] },
    set: { description: 'Set a supported parameter.', verbs: ['set', 'change', 'adjust'] },
    lock: { description: 'Lock a controlled entry point.', verbs: ['lock', 'secure'] },
    unlock: { description: 'Unlock a controlled entry point.', verbs: ['unlock'], confirmation_required: true },
  },
  capabilities: {
    'Lobby lights': {
      description: 'Lighting zone for reception and waiting area.',
      kind: 'lighting',
      aliases: ['entrance lights', 'front lights'],
      actions: ['turn_on', 'turn_off', 'set'],
      parameters: {
        level: { values: ['low', 'medium', 'high'] },
        temperature: { values: ['warm', 'neutral', 'cool'] },
      },
      state: { status: 'inactive', level: 'medium', temperature: 'neutral' },
    },
    'Meeting room climate': {
      description: 'Climate control zone for meeting rooms.',
      kind: 'climate',
      aliases: ['conference climate', 'meeting rooms'],
      actions: ['turn_on', 'turn_off', 'set'],
      parameters: {
        temperature: { range: [18, 27] },
        mode: { values: ['eco', 'comfort', 'boost'] },
      },
      state: { status: 'inactive', temperature: 22, mode: 'eco' },
    },
    'Server room door': {
      description: 'Restricted access door controlled by policy.',
      kind: 'access',
      aliases: ['data room door', 'restricted door'],
      actions: ['lock', 'unlock'],
      parameters: {},
      state: { status: 'active', last_action: 'lock' },
    },
  },
  groups: {
    'Public areas': {
      description: 'All capabilities visible to visitors.',
      members: ['Lobby lights'],
      aliases: ['front of house'],
      actions: ['turn_on', 'turn_off'],
    },
  },
  scenarios: {
    'Opening mode': {
      description: 'Prepare the office for the day.',
      aliases: ['morning mode'],
      steps: [
        { target: 'Public areas', action: 'turn_on', parameters: {} },
        { target: 'Lobby lights', action: 'set', parameters: { level: 'medium', temperature: 'warm' } },
      ],
    },
  },
};

const fallbackPolicy: Policy = {
  fuzzy_cutoff: 0.62,
  inspect_verbs: ['inspect', 'status', 'show', 'check'],
  scenario_verbs: ['run', 'start', 'activate', 'execute'],
  synonyms: { high: ['maximum', 'bright'], low: ['minimum', 'dim'] },
  confirmations: [{ target: 'Server room door', action: 'unlock', reason: 'Restricted access requires explicit confirmation.' }],
  deny: [],
};

const fallbackSnippets: IntegrationSnippets = {
  mcp_stdio: JSON.stringify(
    {
      command: 'python',
      args: ['-m', 'literal.mcp_server', '--catalog', 'literal.catalog.json', '--policy', 'literal.policy.json'],
    },
    null,
    2,
  ),
  python_sdk: "from literal import harness\n\nh = harness('literal.catalog.json', 'literal.policy.json')\nprint(h.simulate('turn on lobby lights'))\n",
  http: 'curl -X POST http://localhost:8787/api/simulate -H "Content-Type: application/json" -d \'{"text":"turn on lobby lights"}\'',
};

async function getJson<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(path);
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  } catch {
    return fallback;
  }
}

async function sendJson<T>(path: string, method: 'POST' | 'PUT', payload: unknown, fallback: T): Promise<T> {
  try {
    const response = await fetch(path, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  } catch {
    return fallback;
  }
}

export async function fetchCatalog(): Promise<Catalog> {
  return getJson<Catalog>('/api/catalog', fallbackCatalog);
}

export async function fetchPolicy(): Promise<Policy> {
  return getJson<Policy>('/api/policies', fallbackPolicy);
}

export async function saveCatalog(catalog: Catalog): Promise<{ ok: boolean; message: string }> {
  return sendJson('/api/catalog', 'PUT', catalog, { ok: true, message: 'Saved locally in UI state.' });
}

export async function savePolicy(policy: Policy): Promise<{ ok: boolean; message: string }> {
  return sendJson('/api/policies', 'PUT', policy, { ok: true, message: 'Saved locally in UI state.' });
}

export async function simulate(text: string): Promise<SimulateResponse> {
  return sendJson<SimulateResponse>('/api/simulate', 'POST', { text }, { ok: false, route: 'offline', message: 'API offline; run literal dev for live simulation.' });
}

export async function runScenario(name: string): Promise<SimulateResponse> {
  return sendJson<SimulateResponse>('/api/scenario', 'POST', { name }, { ok: false, route: 'offline', message: 'API offline; run literal dev for live scenarios.' });
}

export async function fetchTraces(): Promise<DecisionTrace[]> {
  const payload = await getJson<{ traces: DecisionTrace[] }>('/api/traces?limit=100', { traces: [] });
  return payload.traces || [];
}

export async function fetchIntegrations(): Promise<IntegrationSnippets> {
  return getJson<IntegrationSnippets>('/api/integration', fallbackSnippets);
}
