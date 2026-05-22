import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Activity,
  AlertCircle,
  Boxes,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clipboard,
  ClipboardCheck,
  Download,
  FileJson,
  Gauge,
  GitBranch,
  LayoutDashboard,
  Layers,
  MessageSquareCode,
  Moon,
  Play,
  PlugZap,
  Plus,
  RefreshCw,
  Save,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  Sun,
  Trash2,
  Undo2,
  Upload,
  XCircle,
} from 'lucide-react';
import {
  fetchCatalog,
  fetchIntegrations,
  fetchPolicy,
  fetchTraces,
  runScenario,
  saveCatalog,
  savePolicy,
  simulate,
} from './api';
import type {
  ActionDefinition,
  Catalog,
  CapabilityDefinition,
  DecisionTrace,
  GroupDefinition,
  IntegrationSnippets,
  ParameterDefinition,
  Policy,
  Rule,
  ScenarioDefinition,
  ScenarioStep,
  SimulateResponse,
} from './types';

type TabKey =
  | 'dashboard'
  | 'actions'
  | 'capabilities'
  | 'groups'
  | 'scenarios'
  | 'policies'
  | 'simulator'
  | 'traces'
  | 'integrations'
  | 'settings';

type Theme = 'light' | 'dark';

type Notice = { tone: 'ok' | 'err'; text: string };

type EditorProps = { catalog: Catalog; setCatalog: (next: Catalog) => void };

const TABS: Array<{ key: TabKey; label: string; icon: typeof LayoutDashboard; group: string }> = [
  { key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, group: 'Overview' },
  { key: 'actions', label: 'Actions', icon: PlugZap, group: 'Catalog' },
  { key: 'capabilities', label: 'Capabilities', icon: Boxes, group: 'Catalog' },
  { key: 'groups', label: 'Groups', icon: Layers, group: 'Catalog' },
  { key: 'scenarios', label: 'Scenarios', icon: GitBranch, group: 'Catalog' },
  { key: 'policies', label: 'Policies', icon: ShieldCheck, group: 'Governance' },
  { key: 'simulator', label: 'Simulator', icon: MessageSquareCode, group: 'Runtime' },
  { key: 'traces', label: 'Traces', icon: Activity, group: 'Runtime' },
  { key: 'integrations', label: 'Integrations', icon: PlugZap, group: 'Connect' },
  { key: 'settings', label: 'Settings', icon: Settings, group: 'Connect' },
];

const NAV_GROUPS = ['Overview', 'Catalog', 'Governance', 'Runtime', 'Connect'];

const EMPTY_CATALOG: Catalog = { actions: {}, capabilities: {} };
const EMPTY_POLICY: Policy = {};

export default function App() {
  const [activeTab, setActiveTab] = useState<TabKey>('dashboard');
  const [theme, setTheme] = useState<Theme>(() => (localStorage.getItem('literal.theme') as Theme) || 'light');
  const [catalog, setCatalog] = useState<Catalog>(EMPTY_CATALOG);
  const [policy, setPolicy] = useState<Policy>(EMPTY_POLICY);
  const [savedCatalog, setSavedCatalog] = useState<Catalog>(EMPTY_CATALOG);
  const [savedPolicy, setSavedPolicy] = useState<Policy>(EMPTY_POLICY);
  const [traces, setTraces] = useState<DecisionTrace[]>([]);
  const [snippets, setSnippets] = useState<IntegrationSnippets | null>(null);
  const [prompt, setPrompt] = useState('turn on lobby lights');
  const [result, setResult] = useState<SimulateResponse | null>(null);
  const [selectedScenario, setSelectedScenario] = useState('');
  const [notice, setNotice] = useState<Notice | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('literal.theme', theme);
  }, [theme]);

  const refreshAll = useCallback(async () => {
    setLoading(true);
    try {
      const [nextCatalog, nextPolicy, nextTraces, nextSnippets] = await Promise.all([
        fetchCatalog(),
        fetchPolicy(),
        fetchTraces(),
        fetchIntegrations(),
      ]);
      setCatalog(nextCatalog);
      setSavedCatalog(nextCatalog);
      setPolicy(nextPolicy);
      setSavedPolicy(nextPolicy);
      setTraces(nextTraces);
      setSnippets(nextSnippets);
      const firstScenario = Object.keys(nextCatalog.scenarios ?? {})[0] ?? '';
      setSelectedScenario(firstScenario);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshAll();
  }, [refreshAll]);

  const dirty = useMemo(
    () =>
      JSON.stringify(catalog) !== JSON.stringify(savedCatalog) ||
      JSON.stringify(policy) !== JSON.stringify(savedPolicy),
    [catalog, policy, savedCatalog, savedPolicy],
  );

  const metrics = useMemo(() => {
    const actions = Object.keys(catalog.actions ?? {}).length;
    const capabilities = Object.keys(catalog.capabilities ?? {}).length;
    const groups = Object.keys(catalog.groups ?? {}).length;
    const scenarios = Object.keys(catalog.scenarios ?? {}).length;
    const confirmations = policy.confirmations?.length ?? 0;
    const denials = policy.deny?.length ?? 0;
    const synonyms = Object.keys(policy.synonyms ?? {}).length;
    return { actions, capabilities, groups, scenarios, confirmations, denials, synonyms };
  }, [catalog, policy]);

  const notify = useCallback((tone: 'ok' | 'err', text: string) => {
    setNotice({ tone, text });
    window.setTimeout(() => setNotice(null), 3500);
  }, []);

  async function persistAll() {
    setBusy(true);
    try {
      const catalogResponse = await saveCatalog(catalog);
      const policyResponse = await savePolicy(policy);
      setSavedCatalog(catalog);
      setSavedPolicy(policy);
      const ok = catalogResponse.ok && policyResponse.ok;
      notify(ok ? 'ok' : 'err', ok ? 'Configuration saved' : 'Saved locally only');
    } finally {
      setBusy(false);
    }
  }

  function revertAll() {
    setCatalog(savedCatalog);
    setPolicy(savedPolicy);
    notify('ok', 'Reverted unsaved changes');
  }

  async function handleSimulate(text = prompt) {
    setBusy(true);
    try {
      const response = await simulate(text);
      setResult(response);
      setTraces(await fetchTraces());
    } finally {
      setBusy(false);
    }
  }

  async function handleRunScenario(name: string) {
    if (!name) return;
    setBusy(true);
    try {
      const response = await runScenario(name);
      setResult(response);
      setTraces(await fetchTraces());
      setActiveTab('simulator');
    } finally {
      setBusy(false);
    }
  }

  function exportConfig() {
    const blob = new Blob([JSON.stringify({ catalog, policy }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${(catalog.name ?? 'literal').replace(/\s+/g, '-').toLowerCase()}-config.json`;
    link.click();
    URL.revokeObjectURL(url);
    notify('ok', 'Exported configuration');
  }

  function importConfig(file: File) {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const parsed = JSON.parse(String(reader.result));
        if (parsed.catalog) setCatalog(parsed.catalog as Catalog);
        if (parsed.policy) setPolicy(parsed.policy as Policy);
        notify('ok', 'Imported configuration (review and save)');
      } catch (caught) {
        notify('err', caught instanceof Error ? caught.message : 'Invalid JSON');
      }
    };
    reader.readAsText(file);
  }

  if (loading) {
    return (
      <div className="boot">
        <Gauge size={28} />
        <span>Loading Literal Studio…</span>
      </div>
    );
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <SlidersHorizontal size={20} />
          </div>
          <div className="brand-text">
            <strong>Literal</strong>
            <span>{catalog.version ?? '0.2.0'} · Literal Studio</span>
          </div>
        </div>
        <nav>
          {NAV_GROUPS.map((group) => {
            const groupTabs = TABS.filter((tab) => tab.group === group);
            if (!groupTabs.length) return null;
            return (
              <div className="nav-group" key={group}>
                <span className="nav-label">{group}</span>
                {groupTabs.map((tab) => {
                  const Icon = tab.icon;
                  const count = badgeFor(tab.key, metrics, traces);
                  return (
                    <button
                      key={tab.key}
                      className={activeTab === tab.key ? 'active' : ''}
                      onClick={() => setActiveTab(tab.key)}
                    >
                      <Icon size={17} />
                      <span>{tab.label}</span>
                      {count !== undefined && <em>{count}</em>}
                    </button>
                  );
                })}
              </div>
            );
          })}
        </nav>
        <div className="sidebar-footer">
          <button className="ghost" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
            {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />} {theme === 'dark' ? 'Light' : 'Dark'} mode
          </button>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="title-block">
            <p className="eyebrow">{catalog.name ?? 'Agent Harness'}</p>
            <h1>{TABS.find((tab) => tab.key === activeTab)?.label}</h1>
            <p className="subtitle">{subtitleFor(activeTab)}</p>
          </div>
          <div className="top-actions">
            {notice && (
              <span className={`notice ${notice.tone}`}>
                {notice.tone === 'ok' ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
                {notice.text}
              </span>
            )}
            {dirty && <span className="dirty-flag">Unsaved changes</span>}
            <input
              ref={fileInputRef}
              type="file"
              accept="application/json"
              hidden
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) importConfig(file);
                event.target.value = '';
              }}
            />
            <button className="ghost" onClick={() => fileInputRef.current?.click()} title="Import">
              <Upload size={15} /> Import
            </button>
            <button className="ghost" onClick={exportConfig} title="Export">
              <Download size={15} /> Export
            </button>
            <button className="ghost" onClick={() => void refreshAll()} title="Reload from server">
              <RefreshCw size={15} />
            </button>
            <button className="ghost" disabled={!dirty} onClick={revertAll} title="Revert">
              <Undo2 size={15} /> Revert
            </button>
            <button className="primary" disabled={!dirty || busy} onClick={() => void persistAll()}>
              <Save size={16} /> Save changes
            </button>
          </div>
        </header>

        <div className="content">
          {activeTab === 'dashboard' && (
            <DashboardView
              metrics={metrics}
              traces={traces}
              prompt={prompt}
              busy={busy}
              result={result}
              setPrompt={setPrompt}
              onSimulate={() => void handleSimulate()}
            />
          )}
          {activeTab === 'actions' && <ActionsView catalog={catalog} setCatalog={setCatalog} />}
          {activeTab === 'capabilities' && <CapabilitiesView catalog={catalog} setCatalog={setCatalog} />}
          {activeTab === 'groups' && <GroupsView catalog={catalog} setCatalog={setCatalog} />}
          {activeTab === 'scenarios' && (
            <ScenariosView
              catalog={catalog}
              setCatalog={setCatalog}
              onRun={(name) => void handleRunScenario(name)}
              busy={busy}
            />
          )}
          {activeTab === 'policies' && (
            <PoliciesView policy={policy} setPolicy={setPolicy} catalog={catalog} />
          )}
          {activeTab === 'simulator' && (
            <SimulatorView
              prompt={prompt}
              setPrompt={setPrompt}
              busy={busy}
              result={result}
              scenarios={Object.keys(catalog.scenarios ?? {})}
              selectedScenario={selectedScenario}
              setSelectedScenario={setSelectedScenario}
              onSimulate={() => void handleSimulate()}
              onRunScenario={(name) => void handleRunScenario(name)}
            />
          )}
          {activeTab === 'traces' && <TracesView traces={traces} />}
          {activeTab === 'integrations' && <IntegrationsView snippets={snippets} />}
          {activeTab === 'settings' && (
            <SettingsView
              catalog={catalog}
              policy={policy}
              setCatalog={setCatalog}
              setPolicy={setPolicy}
            />
          )}
        </div>
      </main>
    </div>
  );
}

/* ----------------------------- Dashboard ----------------------------- */

function DashboardView({
  metrics,
  traces,
  prompt,
  busy,
  result,
  setPrompt,
  onSimulate,
}: {
  metrics: Record<string, number>;
  traces: DecisionTrace[];
  prompt: string;
  busy: boolean;
  result: SimulateResponse | null;
  setPrompt: (value: string) => void;
  onSimulate: () => void;
}) {
  return (
    <div className="view-grid four">
      <Metric icon={Boxes} label="Capabilities" value={metrics.capabilities} tone="green" />
      <Metric icon={PlugZap} label="Actions" value={metrics.actions} tone="blue" />
      <Metric icon={GitBranch} label="Scenarios" value={metrics.scenarios} tone="amber" />
      <Metric icon={ShieldCheck} label="Guardrails" value={metrics.confirmations + metrics.denials} tone="red" />
      <Panel title="Recent decisions" icon={Activity} span={2}>
        <TraceList traces={traces.slice(0, 6)} compact />
      </Panel>
      <Panel title="Fast simulation" icon={MessageSquareCode} span={2}>
        <div className="prompt-row">
          <input
            aria-label="Simulation prompt"
            placeholder="turn on lobby lights"
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
          />
          <button className="primary" disabled={busy} onClick={onSimulate}>
            <Play size={15} /> Run
          </button>
        </div>
        {result && <ResultCard result={result} />}
      </Panel>
    </div>
  );
}

/* ----------------------------- Actions editor ----------------------------- */

function ActionsView({ catalog, setCatalog }: EditorProps) {
  const [newName, setNewName] = useState('');

  function addAction() {
    const name = newName.trim();
    if (!name || catalog.actions[name]) return;
    setCatalog({
      ...catalog,
      actions: { ...catalog.actions, [name]: { description: '', verbs: [] } },
    });
    setNewName('');
  }
  function updateAction(name: string, next: ActionDefinition) {
    setCatalog({ ...catalog, actions: { ...catalog.actions, [name]: next } });
  }
  function renameAction(oldName: string, nextName: string) {
    nextName = nextName.trim();
    if (!nextName || nextName === oldName || catalog.actions[nextName]) return;
    const entries = Object.entries(catalog.actions).map(([key, value]) =>
      key === oldName ? [nextName, value] : [key, value],
    );
    setCatalog({ ...catalog, actions: Object.fromEntries(entries) });
  }
  function removeAction(name: string) {
    if (!confirm(`Delete action "${name}"?`)) return;
    const next = { ...catalog.actions };
    delete next[name];
    setCatalog({ ...catalog, actions: next });
  }

  return (
    <div className="stack">
      <ToolbarPanel>
        <input
          aria-label="New action name"
          placeholder="e.g. dim, lock, set"
          value={newName}
          onChange={(event) => setNewName(event.target.value)}
        />
        <button className="primary" onClick={addAction}>
          <Plus size={15} /> Add action
        </button>
      </ToolbarPanel>
      <div className="cards-grid">
        {Object.entries(catalog.actions).map(([name, definition]) => (
          <article className="card" key={name}>
            <div className="card-head">
              <EditableTitle value={name} onCommit={(next) => renameAction(name, next)} />
              <button className="icon-button danger" onClick={() => removeAction(name)} aria-label="Delete">
                <Trash2 size={15} />
              </button>
            </div>
            <Field label="Description">
              <input
                aria-label={`${name} description`}
                value={definition.description ?? ''}
                onChange={(event) => updateAction(name, { ...definition, description: event.target.value })}
              />
            </Field>
            <Field label="Verbs / triggers" hint="Comma-separated phrases that map to this action.">
              <TagInput
                values={definition.verbs ?? []}
                onChange={(verbs) => updateAction(name, { ...definition, verbs })}
                placeholder="turn on, enable"
              />
            </Field>
            <Toggle
              label="Requires confirmation"
              value={Boolean(definition.confirmation_required)}
              onChange={(next) => updateAction(name, { ...definition, confirmation_required: next })}
            />
          </article>
        ))}
        {!Object.keys(catalog.actions).length && <Empty label="No actions yet. Add the first one above." />}
      </div>
    </div>
  );
}

/* ----------------------------- Capabilities editor ----------------------------- */

function CapabilitiesView({ catalog, setCatalog }: EditorProps) {
  const [newName, setNewName] = useState('');
  const [expanded, setExpanded] = useState<string | null>(null);
  const actionOptions = Object.keys(catalog.actions);

  function addCapability() {
    const name = newName.trim();
    if (!name || catalog.capabilities[name]) return;
    setCatalog({
      ...catalog,
      capabilities: {
        ...catalog.capabilities,
        [name]: {
          description: '',
          kind: 'custom',
          aliases: [],
          actions: actionOptions.slice(0, 1),
          parameters: {},
          state: { status: 'inactive' },
        },
      },
    });
    setNewName('');
    setExpanded(name);
  }
  function update(name: string, next: CapabilityDefinition) {
    setCatalog({ ...catalog, capabilities: { ...catalog.capabilities, [name]: next } });
  }
  function rename(oldName: string, nextName: string) {
    nextName = nextName.trim();
    if (!nextName || nextName === oldName || catalog.capabilities[nextName]) return;
    const entries = Object.entries(catalog.capabilities).map(([key, value]) =>
      key === oldName ? [nextName, value] : [key, value],
    );
    setCatalog({ ...catalog, capabilities: Object.fromEntries(entries) });
    setExpanded(nextName);
  }
  function remove(name: string) {
    if (!confirm(`Delete capability "${name}"?`)) return;
    const next = { ...catalog.capabilities };
    delete next[name];
    setCatalog({ ...catalog, capabilities: next });
  }

  return (
    <div className="stack">
      <ToolbarPanel>
        <input
          aria-label="New capability name"
          placeholder="e.g. Lobby lights"
          value={newName}
          onChange={(event) => setNewName(event.target.value)}
        />
        <button className="primary" onClick={addCapability}>
          <Plus size={15} /> Add capability
        </button>
      </ToolbarPanel>
      <div className="stack">
        {Object.entries(catalog.capabilities).map(([name, definition]) => (
          <CapabilityRow
            key={name}
            name={name}
            definition={definition}
            actionOptions={actionOptions}
            expanded={expanded === name}
            onToggle={() => setExpanded(expanded === name ? null : name)}
            onUpdate={(next) => update(name, next)}
            onRename={(next) => rename(name, next)}
            onRemove={() => remove(name)}
          />
        ))}
        {!Object.keys(catalog.capabilities).length && (
          <Empty label="No capabilities yet. Add the first one above." />
        )}
      </div>
    </div>
  );
}

function CapabilityRow({
  name,
  definition,
  actionOptions,
  expanded,
  onToggle,
  onUpdate,
  onRename,
  onRemove,
}: {
  name: string;
  definition: CapabilityDefinition;
  actionOptions: string[];
  expanded: boolean;
  onToggle: () => void;
  onUpdate: (next: CapabilityDefinition) => void;
  onRename: (next: string) => void;
  onRemove: () => void;
}) {
  return (
    <article className={`row-card ${expanded ? 'expanded' : ''}`}>
      <header className="row-head" onClick={onToggle}>
        <button className="chevron" aria-label={expanded ? 'Collapse' : 'Expand'}>
          {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </button>
        <div className="row-title">
          <strong>{name}</strong>
          <span>{definition.kind ?? 'capability'}</span>
        </div>
        <div className="row-meta">
          <span className="pill ghost">{(definition.actions ?? []).length} actions</span>
          <span className="pill ghost">{Object.keys(definition.parameters ?? {}).length} params</span>
          <button
            className="icon-button danger"
            onClick={(event) => {
              event.stopPropagation();
              onRemove();
            }}
            aria-label="Delete"
          >
            <Trash2 size={15} />
          </button>
        </div>
      </header>
      {expanded && (
        <div className="row-body">
          <div className="grid two">
            <Field label="Name">
              <input
                aria-label="Capability name"
                value={name}
                onChange={(event) => onRename(event.target.value)}
              />
            </Field>
            <Field label="Kind">
              <input
                aria-label="Capability kind"
                value={definition.kind ?? ''}
                placeholder="lighting, climate, access…"
                onChange={(event) => onUpdate({ ...definition, kind: event.target.value })}
              />
            </Field>
          </div>
          <Field label="Description">
            <textarea
              aria-label="Capability description"
              value={definition.description ?? ''}
              rows={2}
              onChange={(event) => onUpdate({ ...definition, description: event.target.value })}
            />
          </Field>
          <Field label="Aliases">
            <TagInput
              values={definition.aliases ?? []}
              onChange={(aliases) => onUpdate({ ...definition, aliases })}
              placeholder="alternative names"
            />
          </Field>
          <Field label="Supported actions">
            <MultiCheck
              options={actionOptions}
              values={definition.actions ?? []}
              onChange={(actions) => onUpdate({ ...definition, actions })}
            />
          </Field>
          <ParametersEditor
            parameters={definition.parameters ?? {}}
            onChange={(parameters) => onUpdate({ ...definition, parameters })}
          />
          <StateEditor
            state={definition.state ?? {}}
            onChange={(state) => onUpdate({ ...definition, state })}
          />
        </div>
      )}
    </article>
  );
}

function ParametersEditor({
  parameters,
  onChange,
}: {
  parameters: Record<string, ParameterDefinition>;
  onChange: (next: Record<string, ParameterDefinition>) => void;
}) {
  const [name, setName] = useState('');

  function add() {
    const key = name.trim();
    if (!key || parameters[key]) return;
    onChange({ ...parameters, [key]: { values: [] } });
    setName('');
  }
  function update(key: string, next: ParameterDefinition) {
    onChange({ ...parameters, [key]: next });
  }
  function rename(oldKey: string, nextKey: string) {
    nextKey = nextKey.trim();
    if (!nextKey || nextKey === oldKey || parameters[nextKey]) return;
    const entries = Object.entries(parameters).map(([key, value]) =>
      key === oldKey ? [nextKey, value] : [key, value],
    );
    onChange(Object.fromEntries(entries));
  }
  function remove(key: string) {
    const next = { ...parameters };
    delete next[key];
    onChange(next);
  }

  return (
    <div className="subsection">
      <div className="subsection-head">
        <h3>Parameters</h3>
        <div className="inline">
          <input
            aria-label="New parameter name"
            placeholder="level, temperature…"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
          <button onClick={add}>
            <Plus size={14} /> Add
          </button>
        </div>
      </div>
      <div className="stack">
        {Object.entries(parameters).map(([key, definition]) => {
          const mode: 'values' | 'range' | 'free' = definition.range
            ? 'range'
            : definition.values
            ? 'values'
            : 'free';
          return (
            <div className="param-row" key={key}>
              <div className="grid three">
                <Field label="Name">
                  <input
                    aria-label="Parameter name"
                    value={key}
                    onChange={(event) => rename(key, event.target.value)}
                  />
                </Field>
                <Field label="Mode">
                  <select
                    aria-label="Parameter mode"
                    value={mode}
                    onChange={(event) => {
                      const next = event.target.value as 'values' | 'range' | 'free';
                      if (next === 'values')
                        update(key, { ...definition, values: definition.values ?? [], range: undefined });
                      else if (next === 'range')
                        update(key, { ...definition, range: definition.range ?? [0, 100], values: undefined });
                      else update(key, { ...definition, values: undefined, range: undefined });
                    }}
                  >
                    <option value="values">Enum values</option>
                    <option value="range">Numeric range</option>
                    <option value="free">Freeform</option>
                  </select>
                </Field>
                <div className="param-actions">
                  <Toggle
                    label="Required"
                    value={Boolean(definition.required)}
                    onChange={(required) => update(key, { ...definition, required })}
                  />
                  <button className="icon-button danger" onClick={() => remove(key)} aria-label="Delete parameter">
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
              {mode === 'values' && (
                <Field label="Allowed values">
                  <TagInput
                    values={definition.values ?? []}
                    onChange={(values) => update(key, { ...definition, values })}
                    placeholder="low, medium, high"
                  />
                </Field>
              )}
              {mode === 'range' && (
                <div className="grid two">
                  <Field label="Min">
                    <input
                      aria-label="Range minimum"
                      type="number"
                      value={definition.range?.[0] ?? 0}
                      onChange={(event) =>
                        update(key, {
                          ...definition,
                          range: [Number(event.target.value), definition.range?.[1] ?? 0],
                        })
                      }
                    />
                  </Field>
                  <Field label="Max">
                    <input
                      aria-label="Range maximum"
                      type="number"
                      value={definition.range?.[1] ?? 0}
                      onChange={(event) =>
                        update(key, {
                          ...definition,
                          range: [definition.range?.[0] ?? 0, Number(event.target.value)],
                        })
                      }
                    />
                  </Field>
                </div>
              )}
              <Field label="Description">
                <input
                  aria-label="Parameter description"
                  value={definition.description ?? ''}
                  onChange={(event) => update(key, { ...definition, description: event.target.value })}
                />
              </Field>
            </div>
          );
        })}
        {!Object.keys(parameters).length && <Empty label="No parameters" small />}
      </div>
    </div>
  );
}

function StateEditor({
  state,
  onChange,
}: {
  state: Record<string, unknown>;
  onChange: (next: Record<string, unknown>) => void;
}) {
  const [key, setKey] = useState('');

  function add() {
    const name = key.trim();
    if (!name || name in state) return;
    onChange({ ...state, [name]: '' });
    setKey('');
  }
  function update(name: string, value: string) {
    let parsed: unknown = value;
    if (value === 'true') parsed = true;
    else if (value === 'false') parsed = false;
    else if (value !== '' && !Number.isNaN(Number(value))) parsed = Number(value);
    onChange({ ...state, [name]: parsed });
  }
  function remove(name: string) {
    const next = { ...state };
    delete next[name];
    onChange(next);
  }

  return (
    <div className="subsection">
      <div className="subsection-head">
        <h3>Initial state</h3>
        <div className="inline">
          <input
            aria-label="New state key"
            placeholder="status, level…"
            value={key}
            onChange={(event) => setKey(event.target.value)}
          />
          <button onClick={add}>
            <Plus size={14} /> Add
          </button>
        </div>
      </div>
      <div className="kv-grid">
        {Object.entries(state).map(([name, value]) => (
          <div className="kv-row" key={name}>
            <code>{name}</code>
            <input
              aria-label={`State value for ${name}`}
              value={String(value ?? '')}
              onChange={(event) => update(name, event.target.value)}
            />
            <button className="icon-button danger" onClick={() => remove(name)} aria-label={`Delete ${name}`}>
              <Trash2 size={14} />
            </button>
          </div>
        ))}
        {!Object.keys(state).length && <Empty label="No state" small />}
      </div>
    </div>
  );
}

/* ----------------------------- Groups editor ----------------------------- */

function GroupsView({ catalog, setCatalog }: EditorProps) {
  const [newName, setNewName] = useState('');
  const capabilityOptions = Object.keys(catalog.capabilities);
  const actionOptions = Object.keys(catalog.actions);
  const groups = catalog.groups ?? {};

  function add() {
    const name = newName.trim();
    if (!name || groups[name]) return;
    setCatalog({
      ...catalog,
      groups: { ...groups, [name]: { description: '', members: [], aliases: [], actions: [] } },
    });
    setNewName('');
  }
  function update(name: string, next: GroupDefinition) {
    setCatalog({ ...catalog, groups: { ...groups, [name]: next } });
  }
  function rename(oldName: string, nextName: string) {
    nextName = nextName.trim();
    if (!nextName || nextName === oldName || groups[nextName]) return;
    const entries = Object.entries(groups).map(([key, value]) =>
      key === oldName ? [nextName, value] : [key, value],
    );
    setCatalog({ ...catalog, groups: Object.fromEntries(entries) });
  }
  function remove(name: string) {
    if (!confirm(`Delete group "${name}"?`)) return;
    const next = { ...groups };
    delete next[name];
    setCatalog({ ...catalog, groups: next });
  }

  return (
    <div className="stack">
      <ToolbarPanel>
        <input
          aria-label="New group name"
          placeholder="Public areas, Restricted zones…"
          value={newName}
          onChange={(event) => setNewName(event.target.value)}
        />
        <button className="primary" onClick={add}>
          <Plus size={15} /> Add group
        </button>
      </ToolbarPanel>
      <div className="cards-grid">
        {Object.entries(groups).map(([name, group]) => (
          <article className="card" key={name}>
            <div className="card-head">
              <EditableTitle value={name} onCommit={(next) => rename(name, next)} />
              <button className="icon-button danger" onClick={() => remove(name)} aria-label="Delete group">
                <Trash2 size={15} />
              </button>
            </div>
            <Field label="Description">
              <input
                aria-label="Group description"
                value={group.description ?? ''}
                onChange={(event) => update(name, { ...group, description: event.target.value })}
              />
            </Field>
            <Field label="Members">
              <MultiCheck
                options={capabilityOptions}
                values={group.members ?? []}
                onChange={(members) => update(name, { ...group, members })}
              />
            </Field>
            <Field label="Allowed actions">
              <MultiCheck
                options={actionOptions}
                values={group.actions ?? []}
                onChange={(actions) => update(name, { ...group, actions })}
              />
            </Field>
            <Field label="Aliases">
              <TagInput
                values={group.aliases ?? []}
                onChange={(aliases) => update(name, { ...group, aliases })}
                placeholder="front of house, all lights"
              />
            </Field>
          </article>
        ))}
        {!Object.keys(groups).length && <Empty label="No groups yet" />}
      </div>
    </div>
  );
}

/* ----------------------------- Scenarios editor ----------------------------- */

function ScenariosView({
  catalog,
  setCatalog,
  onRun,
  busy,
}: EditorProps & { onRun: (name: string) => void; busy: boolean }) {
  const [newName, setNewName] = useState('');
  const scenarios = catalog.scenarios ?? {};
  const targets = [...Object.keys(catalog.capabilities), ...Object.keys(catalog.groups ?? {})];
  const actions = Object.keys(catalog.actions);

  function add() {
    const name = newName.trim();
    if (!name || scenarios[name]) return;
    setCatalog({
      ...catalog,
      scenarios: { ...scenarios, [name]: { description: '', aliases: [], steps: [] } },
    });
    setNewName('');
  }
  function update(name: string, next: ScenarioDefinition) {
    setCatalog({ ...catalog, scenarios: { ...scenarios, [name]: next } });
  }
  function rename(oldName: string, nextName: string) {
    nextName = nextName.trim();
    if (!nextName || nextName === oldName || scenarios[nextName]) return;
    const entries = Object.entries(scenarios).map(([key, value]) =>
      key === oldName ? [nextName, value] : [key, value],
    );
    setCatalog({ ...catalog, scenarios: Object.fromEntries(entries) });
  }
  function remove(name: string) {
    if (!confirm(`Delete scenario "${name}"?`)) return;
    const next = { ...scenarios };
    delete next[name];
    setCatalog({ ...catalog, scenarios: next });
  }

  return (
    <div className="stack">
      <ToolbarPanel>
        <input
          aria-label="New scenario name"
          placeholder="Opening mode, Closing mode…"
          value={newName}
          onChange={(event) => setNewName(event.target.value)}
        />
        <button className="primary" onClick={add}>
          <Plus size={15} /> Add scenario
        </button>
      </ToolbarPanel>
      <div className="cards-grid scenario-grid">
        {Object.entries(scenarios).map(([name, scenario]) => (
          <article className="card" key={name}>
            <div className="card-head">
              <EditableTitle value={name} onCommit={(next) => rename(name, next)} />
              <div className="inline">
                <button className="primary small" disabled={busy} onClick={() => onRun(name)}>
                  <Play size={14} /> Run
                </button>
                <button className="icon-button danger" onClick={() => remove(name)} aria-label="Delete scenario">
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
            <Field label="Description">
              <input
                aria-label="Scenario description"
                value={scenario.description ?? ''}
                onChange={(event) => update(name, { ...scenario, description: event.target.value })}
              />
            </Field>
            <Field label="Aliases">
              <TagInput
                values={scenario.aliases ?? []}
                onChange={(aliases) => update(name, { ...scenario, aliases })}
                placeholder="morning mode"
              />
            </Field>
            <ScenarioStepsEditor
              steps={scenario.steps ?? []}
              targets={targets}
              actions={actions}
              onChange={(steps) => update(name, { ...scenario, steps })}
            />
          </article>
        ))}
        {!Object.keys(scenarios).length && <Empty label="No scenarios yet" />}
      </div>
    </div>
  );
}

function ScenarioStepsEditor({
  steps,
  targets,
  actions,
  onChange,
}: {
  steps: ScenarioStep[];
  targets: string[];
  actions: string[];
  onChange: (next: ScenarioStep[]) => void;
}) {
  function update(index: number, next: ScenarioStep) {
    onChange(steps.map((step, i) => (i === index ? next : step)));
  }
  function add() {
    onChange([...steps, { target: targets[0] ?? '', action: actions[0] ?? '', parameters: {} }]);
  }
  function remove(index: number) {
    onChange(steps.filter((_, i) => i !== index));
  }
  function move(index: number, delta: number) {
    const target = index + delta;
    if (target < 0 || target >= steps.length) return;
    const next = steps.slice();
    [next[index], next[target]] = [next[target], next[index]];
    onChange(next);
  }

  return (
    <div className="subsection">
      <div className="subsection-head">
        <h3>Steps</h3>
        <button onClick={add}>
          <Plus size={14} /> Add step
        </button>
      </div>
      <ol className="steps">
        {steps.map((step, index) => (
          <li key={index}>
            <div className="step-grid">
              <select
                aria-label="Step target"
                value={step.target}
                onChange={(event) => update(index, { ...step, target: event.target.value })}
              >
                {!targets.includes(step.target) && step.target && <option>{step.target}</option>}
                {targets.map((target) => (
                  <option key={target}>{target}</option>
                ))}
              </select>
              <select
                aria-label="Step action"
                value={step.action}
                onChange={(event) => update(index, { ...step, action: event.target.value })}
              >
                {!actions.includes(step.action) && step.action && <option>{step.action}</option>}
                {actions.map((action) => (
                  <option key={action}>{action}</option>
                ))}
              </select>
              <input
                aria-label="Step parameters JSON"
                value={JSON.stringify(step.parameters ?? {})}
                placeholder='{"level":"medium"}'
                onChange={(event) => {
                  try {
                    const parsed = JSON.parse(event.target.value || '{}');
                    update(index, { ...step, parameters: parsed });
                  } catch {
                    /* keep typing */
                  }
                }}
              />
              <div className="inline">
                <button className="icon-button" onClick={() => move(index, -1)} aria-label="Move up">
                  ↑
                </button>
                <button className="icon-button" onClick={() => move(index, 1)} aria-label="Move down">
                  ↓
                </button>
                <button className="icon-button danger" onClick={() => remove(index)} aria-label="Delete step">
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          </li>
        ))}
        {!steps.length && <Empty label="No steps" small />}
      </ol>
    </div>
  );
}

/* ----------------------------- Policies editor ----------------------------- */

function PoliciesView({
  policy,
  setPolicy,
  catalog,
}: {
  policy: Policy;
  setPolicy: (next: Policy) => void;
  catalog: Catalog;
}) {
  const targets = ['*', ...Object.keys(catalog.capabilities), ...Object.keys(catalog.groups ?? {})];
  const actions = ['*', ...Object.keys(catalog.actions)];

  return (
    <div className="view-grid two">
      <Panel title="Fuzzy resolution" icon={ShieldCheck}>
        <Field label={`Cutoff ${Number(policy.fuzzy_cutoff ?? 0.62).toFixed(2)}`} hint="Lower values accept looser matches.">
          <input
            aria-label="Fuzzy cutoff"
            type="range"
            min={0.35}
            max={0.95}
            step={0.01}
            value={policy.fuzzy_cutoff ?? 0.62}
            onChange={(event) => setPolicy({ ...policy, fuzzy_cutoff: Number(event.target.value) })}
          />
        </Field>
        <Field label="Inspect verbs">
          <TagInput
            values={policy.inspect_verbs ?? []}
            onChange={(inspect_verbs) => setPolicy({ ...policy, inspect_verbs })}
            placeholder="inspect, status, show"
          />
        </Field>
        <Field label="Scenario verbs">
          <TagInput
            values={policy.scenario_verbs ?? []}
            onChange={(scenario_verbs) => setPolicy({ ...policy, scenario_verbs })}
            placeholder="run, start, execute"
          />
        </Field>
      </Panel>

      <RulesPanel
        title="Confirmations"
        rules={policy.confirmations ?? []}
        targets={targets}
        actions={actions}
        onChange={(confirmations) => setPolicy({ ...policy, confirmations })}
      />
      <RulesPanel
        title="Deny rules"
        rules={policy.deny ?? []}
        targets={targets}
        actions={actions}
        onChange={(deny) => setPolicy({ ...policy, deny })}
      />
      <SynonymsPanel
        synonyms={policy.synonyms ?? {}}
        onChange={(synonyms) => setPolicy({ ...policy, synonyms })}
      />
    </div>
  );
}

function RulesPanel({
  title,
  rules,
  targets,
  actions,
  onChange,
}: {
  title: string;
  rules: Rule[];
  targets: string[];
  actions: string[];
  onChange: (next: Rule[]) => void;
}) {
  function add() {
    onChange([...rules, { target: '*', action: '*', reason: '' }]);
  }
  function update(index: number, next: Rule) {
    onChange(rules.map((rule, i) => (i === index ? next : rule)));
  }
  function remove(index: number) {
    onChange(rules.filter((_, i) => i !== index));
  }
  return (
    <Panel
      title={title}
      icon={ShieldCheck}
      actions={
        <button onClick={add}>
          <Plus size={14} /> Add rule
        </button>
      }
    >
      <div className="stack">
        {rules.map((rule, index) => (
          <div className="rule-editor" key={index}>
            <select
              aria-label="Rule target"
              value={rule.target ?? '*'}
              onChange={(event) => update(index, { ...rule, target: event.target.value })}
            >
              {targets.map((target) => (
                <option key={target}>{target}</option>
              ))}
            </select>
            <select
              aria-label="Rule action"
              value={rule.action ?? '*'}
              onChange={(event) => update(index, { ...rule, action: event.target.value })}
            >
              {actions.map((action) => (
                <option key={action}>{action}</option>
              ))}
            </select>
            <input
              aria-label="Rule reason"
              placeholder="reason"
              value={rule.reason ?? ''}
              onChange={(event) => update(index, { ...rule, reason: event.target.value })}
            />
            <button className="icon-button danger" onClick={() => remove(index)} aria-label="Delete rule">
              <Trash2 size={14} />
            </button>
          </div>
        ))}
        {!rules.length && <Empty label="No rules" small />}
      </div>
    </Panel>
  );
}

function SynonymsPanel({
  synonyms,
  onChange,
}: {
  synonyms: Record<string, string[]>;
  onChange: (next: Record<string, string[]>) => void;
}) {
  const [key, setKey] = useState('');
  function add() {
    const name = key.trim();
    if (!name || synonyms[name]) return;
    onChange({ ...synonyms, [name]: [] });
    setKey('');
  }
  function update(name: string, values: string[]) {
    onChange({ ...synonyms, [name]: values });
  }
  function rename(oldKey: string, nextKey: string) {
    nextKey = nextKey.trim();
    if (!nextKey || nextKey === oldKey || synonyms[nextKey]) return;
    const entries = Object.entries(synonyms).map(([k, v]) => (k === oldKey ? [nextKey, v] : [k, v]));
    onChange(Object.fromEntries(entries));
  }
  function remove(name: string) {
    const next = { ...synonyms };
    delete next[name];
    onChange(next);
  }
  return (
    <Panel
      title="Synonyms"
      icon={SlidersHorizontal}
      span={2}
      actions={
        <div className="inline">
          <input
            aria-label="New synonym key"
            placeholder="canonical word"
            value={key}
            onChange={(event) => setKey(event.target.value)}
          />
          <button onClick={add}>
            <Plus size={14} /> Add
          </button>
        </div>
      }
    >
      <div className="synonym-grid">
        {Object.entries(synonyms).map(([name, values]) => (
          <div className="synonym-row" key={name}>
            <input
              aria-label="Synonym key"
              value={name}
              onChange={(event) => rename(name, event.target.value)}
            />
            <TagInput values={values} onChange={(next) => update(name, next)} placeholder="aliases" />
            <button className="icon-button danger" onClick={() => remove(name)} aria-label={`Delete ${name}`}>
              <Trash2 size={14} />
            </button>
          </div>
        ))}
        {!Object.keys(synonyms).length && <Empty label="No synonyms" small />}
      </div>
    </Panel>
  );
}

/* ----------------------------- Simulator, traces, integrations ----------------------------- */

function SimulatorView({
  prompt,
  setPrompt,
  busy,
  result,
  scenarios,
  selectedScenario,
  setSelectedScenario,
  onSimulate,
  onRunScenario,
}: {
  prompt: string;
  setPrompt: (value: string) => void;
  busy: boolean;
  result: SimulateResponse | null;
  scenarios: string[];
  selectedScenario: string;
  setSelectedScenario: (value: string) => void;
  onSimulate: () => void;
  onRunScenario: (name: string) => void;
}) {
  return (
    <div className="view-grid two">
      <Panel title="Prompt simulator" icon={MessageSquareCode} span={2}>
        <Field label="Prompt">
          <textarea
            aria-label="Simulator prompt"
            value={prompt}
            rows={4}
            onChange={(event) => setPrompt(event.target.value)}
          />
        </Field>
        <div className="button-row">
          <button className="primary" disabled={busy} onClick={onSimulate}>
            <Play size={15} /> Simulate
          </button>
          <select
            aria-label="Scenario"
            value={selectedScenario}
            onChange={(event) => setSelectedScenario(event.target.value)}
          >
            {scenarios.map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
          <button disabled={!selectedScenario || busy} onClick={() => onRunScenario(selectedScenario)}>
            Run scenario
          </button>
        </div>
      </Panel>
      <Panel title="Result" icon={CheckCircle2} span={2}>
        {result ? <ResultCard result={result} large /> : <Empty label="No simulation yet" />}
      </Panel>
    </div>
  );
}

function TracesView({ traces }: { traces: DecisionTrace[] }) {
  return (
    <Panel title="Decision traces" icon={Activity}>
      <TraceList traces={traces} />
    </Panel>
  );
}

function IntegrationsView({ snippets }: { snippets: IntegrationSnippets | null }) {
  if (!snippets) return <Empty label="Integration snippets unavailable" />;
  return (
    <div className="view-grid two">
      {Object.entries(snippets).map(([name, code]) => (
        <CodeBlock key={name} title={name} code={code} />
      ))}
    </div>
  );
}

function SettingsView({
  catalog,
  policy,
  setCatalog,
  setPolicy,
}: {
  catalog: Catalog;
  policy: Policy;
  setCatalog: (next: Catalog) => void;
  setPolicy: (next: Policy) => void;
}) {
  return (
    <div className="view-grid two">
      <Panel title="Catalog metadata" icon={Settings}>
        <Field label="Name">
          <input
            aria-label="Catalog name"
            value={catalog.name ?? ''}
            onChange={(event) => setCatalog({ ...catalog, name: event.target.value })}
          />
        </Field>
        <Field label="Version">
          <input
            aria-label="Catalog version"
            value={catalog.version ?? ''}
            onChange={(event) => setCatalog({ ...catalog, version: event.target.value })}
          />
        </Field>
      </Panel>
      <Panel title="Raw editors" icon={FileJson}>
        <p className="hint">Advanced JSON access. Apply parses and validates, then surfaces it in the editors above.</p>
      </Panel>
      <JsonEditor title="Catalog JSON" value={catalog} onApply={(next) => setCatalog(next as Catalog)} />
      <JsonEditor title="Policy JSON" value={policy} onApply={(next) => setPolicy(next as Policy)} />
    </div>
  );
}

/* ----------------------------- Reusable primitives ----------------------------- */

function Metric({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: typeof Boxes;
  label: string;
  value: number;
  tone: string;
}) {
  return (
    <div className={`metric ${tone}`}>
      <div className="metric-icon">
        <Icon size={20} />
      </div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Panel({
  title,
  icon: Icon,
  children,
  span,
  actions,
}: {
  title: string;
  icon: typeof Boxes;
  children: React.ReactNode;
  span?: number;
  actions?: React.ReactNode;
}) {
  return (
    <section className="panel" data-span={span}>
      <header className="panel-title">
        <Icon size={17} />
        <span>{title}</span>
        {actions && <div className="panel-actions">{actions}</div>}
      </header>
      <div className="panel-body">{children}</div>
    </section>
  );
}

function ToolbarPanel({ children }: { children: React.ReactNode }) {
  return <div className="toolbar-panel">{children}</div>;
}

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="field">
      <label className="field-label">{label}</label>
      {children}
      {hint && <small className="field-hint">{hint}</small>}
    </div>
  );
}

function EditableTitle({ value, onCommit }: { value: string; onCommit: (next: string) => void }) {
  const [local, setLocal] = useState(value);
  useEffect(() => setLocal(value), [value]);
  return (
    <input
      aria-label="Name"
      className="editable-title"
      value={local}
      onChange={(event) => setLocal(event.target.value)}
      onBlur={() => onCommit(local)}
      onKeyDown={(event) => {
        if (event.key === 'Enter') (event.target as HTMLInputElement).blur();
      }}
    />
  );
}

function TagInput({
  values,
  onChange,
  placeholder,
}: {
  values: string[];
  onChange: (next: string[]) => void;
  placeholder?: string;
}) {
  const [draft, setDraft] = useState('');
  function commit(value: string) {
    const next = value.trim();
    if (!next || values.includes(next)) return;
    onChange([...values, next]);
    setDraft('');
  }
  return (
    <div className="tag-input">
      {values.map((value) => (
        <span className="tag" key={value}>
          {value}
          <button
            aria-label={`Remove ${value}`}
            onClick={() => onChange(values.filter((existing) => existing !== value))}
          >
            ×
          </button>
        </span>
      ))}
      <input
        aria-label={placeholder ?? 'Add tag'}
        value={draft}
        placeholder={placeholder ?? 'Add value'}
        onChange={(event) => setDraft(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ',') {
            event.preventDefault();
            commit(draft);
          } else if (event.key === 'Backspace' && !draft && values.length) {
            onChange(values.slice(0, -1));
          }
        }}
        onBlur={() => draft && commit(draft)}
      />
    </div>
  );
}

function MultiCheck({
  options,
  values,
  onChange,
}: {
  options: string[];
  values: string[];
  onChange: (next: string[]) => void;
}) {
  function toggle(option: string) {
    if (values.includes(option)) onChange(values.filter((value) => value !== option));
    else onChange([...values, option]);
  }
  if (!options.length) return <Empty label="Define base items first" small />;
  return (
    <div className="multi-check">
      {options.map((option) => {
        const checked = values.includes(option);
        return (
          <label key={option} className={`chip ${checked ? 'on' : ''}`}>
            <input
              type="checkbox"
              checked={checked}
              onChange={() => toggle(option)}
              aria-label={option}
            />
            {option}
          </label>
        );
      })}
    </div>
  );
}

function Toggle({
  label,
  value,
  onChange,
}: {
  label: string;
  value: boolean;
  onChange: (next: boolean) => void;
}) {
  return (
    <label className="toggle">
      <input type="checkbox" checked={value} onChange={(event) => onChange(event.target.checked)} aria-label={label} />
      <span className="track" aria-hidden="true">
        <span className="thumb" />
      </span>
      <span className="toggle-label">{label}</span>
    </label>
  );
}

function ResultCard({ result, large = false }: { result: SimulateResponse; large?: boolean }) {
  const ok = Boolean(result.ok);
  return (
    <div className={`result-card ${ok ? 'ok' : 'bad'} ${large ? 'large' : ''}`}>
      <div className="result-head">
        {ok ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
        <strong>{result.route ?? result.trace?.route ?? 'result'}</strong>
      </div>
      <p>{result.message ?? result.trace?.outcome ?? 'completed'}</p>
      <dl>
        {result.target && (
          <>
            <dt>Target</dt>
            <dd>{result.target}</dd>
          </>
        )}
        {result.action && (
          <>
            <dt>Action</dt>
            <dd>{result.action}</dd>
          </>
        )}
        {result.parameters && (
          <>
            <dt>Parameters</dt>
            <dd>
              <code>{JSON.stringify(result.parameters)}</code>
            </dd>
          </>
        )}
        {result.trace?.latency_ms !== undefined && (
          <>
            <dt>Latency</dt>
            <dd>{result.trace.latency_ms} ms</dd>
          </>
        )}
      </dl>
      {large && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}

function TraceList({ traces, compact = false }: { traces: DecisionTrace[]; compact?: boolean }) {
  if (!traces.length) return <Empty label="No traces yet" />;
  return (
    <div className={`trace-list ${compact ? 'compact' : ''}`}>
      {traces.map((trace) => (
        <div className="trace-row" key={trace.id}>
          <span className={`dot ${trace.outcome === 'completed' ? 'ok' : 'warn'}`} />
          <div className="trace-meta">
            <b>{trace.route}</b>
            <span>
              {trace.target || trace.input_text || 'decision'} {trace.action ? `→ ${trace.action}` : ''}
            </span>
          </div>
          <code className="trace-outcome">{trace.outcome}</code>
          {!compact && <small>{new Date(trace.created_at * 1000).toLocaleString()}</small>}
        </div>
      ))}
    </div>
  );
}

function CodeBlock({ title, code }: { title: string; code: string }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  }
  return (
    <section className="panel code-panel">
      <header className="panel-title">
        <Clipboard size={16} />
        <span>{title}</span>
        <div className="panel-actions">
          <button className="ghost small" onClick={() => void copy()}>
            {copied ? <ClipboardCheck size={14} /> : <Clipboard size={14} />} {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
      </header>
      <pre>{code}</pre>
    </section>
  );
}

function JsonEditor({
  title,
  value,
  onApply,
}: {
  title: string;
  value: unknown;
  onApply: (value: unknown) => void;
}) {
  const [text, setText] = useState(JSON.stringify(value, null, 2));
  const [error, setError] = useState('');
  useEffect(() => {
    setText(JSON.stringify(value, null, 2));
  }, [value]);
  function apply() {
    try {
      onApply(JSON.parse(text));
      setError('');
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Invalid JSON');
    }
  }
  return (
    <section className="panel json-panel" data-span={2}>
      <header className="panel-title">
        <FileJson size={16} />
        <span>{title}</span>
        <div className="panel-actions">
          <button className="primary small" onClick={apply}>
            Apply
          </button>
        </div>
      </header>
      <textarea
        aria-label={title}
        value={text}
        rows={22}
        onChange={(event) => setText(event.target.value)}
      />
      {error && <span className="error-text">{error}</span>}
    </section>
  );
}

function Empty({ label, small = false }: { label: string; small?: boolean }) {
  return <div className={`empty ${small ? 'small' : ''}`}>{label}</div>;
}

/* ----------------------------- Helpers ----------------------------- */

function badgeFor(
  key: TabKey,
  metrics: Record<string, number>,
  traces: DecisionTrace[],
): number | undefined {
  switch (key) {
    case 'actions':
      return metrics.actions;
    case 'capabilities':
      return metrics.capabilities;
    case 'groups':
      return metrics.groups;
    case 'scenarios':
      return metrics.scenarios;
    case 'policies':
      return metrics.confirmations + metrics.denials + metrics.synonyms;
    case 'traces':
      return traces.length;
    default:
      return undefined;
  }
}

function subtitleFor(tab: TabKey): string {
  switch (tab) {
    case 'dashboard':
      return 'Overview of catalog, governance, and live simulation.';
    case 'actions':
      return 'Verbs the harness recognises and the actions they map to.';
    case 'capabilities':
      return 'Controllable entities, their parameters and initial state.';
    case 'groups':
      return 'Logical aggregations that combine capabilities.';
    case 'scenarios':
      return 'Multi-step automations triggered by name or natural language.';
    case 'policies':
      return 'Confirmations, deny rules, synonyms and fuzzy matching cutoff.';
    case 'simulator':
      return 'Send prompts through the deterministic router and inspect results.';
    case 'traces':
      return 'Append-only audit log of every routing decision.';
    case 'integrations':
      return 'Copy snippets to embed the harness in any client.';
    case 'settings':
      return 'Metadata and advanced JSON editors.';
  }
}
