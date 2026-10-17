# Final check

Run 2026-10-17T10:21:09.212Z by `tools/final_check.mjs` against commit `5b3832711b` and Studio Dev. **8/10 PASS.**

## PASS: Source match: gen_getContractCode byte-identical to contracts/ at HEAD for every deployment, all from one commit, contracts/ unchanged since

```
HEAD 5b3832711b399cf1e7626d2618920450ab202287
BurnProof            0x85807B7781303c0519a4b53734e04798DAD33fda  chain sha256 f91a03ee469ecd852d05787b4da378c4823425aba7fa151144da88f04c0a24a6  identical to HEAD  matches deployments.json  deploy commit ce9cd9d37c  contracts/ unchanged since
BurnProofDemo        0x9433099Eb1Ece546c9A092A09D9695c23fc12353  chain sha256 f91a03ee469ecd852d05787b4da378c4823425aba7fa151144da88f04c0a24a6  identical to HEAD  matches deployments.json  deploy commit ce9cd9d37c  contracts/ unchanged since
BurnGate             0x019C114C50D2a9B3e526E1B473b4840EEE7C0De0  chain sha256 240f74d736804eae9e7c27350e9412a3071cedc75a9afa8b3f452adc78a865ae  identical to HEAD  matches deployments.json  deploy commit ce9cd9d37c  contracts/ unchanged since
BurnGateDemo         0x01cc28ff81e5d773F6fAe6b37E4e71b85e2Bc1C4  chain sha256 240f74d736804eae9e7c27350e9412a3071cedc75a9afa8b3f452adc78a865ae  identical to HEAD  matches deployments.json  deploy commit ce9cd9d37c  contracts/ unchanged since
all deployments from one commit: ce9cd9d37c95b482e0941ec6b4c7b5f3c7e50692
```

## PASS: Seeds: every real seed filed on the canonical contract, final (tx FINALIZED) with a TRUE/FALSE/UNVERIFIABLE verdict matching docs/seeds.onchain.json

```
S1 check #1 TRUE/BURNED_ENOUGH (expected TRUE) tx 0xcec1a482f4 FINALIZED ok
S2 check #2 UNVERIFIABLE/NOT_A_BURN_CLAIM (expected UNVERIFIABLE) tx 0x72ec4b87e8 FINALIZED ok
S3 check #3 UNVERIFIABLE/MULTIPLE_CLAIM_NUMBERS (expected UNVERIFIABLE) tx 0x9778257dd8 FINALIZED ok
S4 check #8 FALSE/BURNED_SHORT (expected FALSE) tx 0xa1829716a5 FINALIZED ok
S5 check #9 TRUE/SUPPLY_WITHIN (expected TRUE) tx 0x2cbe14c657 FINALIZED ok
S6 check #10 TRUE/SUPPLY_WITHIN (expected TRUE) tx 0xdbd0af5bc1 FINALIZED ok
S7 check #7 TRUE/BURNED_ENOUGH (expected TRUE) tx 0x5d4b18eb54 FINALIZED ok
```

## PASS: Seed mix: at least 2 TRUE, 1 FALSE, 1 UNVERIFIABLE, each as researched

```
{"TRUE":4,"FALSE":1,"UNVERIFIABLE":2}; every verdict equals docs/FEASIBILITY.md
```

## PASS: Canonical counters equal the filed checks (checks = true + false + unverifiable)

```
{"checks":10,"false":1,"mode":"CANONICAL","rate_max":5,"rate_window":3600,"true":4,"unverifiable":5,"version":"1.0.0"}
```

## FAIL: Demo: every path on chain (each verdict, each refusal, consumer allow + refuse), all expectations met

```
1 PASS, 0 FAIL in the last run of docs/demo-run.log; paths missing: verdict TRUE, verdict FALSE, verdict UNVERIFIABLE, refusal RATE_LIMITED, refusal DUPLICATE, refusal NOT_ARCHIVE_URL, refusal BAD_TIMESTAMP, gate ALLOW, gate REFUSE
```

## PASS: Addresses consistent everywhere (deployments.json = README = SEEDS = SUBMISSION = logs; no other contract address appears)

```
deployments: BurnProof 0x85807B7781303c0519a4b53734e04798DAD33fda, BurnProofDemo 0x9433099Eb1Ece546c9A092A09D9695c23fc12353, BurnGate 0x019C114C50D2a9B3e526E1B473b4840EEE7C0De0, BurnGateDemo 0x01cc28ff81e5d773F6fAe6b37E4e71b85e2Bc1C4
missing: none
unknown addresses: none
```

## PASS: Every link in README and docs answers HTTP 200 (Wayback captures, Etherscan token and block pages, explorer, GitHub)

```
29 links checked (RPC endpoints and test hosts excluded); failing: none
```

## PASS: All offline tests pass (200+)

```
Ran 358 tests in 0.152s  OK
```

## PASS: Docs: README sections (Scope, Rules, Addresses, How to verify), no 'Known limitations'/'TODO', SUBMISSION plain ASCII

```
missing: none; banned words: none; SUBMISSION ASCII: true
```

## FAIL: Git: keys never committed, no assistant attribution in history or files

```
commits touching test/.accounts.json: none; attribution in messages: none; in files: tools/final_check.mjs:155:  const bad = /co-authored-by|claude|anthropic|chatgpt|openai/i.test(msgs);
tools/final_check.mjs:157:  const words = sh("git", ["grep", "-n", "-i", "-E", "claude|anthropic|chatgpt|co-authored", "--", "."]).stdout.trim();
```
