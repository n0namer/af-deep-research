import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';

const root = new URL('../../', import.meta.url);
const base = 'docs/architecture/basefive-r14-';
const runPath = 'reasoners/deep_research_ext/research_run.py';
const pipelinePath = 'reasoners/deep_research_ext/verified_pipeline.py';
const sourcePins = {
  [runPath]: 'a4caa1f2d1ea2f4d70d3039fa3b2eac8371dde530ee0ebe5ec9537a602ac36ea',
  [pipelinePath]: '97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87',
  '.archsteer/model.json': 'ba854b09ce33e4095e370dd0f82d80d60683ea69b193e59bb47a887287c9f539',
  '.archsteer/architecture.md': '66b01056637fc68119270cf62e871d297803e2fbadcaebb3b0cfed406b0a8680',
  'graphify-out/graph.json': '40bfff7919e18ba5b929abf1565680ce8fb055c8e2e1d36b3ccd967e5a9705ec',
  'docs/acceptance/c4-releasegate-reducer-frontier-20261013.md': 'e776f4091b4e24a2091e97d08ea6f215fbe2b1ed548d1e13b5fed75fb09538ce'
};
const artifactPins = {
  [base + 'contracts.json']: '7d81581ed610a64337712806f7fb2edf4d6fc85d981cbfbdc692d267e79afc66',
  [base + 'C4-context.md']: 'fffd05d205fa5a4dab633cf84965ffae84376ab254be25e4f30b532f9fbbecd5',
  [base + 'container.mmd']: '6d9faf6b122df5b8f54f5606769e794172b5452fa780d3dfc931ecfa90c6d8d9',
  [base + 'component.mmd']: '95163a052c8823406155b0e4c35b0ebbc62bc72eeb32c15d3e7be65828ab60e2',
  [base + 'drift-analysis.md']: 'c6d85624be01b2463821afe0036ca0863309fe4fac1c8a18c65673ad36d8d004',
  [base + 'contract.test.mjs']: '1bd1a1f11fae0fbfa94cd87f1e52151ce150d1dbbbd70914d366becc82848d6f'
};
const read = (path) => readFileSync(new URL(path, root));
const sha = (bytes) => createHash('sha256').update(bytes).digest('hex');
const normalize = (text) => text.replace(/\s+/g, ' ').trim();
const sourceBytes = Object.fromEntries(Object.keys(sourcePins).map((path) => [path, read(path)]));
const sourceText = Object.fromEntries(Object.entries(sourceBytes).map(([path, bytes]) => [path, bytes.toString('utf8')]));
const contractBytes = read(base + 'contracts.json');
const contract = JSON.parse(contractBytes);
const diagrams = Object.fromEntries(['C4-context.md', 'container.mmd', 'component.mmd'].map((suffix) => [base + suffix, read(base + suffix).toString('utf8')]));
const expectedEdges = {
  context: ['caller|system|query and callbacks', 'system|research|await research package', 'system|generation|await document', 'system|storage|checkpoint through run store'],
  container: ['pipeline|callbacks|await callbacks', 'pipeline|runstore|begin and checkpoint', 'runstore|files|save and load JSON', 'pipeline|reportstore|persist legacy-default DTO'],
  component: ['execute|checkpoint|persist phase state', 'build|dto|construct grounded DTO', 'persist|replay|canonical revision', 'persist|store|save then optional record_effect']
};
const expectedDtoFields = {
  ResearchRun: ['run_id', 'query', 'stage', 'checkpoint_seq', 'status', 'created_at', 'updated_at', 'schema_version', 'replay_source_run_id', 'source_revision', 'source_owner', 'source_ids', 'evidence_ids', 'evidence_summary', 'coverage_state', 'open_gap_ids', 'conflicts', 'stage_history', 'budgets', 'payload'],
  GroundedFact: ['fact_id', 'source_id', 'source_sha256'],
  VerifiedSourceReport: ['report_id', 'query', 'source_ids', 'revision', 'payload', 'source_revision', 'source_owner', 'source_file_sha256', 'facts', 'abstained_requirement_ids', 'dto_version']
};

function functionBody(text, symbol) {
  const lines = text.split(/\r?\n/);
  const start = lines.findIndex((line) => line.startsWith(`def ${symbol}(`) || line.startsWith(`async def ${symbol}(`));
  assert.ok(start >= 0, `function absent: ${symbol}`);
  const end = lines.findIndex((line, index) => index > start && /^(?:class |def |async def |from |@)/.test(line));
  return lines.slice(start, end < 0 ? undefined : end).join('\n');
}

function dtoDeclarations(text, name) {
  const match = text.match(new RegExp(`^class ${name}:\\r?\\n([\\s\\S]*?)(?=^    (?:def |@)|^class |^def |^async def |$(?![\\s\\S]))`, 'm'));
  assert.ok(match, `DTO absent: ${name}`);
  return [...match[1].matchAll(/^    (\w+): ([^\r\n]+)$/gm)].map((entry) => `${entry[1]}: ${entry[2]}`);
}

function validateDtos(candidate, texts = sourceText) {
  assert.deepEqual(candidate.versions, { ResearchRun: '0.1', VerifiedSourceReport: 'r10', ArchSteer: '1.0.0' });
  assert.match(texts[runPath], /^SCHEMA_VERSION = "0\.1"$/m);
  assert.match(texts[pipelinePath], /if self\.dto_version != "r10":/);
  assert.deepEqual(candidate.dtos.map((dto) => dto.name), Object.keys(expectedDtoFields));
  for (const dto of candidate.dtos) {
    assert.equal(dto.source, dto.name === 'ResearchRun' ? runPath : pipelinePath);
    const actual = dtoDeclarations(texts[dto.source], dto.name);
    assert.deepEqual(actual.map((field) => field.split(':')[0]), expectedDtoFields[dto.name], `independent DTO fields: ${dto.name}`);
    assert.deepEqual(dto.fields, expectedDtoFields[dto.name], `contract DTO fields: ${dto.name}`);
    assert.deepEqual(actual, candidate.dto_types[dto.name], `typed DTO drift: ${dto.name}`);
  }
  assert.ok(dtoDeclarations(texts[pipelinePath], 'VerifiedSourceReport').includes('source_owner: str = "legacy"'), 'legacy default is not grounded ownership');
  assert.ok(dtoDeclarations(texts[pipelinePath], 'VerifiedSourceReport').includes('dto_version: str = "r10"'), 'independent r10 default');
  const requiredApis = ['begin_research_run', 'checkpoint_research_run', 'resume_research_run', 'build_grounded_verified_report', 'persist_grounded_verified_report', 'resume_grounded_verified_report', 'execute_verified_pipeline'];
  assert.deepEqual(candidate.apis.map((api) => api.symbol), requiredApis);
  for (const api of candidate.apis) {
    assert.equal(api.source, requiredApis.indexOf(api.symbol) < 3 ? runPath : pipelinePath);
    const header = functionBody(texts[api.source], api.symbol).match(/^[\s\S]*?:\s*\n/);
    assert.ok(header, `API header: ${api.symbol}`);
    assert.equal(normalize(header[0]), api.signature, `API drift: ${api.symbol}`);
  }
}

function parseDiagram(text, markdown) {
  if (markdown) {
    const blocks = [...text.matchAll(/```mermaid\r?\n([\s\S]*?)```/g)];
    assert.equal(blocks.length, 1);
    text = blocks[0][1];
  }
  const lines = text.trim().split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  assert.equal(lines.shift(), 'flowchart LR');
  const nodes = [];
  const edges = [];
  for (const line of lines) {
    const node = line.match(/^(\w+)\["([^"<>\[\]]+)"\]$/);
    const edge = line.match(/^(\w+) -->\|([^|<>]+)\| (\w+)$/);
    assert.ok(node || edge, `unsupported diagram statement: ${line}`);
    if (node) nodes.push({ id: node[1], label: node[2] });
    if (edge) edges.push({ from: edge[1], to: edge[3], label: edge[2] });
  }
  const ids = new Set(nodes.map((node) => node.id));
  assert.equal(ids.size, nodes.length, 'duplicate node');
  assert.equal(new Set(edges.map((edge) => JSON.stringify(edge))).size, edges.length, 'duplicate edge');
  for (const edge of edges) assert.ok(ids.has(edge.from) && ids.has(edge.to), 'dangling edge');
  return { nodes, edges };
}

function validateEdges(candidate, diagramTexts = diagrams, texts = sourceText) {
  assert.deepEqual(candidate.diagrams.map((entry) => entry.level), Object.keys(expectedEdges));
  assert.deepEqual(candidate.diagrams.map((entry) => entry.path), Object.keys(diagrams));
  for (const diagram of candidate.diagrams) {
    const parsed = parseDiagram(diagramTexts[diagram.path], diagram.level === 'context');
    const keys = (edges) => edges.map(({ from, to, label }) => `${from}|${to}|${label}`);
    assert.deepEqual(keys(diagram.edges), expectedEdges[diagram.level], `independent edge semantics: ${diagram.level}`);
    assert.deepEqual(keys(parsed.edges), expectedEdges[diagram.level], `diagram edge semantics: ${diagram.level}`);
    assert.deepEqual(parsed.nodes, diagram.nodes.map(({ id, label }) => ({ id, label })), 'node consistency');
    for (const entry of [...diagram.nodes, ...diagram.edges]) {
      assert.ok([runPath, pipelinePath].includes(entry.source), 'evidence source allowlist');
      const anchor = entry.anchor.replaceAll('\\"', '"');
      assert.ok(anchor.length > 10 && texts[entry.source].includes(anchor), `source anchor: ${anchor}`);
    }
  }
  const execute = functionBody(texts[pipelinePath], 'execute_verified_pipeline');
  for (const call of ['begin_research_run(', 'checkpoint_research_run(', 'await prepare_research_package(', 'await generate_document_from_package(', 'build_verified_source_report(', 'persist_verified_source_report(']) {
    assert.ok(execute.includes(call), `orchestrator edge call: ${call}`);
  }
  for (const call of ['build_grounded_verified_report(', 'persist_grounded_verified_report(', 'resume_research_run(']) {
    assert.ok(!execute.includes(call), `unmodeled grounded/resume integration: ${call}`);
  }
  const persist = functionBody(texts[pipelinePath], 'persist_grounded_verified_report');
  for (const call of ['replay_verified_source_report(existing, candidate)', 'store.save(', 'store.record_effect(']) assert.ok(persist.includes(call), `grounded edge: ${call}`);
  assert.ok(functionBody(texts[pipelinePath], 'build_grounded_verified_report').includes('return VerifiedSourceReport('));
  assert.match(texts[runPath], /os\.fsync\(handle\.fileno\(\)\)/);
  assert.match(texts[runPath], /os\.replace\(tmp, path\)/);
}

function measureCoverage(texts = sourceText) {
  const model = JSON.parse(texts['.archsteer/model.json']);
  const graph = JSON.parse(texts['graphify-out/graph.json']);
  assert.ok(Array.isArray(graph.nodes) && Array.isArray(graph.edges));
  const isGo = (path) => /(?:\.go$|(?:^|\/)go\.(?:mod|sum)$)/.test(path || '');
  const coverage = {
    archsteer_component_count: Object.keys(model.components).length,
    archsteer_languages: [...new Set(Object.values(model.components).map((entry) => entry.language))].sort(),
    archsteer_go_paths: Object.keys(model.components).filter(isGo).sort(),
    graphify_go_paths: [...new Set(graph.nodes.map((node) => node.source_file).filter(isGo))].sort(),
    targets: []
  };
  for (const path of [runPath, pipelinePath]) {
    const names = [...texts[path].matchAll(/^(?:class|(?:async )?def) (\w+)/gm)].map((match) => match[1]);
    assert.deepEqual(model.components[path].exported_apis, names, `ArchSteer exports: ${path}`);
    const indexed = graph.nodes.filter((node) => node.source_file === path);
    const labels = new Set(indexed.map((node) => node.label.replace(/\(\)$/, '')));
    coverage.targets.push({ source: path, graphify_missing_top_level: names.filter((name) => !labels.has(name)) });
  }
  return coverage;
}

function validateCoverage(candidate, texts = sourceText) {
  const actual = measureCoverage(texts);
  for (const key of ['archsteer_component_count', 'archsteer_languages', 'archsteer_go_paths', 'graphify_go_paths']) assert.deepEqual(candidate.coverage[key], actual[key], `coverage drift: ${key}`);
  assert.match(candidate.coverage.go_package_status, /^UNVERIFIED:.*not proof/);
  assert.deepEqual(candidate.coverage.targets.map((target) => ({ source: target.source, graphify_missing_top_level: target.graphify_missing_top_level })), actual.targets, 'Graphify gap drift');
  const graph = JSON.parse(texts['graphify-out/graph.json']);
  for (const target of candidate.coverage.targets) {
    for (const location of target.graphify_stale_locations) {
      const node = graph.nodes.find((entry) => entry.source_file === target.source && entry.label.replace(/\(\)$/, '') === location.symbol);
      assert.equal(node?.source_location, `L${location.indexed}`);
      const measured = texts[target.source].split(/\r?\n/).findIndex((line) => new RegExp(`^(?:class|(?:async )?def) ${location.symbol}\\b`).test(line)) + 1;
      assert.equal(measured, location.actual, `source location drift: ${location.symbol}`);
      assert.notEqual(measured, location.indexed);
    }
  }
  return actual;
}

const copyContract = (edit) => { const copy = structuredClone(contract); edit(copy); return copy; };

test('independent raw-byte pins bind the exact candidate and all six sources', () => {
  assert.equal(sha(contractBytes), '7d81581ed610a64337712806f7fb2edf4d6fc85d981cbfbdc692d267e79afc66');
  assert.equal(contract.schema, 'basefive-r14-architecture-contract.v1');
  assert.equal(contract.project, 'af-deep-research');
  assert.equal(contract.status, 'CANDIDATE/UNACCEPTED');
  assert.equal(contract.baseline_commit, 'e10580c89eac7a4f6efb50c921ae9107ce8ad8dc');
  assert.deepEqual(contract.sources.map((entry) => entry.path), Object.keys(sourcePins));
  for (const entry of contract.sources) {
    assert.equal(entry.sha256, sourcePins[entry.path]);
    assert.equal(sha(sourceBytes[entry.path]), sourcePins[entry.path], `raw-byte SHA: ${entry.path}`);
  }
});
test('independent DTO types, defaults, versions and seven API boundaries', () => validateDtos(contract));
test('independent three-level edges match function-scoped calls and diagrams', () => validateEdges(contract));
test('inventory Go coverage and stale Graphify locations are explicitly bounded', () => {
  console.log('INDEPENDENT_COVERAGE ' + JSON.stringify(validateCoverage(contract)));
});
test('negative DTO drift is rejected after the source hash is deliberately rebound', () => {
  const changed = sourceText[pipelinePath].replace('source_owner: str = "legacy"', 'source_owner: int = 0');
  assert.notEqual(changed, sourceText[pipelinePath], 'mutation applied');
  const copy = copyContract((entry) => { entry.sources.find((source) => source.path === pipelinePath).sha256 = sha(changed); });
  assert.equal(copy.sources.find((entry) => entry.path === pipelinePath).sha256, sha(changed));
  assert.throws(() => validateDtos(copy, { ...sourceText, [pipelinePath]: changed }), /typed DTO drift/);
});
test('negative coordinated topology drift fails despite a real but unrelated anchor', () => {
  const copy = copyContract((entry) => { entry.diagrams[2].edges.push({ from: 'execute', to: 'persist', label: 'automatic grounded persistence', source: pipelinePath, anchor: 'def persist_grounded_verified_report(' }); });
  const diagramTexts = { ...diagrams, [base + 'component.mmd']: diagrams[base + 'component.mmd'] + '\nexecute -->|automatic grounded persistence| persist\n' };
  assert.deepEqual(parseDiagram(diagramTexts[base + 'component.mmd'], false).edges, copy.diagrams[2].edges.map(({ from, to, label }) => ({ from, to, label })));
  assert.ok(sourceText[pipelinePath].includes(copy.diagrams[2].edges.at(-1).anchor));
  assert.throws(() => validateEdges(copy, diagramTexts), /independent edge semantics/);
});
test('negative hidden Go inventory entry is rejected after rehashing Graphify', () => {
  const graph = JSON.parse(sourceText['graphify-out/graph.json']);
  graph.nodes.push({ id: 'independent_go_fixture', label: 'main()', source_file: 'fixture/main.go' });
  const changed = JSON.stringify(graph);
  const copy = copyContract((entry) => { entry.sources.find((source) => source.path === 'graphify-out/graph.json').sha256 = sha(changed); });
  assert.throws(() => validateCoverage(copy, { ...sourceText, 'graphify-out/graph.json': changed }), /coverage drift: graphify_go_paths/);
});
test('negative boundary API loss is not hidden by an unchanged DTO version', () => {
  const changed = sourceText[pipelinePath].replace('owner, cancellation=None, effect_id=None', 'cancellation=None, effect_id=None');
  assert.notEqual(changed, sourceText[pipelinePath]);
  assert.throws(() => validateDtos(contract, { ...sourceText, [pipelinePath]: changed }), /API drift: persist_grounded_verified_report/);
});
test('negative hidden Graphify symbol loss is detected', () => {
  const graph = JSON.parse(sourceText['graphify-out/graph.json']);
  const initial = graph.nodes.length;
  graph.nodes = graph.nodes.filter((node) => !(node.source_file === runPath && node.label === 'checkpoint_research_run()'));
  assert.ok(graph.nodes.length < initial, 'mutation applied');
  assert.throws(() => validateCoverage(contract, { ...sourceText, 'graphify-out/graph.json': JSON.stringify(graph) }), /Graphify gap drift/);
});
test('negative invented grounded orchestration is rejected even with unchanged diagrams', () => {
  const changed = sourceText[pipelinePath].replace('persisted_report = persist_verified_source_report(report_store, report)', 'persisted_report = persist_grounded_verified_report(report_store, report)') + '\ndef unrelated_fixture(report_store, report):\n    persisted_report = persist_verified_source_report(report_store, report)\n';
  assert.notEqual(changed, sourceText[pipelinePath]);
  assert.throws(() => validateEdges(contract, diagrams, { ...sourceText, [pipelinePath]: changed }), /orchestrator edge call/);
});
test('scoped report preserves the existing gate and review limitations', () => {
  const report = read(base + 'independent-c4-review.md').toString('utf8');
  for (const term of ['UNACCEPTED', 'Go source inspection: BLOCKED', 'static', 'c4-releasegate-reducer-frontier-20261013.md', 'native task-to-result', 'not executed', 'coordinated topology']) assert.ok(report.includes(term), `review disclosure: ${term}`);
  for (const suffix of ['independent-c4-review.md', 'independent-c4.test.mjs']) assert.ok(read(base + suffix).toString('utf8').trimEnd().split(/\r?\n/).length < 500);
});
test('immutable QA receipt identifies every reviewed artifact without accepting product', () => {
  validateDtos(contract);
  validateEdges(contract);
  validateCoverage(contract);
  for (const [path, fingerprint] of Object.entries({ ...sourcePins, ...artifactPins })) assert.equal(sha(read(path)), fingerprint, `final pinned identity: ${path}`);
  assert.equal(sha(read(base + 'contracts.json')), sha(contractBytes));
  const paths = [...Object.keys(sourcePins), base + 'contracts.json', ...Object.keys(diagrams), base + 'drift-analysis.md', base + 'contract.test.mjs', base + 'independent-c4-review.md', base + 'independent-c4.test.mjs'];
  console.log('INDEPENDENT_QA_RECEIPT ' + JSON.stringify({ schema: 'basefive-r14-independent-c4-qa.v1', verdict: 'STATIC_SLICE_CANDIDATE', acceptance: 'UNACCEPTED', go_source_status: 'BLOCKED_SCOPE', python_runtime_status: 'NOT_EXECUTED', native_e2e_status: 'NOT_EXECUTED', recorded_at: new Date().toISOString(), artifacts: paths.map((path) => ({ path, sha256: sha(read(path)), bytes: read(path).length })) }));
});
