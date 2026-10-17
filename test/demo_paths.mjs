/**
 * Drives every path on the DEMO deployment (BurnProofDemo: 2 filings per
 * sender per 10 minutes; BurnGateDemo) and appends a plain log to
 * docs/demo-run.log: each verdict, each refusal, the consumer's allow and
 * refuse. Real seeds only.
 *   node demo_paths.mjs
 */
import { readFileSync, appendFileSync } from "node:fs";
import { connect, returnedJson } from "./harness.mjs";

const root = new URL("..", import.meta.url);
const dep = JSON.parse(readFileSync(new URL("deployments.json", root), "utf8")).contracts;
const BP = dep.BurnProofDemo.address;
const GATE = dep.BurnGateDemo.address;
const logFile = new URL("docs/demo-run.log", root);
const log = (line) => { console.log(line); appendFileSync(logFile, line + "\n"); };

const SHIB = "0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce";
const AKITA = "0x3301ee63fb29f863f2333bd4466acb46cd8323e6";
const FLOKI = "0xcf0c122c6b73ff809c693db761e7baebe62b6a2e";
const SHIB_0902 = "https://web.archive.org/web/20210902070016/https://shibatoken.com/";
const AKITA_1224 = "https://web.archive.org/web/20211224103559/https://www.akita.network/";
const FLOKI_1231 = "https://web.archive.org/web/20231231033517/https://floki.com/";
// the first Ethereum block at or after each snapshot (inside the 24-hour window)
const B_SHIB = 13144796, B_AKITA = 13867390, B_FLOKI = 18902821;

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

async function step(label, address, role, fn, args, expect) {
  const { send } = connect({ address, role });
  const r = await send(fn, args);
  const ret = returnedJson(r);
  const got = r.ok ? (ret ? JSON.stringify(ret) : String(r.returned)) : `REVERTED ${String(r.revertReason).slice(0, 160)}`;
  const pass = expect(r, ret);
  log(`[${new Date().toISOString()}] ${pass ? "PASS" : "FAIL"} ${label}`);
  log(`    ${role} -> ${fn}(${JSON.stringify(args).slice(0, 300)})`);
  log(`    tx ${r.hash} status ${r.status} ${r.seconds?.toFixed?.(1)}s`);
  log(`    => ${got}`);
  return { r, ret, pass };
}
const verdict = (v, code) => (r, ret) => r.ok && ret?.verdict === v && (!code || [].concat(code).includes(ret?.code));
// Wayback throttles bursts of fetches from Studio's nodes; space out the filings that reach the archive
const coolDown = () => new Promise((r) => setTimeout(r, 120_000));
const refused = (code) => (r) => !r.ok && String(r.revertReason).includes("REFUSED: " + code);

log(`\n=== demo run ${new Date().toISOString()}  BurnProofDemo ${BP}  BurnGateDemo ${GATE} ===`);
const B = B_SHIB;
const NOW_BLOCK = await finalized();
log(`snapshot blocks: SHIB ${B_SHIB}, AKITA ${B_AKITA}, FLOKI ${B_FLOKI}; finalized now ${NOW_BLOCK}`);
let fails = 0;
const t = async (...a) => { const o = await step(...a); if (!o.pass) fails++; return o; };

// verdicts
await t("verdict TRUE (SHIB 40% burned)", BP, "demo", "file_claim", [1, SHIB, SHIB_0902, "and then actually burned 40% of its total supply to a dead wallet", B], verdict("TRUE"));
await coolDown();
await t("verdict FALSE (AKITA 7.82% burned)", BP, "demo", "file_claim", [1, AKITA, AKITA_1224, "Percent burned: 7.82%", B_AKITA], verdict("FALSE"));
// refusal: rate limit (third filing by the same sender inside 10 minutes)
await t("refusal RATE_LIMITED (3rd filing by one sender in 10 min)", BP, "demo", "file_claim", [1, SHIB, SHIB_0902, "Starting with a supply of 1 quadrillion, our founder, Ryoshi, locked 50% in Uniswap", B], refused("RATE_LIMITED"));
await coolDown();
await t("verdict UNVERIFIABLE (two claim-shaped numbers)", BP, "demo2", "file_claim", [1, SHIB, SHIB_0902, "Starting with a supply of 1 quadrillion, our founder, Ryoshi, locked 50% in Uniswap", B], verdict("UNVERIFIABLE", "MULTIPLE_CLAIM_NUMBERS"));
await coolDown();
await t("verdict UNVERIFIABLE (quote not on the archived page)", BP, "demo2", "file_claim", [1, SHIB, SHIB_0902, "and then actually burned 90% of its total supply to a dead wallet", B], verdict("UNVERIFIABLE", "QUOTE_NOT_ON_PAGE"));
await coolDown();
await t("verdict UNVERIFIABLE (capture timestamp not exact: archive served another capture)", BP, "probe", "file_claim", [1, SHIB, "https://web.archive.org/web/20210902070000/https://shibatoken.com/", "and then actually burned 40% of its total supply to a dead wallet", B], verdict("UNVERIFIABLE", "SNAPSHOT_MISMATCH"));
await coolDown();
await t("verdict UNVERIFIABLE (circulating supply: code qualifier, model not asked)", BP, "probe", "file_claim", [1, AKITA, AKITA_1224, "Circulating Supply: 92,179,835,873,886", B_AKITA], verdict("UNVERIFIABLE", "CLAIM_QUALIFIED"));
await coolDown();
await t("verdict UNVERIFIABLE BLOCK_AFTER_WINDOW (SHIB 40% at today's block, years after the snapshot)", BP, "filer3", "file_claim", [1, SHIB, SHIB_0902, "and then actually burned 40% of its total supply to a dead wallet", NOW_BLOCK], verdict("UNVERIFIABLE", "BLOCK_AFTER_WINDOW"));
await coolDown();
await t("model path (no burn or supply words: the model labels it; a TVL figure is not a burn claim)", BP, "filer3", "file_claim", [1, FLOKI, FLOKI_1231, "Floki staking TVL hits new ATH of $80M", B_FLOKI], verdict("UNVERIFIABLE", "NOT_A_BURN_CLAIM"));
// refusals at the door
await t("refusal DUPLICATE (same token, snapshot, quote, block)", BP, "filer2", "file_claim", [1, SHIB, SHIB_0902, "and then actually burned 40% of its total supply to a dead wallet", B], refused("DUPLICATE_OF_"));
await t("refusal NOT_ARCHIVE_URL", BP, "filer2", "file_claim", [1, SHIB, "https://shibatoken.com/", "and then actually burned 40% of its total supply to a dead wallet", B], refused("NOT_ARCHIVE_URL"));
await t("refusal NOT_ARCHIVE_URL (lookalike host)", BP, "filer2", "file_claim", [1, SHIB, "https://web.archive.org.evil.io/web/20210902070016/https://shibatoken.com/", "and then actually burned 40% of its total supply to a dead wallet", B], refused("NOT_ARCHIVE_URL"));
await t("refusal BAD_TIMESTAMP (not 14 digits)", BP, "filer2", "file_claim", [1, SHIB, "https://web.archive.org/web/2021/https://shibatoken.com/", "and then actually burned 40% of its total supply to a dead wallet", B], refused("BAD_TIMESTAMP"));
await t("refusal BAD_TIMESTAMP (Feb 30)", BP, "filer2", "file_claim", [1, SHIB, "https://web.archive.org/web/20210230070016/https://shibatoken.com/", "and then actually burned 40% of its total supply to a dead wallet", B], refused("BAD_TIMESTAMP"));
await t("refusal UNSUPPORTED_CHAIN (BSC)", BP, "filer2", "file_claim", [56, SHIB, SHIB_0902, "and then actually burned 40% of its total supply to a dead wallet", B], refused("UNSUPPORTED_CHAIN"));
await t("refusal BAD_TOKEN_ADDRESS (a dead address)", BP, "filer2", "file_claim", [1, "0x000000000000000000000000000000000000dEaD", SHIB_0902, "and then actually burned 40% of its total supply to a dead wallet", B], refused("BAD_TOKEN_ADDRESS"));
await t("refusal BAD_QUOTE (too short)", BP, "filer2", "file_claim", [1, SHIB, SHIB_0902, "40% burned", B], refused("BAD_QUOTE"));
await t("refusal BAD_BLOCK", BP, "filer2", "file_claim", [1, SHIB, SHIB_0902, "and then actually burned 40% of its total supply to a dead wallet", 0], refused("BAD_BLOCK"));
// consumer
await t("gate ALLOW (SHIB: latest decisive claim from shibatoken.com is TRUE)", GATE, "demo", "request_listing", [1, SHIB, "shibatoken.com"], (r, ret) => r.ok && ret?.listed === true && ret?.verdict === "TRUE");
await t("gate REFUSE (AKITA: latest decisive claim from www.akita.network is FALSE)", GATE, "demo", "request_listing", [1, AKITA, "www.akita.network"], (r, ret) => r.ok && ret?.listed === false && ret?.verdict === "FALSE");
await t("gate ALLOW (FLOKI: no decisive claim from floki.com)", GATE, "demo", "request_listing", [1, FLOKI, "floki.com"], (r, ret) => r.ok && ret?.listed === true && ret?.verdict === "NONE");
await t("gate refusal BAD_SITE", GATE, "demo", "request_listing", [1, SHIB, "not a site"], refused("BAD_SITE"));
log(`=== demo run done: ${fails === 0 ? "ALL PASS" : fails + " FAIL"} ===`);
process.exit(fails ? 1 : 0);
