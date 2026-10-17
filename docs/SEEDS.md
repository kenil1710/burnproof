# Seeds

Real burn and supply claims from official project pages, each filed on the canonical BurnProof [`0x85807B7781303c0519a4b53734e04798DAD33fda`](https://explorer-studio-dev.genlayer.com/address/0x85807B7781303c0519a4b53734e04798DAD33fda) at an Ethereum finalized block, each final. The research (sources, rejected candidates, measured balances) is in [FEASIBILITY.md](FEASIBILITY.md). The raw records are in [seeds.onchain.json](seeds.onchain.json) (`get_check` output).

| Seed | Project | Wayback | Quote | Verdict | Why (computed by code) | Check / tx |
|---|---|---|---|---|---|---|
| S1 | Shiba Inu (SHIB) | [capture](https://web.archive.org/web/20210902070016/https://shibatoken.com/) | "and then actually burned 40% of its total supply to a dead wallet" | **TRUE** | dead addresses hold 41.0493% of totalSupply >= claimed 40.0000% | [#1](https://explorer-studio-dev.genlayer.com/tx/0xcec1a482f4ab24f51b92744ac026796a3856bd8a514edb823713a1357ff832db) |
| S2 | Shiba Inu (SHIB) | [capture](https://web.archive.org/web/20210604091955/https://shibatoken.com/) | "The remaining 50% was burned to Vitalik Buterin" | **UNVERIFIABLE** | NOT_A_BURN_CLAIM | [#2](https://explorer-studio-dev.genlayer.com/tx/0x72ec4b87e8104531850f5bc732febe51e5accdde0dc5d3a95d164961648f6d56) |
| S3 | Shiba Inu (SHIB) | [capture](https://web.archive.org/web/20210902070016/https://shibatoken.com/) | "Starting with a supply of 1 quadrillion, our founder, Ryoshi, locked 50% in Uniswap" | **UNVERIFIABLE** | MULTIPLE_CLAIM_NUMBERS | [#3](https://explorer-studio-dev.genlayer.com/tx/0x9778257dd8965b78169b90cacd479c4fbcaf31eed79557ef3eb6ab630675b835) |
| S4 | Akita Inu (AKITA) | [capture](https://web.archive.org/web/20211224103559/https://www.akita.network/) | "Percent burned: 7.82%" | **FALSE** | dead addresses hold 5.0201% of totalSupply < claimed 7.8200% | [#8](https://explorer-studio-dev.genlayer.com/tx/0xa1829716a5f0e0e96d2763d15c6f72774e40ea65fa9fc12acf184c5b959134cc) |
| S5 | Akita Inu (AKITA) | [capture](https://web.archive.org/web/20211224103559/https://www.akita.network/) | "Max Supply: 100,000,000,000,000" | **TRUE** | totalSupply 99,999,999,999,999.9999 <= claimed 100,000,000,000,000.0000 | [#9](https://explorer-studio-dev.genlayer.com/tx/0x2cbe14c657bb503c26c25b58bc81feebaa76a308e618e133c2781b70f9fcb34c) |
| S6 | FLOKI | [capture](https://web.archive.org/web/20231231033517/https://floki.com/) | "Total Supply: 10,000,000,000,000" | **TRUE** | totalSupply 10,000,000,000,000.0000 <= claimed 10,000,000,000,000.0000 | [#10](https://explorer-studio-dev.genlayer.com/tx/0xdbd0af5bc1364f89583029181b246fcb0d9d11dafb55f3338f15f166cac7da6e) |
| S7 | Saitama Inu (SAITAMA v1) | [capture](https://web.archive.org/web/20211230180830/https://saitamatoken.com/) | "We have already started with 49% of the supply burned." | **TRUE** | dead addresses hold 59.4128% of totalSupply >= claimed 49.0000% | [#7](https://explorer-studio-dev.genlayer.com/tx/0x5d4b18eb5446432eed445ec3fbe1e8453c81d3f289cae1f7732c966be723c600) |

## S1: Shiba Inu (SHIB), TRUE

- Quote: "and then actually burned 40% of its total supply to a dead wallet"
- Archived page: https://web.archive.org/web/20210902070016/https://shibatoken.com/ (capture 20210902070016, host `shibatoken.com`)
- Token: [`0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce`](https://etherscan.io/token/0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce) (Ethereum, 18 decimals)
- Block: [26211211](https://etherscan.io/block/26211211), hash `0xae258b0284618da8b815be4c565b294cc7b3bbe3f02f978c243dbc21148184ce`, time 2026-10-17T08:54:47.000Z
- Claim read: BURNED_PERCENT `40%` = 40/1
- totalSupply: 999,982,329,050,358.46; at dead addresses: 410,486,591,165,039.90 (0x0000...0000 0.00, 0x0000...0001 0.00, 0x0000...dead 49,480,381,609.10, 0xdead...2069 410,437,110,783,430.79)
- Verdict: **TRUE** / `BURNED_ENOUGH`: dead addresses hold 41.0493% of totalSupply >= claimed 40.0000% -0.5%
- Expected from research: TRUE
- On chain: BurnProof `0x85807B7781303c0519a4b53734e04798DAD33fda` check #1, filing tx [`0xcec1a482f4ab24f51b92744ac026796a3856bd8a514edb823713a1357ff832db`](https://explorer-studio-dev.genlayer.com/tx/0xcec1a482f4ab24f51b92744ac026796a3856bd8a514edb823713a1357ff832db), filed by `0x96bd3efa59880bd5a51e5debd817bd544f8584ae`

## S2: Shiba Inu (SHIB), UNVERIFIABLE

- Quote: "The remaining 50% was burned to Vitalik Buterin"
- Archived page: https://web.archive.org/web/20210604091955/https://shibatoken.com/ (capture 20210604091955, host `shibatoken.com`)
- Token: [`0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce`](https://etherscan.io/token/0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce) (Ethereum, 0 decimals)
- Block: [26211211](https://etherscan.io/block/26211211), hash ``, time 1970-01-01T00:00:00.000Z
- Claim read: (none) `50%`
- Chain: not read (the filing ended before the chain stage)
- Verdict: **UNVERIFIABLE** / `NOT_A_BURN_CLAIM`: the model reading did not pass code validation
- Expected from research: UNVERIFIABLE
- On chain: BurnProof `0x85807B7781303c0519a4b53734e04798DAD33fda` check #2, filing tx [`0x72ec4b87e8104531850f5bc732febe51e5accdde0dc5d3a95d164961648f6d56`](https://explorer-studio-dev.genlayer.com/tx/0x72ec4b87e8104531850f5bc732febe51e5accdde0dc5d3a95d164961648f6d56), filed by `0x96bd3efa59880bd5a51e5debd817bd544f8584ae`

## S3: Shiba Inu (SHIB), UNVERIFIABLE

- Quote: "Starting with a supply of 1 quadrillion, our founder, Ryoshi, locked 50% in Uniswap"
- Archived page: https://web.archive.org/web/20210902070016/https://shibatoken.com/ (capture 20210902070016, host `shibatoken.com`)
- Token: [`0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce`](https://etherscan.io/token/0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce) (Ethereum, 0 decimals)
- Block: [26211211](https://etherscan.io/block/26211211), hash ``, time 1970-01-01T00:00:00.000Z
- Claim read: (none) `-`
- Chain: not read (the filing ended before the chain stage)
- Verdict: **UNVERIFIABLE** / `MULTIPLE_CLAIM_NUMBERS`: the quote holds more than one claim-shaped number
- Expected from research: UNVERIFIABLE
- On chain: BurnProof `0x85807B7781303c0519a4b53734e04798DAD33fda` check #3, filing tx [`0x9778257dd8965b78169b90cacd479c4fbcaf31eed79557ef3eb6ab630675b835`](https://explorer-studio-dev.genlayer.com/tx/0x9778257dd8965b78169b90cacd479c4fbcaf31eed79557ef3eb6ab630675b835), filed by `0x96bd3efa59880bd5a51e5debd817bd544f8584ae`

## S4: Akita Inu (AKITA), FALSE

- Quote: "Percent burned: 7.82%"
- Archived page: https://web.archive.org/web/20211224103559/https://www.akita.network/ (capture 20211224103559, host `www.akita.network`)
- Token: [`0x3301ee63fb29f863f2333bd4466acb46cd8323e6`](https://etherscan.io/token/0x3301ee63fb29f863f2333bd4466acb46cd8323e6) (Ethereum, 18 decimals)
- Block: [26211402](https://etherscan.io/block/26211402), hash `0x55e15e807ab972b67f3f715ca5a22d8cf6d98444763b442e47f3bb3288221f7d`, time 2026-10-17T09:33:11.000Z
- Claim read: BURNED_PERCENT `7.82%` = 391/50
- totalSupply: 99,999,999,999,999.99; at dead addresses: 5,020,142,688,229.79 (0x0000...0000 0.00, 0x0000...0001 0.00, 0x0000...dead 5,020,142,688,229.79, 0xdead...2069 0.00)
- Verdict: **FALSE** / `BURNED_SHORT`: dead addresses hold 5.0201% of totalSupply < claimed 7.8200% -0.5%
- Expected from research: FALSE
- On chain: BurnProof `0x85807B7781303c0519a4b53734e04798DAD33fda` check #8, filing tx [`0xa1829716a5f0e0e96d2763d15c6f72774e40ea65fa9fc12acf184c5b959134cc`](https://explorer-studio-dev.genlayer.com/tx/0xa1829716a5f0e0e96d2763d15c6f72774e40ea65fa9fc12acf184c5b959134cc), filed by `0xe9addbbc2e459c05d79cb3700539fe748f58ee52`

## S5: Akita Inu (AKITA), TRUE

- Quote: "Max Supply: 100,000,000,000,000"
- Archived page: https://web.archive.org/web/20211224103559/https://www.akita.network/ (capture 20211224103559, host `www.akita.network`)
- Token: [`0x3301ee63fb29f863f2333bd4466acb46cd8323e6`](https://etherscan.io/token/0x3301ee63fb29f863f2333bd4466acb46cd8323e6) (Ethereum, 18 decimals)
- Block: [26211433](https://etherscan.io/block/26211433), hash `0x34c6d77127a5c443bbc1aff2b460301e2a237df05093509a0f080c68248722fe`, time 2026-10-17T09:39:35.000Z
- Claim read: SUPPLY_AT_MOST `100,000,000,000,000` = 100000000000000/1
- totalSupply: 99,999,999,999,999.99; at dead addresses: 5,020,142,688,229.79 (0x0000...0000 0.00, 0x0000...0001 0.00, 0x0000...dead 5,020,142,688,229.79, 0xdead...2069 0.00)
- Verdict: **TRUE** / `SUPPLY_WITHIN`: totalSupply 99,999,999,999,999.9999 <= claimed 100,000,000,000,000.0000 +0.5%
- Expected from research: TRUE
- On chain: BurnProof `0x85807B7781303c0519a4b53734e04798DAD33fda` check #9, filing tx [`0x2cbe14c657bb503c26c25b58bc81feebaa76a308e618e133c2781b70f9fcb34c`](https://explorer-studio-dev.genlayer.com/tx/0x2cbe14c657bb503c26c25b58bc81feebaa76a308e618e133c2781b70f9fcb34c), filed by `0xe9addbbc2e459c05d79cb3700539fe748f58ee52`

## S6: FLOKI, TRUE

- Quote: "Total Supply: 10,000,000,000,000"
- Archived page: https://web.archive.org/web/20231231033517/https://floki.com/ (capture 20231231033517, host `floki.com`)
- Token: [`0xcf0c122c6b73ff809c693db761e7baebe62b6a2e`](https://etherscan.io/token/0xcf0c122c6b73ff809c693db761e7baebe62b6a2e) (Ethereum, 9 decimals)
- Block: [26211465](https://etherscan.io/block/26211465), hash `0x477f46679b27fcca2fc45be355069c289a2d29698d3f1af7c4277d7c68204487`, time 2026-10-17T09:45:59.000Z
- Claim read: SUPPLY_AT_MOST `10,000,000,000,000` = 10000000000000/1
- totalSupply: 10,000,000,000,000.00; at dead addresses: 4,459,889,420,851.34 (0x0000...0000 0.00, 0x0000...0001 0.00, 0x0000...dead 4,459,889,400,801.23, 0xdead...2069 20,050.10)
- Verdict: **TRUE** / `SUPPLY_WITHIN`: totalSupply 10,000,000,000,000.0000 <= claimed 10,000,000,000,000.0000 +0.5%
- Expected from research: TRUE
- On chain: BurnProof `0x85807B7781303c0519a4b53734e04798DAD33fda` check #10, filing tx [`0xdbd0af5bc1364f89583029181b246fcb0d9d11dafb55f3338f15f166cac7da6e`](https://explorer-studio-dev.genlayer.com/tx/0xdbd0af5bc1364f89583029181b246fcb0d9d11dafb55f3338f15f166cac7da6e), filed by `0xe9addbbc2e459c05d79cb3700539fe748f58ee52`

## S7: Saitama Inu (SAITAMA v1), TRUE

- Quote: "We have already started with 49% of the supply burned."
- Archived page: https://web.archive.org/web/20211230180830/https://saitamatoken.com/ (capture 20211230180830, host `saitamatoken.com`)
- Token: [`0x8b3192f5eebd8579568a2ed41e6feb402f93f73f`](https://etherscan.io/token/0x8b3192f5eebd8579568a2ed41e6feb402f93f73f) (Ethereum, 9 decimals)
- Block: [26211243](https://etherscan.io/block/26211243), hash `0x4ed6fc5f1c09115de97547a2d00d604f0423ed2a521e1e318d9231c4e9f82750`, time 2026-10-17T09:01:11.000Z
- Claim read: BURNED_PERCENT `49%` = 49/1
- totalSupply: 100,000,000,000,000,000.00; at dead addresses: 59,412,856,357,852,166.54 (0x0000...0000 0.00, 0x0000...0001 1,929,725,779.77, 0x0000...dead 59,412,845,974,111,341.67, 0xdead...2069 8,454,015,045.09)
- Verdict: **TRUE** / `BURNED_ENOUGH`: dead addresses hold 59.4128% of totalSupply >= claimed 49.0000% -0.5%
- Expected from research: TRUE
- On chain: BurnProof `0x85807B7781303c0519a4b53734e04798DAD33fda` check #7, filing tx [`0x5d4b18eb5446432eed445ec3fbe1e8453c81d3f289cae1f7732c966be723c600`](https://explorer-studio-dev.genlayer.com/tx/0x5d4b18eb5446432eed445ec3fbe1e8453c81d3f289cae1f7732c966be723c600), filed by `0xf9469ea4a318403492e230ff60e397aa33319bf2`
## Transient checks on the canonical contract

Checks #4, #5 and #6 are the first filings of S4, S5 and S6. Each ended `UNVERIFIABLE / PAGE_UNAVAILABLE` ("archive did not answer") because web.archive.org throttled the bursts of fetches coming from Studio Dev's nodes. A rule says a transport failure ends the filing UNVERIFIABLE, so they stay on chain as final records. Each seed was filed again at a newer block after a 3-minute cool-down (`test/seed_canonical.mjs`), which produced checks #8, #9 and #10 above. `latest_verdict` never counts an UNVERIFIABLE as decisive, so these records do not change any token's standing.
