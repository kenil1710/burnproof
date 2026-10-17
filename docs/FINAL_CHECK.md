# Final check

Run 2026-10-17T13:39:14.281Z by `tools/final_check.mjs` against commit `867cd4ed40` and Studio Dev. **11/11 PASS.**

## PASS: Source match: gen_getContractCode byte-identical to contracts/ at HEAD for every deployment, all from one commit, contracts/ unchanged since

```
HEAD 867cd4ed40dae880afcc27bf6aacb16ab03e2f4c
BurnProof            0xF020B9B711781Ed712195584315F8dB49d1f89f4  chain sha256 7356b4261b1baef8ed9bed664253e833fcb90303fd9a7c2f367d4375e2aa2c67  identical to HEAD  matches deployments.json  deploy commit 6636900373  contracts/ unchanged since
BurnProofDemo        0x019603fa4756dafDf820932b192D49d2Fe8D5014  chain sha256 7356b4261b1baef8ed9bed664253e833fcb90303fd9a7c2f367d4375e2aa2c67  identical to HEAD  matches deployments.json  deploy commit 6636900373  contracts/ unchanged since
BurnGate             0x16aAcCD15eB1756075bE15e727Ab3eBaBe8d2448  chain sha256 240f74d736804eae9e7c27350e9412a3071cedc75a9afa8b3f452adc78a865ae  identical to HEAD  matches deployments.json  deploy commit 6636900373  contracts/ unchanged since
BurnGateDemo         0x307ed86b8CccAb6841ae18FaE1c559C89d7F606E  chain sha256 240f74d736804eae9e7c27350e9412a3071cedc75a9afa8b3f452adc78a865ae  identical to HEAD  matches deployments.json  deploy commit 6636900373  contracts/ unchanged since
all deployments from one commit: 663690037372a21f64c60deb4a73f800f27224f6
```

## PASS: Seeds: every real seed filed on the canonical contract, final (tx FINALIZED) with a TRUE/FALSE/UNVERIFIABLE verdict matching docs/seeds.onchain.json

```
S1 check #1 TRUE/BURNED_ENOUGH (expected TRUE) tx 0x2e72697f77 FINALIZED ok
S2 check #2 FALSE/BURNED_SHORT (expected FALSE) tx 0xb00c26c581 FINALIZED ok
S3 check #3 UNVERIFIABLE/MULTIPLE_CLAIM_NUMBERS (expected UNVERIFIABLE) tx 0xd558484cb5 FINALIZED ok
S4 check #4 FALSE/BURNED_SHORT (expected FALSE) tx 0xcdd06d2c04 FINALIZED ok
S5 check #5 TRUE/SUPPLY_WITHIN (expected TRUE) tx 0xf6110b27fa FINALIZED ok
S6 check #6 TRUE/SUPPLY_WITHIN (expected TRUE) tx 0x8350f24cb5 FINALIZED ok
S7 check #7 TRUE/BURNED_ENOUGH (expected TRUE) tx 0xf2befff771 FINALIZED ok
```

## PASS: Seeds: every TRUE/FALSE read at a block within 24 h after its snapshot, claim type decided by code (no model choice)

```
S1 block 13144796: 6 s after the snapshot, claim type by code ok
S2 block 12567135: 22 s after the snapshot, claim type by code ok
S3 block 13144796: MULTIPLE_CLAIM_NUMBERS (no chain read) ok
S4 block 13867390: 18 s after the snapshot, claim type by code ok
S5 block 13867390: 18 s after the snapshot, claim type by code ok
S6 block 18902821: 6 s after the snapshot, claim type by code ok
S7 block 13908188: 1 s after the snapshot, claim type by code ok
```

## PASS: Seed mix: at least 2 TRUE, 1 FALSE, 1 UNVERIFIABLE, each as researched

```
{"TRUE":4,"FALSE":2,"UNVERIFIABLE":1}; every verdict equals docs/FEASIBILITY.md
```

## PASS: Canonical counters equal the filed checks (checks = true + false + unverifiable)

```
{"checks":7,"false":2,"mode":"CANONICAL","rate_max":5,"rate_window":3600,"true":4,"unverifiable":1,"version":"1.1.0"}
```

## PASS: Demo: every path on chain (each verdict, each refusal, consumer allow + refuse), all expectations met

```
23 PASS, 0 FAIL in the last run of docs/demo-run.log; paths missing: none
```

## PASS: Addresses consistent everywhere (deployments.json = README = SEEDS = SUBMISSION = logs; no other contract address appears)

```
deployments: BurnProof 0xF020B9B711781Ed712195584315F8dB49d1f89f4, BurnProofDemo 0x019603fa4756dafDf820932b192D49d2Fe8D5014, BurnGate 0x16aAcCD15eB1756075bE15e727Ab3eBaBe8d2448, BurnGateDemo 0x307ed86b8CccAb6841ae18FaE1c559C89d7F606E
missing: none
unknown addresses: none
```

## PASS: Every link in README and docs answers HTTP 200 (Wayback captures, Etherscan token and block pages, explorer, GitHub)

```
34 links checked (RPC endpoints and test hosts excluded); failing: none
```

## PASS: All offline tests pass (200+)

```
Ran 372 tests in 0.166s  OK
```

## PASS: Docs: README sections (Scope, Rules, Addresses, How to verify), no word from the hygiene list in README or docs/, SUBMISSION plain ASCII

```
missing: none; files with a listed word: none (8 files scanned; docs/superseded/ is not scanned); SUBMISSION ASCII: true
```

## PASS: Git: keys never committed, no assistant attribution in history or files

```
commits touching test/.accounts.json: none; attribution in messages: none; in files: none
```
