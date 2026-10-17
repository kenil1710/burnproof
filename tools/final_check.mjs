/**
 * docs/FINAL_CHECK.md: every requirement, PASS / FAIL, each with its proof
 * read live (Studio Dev, git, links, tests).
 *   node tools/final_check.mjs
 */
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { execFileSync, spawnSync } from "node:child_process";
import { createRequire } from "node:module";
const require = createRequire(new URL("../test/package.json", import.meta.url));
const { createClient } = require("genlayer-js");
const { studioDevnet } = require("genlayer-js/chains");
const { transactionsStatusNumberToName } = require("genlayer-js/types");
const root = new URL("..", import.meta.url).pathname;
const client = createClient({ chain: studioDevnet });
const depDoc = JSON.parse(readFileSync(root + "deployments.json", "utf8"));
const dep = depDoc.contracts;
const git = (...a) => execFileSync("git", ["-C", root, ...a]).toString().trim();
const sh = (cmd, args, cwd = root) => spawnSync(cmd, args, { cwd, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const plain = (v) => (v instanceof Map ? Object.fromEntries([...v.entries()].map(([k, x]) => [String(k), plain(x)])) : Array.isArray(v) ? v.map(plain) : typeof v === "bigint" ? Number(v) : v);
async function view(address, fn, args = []) {
  for (let i = 0; i < 8; i++) {
    try { const r = await client.readContract({ address, functionName: fn, args }); return typeof r === "string" ? JSON.parse(r) : plain(r); }
    catch (e) { if (i === 7) throw e; await sleep(5000 * (i + 1)); }
  }
}
async function txStatus(hash) {
  for (let i = 0; i < 8; i++) {
    try { const tx = await client.getTransaction({ hash }); return transactionsStatusNumberToName[tx.status] ?? String(tx.status); }
    catch (e) { if (i === 7) return "UNREADABLE"; await sleep(5000 * (i + 1)); }
  }
}
const rows = [];
const check = (name, ok, proof) => { rows.push({ name, ok, proof }); console.log(`${ok ? "PASS" : "FAIL"}  ${name}`); };
const read = (f) => (existsSync(root + f) ? readFileSync(root + f, "utf8") : "");

// 1 source match
{
  const r = sh("node", ["tools/verify_source.mjs"]);
  check("Source match: gen_getContractCode byte-identical to contracts/ at HEAD for every deployment, all from one commit, contracts/ unchanged since",
    r.status === 0, (r.stdout + r.stderr).trim());
}

// 2 seeds final
const seedsOn = JSON.parse(read("docs/seeds.onchain.json") || '{"seeds":[]}');
const seedsDef = JSON.parse(read("test/seeds.json")).seeds;
{
  const lines = [];
  let ok = seedsOn.contract === dep.BurnProof.address && seedsOn.seeds.length === seedsDef.length;
  for (const s of seedsDef) {
    const rec = seedsOn.seeds.find((x) => x.id === s.id);
    if (!rec) { ok = false; lines.push(`${s.id} missing from docs/seeds.onchain.json`); continue; }
    const live = await view(dep.BurnProof.address, "get_check", [rec.check_id]);
    const st = rec.tx ? await txStatus(rec.tx) : "NO TX RECORDED";
    const good = live.found && live.verdict === rec.verdict && live.quote === s.quote && live.snapshot === s.snapshot
      && ["TRUE", "FALSE", "UNVERIFIABLE"].includes(live.verdict) && st === "FINALIZED";
    ok &&= good;
    lines.push(`${s.id} check #${rec.check_id} ${live.verdict}/${live.code} (expected ${s.expect}) tx ${rec.tx?.slice(0, 12)} ${st} ${good ? "ok" : "PROBLEM"}`);
  }
  check("Seeds: every real seed filed on the canonical contract, final (tx FINALIZED) with a TRUE/FALSE/UNVERIFIABLE verdict matching docs/seeds.onchain.json", ok, lines.join("\n"));
  const mix = { TRUE: 0, FALSE: 0, UNVERIFIABLE: 0 };
  for (const r of seedsOn.seeds) mix[r.verdict] = (mix[r.verdict] ?? 0) + 1;
  const exp = seedsOn.seeds.every((r) => r.verdict === r.expect);
  check("Seed mix: at least 2 TRUE, 1 FALSE, 1 UNVERIFIABLE, each as researched", mix.TRUE >= 2 && mix.FALSE >= 1 && mix.UNVERIFIABLE >= 1 && exp, JSON.stringify(mix) + (exp ? "; every verdict equals docs/FEASIBILITY.md" : "; a verdict differs from research"));
}

// 3 counters
{
  const st = await view(dep.BurnProof.address, "get_stats");
  const n = seedsOn.seeds.length;
  check("Canonical counters equal the filed checks (checks = true + false + unverifiable)", st.checks === st.true + st.false + st.unverifiable && st.checks >= n,
    JSON.stringify(st));
}

// 4 demo
{
  const log = read("docs/demo-run.log");
  const runs = log.split("=== demo run ").filter((x) => x.trim());
  const last = runs[runs.length - 1] ?? "";
  const pass = (last.match(/ PASS /g) || []).length, fail = (last.match(/ FAIL /g) || []).length;
  const need = ["verdict TRUE", "verdict FALSE", "verdict UNVERIFIABLE", "refusal RATE_LIMITED", "refusal DUPLICATE", "refusal NOT_ARCHIVE_URL", "refusal BAD_TIMESTAMP", "gate ALLOW", "gate REFUSE"];
  const missing = need.filter((k) => !last.includes(k));
  check("Demo: every path on chain (each verdict, each refusal, consumer allow + refuse), all expectations met", pass > 0 && fail === 0 && missing.length === 0 && /ALL PASS/.test(last),
    `${pass} PASS, ${fail} FAIL in the last run of docs/demo-run.log; paths missing: ${missing.join(", ") || "none"}`);
}

// 5 addresses consistent
{
  const files = ["README.md", "docs/SEEDS.md", "docs/SUBMISSION.md", "docs/RULES.md", "docs/demo-run.log", "docs/seeds.onchain.json"];
  const all = Object.values(dep).map((d) => d.address);
  const text = Object.fromEntries(files.map((f) => [f, read(f)]));
  const missing = [];
  for (const [name, d] of Object.entries(dep)) if (!text["README.md"].includes(d.address)) missing.push(`README lacks ${name}`);
  if (!text["docs/SUBMISSION.md"].includes(dep.BurnProof.address)) missing.push("SUBMISSION lacks BurnProof");
  if (!text["docs/SEEDS.md"].includes(dep.BurnProof.address)) missing.push("SEEDS lacks BurnProof");
  const tokens = seedsDef.map((s) => s.token);
  const dead = ["0x0000000000000000000000000000000000000000", "0x0000000000000000000000000000000000000001", "0x000000000000000000000000000000000000dead", "0xdead000000000000000042069420694206942069"];
  const roles = existsSync(root + "test/.accounts.json") ? Object.values(JSON.parse(read("test/.accounts.json"))).map((r) => r.address.toLowerCase()) : [];
  const known = new Set([...all, ...tokens, ...dead, ...roles, depDoc.deployer ?? ""].map((a) => a.toLowerCase()));
  for (const d of Object.values(dep)) known.add(d.deployer.toLowerCase());
  const stray = [];
  for (const [f, t] of Object.entries(text)) {
    for (const m of t.matchAll(/(?<![0-9a-fA-Fx])0x[0-9a-fA-F]{40}(?![0-9a-fA-F])/g)) if (!known.has(m[0].toLowerCase())) stray.push(`${f}: ${m[0]}`);
  }
  check("Addresses consistent everywhere (deployments.json = README = SEEDS = SUBMISSION = logs; no other contract address appears)", missing.length === 0 && stray.length === 0,
    `deployments: ${Object.entries(dep).map(([k, d]) => `${k} ${d.address}`).join(", ")}\nmissing: ${missing.join("; ") || "none"}\nunknown addresses: ${[...new Set(stray)].join("; ") || "none"}`);
}

// 6 links
{
  const urls = new Set();
  for (const f of ["README.md", "docs/SEEDS.md", "docs/RULES.md", "docs/FEASIBILITY.md", "docs/SUBMISSION.md", "docs/ATTACK_REPORT.md"]) {
    for (const m of read(f).matchAll(/https?:\/\/[^\s)\]>"'`|]+/g)) urls.add(m[0].replace(/[.,;:]+$/, ""));
  }
  const skip = (u) => /eth-pokt\.nodies\.app|rpc\.mevblocker\.io|studio-dev\.genlayer\.com\/api|blastapi|onfinality|publicnode|drpc|web\.archive\.org\/web\/\d{14}id_|example|evil|web\.archive\.org\/web\/$/.test(u);
  const bad = [];
  let n = 0;
  for (const u of [...urls].filter((x) => !skip(x))) {
    let code = "";
    for (let i = 0; i < 3 && code !== "200"; i++) {
      code = sh("curl", ["-s", "-o", "/dev/null", "-m", "60", "-L", "-A", "Mozilla/5.0", "-w", "%{http_code}", u]).stdout;
      if (code !== "200") await sleep(5000);
    }
    n++;
    if (code !== "200") bad.push(`${code} ${u}`);
  }
  check("Every link in README and docs answers HTTP 200 (Wayback captures, Etherscan token and block pages, explorer, GitHub)", bad.length === 0,
    `${n} links checked (RPC endpoints and test hosts excluded); failing: ${bad.join("; ") || "none"}`);
}

// 7 tests
{
  const t = sh("python3", ["-m", "unittest", "test_burnproof", "test_attacks"], root + "test");
  const tail = t.stderr.trim().split("\n").slice(-3).join(" ");
  const n = Number((tail.match(/Ran (\d+) tests/) || [])[1] || 0);
  check("All offline tests pass (200+)", t.status === 0 && n >= 200, tail);
}

// 8 docs
{
  const r = read("README.md");
  const need = ["## Scope", "## Rules", "## Addresses", "## How to verify"];
  const miss = need.filter((s) => !r.includes(s));
  const banned = ["Known limitations", "TODO"].filter((w) => (r + read("docs/RULES.md") + read("docs/SEEDS.md")).includes(w));
  const sub = read("docs/SUBMISSION.md");
  const ascii = /^[\x00-\x7f]*$/.test(sub);
  check("Docs: README sections (Scope, Rules, Addresses, How to verify), no 'Known limitations'/'TODO', SUBMISSION plain ASCII", miss.length === 0 && banned.length === 0 && ascii,
    `missing: ${miss.join(",") || "none"}; banned words: ${banned.join(",") || "none"}; SUBMISSION ASCII: ${ascii}`);
}

// 9 git hygiene
{
  const leaked = git("log", "--all", "--format=%h", "--", "test/.accounts.json");
  const msgs = git("log", "--all", "--format=%B");
  const bad = /co-authored-by|claude|anthropic|chatgpt|openai/i.test(msgs);
  const tracked = git("ls-files");
  const words = sh("git", ["grep", "-n", "-i", "-E", "claude|anthropic|chatgpt|co-authored", "--", "."]).stdout.trim();
  check("Git: keys never committed, no assistant attribution in history or files", leaked === "" && !bad && words === "" && !tracked.includes(".accounts.json"),
    `commits touching test/.accounts.json: ${leaked || "none"}; attribution in messages: ${bad ? "FOUND" : "none"}; in files: ${words || "none"}`);
}

const pass = rows.filter((r) => r.ok).length;
writeFileSync(root + "docs/FINAL_CHECK.md", [
  "# Final check", "", `Run ${new Date().toISOString()} by \`tools/final_check.mjs\` against commit \`${git("rev-parse", "HEAD").slice(0, 10)}\` and Studio Dev. **${pass}/${rows.length} PASS.**`, "",
  ...rows.flatMap((r) => [`## ${r.ok ? "PASS" : "FAIL"}: ${r.name}`, "", "```", r.proof, "```", ""]),
].join("\n"));
console.log(`${pass}/${rows.length} PASS`);
process.exit(pass === rows.length ? 0 : 1);
