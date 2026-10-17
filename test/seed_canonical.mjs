/**
 * Files every seed in test/seeds.json on the CANONICAL BurnProof, pinned at
 * the Ethereum finalized block of the moment, and records each final check in
 * docs/seeds.onchain.json. Resumable: a seed whose (snapshot, quote) is already
 * on chain is read back, not filed again.
 *   node seed_canonical.mjs
 */
import { readFileSync, writeFileSync } from "node:fs";
import { connect, returnedJson } from "./harness.mjs";

const root = new URL("..", import.meta.url);
const dep = JSON.parse(readFileSync(new URL("deployments.json", root), "utf8"));
const seeds = JSON.parse(readFileSync(new URL("./seeds.json", import.meta.url), "utf8")).seeds;
const out = new URL("docs/seeds.onchain.json", root);
const address = dep.contracts.BurnProof.address;
const roles = ["filer", "filer", "filer", "filer", "filer", "filer2", "filer2", "filer2", "filer2", "filer2"];

async function finalized() {
  const res = await fetch("https://eth-pokt.nodies.app", {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "eth_getBlockByNumber", params: ["finalized", false] }),
  });
  return parseInt((await res.json()).result.number, 16);
}

const reader = connect({ address, role: "filer" });
async function onChain() {
  const all = [];
  for (let s = 1; ; s += 50) {
    const raw = await reader.view("list_checks", [s, 50]);
    const page = typeof raw === "string" ? JSON.parse(raw) : raw;
    const list = page.checks ?? [];
    all.push(...list);
    if (list.length < 50) break;
  }
  return all;
}

const results = [];
for (let i = 0; i < seeds.length; i++) {
  const s = seeds[i];
  const TRANSPORT = ["PAGE_UNAVAILABLE", "RPC_UNAVAILABLE", "RPC_DISAGREE", "BLOCK_NOT_FINALIZED"];
  const latest = async () => (await onChain()).filter((c) => c.snapshot === s.snapshot && c.quote === s.quote).pop();
  let found = await latest();
  // a transport failure (archive or RPC did not answer) is a final UNVERIFIABLE
  // check; the seed is filed again at a newer block, up to 3 times
  for (let k = 0; k < 3 && found && TRANSPORT.includes(found.code); k++) {
    const block = await finalized();
    const { send } = connect({ address, role: roles[i] === "filer" ? "filer2" : "filer" });
    console.log(`${s.id} check #${found.check_id} was ${found.code}; filing again at block ${block}`);
    const r = await send("file_claim", [s.chain_id, s.token, s.snapshot, s.quote, block]);
    console.log(`  ${r.status} ok=${r.ok} ${r.seconds}s ${r.hash}`, returnedJson(r) ?? r.revertReason?.slice(0, 200));
    found = await latest();
    if (found) found.tx = r.hash;
  }
  if (!found) {
    const block = await finalized();
    const { send } = connect({ address, role: roles[i] });
    console.log(`${s.id} filing as ${roles[i]} at block ${block}`);
    const r = await send("file_claim", [s.chain_id, s.token, s.snapshot, s.quote, block]);
    console.log(`  ${r.status} ok=${r.ok} ${r.seconds}s ${r.hash}`, returnedJson(r) ?? r.revertReason?.slice(0, 200));
    found = await latest();
    if (found) found.tx = r.hash;
  }
  if (!found) { console.log(`  ${s.id} NOT ON CHAIN`); results.push({ id: s.id, error: "not on chain" }); continue; }
  console.log(`${s.id} check #${found.check_id} ${found.verdict} ${found.code} - ${found.why}`);
  results.push({ id: s.id, project: s.project, expect: s.expect, ...found });
  writeFileSync(out, JSON.stringify({ contract: address, seeds: results }, null, 1) + "\n");
}
