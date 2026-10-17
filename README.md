# BurnProof

A GenLayer intelligent contract that checks **one** published token-burn claim against the chain, and answers **TRUE**, **FALSE** or **UNVERIFIABLE**.

The filer chooses one sentence from an archived page of a project's website. Code checks that the sentence really is on that Wayback capture. The model only labels that one sentence: which kind of claim it makes and which number it uses. Code then checks the label against its own parse of the quote. It reads the token at a pinned finalized Ethereum block from two independent RPCs that must agree exactly, and computes every number and the verdict with integer arithmetic.

```
filer: (chain, token, web.archive.org snapshot, one exact quote, block)
  -> door checks (format, duplicate, rate limit)           refused: nothing stored
  -> Wayback capture: exact Memento-Datetime, same host, quote inside one block
  -> code: exactly one claim-shaped number in the quote
  -> model x2: {type, number, unit} from the quote only; code validates
  -> two RPCs at the block: decimals, totalSupply, balanceOf(dead x4)
  -> code: TRUE / FALSE (0.5% tolerance) or UNVERIFIABLE; stored, final
```

Contract only, no frontend. Studio Dev (chain 61997), GenVM v0.6 format (`# v0.3.0`, `py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng`).

## Rules

The full rules are in [docs/RULES.md](docs/RULES.md). In short:

1. **The quote must be on the archived page.** The URL must be `https://web.archive.org/web/<14-digit timestamp>/<page>`. The archive must serve exactly that capture of that host. The quote must appear, case-sensitively and with whitespace collapsed, inside one block of the page's visible text. Otherwise the result is UNVERIFIABLE.
2. **Three claim types:** `BURNED_AMOUNT` (at least N tokens burned), `BURNED_PERCENT` (at least P% of supply burned) and `SUPPLY_AT_MOST` (total supply is at most N). The quote must hold exactly one claim-shaped number, written in ASCII with no invisible characters, no ranges and no qualifier words (fee, plan, circulating, not burned, ...). The model's number must be written in the quote and equal code's own parse. The leader reads the quote twice, and validators read it again. Any mismatch is UNVERIFIABLE.
3. **The chain is read at one pinned finalized block** from `eth-pokt.nodies.app` and `rpc.mevblocker.io`, which must agree exactly. Burned means the sum of `balanceOf` over the frozen dead addresses `0x0`, `0x...01`, `0x...dEaD` and `0xdEAD...42069`. When none of them holds anything, burn claims are UNVERIFIABLE: tokens whose burns lower `totalSupply` have no readable original supply at one block.
4. **Claims are "at least".** TRUE if `actual >= claimed x (1 - 0.5%)`, and `SUPPLY_AT_MOST` is TRUE if `totalSupply <= N x (1 + 0.5%)`. Decimals come from the token. The boundary itself is TRUE.
5. **No funds held.** Filing is free but rate-limited per sender (canonical: 5 per hour). Duplicates of (token, snapshot, quote, block) are refused. Counters change only after all checks pass. Every accepted filing ends with a stored, final verdict, and timeouts end UNVERIFIABLE.

Reads: `get_check(id)`, `list_checks(start, count)`, `latest_verdict(chain_id, token, host)`, plus `get_stats()`, `get_rules()` and `rate_status(sender)`.

**BurnGate** is a small listing contract that consumes BurnProof. `request_listing(chain_id, token, site)` refuses a token whose latest decisive burn claim from its own `site` is FALSE, and lists it otherwise. "Latest" means the most recent snapshot time, so a later filing cannot mask a FALSE. Claims from other sites do not count, so a third party cannot get a token refused.

## How a burn claim is decided

This is `decide()` and `read_chain()` in `contracts/BurnProof.py`. It uses integer arithmetic only.

**What counts as burned.** `burned` is the sum of `balanceOf` at the pinned block over exactly four frozen addresses:

| Address | What it is |
|---|---|
| `0x0000000000000000000000000000000000000000` | the zero address |
| `0x0000000000000000000000000000000000000001` | the `ecrecover` precompile |
| `0x000000000000000000000000000000000000dEaD` | the conventional burn address |
| `0xdEAD000000000000000042069420694206942069` | Shiba Inu's burn address |

Tokens held anywhere else count as not burned. That includes team wallets, LP locks and any other "burn" wallet. Tokens destroyed by a `burn()` that lowers `totalSupply` are not counted either. If all four balances are zero, a burn claim ends UNVERIFIABLE (`NO_DEAD_ADDRESS_BURNS`), not FALSE.

**The percentage rule (`BURNED_PERCENT`, claimed P%).**

```
TRUE  iff  burned / totalSupply  >=  P/100 x (1 - 0.005)
in code:   burned * 100 * 1000 * den  >=  num * 995 * totalSupply      (P = num/den, parsed by code)
```

- The tolerance is **relative**: 0.5% of the claimed figure, not 0.5 percentage points. A 40% claim passes from 39.8%, and a 49% claim passes from 48.755%.
- The denominator is `totalSupply()` at the pinned block, so it is the supply as it stands at that block, not the original supply.
- The rule is a **floor**. Any share at or above the threshold is TRUE, however far above it is. The contract does not test whether the figure is exact, and it does not flag a claim that understates. The boundary itself is TRUE and one base unit below it is FALSE (`test_percent_exact_boundary_is_true`, `test_percent_one_wei_below_boundary_is_false`).
- The block is chosen by the filer. It must be finalized on both RPCs and no older than the snapshot (`BLOCK_BEFORE_SNAPSHOT`). See [Limitations](#limitations) for what that means for a TRUE.

The other two types use the same tolerance. `BURNED_AMOUNT` is TRUE iff `burned >= N x 0.995` tokens. `SUPPLY_AT_MOST` is TRUE iff `totalSupply <= N x 1.005` tokens.

| Seed | Claimed | TRUE from | Dead addresses hold (block) | Verdict |
|---|---|---|---|---|
| S1 SHIB | 40% | 39.8% | 41.0493% (26211211) | **TRUE** |
| S7 SAITAMA | 49% | 48.755% | 59.4128% (26211243) | **TRUE** |
| S4 AKITA | 7.82% | 7.7809% | 5.0201% (26211402) | **FALSE** |

S7 is TRUE even though the measured share is 10.4 points above the claim. "We have already started with 49% of the supply burned" is read as "at least 49%", and 59.41% is at least 49%. Almost all of S7's share is at `0x...dEaD`: 59,412,845,974,111,341 of 100,000,000,000,000,000 SAITAMA. S1 is TRUE with a 1.05-point margin, and almost all of its share is at SHIB's `0xdEAD...42069`.

## What's deterministic vs what the model decides

**Pure code.** Every node computes the same result from the same bytes:

- **Door checks:** the chain id, the token format, the snapshot URL and its timestamp, the quote's length and characters, the block range, duplicates and the rate limit. A refusal stores nothing.
- **The page:** that the archive served exactly the filed capture (`Memento-Datetime`, original host), and that the quote sits inside one text block.
- **The number:** code finds every number in the quote and keeps the claim-shaped ones (a percent, a scaled number, or a plain number of at least 10,000). The check ends UNVERIFIABLE before any model call if the quote has no such number, more than one, a zero, a range or list, ambiguous digit grouping, non-ASCII digits or invisible characters. S3 ("supply of 1 quadrillion ... locked 50%") ends `MULTIPLE_CLAIM_NUMBERS` this way.
- **Qualifier words** (`fee`, `tax`, `plan`, `will `, `liquidity`, `circulat`, `not burn`, ...) end the check `CLAIM_QUALIFIED`, whatever the model said.
- **Checking the model's answer** (see below).
- **The chain:** both RPCs must return the same block hash, timestamp, code presence, `decimals`, `totalSupply` and the four dead balances at a block that is finalized on both and no older than the snapshot. Any difference ends `RPC_DISAGREE`.
- **The verdict:** the arithmetic above.

**What the model decides.** It reads only the quote, never the page or the chain, and returns `{type, number, unit}`. It decides two things:

1. **Whether the sentence is a burn or supply claim at all.** `NONE` ends `NOT_A_BURN_CLAIM`. In S2, "The remaining 50% was burned to Vitalik Buterin", the number parses fine and dead addresses hold 41.05%, which would be FALSE on the numbers. Both readings returned `NONE`, because tokens sent to a person are not burned. So the check is UNVERIFIABLE.
2. **For a non-percent number only, which claim it is:** `BURNED_AMOUNT` or `SUPPLY_AT_MOST`. This selects which comparison runs. For a percent, code requires `BURNED_PERCENT`, and any other type is `MODEL_OUTPUT_INVALID`.

The model never supplies the value. Its `number` must be written in the quote, and together with any scale word in `unit` it must equal code's own parse, in value and kind (percent or not). The value stored and used is code's parse.

**When the model readings disagree.**

- **Leader.** The leader reads the quote twice. The value comes from code, so two valid readings can differ only in type. If they differ, the check ends UNVERIFIABLE `READINGS_DIFFER`. If either reading is `NONE`, invalid or fails, the check ends UNVERIFIABLE with that code.
- **Validators, when the leader ended UNVERIFIABLE at the model stage.** A validator accepts if its own code finds the same claim-shaped number. Withholding a verdict needs no agreement.
- **Validators, when the leader reached TRUE or FALSE.** Each validator reads the quote once itself. If its reading is `NONE`, invalid or a different type, it rejects. Otherwise it reads the chain again and must reproduce the result exactly. If no leader's result is accepted, the transaction ends with nothing stored, and the claim can be filed again.

So a TRUE or FALSE needs every reading to agree. The model can stop a verdict, and for a plain number it chooses which comparison applies. It cannot change a number or the arithmetic.

## Addresses

Studio Dev, chain id 61997, RPC `https://studio-dev.genlayer.com/api`. All four contracts were deployed from commit `ce9cd9d`. `deployments.json` holds the sha256 of each one's code, its deploy tx and its constructor arguments.

| Contract | Address | Constructor |
|---|---|---|
| BurnProof (canonical) | [`0x85807B7781303c0519a4b53734e04798DAD33fda`](https://explorer-studio-dev.genlayer.com/address/0x85807B7781303c0519a4b53734e04798DAD33fda) | `("CANONICAL", 5, 3600)` |
| BurnProofDemo | [`0x9433099Eb1Ece546c9A092A09D9695c23fc12353`](https://explorer-studio-dev.genlayer.com/address/0x9433099Eb1Ece546c9A092A09D9695c23fc12353) | `("DEMO", 2, 600)` |
| BurnGate | [`0x019C114C50D2a9B3e526E1B473b4840EEE7C0De0`](https://explorer-studio-dev.genlayer.com/address/0x019C114C50D2a9B3e526E1B473b4840EEE7C0De0) | `(BurnProof)` |
| BurnGateDemo | [`0x01cc28ff81e5d773F6fAe6b37E4e71b85e2Bc1C4`](https://explorer-studio-dev.genlayer.com/address/0x01cc28ff81e5d773F6fAe6b37E4e71b85e2Bc1C4) | `(BurnProofDemo)` |

BurnProof and BurnProofDemo run the same file, byte for byte. They differ only in the rate-limit arguments: the demo allows 2 filings per 10 minutes, so the rate limit can be shown on chain.

## Seeds

Every seed is a real claim from an official project page with a Wayback capture, filed on the canonical contract. [docs/SEEDS.md](docs/SEEDS.md) lists each check with its Wayback link, Etherscan token and block links, and the numbers read. The research behind them, including the rejected candidates and the measured RPCs, is in [docs/FEASIBILITY.md](docs/FEASIBILITY.md).

| Seed | Project | Wayback | Quote | Verdict | Why (computed by code) | Check / tx |
|---|---|---|---|---|---|---|
| S1 | Shiba Inu (SHIB) | [capture](https://web.archive.org/web/20210902070016/https://shibatoken.com/) | "and then actually burned 40% of its total supply to a dead wallet" | **TRUE** | dead addresses hold 41.0493% of totalSupply >= claimed 40.0000% | [#1](https://explorer-studio-dev.genlayer.com/tx/0xcec1a482f4ab24f51b92744ac026796a3856bd8a514edb823713a1357ff832db) |
| S2 | Shiba Inu (SHIB) | [capture](https://web.archive.org/web/20210604091955/https://shibatoken.com/) | "The remaining 50% was burned to Vitalik Buterin" | **UNVERIFIABLE** | NOT_A_BURN_CLAIM | [#2](https://explorer-studio-dev.genlayer.com/tx/0x72ec4b87e8104531850f5bc732febe51e5accdde0dc5d3a95d164961648f6d56) |
| S3 | Shiba Inu (SHIB) | [capture](https://web.archive.org/web/20210902070016/https://shibatoken.com/) | "Starting with a supply of 1 quadrillion, our founder, Ryoshi, locked 50% in Uniswap" | **UNVERIFIABLE** | MULTIPLE_CLAIM_NUMBERS | [#3](https://explorer-studio-dev.genlayer.com/tx/0x9778257dd8965b78169b90cacd479c4fbcaf31eed79557ef3eb6ab630675b835) |
| S4 | Akita Inu (AKITA) | [capture](https://web.archive.org/web/20211224103559/https://www.akita.network/) | "Percent burned: 7.82%" | **FALSE** | dead addresses hold 5.0201% of totalSupply < claimed 7.8200% | [#8](https://explorer-studio-dev.genlayer.com/tx/0xa1829716a5f0e0e96d2763d15c6f72774e40ea65fa9fc12acf184c5b959134cc) |
| S5 | Akita Inu (AKITA) | [capture](https://web.archive.org/web/20211224103559/https://www.akita.network/) | "Max Supply: 100,000,000,000,000" | **TRUE** | totalSupply 99,999,999,999,999.9999 <= claimed 100,000,000,000,000.0000 | [#9](https://explorer-studio-dev.genlayer.com/tx/0x2cbe14c657bb503c26c25b58bc81feebaa76a308e618e133c2781b70f9fcb34c) |
| S6 | FLOKI | [capture](https://web.archive.org/web/20231231033517/https://floki.com/) | "Total Supply: 10,000,000,000,000" | **TRUE** | totalSupply 10,000,000,000,000.0000 <= claimed 10,000,000,000,000.0000 | [#10](https://explorer-studio-dev.genlayer.com/tx/0xdbd0af5bc1364f89583029181b246fcb0d9d11dafb55f3338f15f166cac7da6e) |
| S7 | Saitama Inu (SAITAMA v1) | [capture](https://web.archive.org/web/20211230180830/https://saitamatoken.com/) | "We have already started with 49% of the supply burned." | **TRUE** | dead addresses hold 59.4128% of totalSupply >= claimed 49.0000% | [#7](https://explorer-studio-dev.genlayer.com/tx/0x5d4b18eb5446432eed445ec3fbe1e8453c81d3f289cae1f7732c966be723c600) |

The demo deployment runs every path on chain: each verdict, each refusal, and the consumer's allow and refuse. The log is in [docs/demo-run.log](docs/demo-run.log). The log keeps every run. The first run had 5 failures because web.archive.org throttled concurrent fetches from Studio Dev's nodes (each ended `PAGE_UNAVAILABLE`, as the rules require). The last run spaces out archive fetches and passes all 20 paths.

S2 was expected FALSE on the numbers: 41.05% is at dead addresses, short of 50%. On chain, both model readings returned NONE, because the sentence says the tokens were "burned to Vitalik Buterin", which means sent to a person. The model can withhold a verdict, but it cannot supply a number (see [What's deterministic vs what the model decides](#whats-deterministic-vs-what-the-model-decides)).

## How to verify

```sh
git clone https://github.com/kenil1710/burnproof && cd burnproof/test && npm ci

# 1. the deployed code is byte-identical to contracts/ at HEAD (gen_getContractCode)
node ../tools/verify_source.mjs

# 2. read any check straight from the chain
node tx.mjs --set=final --c=BurnProof --view=get_check --args='[1]'
node tx.mjs --set=final --c=BurnProof --view=latest_verdict --args='[1,"0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce",""]'

# 3. the offline suite (no network, no dependencies)
python3 -m unittest -q test_burnproof test_attacks

# 4. everything at once: source match, seeds final, addresses, links, tests -> docs/FINAL_CHECK.md
node ../tools/final_check.mjs
```

You can also recompute any verdict by hand. Open the Wayback link and find the quote. Then open the Etherscan block and call `totalSupply()` and `balanceOf()` for the four dead addresses at that block. The stored `dead_balances`, `total_supply` and `why` of the check show the same numbers.

## Scope

- **Burned means held by a frozen dead address.** Burns that only lower `totalSupply` make burn claims UNVERIFIABLE. A token that burns both ways is measured by its dead-address holdings, and the FALSE reason states the measured share.
- **The token reports its own balances.** BurnProof reads what the token contract answers at the pinned block, from two RPCs. A token contract that lies about `balanceOf` is outside what a chain read can establish.
- **Static HTML only.** The quote must be in the archived HTML. Numbers that a page fills in with JavaScript are not in the capture, and such quotes end QUOTE_NOT_ON_PAGE.
- **One claim per filing, read as a floor.** Hedges ("over", "nearly") are not interpreted. Ranges, multiple numbers and qualified numbers are UNVERIFIABLE by rule.
- **The model's only freedom** is the claim type for a non-percent number (`BURNED_AMOUNT` vs `SUPPLY_AT_MOST`), and both readings and every validator must agree on it.
- **A transport failure ends UNVERIFIABLE**, and validators accept a leader's transport failure without reproducing it. Such a check asserts nothing, and the claim can be filed again at another block.

## Limitations

- **Ethereum mainnet only.** Every read needs two independent archive RPCs that answer from GenVM and agree exactly. BSC was dropped because only one archive RPC answered from GenVM, so the two-RPC rule could not be met (docs/FEASIBILITY.md). Chain 56 is refused with `UNSUPPORTED_CHAIN`.
- **No BURNED_AMOUNT seed.** No official page had an absolute burned-amount claim in its static HTML. BURNED_AMOUNT is covered by the offline tests only (`test_amount_true`, `test_amount_false`, `test_amount_exact_boundary_is_true`, `test_amount_one_wei_below_boundary_is_false`).
- **A TRUE is measured at the filed block, not at the snapshot.** The seeds were read at Ethereum blocks from 2026-10-17, years after their 2021 and 2023 snapshots. Dead-address balances only grow, so a later block can only show more burned. S7's TRUE shows that dead addresses held at least 49% of supply in October 2026. It does not show they held 49% on 2021-12-30. If a token's supply never grows, a FALSE at a later block also held at snapshot time. The contract accepts any finalized block from the snapshot onward, so filing at a block close to the snapshot gives the strictest test.
- **Wayback throttles Studio Dev.** web.archive.org throttles bursts of fetches from Studio Dev's nodes. A throttled fetch ends UNVERIFIABLE `PAGE_UNAVAILABLE`, and that result is final, because transport failures are accepted as they are. The first canonical filings of three seeds ended this way, and they stay on chain:

  | Early check | Seed | Result | Refiled as |
  |---|---|---|---|
  | #4 | S4 AKITA "Percent burned: 7.82%" | UNVERIFIABLE `PAGE_UNAVAILABLE` | #8, FALSE |
  | #5 | S5 AKITA "Max Supply: 100,000,000,000,000" | UNVERIFIABLE `PAGE_UNAVAILABLE` | #9, TRUE |
  | #6 | S6 FLOKI "Total Supply: 10,000,000,000,000" | UNVERIFIABLE `PAGE_UNAVAILABLE` | #10, TRUE |

  Each was refiled at a newer block after a 3-minute cool-down. `latest_verdict` never counts an UNVERIFIABLE as decisive, so these three records do not change any token's standing or BurnGate's answer. The first demo run had 5 failures for the same reason (docs/demo-run.log).

## Repository

| Path | What |
|---|---|
| `contracts/BurnProof.py` | The checker (canonical and demo) |
| `contracts/BurnGate.py` | The consumer |
| `test/test_burnproof.py`, `test/test_attacks.py` | Offline suite (stubbed GenVM, mock Wayback, mock RPCs, scripted model) |
| `test/deploy.mjs`, `test/seed_canonical.mjs`, `test/demo_paths.mjs`, `test/tx.mjs` | Deploy from HEAD, seed, demo, single calls |
| `tools/verify_source.mjs`, `tools/final_check.mjs` | Source match, final check |
| `docs/` | RULES, SEEDS, FEASIBILITY, ATTACK_REPORT, FINAL_CHECK, SUBMISSION, demo-run.log |

Test keys are throwaway Studio Dev accounts in the gitignored `test/.accounts.json` (`node test/accounts.mjs` creates them).
