/**
 * docs/SEEDS.md and the README seed table, from docs/seeds.onchain.json (what
 * the canonical contract stored) and test/seeds.json (the research).
 *   node tools/seeds_md.mjs
 */
import { readFileSync, writeFileSync } from "node:fs";
const root = new URL("..", import.meta.url).pathname;
const on = JSON.parse(readFileSync(root + "docs/seeds.onchain.json", "utf8"));
const def = Object.fromEntries(JSON.parse(readFileSync(root + "test/seeds.json", "utf8")).seeds.map((s) => [s.id, s]));
const dep = JSON.parse(readFileSync(root + "deployments.json", "utf8")).contracts;
const fmt = (raw, dec) => {
  const s = String(raw).padStart(dec + 1, "0");
  const whole = s.slice(0, s.length - dec).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return whole + (dec ? "." + s.slice(s.length - dec, s.length - dec + 2) : "");
};
const short = (c) => c.verdict === "UNVERIFIABLE" ? `${c.code}` : c.why.replace(/ -0\.5%| \+0\.5%/, "");
const rows = on.seeds.map((c) => {
  const s = def[c.id];
  return `| ${c.id} | ${s.project} | [capture](${c.snapshot}) | "${c.quote}" | **${c.verdict}** | ${short(c)} | [#${c.check_id}](https://explorer-studio-dev.genlayer.com/tx/${c.tx}) |`;
});
const table = ["| Seed | Project | Wayback | Quote | Verdict | Why (computed by code) | Check / tx |", "|---|---|---|---|---|---|---|", ...rows].join("\n");
const detail = on.seeds.map((c) => {
  const s = def[c.id];
  return [`## ${c.id}: ${s.project}, ${c.verdict}`, "",
    `- Quote: "${c.quote}"`,
    `- Archived page: ${c.snapshot} (capture ${c.snapshot_ts}, host \`${c.host}\`)`,
    `- Token: [\`${c.token}\`](${c.token_url}) (Ethereum, ${c.decimals} decimals)`,
    `- Block: [${c.block}](${c.block_url}), hash \`${c.block_hash}\`, time ${new Date(c.block_time * 1000).toISOString()}`,
    `- Claim read: ${c.claim_type || "(none)"} \`${c.claim_text || "-"}\`${c.claim_value ? ` = ${c.claim_value}` : ""}`,
    c.total_supply ? `- totalSupply: ${fmt(c.total_supply, c.decimals)}; at dead addresses: ${fmt(c.burned, c.decimals)} (${c.dead_balances.map((b, i) => `${c.dead_addresses[i].slice(0, 6)}...${c.dead_addresses[i].slice(-4)} ${fmt(b, c.decimals)}`).join(", ")})` : "- Chain: not read (the filing ended before the chain stage)",
    `- Verdict: **${c.verdict}** / \`${c.code}\`: ${c.why}`,
    `- Expected from research: ${s.expect}`,
    `- On chain: BurnProof \`${on.contract}\` check #${c.check_id}, filing tx [\`${c.tx}\`](https://explorer-studio-dev.genlayer.com/tx/${c.tx}), filed by \`${c.filer}\``,
    ""].join("\n");
});
writeFileSync(root + "docs/SEEDS.md", [
  "# Seeds", "",
  `Real burn and supply claims from official project pages, each filed on the canonical BurnProof [\`${dep.BurnProof.address}\`](https://explorer-studio-dev.genlayer.com/address/${dep.BurnProof.address}) at an Ethereum finalized block, each final. The research (sources, rejected candidates, measured balances) is in [FEASIBILITY.md](FEASIBILITY.md). The raw records are in [seeds.onchain.json](seeds.onchain.json) (\`get_check\` output).`, "",
  table, "", ...detail].join("\n"));
const readme = readFileSync(root + "README.md", "utf8");
const start = readme.indexOf("| Seed | Project |");
const marker = readme.includes("SEEDS_TABLE") ? "SEEDS_TABLE" : readme.slice(start, readme.indexOf("\n\n", start));
writeFileSync(root + "README.md", readme.replace(marker, table));
console.log(table);
