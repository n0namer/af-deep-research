import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';

const root = new URL('../../', import.meta.url);
const base = 'docs/architecture/';
const runPath = 'reasoners/deep_research_ext/research_run.py';
const pipelinePath = 'reasoners/deep_research_ext/verified_pipeline.py';
const allowedSources = [runPath, pipelinePath, '.archsteer/model.json', '.archsteer/architecture.md', 'graphify-out/graph.json', 'docs/acceptance/c4-releasegate-reducer-frontier-20261013.md'];
const allowedDiagrams = [base + 'basefive-r14-C4-context.md', base + 'basefive-r14-container.mmd', base + 'basefive-r14-component.mmd'];
const read = (path) => readFileSync(new URL(path, root));
const digest = (value) => createHash('sha256').update(value).digest('hex');
const normalize = (value) => value.replace(/\s+/g, ' ').trim();
const contract = JSON.parse(read(base + 'basefive-r14-contracts.json'));
const sources = Object.fromEntries(allowedSources.map((path) => [path, read(path)]));
const diagrams = Object.fromEntries(allowedDiagrams.map((path) => [path, read(path).toString('utf8')]));

function declaration(source, symbol) {
  const lines = source.toString('utf8').split(/\r?\n/);
  const start = lines.findIndex((line) => new RegExp(`^(?:async )?def ${symbol}\\(`).test(line));
  assert.ok(start >= 0, `missing API ${symbol}`);
  const header = [];
  for (const line of lines.slice(start)) {
    header.push(line);
    if (line.trimEnd().endsWith(':')) return normalize(header.join(' '));
  }
  assert.fail(`unterminated API ${symbol}`);
}

function fields(source, name) {
  const text = source.toString('utf8');
  const start = text.indexOf(`class ${name}:`);
  assert.ok(start >= 0, `missing DTO ${name}`);
  const body = text.slice(start).split(/\n(?=class |def |async def )/)[0];
  return [...body.matchAll(/^    (\w+: [^\r\n]+)$/gm)].map((match) => match[1]);
}

function topLevel(source) {
  return [...source.toString('utf8').matchAll(/^(?:class|(?:async )?def) (\w+)/gm)].map((match) => match[1]);
}

function parseDiagram(text, markdown = false) {
  if (markdown) {
    const blocks = [...text.matchAll(/```mermaid\r?\n([\s\S]*?)```/g)];
    assert.equal(blocks.length, 1, 'exactly one Mermaid block');
    text = blocks[0][1];
  }
  const lines = text.trim().split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  assert.equal(lines.shift(), 'flowchart LR', 'restricted Mermaid grammar');
  const nodes = [];
  const edges = [];
  for (const line of lines) {
    const node = line.match(/^(\w+)\["([^"\[\]<>]+)"\]$/);
    const edge = line.match(/^(\w+) -->\|([^|<>]+)\| (\w+)$/);
    assert.ok(node || edge, `unsupported Mermaid statement: ${line}`);
    if (node) nodes.push({ id: node[1], label: node[2] });
    if (edge) edges.push({ from: edge[1], to: edge[3], label: edge[2] });
  }
  assert.equal(new Set(nodes.map((node) => node.id)).size, nodes.length, 'duplicate Mermaid node');
  assert.equal(new Set(edges.map((edge) => JSON.stringify(edge))).size, edges.length, 'duplicate Mermaid edge');
  const ids = new Set(nodes.map((node) => node.id));
  for (const edge of edges) assert.ok(ids.has(edge.from) && ids.has(edge.to), 'dangling Mermaid edge');
  return { nodes, edges };
}

function coverageSummary(sourceMap) {
  const model = JSON.parse(sourceMap['.archsteer/model.json']);
  const graph = JSON.parse(sourceMap['graphify-out/graph.json']);
  assert.ok(Array.isArray(graph.nodes) && Array.isArray(graph.edges), 'graph structure');
  const isGo = (path) => /\.go$|(^|\/)go\.(mod|sum)$/.test(path || '');
  return {
    archsteer_component_count: Object.keys(model.components).length,
    archsteer_languages: [...new Set(Object.values(model.components).map((entry) => entry.language))].sort(),
    archsteer_go_paths: Object.keys(model.components).filter(isGo).sort(),
    graphify_go_paths: [...new Set(graph.nodes.map((node) => node.source_file).filter(isGo))].sort(),
    targets: [runPath, pipelinePath].map((path) => {
      const indexed = new Set(graph.nodes.filter((node) => node.source_file === path).map((node) => node.label.replace(/\(\)$/, '')));
      assert.deepEqual(model.components[path].exported_apis, topLevel(sourceMap[path]), `ArchSteer API names ${path}`);
      return { source: path, graphify_missing_top_level: topLevel(sourceMap[path]).filter((name) => !indexed.has(name)) };
    })
  };
}

function validate(candidate, sourceMap = sources, diagramMap = diagrams) {
  assert.equal(candidate.schema, 'basefive-r14-architecture-contract.v1');
  assert.equal(candidate.project, 'af-deep-research');
  assert.equal(candidate.status, 'CANDIDATE/UNACCEPTED');
  assert.deepEqual(candidate.sources.map((entry) => entry.path), allowedSources, 'exact source allowlist');
  for (const entry of candidate.sources) {
    assert.match(entry.sha256, /^[0-9a-f]{64}$/);
    assert.equal(digest(sourceMap[entry.path]), entry.sha256, `source SHA ${entry.path}`);
  }
  assert.deepEqual(candidate.versions, { ResearchRun: '0.1', VerifiedSourceReport: 'r10', ArchSteer: '1.0.0' });
  assert.match(sourceMap[runPath].toString(), /SCHEMA_VERSION = "0\.1"/);
  assert.match(sourceMap[pipelinePath].toString(), /if self\.dto_version != "r10":/);
  assert.equal(JSON.parse(sourceMap['.archsteer/model.json']).schema_version, candidate.versions.ArchSteer);
  assert.equal(candidate.dtos.length, 3);
  assert.deepEqual(candidate.dtos.map((dto) => dto.name), ['ResearchRun', 'GroundedFact', 'VerifiedSourceReport']);
  for (const dto of candidate.dtos) {
    assert.ok([runPath, pipelinePath].includes(dto.source), 'DTO source allowlist');
    const actual = fields(sourceMap[dto.source], dto.name);
    assert.deepEqual(actual, candidate.dto_types[dto.name], `DTO types ${dto.name}`);
    assert.deepEqual(actual.map((field) => field.split(':')[0]), dto.fields, `DTO fields ${dto.name}`);
  }
  assert.equal(candidate.apis.length, 7);
  for (const api of candidate.apis) {
    assert.ok([runPath, pipelinePath].includes(api.source), 'API source allowlist');
    assert.match(api.symbol, /^\w+$/);
    assert.equal(declaration(sourceMap[api.source], api.symbol), api.signature, `API signature ${api.symbol}`);
  }
  const measured = coverageSummary(sourceMap);
  for (const key of ['archsteer_component_count', 'archsteer_languages', 'archsteer_go_paths', 'graphify_go_paths']) {
    assert.deepEqual(candidate.coverage[key], measured[key], `coverage ${key}`);
  }
  assert.match(candidate.coverage.go_package_status, /^UNVERIFIED:/);
  assert.equal(candidate.coverage.targets.length, 2);
  const graph = JSON.parse(sourceMap['graphify-out/graph.json']);
  for (const target of candidate.coverage.targets) {
    assert.deepEqual(target.graphify_missing_top_level, measured.targets.find((entry) => entry.source === target.source).graphify_missing_top_level, 'Graphify missing API set');
    for (const location of target.graphify_stale_locations) {
      const node = graph.nodes.find((entry) => entry.source_file === target.source && entry.label.replace(/\(\)$/, '') === location.symbol);
      assert.equal(node?.source_location, `L${location.indexed}`, 'indexed location');
      const lines = sourceMap[target.source].toString().split(/\r?\n/);
      const actual = lines.findIndex((line) => new RegExp(`^(?:class|(?:async )?def) ${location.symbol}\\b`).test(line)) + 1;
      assert.equal(actual, location.actual, `actual location ${location.symbol}`);
      assert.notEqual(actual, location.indexed, 'staleness must be measured');
    }
  }
  assert.deepEqual(candidate.diagrams.map((diagram) => diagram.path), allowedDiagrams);
  assert.deepEqual(candidate.diagrams.map((diagram) => diagram.level), ['context', 'container', 'component']);
  for (const diagram of candidate.diagrams) {
    const actual = parseDiagram(diagramMap[diagram.path], diagram.level === 'context');
    assert.deepEqual(actual.nodes, diagram.nodes.map(({ id, label }) => ({ id, label })), `diagram nodes ${diagram.level}`);
    assert.deepEqual(actual.edges, diagram.edges.map(({ from, to, label }) => ({ from, to, label })), `diagram edges ${diagram.level}`);
    for (const entry of [...diagram.nodes, ...diagram.edges]) {
      assert.ok([runPath, pipelinePath].includes(entry.source), 'diagram source allowlist');
      assert.ok(typeof entry.anchor === 'string' && entry.anchor.length > 10, 'nonempty source anchor');
      assert.ok(sourceMap[entry.source].toString().includes(entry.anchor), `missing source anchor ${entry.anchor}`);
    }
  }
  assert.ok(candidate.limitations.some((item) => item.includes('do not execute Python')));
  return measured;
}

function validateGuards(sourceMap = sources) {
  const run = sourceMap[runPath].toString();
  const pipeline = sourceMap[pipelinePath].toString();
  for (const anchor of ['data.get("schema_version") != SCHEMA_VERSION', 'data.get("stage") not in CHECKPOINT_STAGES', 'safe != run_id', 'persisted.query != run.query', 'current.checkpoint_seq != run.checkpoint_seq', 'current.checkpoint_seq != expected_checkpoint_seq', 'current.source_revision not in {None, source_revision}', 'current.source_owner not in {None, source_owner}']) {
    assert.ok(run.includes(anchor), `missing checkpoint guard ${anchor}`);
  }
  for (const anchor of ['isinstance(self.revision, bool)', 'len(set(self.source_ids)) != len(self.source_ids)', 'fact.source_id not in self.source_ids', 'candidate_identity', 'existing_identity != candidate_identity', 'candidate.revision != existing.revision + 1', 'candidate.payload != existing.payload', 'owner != candidate.source_owner', 'report.source_file_sha256 != source_file_sha256', '_raise_if_cancelled(cancellation)', 'effect_id in self._effects']) {
    assert.ok(pipeline.includes(anchor), `missing report guard ${anchor}`);
  }
}

test('source-bound contract, DTO/API snapshots and all three diagram levels', () => {
  console.log('SOURCE_LOCATIONS ' + JSON.stringify(contract.coverage.targets.map((target) => ({ source: target.source, locations: target.graphify_stale_locations.map((entry) => ({ symbol: entry.symbol, actual: sources[target.source].toString().split(/\r?\n/).findIndex((line) => new RegExp(`^(?:class|(?:async )?def) ${entry.symbol}\\b`).test(line)) + 1 })) }))));
  const measured = validate(contract);
  console.log('ARCHITECTURE_COVERAGE ' + JSON.stringify(measured));
});

test('checkpoint and report negative-boundary guards remain present (static only)', () => validateGuards());

const mutate = (edit) => { const copy = structuredClone(contract); edit(copy); return copy; };
const negatives = [
  ['stale source SHA', (copy) => { copy.sources[0].sha256 = '0'.repeat(64); }, /source SHA/],
  ['uppercase fingerprint', (copy) => { copy.sources[0].sha256 = 'A'.repeat(64); }, /regular expression/],
  ['out-of-scope path', (copy) => { copy.sources[0].path = '../../foreign.py'; }, /source allowlist/],
  ['unsupported DTO version', (copy) => { copy.versions.VerifiedSourceReport = 'r11'; }, /deep-equal/],
  ['missing checkpoint sequence', (copy) => { copy.dtos[0].fields.splice(3, 1); }, /DTO fields/],
  ['wrong DTO field type', (copy) => { copy.dto_types.GroundedFact[2] = 'source_sha256: int'; }, /DTO types/],
  ['missing owner parameter', (copy) => { copy.apis[4].signature = copy.apis[4].signature.replace('owner, ', ''); }, /API signature/],
  ['Go completeness claim', (copy) => { copy.coverage.go_package_status = 'VERIFIED: no Go'; }, /regular expression/],
  ['hidden Graphify gap', (copy) => { copy.coverage.targets[1].graphify_missing_top_level.pop(); }, /Graphify missing API set/],
  ['stale source location', (copy) => { copy.coverage.targets[0].graphify_stale_locations[0].actual = 16; }, /actual location/],
  ['invented diagram label', (copy) => { copy.diagrams[1].nodes[5].label = 'Restart durable database'; }, /diagram nodes/],
  ['fabricated diagram edge', (copy) => { copy.diagrams[2].edges.push({ from: 'execute', to: 'persist', label: 'automatic grounded persistence' }); }, /diagram edges/],
  ['unbound diagram evidence', (copy) => { copy.diagrams[0].edges[0].anchor = 'nonexistent_provider_gateway'; }, /missing source anchor/],
  ['self-acceptance', (copy) => { copy.status = 'ACCEPTED_GREEN'; }, /strictly equal/]
];
for (const [name, edit, error] of negatives) test(`reject ${name}`, () => assert.throws(() => validate(mutate(edit)), error));

for (const [name, transform, error] of [
  ['dangling edge', (text) => text + '\nexecute -->|invented dependency| missing\n', /dangling Mermaid edge/],
  ['duplicate node', (text) => text + '\nexecute["duplicate"]\n', /duplicate Mermaid node/],
  ['duplicate edge', (text) => text + '\nexecute -->|persist phase state| checkpoint\n', /duplicate Mermaid edge/],
  ['unsupported directive', (text) => text + '\nclick execute "https://invalid.example"\n', /unsupported Mermaid statement/],
  ['valid syntax invented edge', (text) => text + '\nexecute -->|invented grounded integration| persist\n', /diagram edges/]
]) {
  test(`reject Mermaid ${name}`, () => {
    const map = { ...diagrams, [allowedDiagrams[2]]: transform(diagrams[allowedDiagrams[2]]) };
    assert.throws(() => validate(contract, sources, map), error);
  });
}

test('source API mutation fails even after rebinding its fingerprint', () => {
  const changed = Buffer.from(sources[pipelinePath].toString().replace('owner, cancellation=None, effect_id=None', 'cancellation=None, effect_id=None'));
  const copy = mutate((entry) => { entry.sources.find((source) => source.path === pipelinePath).sha256 = digest(changed); });
  assert.throws(() => validate(copy, { ...sources, [pipelinePath]: changed }), /API signature/);
});

test('removed stale-sequence guard is detected independently of fingerprint', () => {
  const changed = Buffer.from(sources[runPath].toString().replace('current.checkpoint_seq != expected_checkpoint_seq', 'False'));
  assert.throws(() => validateGuards({ ...sources, [runPath]: changed }), /missing checkpoint guard/);
});

test('indexed Go fixture cannot silently retain the no-Go inventory', () => {
  const graph = JSON.parse(sources['graphify-out/graph.json']);
  graph.nodes.push({ id: 'fixture_go', source_file: 'fixture/package/main.go', label: 'fixture' });
  const changed = Buffer.from(JSON.stringify(graph));
  const copy = mutate((entry) => { entry.sources.find((source) => source.path === 'graphify-out/graph.json').sha256 = digest(changed); });
  assert.throws(() => validate(copy, { ...sources, 'graphify-out/graph.json': changed }), /coverage graphify_go_paths/);
});

test('rehashed DTO default drift still fails the typed snapshot', () => {
  const changed = Buffer.from(sources[pipelinePath].toString().replace('source_owner: str = "legacy"', 'source_owner: str = "new-owner"'));
  const copy = mutate((entry) => { entry.sources.find((source) => source.path === pipelinePath).sha256 = digest(changed); });
  assert.throws(() => validate(copy, { ...sources, [pipelinePath]: changed }), /DTO types VerifiedSourceReport/);
});

test('rehashed ArchSteer inventory missing a boundary API is rejected', () => {
  const model = JSON.parse(sources['.archsteer/model.json']);
  model.components[runPath].exported_apis = model.components[runPath].exported_apis.filter((name) => name !== 'resume_research_run');
  const changed = Buffer.from(JSON.stringify(model));
  const copy = mutate((entry) => { entry.sources.find((source) => source.path === '.archsteer/model.json').sha256 = digest(changed); });
  assert.throws(() => validate(copy, { ...sources, '.archsteer/model.json': changed }), /ArchSteer API names/);
});

test('rehashed Graphify symbol loss cannot silently preserve the old gap set', () => {
  const graph = JSON.parse(sources['graphify-out/graph.json']);
  graph.nodes = graph.nodes.filter((node) => !(node.source_file === runPath && node.label === 'checkpoint_research_run()'));
  const changed = Buffer.from(JSON.stringify(graph));
  const copy = mutate((entry) => { entry.sources.find((source) => source.path === 'graphify-out/graph.json').sha256 = digest(changed); });
  assert.throws(() => validate(copy, { ...sources, 'graphify-out/graph.json': changed }), /Graphify missing API set/);
});

test('drift write-back preserves explicit evidence limits and existing gate', () => {
  const drift = read(base + 'basefive-r14-drift-analysis.md').toString();
  for (const term of ['CANDIDATE / UNACCEPTED', 'c4-releasegate-reducer-frontier-20261013.md', 'process memory only', 'UNVERIFIED', 'not a Python AST/parser or runtime substitute', 'BLOCKED method steps', '14/24', 'L29/L197/L366']) {
    assert.ok(drift.includes(term), `missing drift disclosure ${term}`);
  }
  for (const source of contract.sources) assert.ok(drift.includes(source.sha256), `undocumented fingerprint ${source.path}`);
});

test('final six-file hygiene and immutable source-state receipt', () => {
  const paths = [...allowedDiagrams, base + 'basefive-r14-contracts.json', base + 'basefive-r14-drift-analysis.md', base + 'basefive-r14-contract.test.mjs'];
  const artifacts = paths.map((path) => {
    const bytes = read(path);
    const text = bytes.toString('utf8');
    const lineCount = text.trimEnd().split(/\r?\n/).length;
    assert.ok(lineCount < 500, `line limit ${path}`);
    assert.ok(!/\b(?:api_key|password|access_token)\s*[:=]\s*["'][^"'\s]{12,}["']/i.test(text), `credential literal ${path}`);
    return { path, sha256: digest(bytes), bytes: bytes.length, lines: lineCount };
  });
  console.log('FINAL_ARTIFACT_RECEIPT ' + JSON.stringify({ recorded_at: new Date().toISOString(), artifacts }));
});
