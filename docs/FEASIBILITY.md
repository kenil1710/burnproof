# BurnProof feasibility and seed research

Researched 2026-10-17 before any contract code was written.

## What had to be true

| Question | Answer | How it was checked |
|---|---|---|
| Can a GenVM node fetch a Wayback capture? | Yes. `https://web.archive.org/web/<ts>id_/<url>` returns the raw archived HTML (53,852 bytes for shibatoken.com 2021-09-02), HTTP 200 | A throwaway probe contract on Studio Dev (`test/probe/Probe.py`, `test/probe.mjs`) |
| Can code tell which capture it got? | Yes. GenVM exposes response headers. Wayback sends `Memento-Datetime` (the exact capture time) and `Link: <original>; rel="original"`. Asking for `...070000id_` returned the 07:00:16 capture after a redirect, so the contract compares `Memento-Datetime` with the timestamp in the URL | Same probe |
| Is the claim text in the raw HTML (no JavaScript rendering)? | Yes, for every seed below. Checked with the contract's own `page_text()` on the cached captures | `scratch` script run against `contracts/BurnProof.py` |
| Can two independent archive RPCs answer at a pinned block? | Ethereum: `eth-pokt.nodies.app` and `rpc.mevblocker.io` answered `eth_call` 100, 5,000 and 500,000 blocks back. BSC: `bsc-mainnet.public.blastapi.io` and `bnb.api.onfinality.io/public` did the same. `bsc-dataseed`, `nodereal`, `48.club` and `1rpc` fail beyond ~128 blocks, and `publicnode` returns 403 for historical calls, so those were rejected | Local probe, then the same RPCs from Studio Dev |
| Does the model answer JSON on Studio Dev? | Yes (`exec_prompt(..., response_format="json")`) | Probe |

## Dead-address balances (Ethereum/BSC, latest block, 2026-10-17)

| Token | Chain | decimals | totalSupply | at dead addresses | share |
|---|---|---|---|---|---|
| SHIB `0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce` | 1 | 18 | 999,982,329,050,358 | 410,486,591,165,039 (`0xdead...42069`: 410.44T, `0x...dEaD`: 49.5B) | 41.05% |
| AKITA `0x3301ee63fb29f863f2333bd4466acb46cd8323e6` | 1 | 18 | 100,000,000,000,000 | 5,020,142,688,229 | 5.02% |
| FLOKI `0xcf0c122c6b73ff809c693db761e7baebe62b6a2e` | 1 | 9 | 10,000,000,000,000 | 4,459,889,420,851 | 44.60% |
| SAITAMA v1 `0x8b3192f5eebd8579568a2ed41e6feb402f93f73f` | 1 | 9 | 100,000,000,000,000,000 | 59,412,856,357,852,170 | 59.41% |
| BabyDoge `0xc748673057861a797275cd8a068abb95a902e8de` | 56 | 9 | 420,000,000,000,000,000 | 217,388,970,693,384,670 | 51.76% |
| SafeMoon v1 `0x8076c74c5e3f5852037f31ff0093eeb8c8add8d3` | 56 | 9 | 1,000,000,000,000,000 | 442,169,443,825,031 (442.17T of it at `0x...0001`) | 44.22% |

SafeMoon v1 is why `0x0000000000000000000000000000000000000001` is on the dead list: the project burned to it, and it now holds 44% of supply. It is not a seed, because no quote from the archived safemoon.net page has a number in its raw HTML (the counters are filled in by JavaScript).

## Seeds

Every quote below was found in the raw capture's page text. The token address for each one appears in that same capture's HTML.

| id | project | capture | quote | expected | why |
|---|---|---|---|---|---|
| S1 | Shiba Inu | [shibatoken.com 2021-09-02](https://web.archive.org/web/20210902070016/https://shibatoken.com/) | `and then actually burned 40% of its total supply to a dead wallet` | TRUE | 41.05% at dead addresses, at least 40% |
| S2 | Shiba Inu | [shibatoken.com 2021-06-04](https://web.archive.org/web/20210604091955/https://shibatoken.com/) | `The remaining 50% was burned to Vitalik Buterin` | FALSE | Sending tokens to Vitalik's wallet was not a burn. Only 41.05% is at dead addresses, below 50% - 0.5% |
| S3 | Shiba Inu | [shibatoken.com 2021-09-02](https://web.archive.org/web/20210902070016/https://shibatoken.com/) | `Starting with a supply of 1 quadrillion, our founder, Ryoshi, locked 50% in Uniswap` | UNVERIFIABLE | two claim-shaped numbers (1 quadrillion, 50%) |
| S4 | Akita Inu | [akita.network 2021-12-24](https://web.archive.org/web/20211224103559/https://www.akita.network/) | `Percent burned: 7.82%` | FALSE | only 5.02% at dead addresses. The site's figure is still displayed in the 2022-05 and 2022-12 captures |
| S5 | Akita Inu | same capture | `Max Supply: 100,000,000,000,000` | TRUE | totalSupply is exactly 100T |
| S6 | FLOKI | [floki.com 2023-12-31](https://web.archive.org/web/20231231033517/https://floki.com/) | `Total Supply: 10,000,000,000,000` | TRUE | totalSupply is exactly 10T (9 decimals) |
| S7 | Saitama v1 | [saitamatoken.com 2021-12-30](https://web.archive.org/web/20211230180830/https://saitamatoken.com/) | `We have already started with 49% of the supply burned.` | TRUE | 59.41% at dead addresses |
| S8 | Baby Doge Coin | [babydoge.com 2022-01-02](https://web.archive.org/web/20220102213647/https://babydoge.com/) | `We have burned 41%+ of the supply.` | TRUE | 51.76% at dead addresses (BSC) |
| S9 | Baby Doge Coin | same capture | `Originally created as a meme joke with 420 Quadrillion supply` | TRUE | totalSupply is exactly 420 quadrillion |

This covers 6 TRUE, 2 FALSE and 1 UNVERIFIABLE across 5 projects, 2 chains, 18- and 9-decimal tokens, and all three claim types (percent, plain integer, scale word). No official page we found states an absolute burned amount in static HTML, so BURNED_AMOUNT is covered by the offline suite and the demo deployment.

Candidates rejected: dogelonmars.com (claims rendered by JavaScript); safemoon.net (counters are JavaScript); hoge.finance (`50% Burned.` sits in a template that shows 0%/50%/70% states, so it is not one claim); kishu.com (no number); floki.com 2025 (no number).
