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
  // the finalized block from both frozen RPCs; the lower one, so both hold it
  const urls = ["https://eth-pokt.nodies.app", "https://rpc.mevblocker.io"];
  const got = [];
  for (const url of urls) {
    for (let i = 1; ; i++) {
      try {
        const res = await fetch(url, {
          method: "POST", headers: { "content-type": "application/json" }, signal: AbortSignal.timeout(20_000),
          body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "eth_getBlockByNumber", params: ["finalized", false] }),
        });
        got.push(parseInt((await res.json()).result.number, 16));
        break;
      } catch (e) {
        if (i >= 8) throw e;
        await new Promise((r) => setTimeout(r, 5000 * i));
      }
    }
  }
  return Math.min(...got);
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

/** The newest file_claim tx (filer or filer2 -> BurnProof) whose calldata holds this quote. */
async function txOf(quote) {
  const acc = JSON.parse(readFileSync(new URL("./.accounts.json", import.meta.url), "utf8"));
  const hits = [];
  for (const role of ["filer", "filer2", "filer3", "filer4"]) {
    const res = await fetch("https://studio-dev.genlayer.com/api", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "sim_getTransactionsForAddress", params: [acc[role].address] }),
    });
    for (const tx of (await res.json()).result ?? []) {
      if (String(tx.to_address).toLowerCase() !== address.toLowerCase()) continue;
      const cd = Buffer.from(tx.data?.calldata ?? "", "base64").toString("latin1");
      if (cd.includes(quote)) hits.push(tx);
    }
  }
  hits.sort((a, b) => String(b.created_at ?? "").localeCompare(String(a.created_at ?? "")));
  return hits[0]?.hash ?? null;
}

const TRANSPORT = ["PAGE_UNAVAILABLE", "RPC_UNAVAILABLE", "RPC_DISAGREE", "BLOCK_NOT_FINALIZED"];
// senders for refilings (5 filings per sender per hour on the canonical contract)
const spare = ["filer3", "filer3", "filer3", "filer3", "filer3", "filer4", "filer4", "filer4", "filer4", "filer4"];
const results = [];
for (let i = 0; i < seeds.length; i++) {
  const s = seeds[i];
  const latest = async () => (await onChain()).filter((c) => c.snapshot === s.snapshot && c.quote === s.quote).pop();
  let found = await latest();
  if (!found) {
    const block = await finalized();
    const { send } = connect({ address, role: roles[i] });
    console.log(`${s.id} filing as ${roles[i]} at block ${block}`);
    const r = await send("file_claim", [s.chain_id, s.token, s.snapshot, s.quote, block]);
    console.log(`  ${r.status} ok=${r.ok} ${r.seconds}s ${r.hash}`, returnedJson(r) ?? r.revertReason?.slice(0, 200));
    found = await latest();
    if (found) found.tx = r.hash;
  }
  // a transport failure (archive or RPC did not answer) is a final UNVERIFIABLE
  // check; the seed is filed again at a newer block after a cool-down, up to 4 times
  for (let k = 0; k < 4 && found && TRANSPORT.includes(found.code); k++) {
    console.log(`${s.id} check #${found.check_id} was ${found.code}; waiting 180 s, then filing again`);
    await new Promise((r) => setTimeout(r, 180_000));
    const block = await finalized();
    const role = spare.shift();
    const { send } = connect({ address, role });
    console.log(`${s.id} filing again as ${role} at block ${block}`);
    const r = await send("file_claim", [s.chain_id, s.token, s.snapshot, s.quote, block]);
    console.log(`  ${r.status} ok=${r.ok} ${r.seconds}s ${r.hash}`, returnedJson(r) ?? r.revertReason?.slice(0, 200));
    found = await latest();
    if (found) found.tx = r.hash;
  }
  if (found && !found.tx) found.tx = await txOf(s.quote);
  if (!found) { console.log(`  ${s.id} NOT ON CHAIN`); results.push({ id: s.id, error: "not on chain" }); continue; }
  console.log(`${s.id} check #${found.check_id} ${found.verdict} ${found.code} - ${found.why}`);
  results.push({ id: s.id, project: s.project, expect: s.expect, ...found });
  writeFileSync(out, JSON.stringify({ contract: address, seeds: results }, null, 1) + "\n");
}
