// Deploys test/probe/Probe.py and runs one probe (web fetch, RPCs, model) on Studio Dev.
import { readFileSync } from "node:fs";
import { createClient, createAccount } from "genlayer-js";
import { CHAINS, accounts, fundOnStudio, deploy, connect, argOf } from "./harness.mjs";
const chain = CHAINS.studiodev;
const acc = accounts();
const account = createAccount(acc.probe.key);
await fundOnStudio(chain, account.address, 100n * 10n ** 18n);
let address = argOf("address");
if (!address) {
  const res = await deploy({ chain, wallet: createClient({ chain, account }), read: createClient({ chain }), code: readFileSync(new URL("./probe/Probe.py", import.meta.url), "utf8"), args: [], label: "probe" });
  if (!res.ok) { console.log("deploy failed", res.out?.revertReason, res.out?.stderr?.slice(-1500)); process.exit(1); }
  address = res.address;
}
console.log("probe at", address);
const { send, view } = connect({ address, role: "probe" });
const out = await send("run", [argOf("url"), argOf("rpcs", "[]"), argOf("prompt", "")]);
console.log(out.status, out.ok, out.revertReason?.slice(0, 300), out.stderr?.slice(-800));
console.log(await view("get", []));
