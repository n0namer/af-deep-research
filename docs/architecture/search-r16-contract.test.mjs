import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
const root = new URL('../../', import.meta.url);
const base = 'docs/architecture/';
const read = (p) => readFileSync(new URL(p, root));
const digest = (b) => createHash('sha256').update(b).digest('hex');
const contract = JSON.parse(read(base + 'search-r16-contract.json'));
const sourceMap = Object.fromEntries(contract.sources.map((s) => [s.path, read(s.path)]));
function parse(text) {
  const lines = text.trim().split(/\r?\n/).map((x) => x.trim()).filter(Boolean);
  assert.equal(lines.shift(), 'flowchart LR');
  const nodes = new Set(), edges = [];
  for (const line of lines) {
    const n = line.match(/^(\w+)\["([^"]+)"\]$/);
    const e = line.match(/^(\w+) -->\|([^|]+)\| (\w+)$/);
    assert.ok(n || e, 'unsupported Mermaid statement');
    if (n) { assert.ok(!nodes.has(n[1]), 'duplicate Mermaid node'); nodes.add(n[1]); }
    if (e) { edges.push([e[1], e[3], e[2]]); assert.ok(nodes.has(e[1]) && nodes.has(e[3]), 'fabricated or dangling edge'); }
  }
  return {nodes:[...nodes], edges};
}
function validate(c, map=sourceMap) {
  assert.equal(c.schema, 'search-r16-architecture-contract.v1');
  assert.equal(c.status, 'CANDIDATE/UNACCEPTED');
  for (const s of c.sources) { assert.match(s.sha256,/^[0-9a-f]{64}$/); assert.equal(digest(map[s.path]),s.sha256,'source SHA'); }
  for (const sig of c.signatures) assert.ok(map[sig.source].toString().includes(sig.signature),'source signature');
  for (const d of c.diagrams) { const actual=parse(read(d.path).toString()); assert.deepEqual(actual.nodes,d.nodes); assert.deepEqual(actual.edges,d.edges); }
  assert.equal(c.graphify_archsteer.status,'UNVERIFIED');
  assert.ok(c.limitations.some((x)=>x.includes('do not execute Python')));
}
test('source SHA, signatures, C4 levels, Structurizr and explicit Graphify/ArchSteer boundary',()=>validate(contract));
for (const [name, edit, error] of [
 ['stale hash', c=>c.sources[0].sha256='0'.repeat(64),/source SHA/],
 ['fabricated edge', c=>c.diagrams[2].edges.push(['search','fusion','invented']),/deep-equal/],
 ['source mismatch', c=>c.signatures[0].signature='async def search(query: int)',/source signature/],
 ['false graph coverage', c=>c.graphify_archsteer.status='VERIFIED',/UNVERIFIED/]
]) test('reject '+name,()=>assert.throws(()=>validate(structuredCloneAnd(edit)),error));
function structuredCloneAnd(edit){const c=structuredClone(contract);edit(c);return c;}
test('Structurizr DSL is present and bounded',()=>{const d=read(base+'search-r16-structurizr.dsl').toString();assert.match(d,/workspace /);assert.match(d,/container system/);assert.match(d,/CANDIDATE \/ UNACCEPTED/);});
