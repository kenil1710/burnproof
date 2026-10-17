# BurnProof rules

Every rule below is enforced by code in `contracts/BurnProof.py`. The model never decides whether a claim is covered, and it never decides a verdict.

## 1. What a filing is

`file_claim(chain_id, token, snapshot_url, quote, block)`

| Field | Rule | Refusal code |
|---|---|---|
| `chain_id` | `1` (Ethereum). A chain is supported only where two independent archive RPCs answer GenVM. BSC was tested and has only one (docs/FEASIBILITY.md) | `UNSUPPORTED_CHAIN` |
| `token` | `0x` + 40 hex, case-insensitive, and not one of the dead addresses | `BAD_TOKEN_ADDRESS` |
| `snapshot_url` | Exactly `https://web.archive.org/web/<14-digit timestamp>/<http(s) URL>`. No other scheme or host, port, userinfo, `id_`/`if_` modifier, fragment, backslash, whitespace or non-ASCII. At most 600 characters | `NOT_ARCHIVE_URL`, `URL_TOO_LONG` |
| timestamp | A real UTC date and time: year 1996 or later, valid month, day (leap years included), hour, minute and second, and not in the future | `BAD_TIMESTAMP` |
| original host | `[a-z0-9.-]`, at least one dot, not `archive.org` or a subdomain of it | `NOT_ARCHIVE_URL` |
| `quote` | 12 to 400 characters after whitespace is collapsed. No control characters | `BAD_QUOTE` |
| `block` | 1 to 10^10 | `BAD_BLOCK` |
| duplicate | The same (chain, token, snapshot, collapsed quote, block) is refused, whoever files it | `DUPLICATE_OF_<id>` |
| rate limit | Per sender, per fixed window: canonical allows 5 filings per 3,600 s, demo allows 2 per 600 s. Only stored filings count | `RATE_LIMITED_UNTIL_<epoch>` |

A refused filing reverts. Nothing is stored and no counter moves. A filing that passes the door ALWAYS ends in a stored check with a final verdict: `TRUE`, `FALSE` or `UNVERIFIABLE`. Counters (total, per verdict, the sender's rate window) change only then. Filing is free. The contract holds no funds and has no owner or setter.

## 2. The archived page

1. Code fetches `https://web.archive.org/web/<ts>id_/<url>`, the raw capture without the Wayback toolbar. It tries up to 3 times on a transport error, HTTP 429 or 5xx.
2. The `Memento-Datetime` header must be exactly the URL's timestamp. Wayback redirects a timestamp it does not hold to the nearest capture, so a different timestamp means a different capture. The `Link rel="original"` header must name the same host as the filed URL. Otherwise: `SNAPSHOT_MISMATCH`.
3. Page text: comments, `<script>`, `<style>`, `<noscript>` and `<template>` are dropped. Inline tags (`a abbr b bdi bdo cite code data dfn em font i kbd mark q s samp small span strong sub sup time u var wbr`) are removed without a space, as a browser renders them. Every other tag ends a block. Entities are decoded, then whitespace is collapsed.
4. The quote, with its whitespace collapsed, must appear **case-sensitively inside one block**. Otherwise: `QUOTE_NOT_ON_PAGE`.

## 3. The number (code) and the claim type (model, validated by code)

A number is `1,234,567` / `1234567` / `7.82`, optionally followed by `%`, ` percent`, ` thousand|million|billion|trillion|quadrillion` (any case), or a `K/M/B/T` suffix written straight after the digits. It is **claim-shaped** if it is a percent, has a scale, or is at least 10,000. Years, dates and small counts are not claim-shaped.

Code ends the filing UNVERIFIABLE, before any model call, when the quote:

| Condition | Code |
|---|---|
| holds a non-ASCII digit, a non-ASCII percent / per-mille sign, or any invisible character (zero-width, bidi control, soft hyphen, BOM, ...) | `UNUSUAL_CHARACTERS` |
| joins numbers into a range or list (`40-50%`, `40 to 50%`, `/`, `~`, `or`, `and`), or groups digits ambiguously (`1,2345`, `1,23`, `400.000.000`) | `AMBIGUOUS_NUMBER` |
| holds no claim-shaped number | `NO_CLAIM_NUMBER` |
| holds more than one claim-shaped number | `MULTIPLE_CLAIM_NUMBERS` |
| its one claim-shaped number is 0 | `ZERO_CLAIM` |

The model then reads **only the quote** (never the page) and returns `{"type", "number", "unit"}`, where type is `BURNED_AMOUNT`, `BURNED_PERCENT`, `SUPPLY_AT_MOST` or `NONE`. Code accepts the reading only if:

- `number` is written literally in the quote, and `number` plus a scale word from `unit` equals the value **and kind** of the one claim-shaped number code found (`400` + `trillion`, `400T` and `400,000,000,000,000` all pass for the right quote);
- a percent number has type `BURNED_PERCENT`, and a non-percent number does not;
- the quote holds none of the qualifier words (`unburn`, `not burn`, `never burn`, `will `, `to be burn`, `plan`, `schedul`, `target`, `goal`, `fee`, `tax`, `per/each/every transaction`, `liquidity`, ` lp `, `lp token`, `circulat`). If it does, the result is `CLAIM_QUALIFIED`, whatever the model said.

The leader reads the quote **twice, independently**. If the two readings differ, the result is `READINGS_DIFFER`. `NONE` gives `NOT_A_BURN_CLAIM`. An invalid answer gives `MODEL_OUTPUT_INVALID`, and a model error gives `MODEL_UNAVAILABLE`. **The value used in the verdict is always code's own parse of the quote.** The model only chooses between the claim types that fit that number.

## 4. The chain read

Both frozen RPCs, `https://eth-pokt.nodies.app` and `https://rpc.mevblocker.io` (archive nodes run by different operators), are asked the same questions at the pinned block:

`eth_chainId`, `eth_getBlockByNumber("finalized")`, `eth_getBlockByNumber(block)` (hash and timestamp), `eth_getCode(token, block)`, `decimals()`, `totalSupply()`, and `balanceOf(d)` for each dead address `d`, all at `block`.

- Either RPC errors, times out or answers the wrong chain id, gives `RPC_UNAVAILABLE`.
- `block` is above either RPC's finalized block, gives `BLOCK_NOT_FINALIZED`.
- The two disagree on any of hash, timestamp, code presence, decimals, supply or any balance, gives `RPC_DISAGREE`.
- No code at the token, a revert, decimals above 36, zero supply, or dead balances above supply, gives `TOKEN_UNREADABLE`.
- The block is older than the snapshot, gives `BLOCK_BEFORE_SNAPSHOT`. A claim is only checked against the chain as it stood at or after the claim was archived.

### Dead addresses (frozen)

| Address | Why nobody can move tokens from it |
|---|---|
| `0x0000000000000000000000000000000000000000` | The zero address. No key exists. Many tokens burn by transfer to it |
| `0x0000000000000000000000000000000000000001` | The `ecrecover` precompile. No key is known for it. SafeMoon v1 burned to it, and it holds 44% of that token's supply (docs/FEASIBILITY.md) |
| `0x000000000000000000000000000000000000dEaD` | The conventional burn address. Its key would need a preimage of a hand-picked address |
| `0xdEAD000000000000000042069420694206942069` | Shiba Inu's burn address, where Vitalik Buterin sent 410 trillion SHIB. Hand-picked, so no key is known |

`burned` is the sum of `balanceOf` over these four addresses at the block.

## 5. The verdict (integer arithmetic, 0.5% tolerance in the claim's favour)

With `N = num/den` the claimed value, `dec` the decimals and `one = 10^dec`:

| Type | TRUE iff | Meaning |
|---|---|---|
| `BURNED_AMOUNT` | `burned * 1000 * den >= num * one * 995` | at least N tokens are at dead addresses (0.5% short is allowed) |
| `BURNED_PERCENT` | `burned * 100 * 1000 * den >= num * 995 * totalSupply` | dead addresses hold at least N% of `totalSupply` (0.5% relative short is allowed) |
| `SUPPLY_AT_MOST` | `totalSupply * 1000 * den <= num * one * 1005` | `totalSupply` is at most N (0.5% over is allowed) |

Otherwise FALSE. Exactly at the boundary is TRUE.

**Burned claims with no dead-address balance are UNVERIFIABLE (`NO_DEAD_ADDRESS_BURNS`).** Some tokens burn by calling `burn()`, which lowers `totalSupply` and leaves nothing at a dead address. For those, the burned amount is the original supply minus the current supply, and the original supply cannot be read from one block. A percent "of supply" claim then has no fixed denominator either. A FALSE would be a guess, so the verdict is UNVERIFIABLE. `SUPPLY_AT_MOST` is still decided for such tokens, because `totalSupply` is exactly what it claims about.

Every number is read as a floor ("at least"). Hedges like "over" or "nearly" are not interpreted.

## 6. Consensus

The leader runs the whole check (page, number, two readings, both RPCs, verdict). Each validator re-runs it independently. It must reproduce the leader's result exactly, with its own model reading equal to the leader's. There are two exceptions, both outcomes that assert nothing:

- a leader result of `UNVERIFIABLE` caused by a transport failure (`PAGE_UNAVAILABLE`, `RPC_UNAVAILABLE`, `RPC_DISAGREE`, `BLOCK_NOT_FINALIZED`) is accepted as is. A timeout must still end the filing;
- a leader result of `UNVERIFIABLE` from the model stage is accepted when the validator finds the same claim-shaped number.

A validator that cannot reproduce a TRUE or FALSE rejects it. If no leader's result is accepted, the transaction ends without state, and the filing can be sent again.

## 7. Reads

- `get_check(id)`: everything stored, plus the frozen dead list and Etherscan links for the token and the block.
- `list_checks(start, count)`: up to 50 checks at a time.
- `latest_verdict(chain_id, token, host)`: the latest claim by **snapshot time** (not filing order), optionally only from `host`. FALSE ranks above TRUE above UNVERIFIABLE at equal snapshot time. `latest_decisive` skips UNVERIFIABLE.
- `get_stats()`, `get_rules()`, `rate_status(sender)`.

## 8. BurnGate (consumer)

`request_listing(chain_id, token, site)` reads `latest_verdict(chain_id, token, site)` from its BurnProof. A FALSE latest decisive verdict refuses the listing (and delists a listed token). TRUE or no decisive claim lists it. Every request is logged with the verdict and BurnProof check id it relied on. Only claims archived from the applicant's own site count, so a third party cannot get a token refused by archiving a false claim on another page. A later filing of an older snapshot cannot mask a newer FALSE.
