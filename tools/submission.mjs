/**
 * docs/SUBMISSION.md: the three submission texts, plain ASCII, each with its
 * character count checked against its limit.
 *   node tools/submission.mjs
 */
import { readFileSync, writeFileSync } from "node:fs";
const root = new URL("..", import.meta.url).pathname;
const dep = JSON.parse(readFileSync(root + "deployments.json", "utf8")).contracts;
const on = JSON.parse(readFileSync(root + "docs/seeds.onchain.json", "utf8"));
const tests = Number(process.argv[2] || 0);
const mix = { TRUE: 0, FALSE: 0, UNVERIFIABLE: 0 };
for (const s of on.seeds) mix[s.verdict]++;

const oneLiner = "BurnProof checks one archived token-burn claim against Ethereum as it stood at the capture, and answers TRUE, FALSE or UNVERIFIABLE. Code decides every number and verdict.";
const description = [
  "BurnProof lets a listing desk, auditor or holder check one token-burn or supply claim from a project's own archived website against Ethereum as of the capture.",
  "The filer gives a token, a Wayback snapshot, one exact quote and a block within 24 hours after the capture.",
  "Code confirms the quote is on that exact capture, finds its one claim-shaped number, and names the claim type when the words settle it (\"burned\", \"total supply\").",
  "For other quotes the model names the type; it never supplies a number, and disagreeing readings end UNVERIFIABLE.",
  "Two RPCs must agree on totalSupply and four dead-address balances; integer math gives TRUE if the claim holds within 0.5%, else FALSE.",
  `Seeds, all decided by code: SHIB 40% burned TRUE, SHIB "50% burned to Vitalik" FALSE, Akita 7.82% FALSE, Akita and FLOKI supply TRUE, Saitama 49% TRUE, a two-number quote UNVERIFIABLE.`,
  "BurnGate refuses listings whose latest claim is FALSE. Scope: Ethereum, burns counted at dead addresses.",
].join(" ");
const review = [
  `BurnProof ${dep.BurnProof.address} on Studio Dev.`,
  "Run node tools/verify_source.mjs: deployed code equals contracts/ at HEAD.",
  "Run node test/tx.mjs --set=final --c=BurnProof --view=get_check --args='[1]' and open its Wayback and Etherscan block links (block within 24 h of the capture) to recompute the verdict.",
  `python3 -m unittest in test/ runs ${tests} offline tests.`,
  "docs/FINAL_CHECK.md has the full check.",
].join(" ");

const seedTx = (id) => on.seeds.find((x) => x.id === id);
const demoLog = readFileSync(root + "docs/demo-run.log", "utf8");
const demoTx = (label) => { const i = demoLog.lastIndexOf(label); return i < 0 ? null : (demoLog.slice(i).match(/tx (0x[0-9a-f]{64})/) || [])[1]; };
const evidence = [
  ...on.seeds.map((x) => [`${x.id} ${x.verdict} (check #${x.check_id}, ${x.code})`, x.tx]),
  ["BurnGateDemo allow (SHIB)", demoTx("gate ALLOW (SHIB")],
  ["BurnGateDemo refuse (AKITA)", demoTx("gate REFUSE (AKITA")],
  ["BurnProofDemo BLOCK_AFTER_WINDOW (SHIB 40% at today's block)", demoTx("BLOCK_AFTER_WINDOW (SHIB")],
  ["BurnProofDemo model path (FLOKI TVL quote)", demoTx("model path")],
].filter(([, h]) => h);
const items = [["One-liner", oneLiner, 180], ["Description", description, 1000], ["Review verification", review, 500]];
const bad = items.filter(([, t, max]) => t.length > max || !/^[\x20-\x7e]*$/.test(t));
if (bad.length) { console.error("over limit or not ASCII:", bad.map(([n, t]) => `${n} ${t.length}`)); process.exit(1); }
writeFileSync(root + "docs/SUBMISSION.md", [
  "# Submission", "",
  "Plain ASCII. Character counts are measured by `tools/submission.mjs`.", "",
  ...items.flatMap(([n, t, max]) => [`## ${n} (${t.length} / ${max} characters)`, "", "```", t, "```", ""]),
  "## Links", "",
  "- Repository: https://github.com/kenil1710/burnproof",
  `- BurnProof (canonical): ${dep.BurnProof.address}`,
  `- BurnProofDemo: ${dep.BurnProofDemo.address}`,
  `- BurnGate: ${dep.BurnGate.address}`,
  `- BurnGateDemo: ${dep.BurnGateDemo.address}`,
  "- Network: GenLayer Studio Dev, chain id 61997, https://studio-dev.genlayer.com/api",
  "- Seeds: https://github.com/kenil1710/burnproof/blob/main/docs/SEEDS.md", "",
  "## Evidence links (Studio Dev explorer)", "",
  ...Object.entries(dep).map(([k, d]) => `- ${k}: https://explorer-studio-dev.genlayer.com/address/${d.address}`),
  ...evidence.map(([label, hash]) => `- ${label}: https://explorer-studio-dev.genlayer.com/tx/${hash}`), "",
].join("\n"));
for (const [n, t, max] of items) console.log(`${n}: ${t.length}/${max}`);
