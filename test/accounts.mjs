/**
 * Creates test/.accounts.json (gitignored): throwaway Studio Dev signing keys.
 * Existing roles are preserved unless --force is passed. Keys never leave this
 * file; scripts load them and print addresses only.
 *
 *   deployer   deploys every contract
 *   filer      files canonical seeds
 *   filer2     a second filer (duplicate / rate-limit paths)
 *   demo       drives the demo deployment
 *   demo2      a second demo sender (duplicate / rate-limit paths)
 *   probe      throwaway GenVM probes
 */
import { createAccount } from "genlayer-js";
import { randomBytes } from "node:crypto";
import { existsSync, readFileSync, writeFileSync } from "node:fs";

const target = new URL("./.accounts.json", import.meta.url);
const force = process.argv.includes("--force");
const ROLES = ["deployer", "filer", "filer2", "demo", "demo2", "probe"];
const existing = existsSync(target) && !force ? JSON.parse(readFileSync(target, "utf8")) : {};
const out = {};
for (const role of ROLES) {
  if (existing[role]?.key) { out[role] = existing[role]; continue; }
  const key = `0x${randomBytes(32).toString("hex")}`;
  out[role] = { key, address: createAccount(key).address };
}
writeFileSync(target, JSON.stringify(out, null, 2) + "\n", { mode: 0o600 });
for (const role of ROLES) console.log(`  ${role.padEnd(9)} ${out[role].address}`);
