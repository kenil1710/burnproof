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

SEEDS_TABLE

The demo deployment runs every path on chain: each verdict, each refusal, and the consumer's allow and refuse. The log is in [docs/demo-run.log](docs/demo-run.log).

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

- **Ethereum mainnet only.** A chain is supported only where two independent archive RPCs answer from GenVM. BSC was probed and only one did (docs/FEASIBILITY.md).
- **Burned means held by a frozen dead address.** Burns that only lower `totalSupply` make burn claims UNVERIFIABLE. A token that burns both ways is measured by its dead-address holdings, and the FALSE reason states the measured share.
- **The token reports its own balances.** BurnProof reads what the token contract answers at the pinned block, from two RPCs. A token contract that lies about `balanceOf` is outside what a chain read can establish.
- **Static HTML only.** The quote must be in the archived HTML. Numbers that a page fills in with JavaScript are not in the capture, and such quotes end QUOTE_NOT_ON_PAGE.
- **One claim per filing, read as a floor.** Hedges ("over", "nearly") are not interpreted. Ranges, multiple numbers and qualified numbers are UNVERIFIABLE by rule.
- **The model's only freedom** is the claim type for a non-percent number (`BURNED_AMOUNT` vs `SUPPLY_AT_MOST`), and both readings and every validator must agree on it.
- **A transport failure ends UNVERIFIABLE**, and validators accept a leader's transport failure without reproducing it. Such a check asserts nothing, and the claim can be filed again at another block.
- **No absolute-amount claim was found in static HTML on an official page.** BURNED_AMOUNT is covered by the offline suite rather than by a seed.

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
