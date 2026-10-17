# BurnProof

A GenLayer intelligent contract that checks **one** published token-burn claim against the chain, and answers **TRUE**, **FALSE** or **UNVERIFIABLE**.

The filer chooses one sentence from an archived page of a project's website. Code checks that the sentence really is on that Wayback capture and finds the one number it claims. When the sentence's own words settle what kind of claim it is ("burned", "total supply"), code names the claim type. Only when they do not does the model read the sentence and name the type, and code checks that answer against its own parse. Code reads the token from two independent RPCs that must agree exactly, at a finalized Ethereum block within 24 hours after the capture, and computes every number and the verdict with integer arithmetic.

```
filer: (chain, token, web.archive.org snapshot, one exact quote, block)
  -> door checks (format, duplicate, rate limit)           refused: nothing stored
  -> Wayback capture: exact Memento-Datetime, same host, quote inside one block
  -> code: exactly one claim-shaped number, no qualifier word
  -> claim type: code, from the quote's words; else model x2, validated by code
  -> two RPCs at the block (snapshot <= block time <= snapshot + 24 h):
     decimals, totalSupply, balanceOf(dead x4)
  -> code: TRUE / FALSE (0.5% tolerance) or UNVERIFIABLE; stored, final
```

Contract only, no frontend. Studio Dev (chain 61997), GenVM v0.6 format (`# v0.3.0`, `py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng`). Version 1.1.0.

## Rules

The full rules are in [docs/RULES.md](docs/RULES.md). In short:

1. **The quote must be on the archived page.** The URL must be `https://web.archive.org/web/<14-digit timestamp>/<page>`. The archive must serve exactly that capture of that host. The quote must appear, case-sensitively and with whitespace collapsed, inside one block of the page's visible text. Otherwise the result is UNVERIFIABLE.
2. **Three claim types:** `BURNED_AMOUNT` (at least N tokens burned), `BURNED_PERCENT` (at least P% of supply burned) and `SUPPLY_AT_MOST` (total supply is at most N). The quote must hold exactly one claim-shaped number, written in ASCII with no invisible characters, no ranges and no qualifier words (fee, plan, circulating, not burned, ...). Code names the type when the quote's words settle it. Otherwise the model names it, its number must be written in the quote and equal code's own parse, and every reading must agree. Any mismatch is UNVERIFIABLE.
3. **The chain is read at one finalized block within 24 hours after the snapshot** from `eth-pokt.nodies.app` and `rpc.mevblocker.io`, which must agree exactly. A block before the snapshot ends `BLOCK_BEFORE_SNAPSHOT`, and a block more than 24 hours after it ends `BLOCK_AFTER_WINDOW`. Burned means the sum of `balanceOf` over the frozen dead addresses `0x0`, `0x...01`, `0x...dEaD` and `0xdEAD...42069`. When none of them holds anything, burn claims are UNVERIFIABLE: tokens whose burns lower `totalSupply` have no readable original supply at one block.
4. **Claims are "at least".** TRUE if `actual >= claimed x (1 - 0.5%)`, and `SUPPLY_AT_MOST` is TRUE if `totalSupply <= N x (1 + 0.5%)`. Decimals come from the token. The boundary itself is TRUE.
5. **No funds held.** Filing is free but rate-limited per sender (canonical: 5 per hour). Duplicates of (token, snapshot, quote, block) are refused. Counters change only after all checks pass. Every accepted filing ends with a stored, final verdict, and timeouts end UNVERIFIABLE.

Reads: `get_check(id)`, `list_checks(start, count)`, `latest_verdict(chain_id, token, host)`, plus `get_stats()`, `get_rules()` and `rate_status(sender)`.

**BurnGate** is a small listing contract that consumes BurnProof. `request_listing(chain_id, token, site)` refuses a token whose latest decisive burn claim from its own `site` is FALSE, and lists it otherwise. "Latest" means the most recent snapshot time, so a later filing cannot mask a FALSE. Claims from other sites do not count, so a third party cannot get a token refused.

## How a burn claim is decided

This is `decide()`, `read_chain()` and `back()` in `contracts/BurnProof.py`. It uses integer arithmetic only.

**What counts as burned.** `burned` is the sum of `balanceOf` at the pinned block over exactly four frozen addresses:

| Address | What it is |
|---|---|
| `0x0000000000000000000000000000000000000000` | the zero address |
| `0x0000000000000000000000000000000000000001` | the `ecrecover` precompile |
| `0x000000000000000000000000000000000000dEaD` | the conventional burn address |
| `0xdEAD000000000000000042069420694206942069` | Shiba Inu's burn address |

Tokens held anywhere else count as not burned. That includes team wallets, LP locks, a person's wallet and any other "burn" wallet. Tokens destroyed by a `burn()` that lowers `totalSupply` are not counted either. If all four balances are zero, a burn claim ends UNVERIFIABLE (`NO_DEAD_ADDRESS_BURNS`), not FALSE.

**When.** The block's timestamp must lie between the snapshot's capture time and 24 hours after it. The claim is therefore checked against the chain as it stood when the page was archived, not years later. Any 24 hours hold about 7,200 Ethereum blocks. The seeds use the first block at or after the capture.

**The percentage rule (`BURNED_PERCENT`, claimed P%).**

```
TRUE  iff  burned / totalSupply  >=  P/100 x (1 - 0.005)
in code:   burned * 100 * 1000 * den  >=  num * 995 * totalSupply      (P = num/den, parsed by code)
```

- The tolerance is **relative**: 0.5% of the claimed figure, not 0.5 percentage points. A 40% claim passes from 39.8%, a 49% claim from 48.755%, and a 50% claim from 49.75%.
- The denominator is `totalSupply()` at the pinned block.
- The rule is a **floor**. Any share at or above the threshold is TRUE, however far above it is. The contract tests "at least", not "exactly". The boundary itself is TRUE and one base unit below it is FALSE (`test_percent_exact_boundary_is_true`, `test_percent_one_wei_below_boundary_is_false`).

The other two types use the same tolerance. `BURNED_AMOUNT` is TRUE iff `burned >= N x 0.995` tokens. `SUPPLY_AT_MOST` is TRUE iff `totalSupply <= N x 1.005` tokens.

| Seed | Claimed | TRUE from | Dead addresses hold (block, time after capture) | Verdict |
|---|---|---|---|---|
| S1 SHIB | 40% | 39.8% | 41.0280% (13144796, +6 s) | **TRUE** |
| S7 SAITAMA | 49% | 48.755% | 56.0887% (13908188, +1 s) | **TRUE** |
| S2 SHIB | 50% | 49.75% | 41.0270% (12567135, +22 s) | **FALSE** |
| S4 AKITA | 7.82% | 7.7809% | 5.0194% (13867390, +18 s) | **FALSE** |

S7 is TRUE even though the measured share is 7.1 points above the claim. "We have already started with 49% of the supply burned" is read as "at least 49%", and 56.09% held one second after the capture is at least 49%. Almost all of it is at `0x...dEaD`. S1 is TRUE with a 1.03-point margin, almost all of it at SHIB's `0xdEAD...42069`.

## What's deterministic vs what the model decides

**Pure code.** Every node computes the same result from the same bytes:

- **Door checks:** the chain id, the token format, the snapshot URL and its timestamp, the quote's length and characters, the block range, duplicates and the rate limit. A refusal stores nothing.
- **The page:** that the archive served exactly the filed capture (`Memento-Datetime`, original host), and that the quote sits inside one text block.
- **The number:** code finds every number in the quote and keeps the claim-shaped ones (a percent, a scaled number, or a plain number of at least 10,000). The check ends UNVERIFIABLE if the quote has no such number, more than one, a zero, a range or list, ambiguous digit grouping, non-ASCII digits or invisible characters. S3 ("supply of 1 quadrillion ... locked 50%") ends `MULTIPLE_CLAIM_NUMBERS` this way.
- **Qualifier words** (`fee`, `tax`, `plan`, `will `, `liquidity`, `circulat`, `not burn`, ...) end the check `CLAIM_QUALIFIED` before any model call.
- **The claim type, when the quote's words settle it** (`code_type()`):

  | The quote has | Number | Type (by code) |
  |---|---|---|
  | "burned" or "burnt" | percent | `BURNED_PERCENT` |
  | "burned" or "burnt", no "total/max/maximum supply" | not a percent | `BURNED_AMOUNT` |
  | "total/max/maximum supply", no "burned"/"burnt" | not a percent | `SUPPLY_AT_MOST` |

  Code leaves the type to the model when none of these rows fits, when both word groups appear with a plain number, when the quote has a non-ASCII letter, or when the number is followed by a further scale-like word ("400 thousand million", "5 zillion").
- **The chain:** both RPCs must return the same block hash, timestamp, code presence, `decimals`, `totalSupply` and the four dead balances, at a block finalized on both and inside the 24-hour window.
- **The verdict:** the arithmetic above.

Every check stores `claim_by`: `code` or `model`.

**What the model decides, for the other quotes.** It reads only the quote, never the page or the chain, and returns `{type, number, unit}`. It decides whether the sentence is a burn or supply claim at all (`NONE` ends `NOT_A_BURN_CLAIM`), and which type it is. Code still requires a percent to be `BURNED_PERCENT`. The model never supplies the value: its `number` must be written in the quote, and together with any scale word in `unit` it must equal code's own parse in value and kind. The value stored and used is code's parse.

**When the model readings disagree.**

- **Leader.** The leader reads the quote twice. The value comes from code, so two valid readings can differ only in type. If they differ, the check ends UNVERIFIABLE `READINGS_DIFFER`. If either reading is `NONE`, invalid or fails, the check ends UNVERIFIABLE with that code.
- **Validators, when the leader ended UNVERIFIABLE at the model stage.** A validator accepts if its own code finds the same claim-shaped number and also leaves the type to the model.
- **Validators, when the leader reached TRUE or FALSE through the model.** Each validator reads the quote once itself. If its reading is `NONE`, invalid or a different type, it rejects. Otherwise it reads the chain again and must reproduce the result exactly. If no leader's result is accepted, the transaction ends with nothing stored, and the claim can be filed again.

**No seed verdict depends on a model choice.** Every seed quote is typed by code or stopped by code before the type matters, so the model is never asked (`TestSeedQuotesByCode` files each seed quote with the model answering `NONE` and then failing, and gets the same verdict both times). The demo shows the model path on chain with a real quote that has no burn or supply words.

## Addresses

Studio Dev, chain id 61997, RPC `https://studio-dev.genlayer.com/api`. All four contracts were deployed from commit `6636900`. `deployments.json` holds the sha256 of each one's code, its deploy tx and its constructor arguments.

| Contract | Address | Constructor |
|---|---|---|
| BurnProof (canonical) | [`0xF020B9B711781Ed712195584315F8dB49d1f89f4`](https://explorer-studio-dev.genlayer.com/address/0xF020B9B711781Ed712195584315F8dB49d1f89f4) | `("CANONICAL", 5, 3600)` |
| BurnProofDemo | [`0x019603fa4756dafDf820932b192D49d2Fe8D5014`](https://explorer-studio-dev.genlayer.com/address/0x019603fa4756dafDf820932b192D49d2Fe8D5014) | `("DEMO", 2, 600)` |
| BurnGate | [`0x16aAcCD15eB1756075bE15e727Ab3eBaBe8d2448`](https://explorer-studio-dev.genlayer.com/address/0x16aAcCD15eB1756075bE15e727Ab3eBaBe8d2448) | `(BurnProof)` |
| BurnGateDemo | [`0x307ed86b8CccAb6841ae18FaE1c559C89d7F606E`](https://explorer-studio-dev.genlayer.com/address/0x307ed86b8CccAb6841ae18FaE1c559C89d7F606E) | `(BurnProofDemo)` |

BurnProof and BurnProofDemo run the same file, byte for byte. They differ only in the rate-limit arguments: the demo allows 2 filings per 10 minutes, so the rate limit can be shown on chain. Earlier versions are listed in [docs/superseded/](docs/superseded/).

## Seeds

Every seed is a real claim from an official project page with a Wayback capture, filed on the canonical contract at the first Ethereum block at or after the capture time. [docs/SEEDS.md](docs/SEEDS.md) lists each check with its Wayback link, Etherscan token and block links, and the numbers read. The research behind them, including the rejected candidates and the measured RPCs, is in [docs/FEASIBILITY.md](docs/FEASIBILITY.md).

| Seed | Project | Wayback | Quote | Verdict | Why (computed by code) | Check / tx |
|---|---|---|---|---|---|---|
| S1 | Shiba Inu (SHIB) | [capture](https://web.archive.org/web/20210902070016/https://shibatoken.com/) | "and then actually burned 40% of its total supply to a dead wallet" | **TRUE** | dead addresses hold 41.0280% of totalSupply >= claimed 40.0000% | [#1](https://explorer-studio-dev.genlayer.com/tx/0x2e72697f77aa204d949830d81b9403b85214a3e74d108c5ccf524e2dad2214a2) |
| S2 | Shiba Inu (SHIB) | [capture](https://web.archive.org/web/20210604091955/https://shibatoken.com/) | "The remaining 50% was burned to Vitalik Buterin" | **FALSE** | dead addresses hold 41.0270% of totalSupply < claimed 50.0000% | [#2](https://explorer-studio-dev.genlayer.com/tx/0xb00c26c581b5002d4c977b9fb971054ac00cd0a4e40152948e314a3248475968) |
| S3 | Shiba Inu (SHIB) | [capture](https://web.archive.org/web/20210902070016/https://shibatoken.com/) | "Starting with a supply of 1 quadrillion, our founder, Ryoshi, locked 50% in Uniswap" | **UNVERIFIABLE** | MULTIPLE_CLAIM_NUMBERS | [#3](https://explorer-studio-dev.genlayer.com/tx/0xd558484cb5f68857ddea9ea67a0ac2547e16125855702a9ee22a95c7ddda11a5) |
| S4 | Akita Inu (AKITA) | [capture](https://web.archive.org/web/20211224103559/https://www.akita.network/) | "Percent burned: 7.82%" | **FALSE** | dead addresses hold 5.0194% of totalSupply < claimed 7.8200% | [#4](https://explorer-studio-dev.genlayer.com/tx/0xcdd06d2c043643b784c8ad4af8f24a4ab0110ec5242b20e79ec9bc030b7fb4a7) |
| S5 | Akita Inu (AKITA) | [capture](https://web.archive.org/web/20211224103559/https://www.akita.network/) | "Max Supply: 100,000,000,000,000" | **TRUE** | totalSupply 99,999,999,999,999.9999 <= claimed 100,000,000,000,000.0000 | [#5](https://explorer-studio-dev.genlayer.com/tx/0xf6110b27fa506ed5d91967f5fbe1dac8885f3860d64dca4e19c88215f45248de) |
| S6 | FLOKI | [capture](https://web.archive.org/web/20231231033517/https://floki.com/) | "Total Supply: 10,000,000,000,000" | **TRUE** | totalSupply 10,000,000,000,000.0000 <= claimed 10,000,000,000,000.0000 | [#6](https://explorer-studio-dev.genlayer.com/tx/0x8350f24cb592a300fc9851700132e177bb808ed75dc5c53a79cdd3b6adf020a5) |
| S7 | Saitama Inu (SAITAMA v1) | [capture](https://web.archive.org/web/20211230180830/https://saitamatoken.com/) | "We have already started with 49% of the supply burned." | **TRUE** | dead addresses hold 56.0887% of totalSupply >= claimed 49.0000% | [#7](https://explorer-studio-dev.genlayer.com/tx/0xf2befff771ac2685e5ff34844356f9bc3317f248fe1b4aaf4ab07b433efd0709) |

S2 is FALSE by code. "The remaining 50% was burned to Vitalik Buterin" says "burned" and gives a percent, so code types it `BURNED_PERCENT`. At the capture, 41.03% of SHIB was at dead addresses, short of 49.75%. The tokens sent to Vitalik Buterin's wallet count only for the part he later sent to a dead address.

The demo deployment runs every path on chain: each verdict, the 24-hour window, the model path, each refusal, and the consumer's allow and refuse. The log is in [docs/demo-run.log](docs/demo-run.log) and keeps every run. In the first run one Studio Dev transaction took 80 minutes to settle, which put the rate-limit and duplicate steps after it out of sequence, and one fee estimate came back zero. The second run files a few blocks later (still inside the window) and passes all 22 paths.

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

You can also recompute any verdict by hand. Open the Wayback link and find the quote. Then open the Etherscan block, check its time against the capture time, and call `totalSupply()` and `balanceOf()` for the four dead addresses at that block. The stored `dead_balances`, `total_supply`, `block_time` and `why` of the check show the same numbers.

## Scope

- **Ethereum mainnet.** Every read needs two independent archive RPCs that answer from GenVM and agree exactly. Both Ethereum RPCs serve state back to 2021 from inside GenVM (docs/FEASIBILITY.md). On BSC only one archive RPC answered from GenVM, so the two-RPC rule cannot be met there, and chain 56 is refused with `UNSUPPORTED_CHAIN`.
- **Burned means held by a frozen dead address.** Burns that only lower `totalSupply` make burn claims UNVERIFIABLE. A token that burns both ways is measured by its dead-address holdings, and the FALSE reason states the measured share.
- **Checked as of the capture.** The block must fall within 24 hours after the snapshot. A later block ends `BLOCK_AFTER_WINDOW`, so a claim cannot be made TRUE by burns that happened after the page said it.
- **The token reports its own balances.** BurnProof reads what the token contract answers at the pinned block, from two RPCs. A token contract that lies about `balanceOf` is outside what a chain read can establish.
- **Static HTML.** The quote must be in the archived HTML. Numbers that a page fills in with JavaScript are absent from the capture, and such quotes end `QUOTE_NOT_ON_PAGE`.
- **One claim per filing, read as a floor.** Hedges ("over", "nearly") are not interpreted. Ranges, multiple numbers and qualified numbers are UNVERIFIABLE by rule.
- **BURNED_AMOUNT** is covered by the offline tests (`test_amount_true`, `test_amount_false`, `test_amount_exact_boundary_is_true`, `test_amount_one_wei_below_boundary_is_false`). No official page in the research states an absolute burned amount in static HTML, so there is no seed of that type.
- **Transport failures end UNVERIFIABLE**, and validators accept a leader's transport failure without reproducing it. Such a check asserts nothing, and the claim can be filed again at another block in the window. web.archive.org throttles bursts of fetches from Studio Dev's nodes, so the seed and demo scripts space out archive fetches by two minutes.

## Repository

| Path | What |
|---|---|
| `contracts/BurnProof.py` | The checker (canonical and demo) |
| `contracts/BurnGate.py` | The consumer |
| `test/test_burnproof.py`, `test/test_attacks.py` | Offline suite (stubbed GenVM, mock Wayback, mock RPCs, scripted model) |
| `test/deploy.mjs`, `test/seed_canonical.mjs`, `test/demo_paths.mjs`, `test/tx.mjs` | Deploy from HEAD, seed, demo, single calls |
| `tools/verify_source.mjs`, `tools/final_check.mjs` | Source match, final check |
| `docs/` | RULES, SEEDS, FEASIBILITY, ATTACK_REPORT, FINAL_CHECK, SUBMISSION, demo-run.log, superseded/ |

Test keys are throwaway Studio Dev accounts in the gitignored `test/.accounts.json` (`node test/accounts.mjs` creates them).
