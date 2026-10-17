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

const oneLiner = "BurnProof checks one archived token-burn claim against Ethereum and answers TRUE, FALSE or UNVERIFIABLE. Code decides every number and verdict; the model only labels one sentence.";
const description = [
  "BurnProof checks one published token-burn claim against the chain.",
  "The filer picks the one claim: a token, a web.archive.org snapshot of the project's page, one exact quote and a block.",
  "Code checks the quote is on the archived page: the archive must serve that exact capture of that host, and the quote must sit inside one block of its visible text.",
  "Code finds the single claim-shaped number in the quote; ranges, several numbers, invisible characters and qualifiers (fees, plans, circulating supply) end UNVERIFIABLE.",
  "The model only formats that one sentence into {type, number, unit}; code requires the number to be written in the quote and equal to its own parse, and two readings must agree.",
  "Code computes every number and the verdict: two RPCs must agree exactly at a pinned finalized block, burned is the sum held by four frozen dead addresses, with 0.5% tolerance.",
  `BurnGate refuses listings whose latest burn claim is FALSE. Seeds: ${on.seeds.length} real claims, ${mix.TRUE} TRUE, ${mix.FALSE} FALSE, ${mix.UNVERIFIABLE} UNVERIFIABLE.`,
].join(" ");
const review = [
  `BurnProof ${dep.BurnProof.address} on Studio Dev.`,
  "Run node tools/verify_source.mjs: deployed code equals contracts/ at HEAD.",
  "Run node test/tx.mjs --set=final --c=BurnProof --view=get_check --args='[1]' and open its Wayback and Etherscan block links to recompute the verdict.",
  `python3 -m unittest in test/ runs ${tests} offline tests.`,
  "docs/FINAL_CHECK.md has the full check.",
].join(" ");

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
  "- Network: GenLayer Studio Dev, chain id 61997, https://studio-dev.genlayer.com/api", "",
].join("\n"));
for (const [n, t, max] of items) console.log(`${n}: ${t.length}/${max}`);
