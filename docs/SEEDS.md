# Seeds

Real burn and supply claims from official project pages, each filed on the canonical BurnProof [`0xF020B9B711781Ed712195584315F8dB49d1f89f4`](https://explorer-studio-dev.genlayer.com/address/0xF020B9B711781Ed712195584315F8dB49d1f89f4) at the first Ethereum block at or after its capture time (inside the contract's 24-hour window), each final. Every claim type was named by code (`claim_by`), so no verdict depends on a model choice. The research (sources, rejected candidates, measured balances) is in [FEASIBILITY.md](FEASIBILITY.md). The raw records are in [seeds.onchain.json](seeds.onchain.json) (`get_check` output).

| Seed | Project | Wayback | Quote | Verdict | Why (computed by code) | Check / tx |
|---|---|---|---|---|---|---|
| S1 | Shiba Inu (SHIB) | [capture](https://web.archive.org/web/20210902070016/https://shibatoken.com/) | "and then actually burned 40% of its total supply to a dead wallet" | **TRUE** | dead addresses hold 41.0280% of totalSupply >= claimed 40.0000% | [#1](https://explorer-studio-dev.genlayer.com/tx/0x2e72697f77aa204d949830d81b9403b85214a3e74d108c5ccf524e2dad2214a2) |
| S2 | Shiba Inu (SHIB) | [capture](https://web.archive.org/web/20210604091955/https://shibatoken.com/) | "The remaining 50% was burned to Vitalik Buterin" | **FALSE** | dead addresses hold 41.0270% of totalSupply < claimed 50.0000% | [#2](https://explorer-studio-dev.genlayer.com/tx/0xb00c26c581b5002d4c977b9fb971054ac00cd0a4e40152948e314a3248475968) |
| S3 | Shiba Inu (SHIB) | [capture](https://web.archive.org/web/20210902070016/https://shibatoken.com/) | "Starting with a supply of 1 quadrillion, our founder, Ryoshi, locked 50% in Uniswap" | **UNVERIFIABLE** | MULTIPLE_CLAIM_NUMBERS | [#3](https://explorer-studio-dev.genlayer.com/tx/0xd558484cb5f68857ddea9ea67a0ac2547e16125855702a9ee22a95c7ddda11a5) |
| S4 | Akita Inu (AKITA) | [capture](https://web.archive.org/web/20211224103559/https://www.akita.network/) | "Percent burned: 7.82%" | **FALSE** | dead addresses hold 5.0194% of totalSupply < claimed 7.8200% | [#4](https://explorer-studio-dev.genlayer.com/tx/0xcdd06d2c043643b784c8ad4af8f24a4ab0110ec5242b20e79ec9bc030b7fb4a7) |
| S5 | Akita Inu (AKITA) | [capture](https://web.archive.org/web/20211224103559/https://www.akita.network/) | "Max Supply: 100,000,000,000,000" | **TRUE** | totalSupply 99,999,999,999,999.9999 <= claimed 100,000,000,000,000.0000 | [#5](https://explorer-studio-dev.genlayer.com/tx/0xf6110b27fa506ed5d91967f5fbe1dac8885f3860d64dca4e19c88215f45248de) |
| S6 | FLOKI | [capture](https://web.archive.org/web/20231231033517/https://floki.com/) | "Total Supply: 10,000,000,000,000" | **TRUE** | totalSupply 10,000,000,000,000.0000 <= claimed 10,000,000,000,000.0000 | [#6](https://explorer-studio-dev.genlayer.com/tx/0x8350f24cb592a300fc9851700132e177bb808ed75dc5c53a79cdd3b6adf020a5) |
| S7 | Saitama Inu (SAITAMA v1) | [capture](https://web.archive.org/web/20211230180830/https://saitamatoken.com/) | "We have already started with 49% of the supply burned." | **TRUE** | dead addresses hold 56.0887% of totalSupply >= claimed 49.0000% | [#7](https://explorer-studio-dev.genlayer.com/tx/0xf2befff771ac2685e5ff34844356f9bc3317f248fe1b4aaf4ab07b433efd0709) |

## S1: Shiba Inu (SHIB), TRUE

- Quote: "and then actually burned 40% of its total supply to a dead wallet"
- Archived page: https://web.archive.org/web/20210902070016/https://shibatoken.com/ (capture 20210902070016, host `shibatoken.com`)
- Token: [`0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce`](https://etherscan.io/token/0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce) (Ethereum, 18 decimals)
- Block: [13144796](https://etherscan.io/block/13144796), hash `0xba893924d265d2256210d6abc16b823d002cf45c65903b8aa3641ddab5406c90`, time 2021-09-02T07:00:22.000Z (6 s after the capture)
- Claim read: BURNED_PERCENT `40%` = 40/1, type named by code
- totalSupply: 999,999,980,899,600.99; at dead addresses: 410,280,450,693,956.63 (0x0000...0000 0.00, 0x0000...0001 0.00, 0x0000...dead 34,180,530,795.11, 0xdead...2069 410,246,270,163,161.52)
- Verdict: **TRUE** / `BURNED_ENOUGH`: dead addresses hold 41.0280% of totalSupply >= claimed 40.0000% -0.5%
- Expected from research: TRUE
- On chain: BurnProof `0xF020B9B711781Ed712195584315F8dB49d1f89f4` check #1, filing tx [`0x2e72697f77aa204d949830d81b9403b85214a3e74d108c5ccf524e2dad2214a2`](https://explorer-studio-dev.genlayer.com/tx/0x2e72697f77aa204d949830d81b9403b85214a3e74d108c5ccf524e2dad2214a2), filed by `0x96bd3efa59880bd5a51e5debd817bd544f8584ae`

## S2: Shiba Inu (SHIB), FALSE

- Quote: "The remaining 50% was burned to Vitalik Buterin"
- Archived page: https://web.archive.org/web/20210604091955/https://shibatoken.com/ (capture 20210604091955, host `shibatoken.com`)
- Token: [`0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce`](https://etherscan.io/token/0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce) (Ethereum, 18 decimals)
- Block: [12567135](https://etherscan.io/block/12567135), hash `0x402464076746969dfe74d8ecc6ac9cbe8f10804721199ade36db1def3535a8a9`, time 2021-06-04T09:20:17.000Z (22 s after the capture)
- Claim read: BURNED_PERCENT `50%` = 50/1, type named by code
- totalSupply: 999,999,980,899,601.99; at dead addresses: 410,270,177,302,446.98 (0x0000...0000 0.00, 0x0000...0001 0.00, 0x0000...dead 26,986,933,978.00, 0xdead...2069 410,243,190,368,468.98)
- Verdict: **FALSE** / `BURNED_SHORT`: dead addresses hold 41.0270% of totalSupply < claimed 50.0000% -0.5%
- Expected from research: FALSE
- On chain: BurnProof `0xF020B9B711781Ed712195584315F8dB49d1f89f4` check #2, filing tx [`0xb00c26c581b5002d4c977b9fb971054ac00cd0a4e40152948e314a3248475968`](https://explorer-studio-dev.genlayer.com/tx/0xb00c26c581b5002d4c977b9fb971054ac00cd0a4e40152948e314a3248475968), filed by `0x96bd3efa59880bd5a51e5debd817bd544f8584ae`

## S3: Shiba Inu (SHIB), UNVERIFIABLE

- Quote: "Starting with a supply of 1 quadrillion, our founder, Ryoshi, locked 50% in Uniswap"
- Archived page: https://web.archive.org/web/20210902070016/https://shibatoken.com/ (capture 20210902070016, host `shibatoken.com`)
- Token: [`0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce`](https://etherscan.io/token/0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce) (Ethereum, 0 decimals)
- Block: [13144796](https://etherscan.io/block/13144796), not read
- Claim read: (none) `-`
- Chain: not read (the filing ended before the chain stage)
- Verdict: **UNVERIFIABLE** / `MULTIPLE_CLAIM_NUMBERS`: the quote holds more than one claim-shaped number
- Expected from research: UNVERIFIABLE
- On chain: BurnProof `0xF020B9B711781Ed712195584315F8dB49d1f89f4` check #3, filing tx [`0xd558484cb5f68857ddea9ea67a0ac2547e16125855702a9ee22a95c7ddda11a5`](https://explorer-studio-dev.genlayer.com/tx/0xd558484cb5f68857ddea9ea67a0ac2547e16125855702a9ee22a95c7ddda11a5), filed by `0x96bd3efa59880bd5a51e5debd817bd544f8584ae`

## S4: Akita Inu (AKITA), FALSE

- Quote: "Percent burned: 7.82%"
- Archived page: https://web.archive.org/web/20211224103559/https://www.akita.network/ (capture 20211224103559, host `www.akita.network`)
- Token: [`0x3301ee63fb29f863f2333bd4466acb46cd8323e6`](https://etherscan.io/token/0x3301ee63fb29f863f2333bd4466acb46cd8323e6) (Ethereum, 18 decimals)
- Block: [13867390](https://etherscan.io/block/13867390), hash `0x49a12c49b8d351f08278409c055ae92f416abf1dc82d9249fdbd945e62459590`, time 2021-12-24T10:36:17.000Z (18 s after the capture)
- Claim read: BURNED_PERCENT `7.82%` = 391/50, type named by code
- totalSupply: 99,999,999,999,999.99; at dead addresses: 5,019,428,718,076.01 (0x0000...0000 0.00, 0x0000...0001 0.00, 0x0000...dead 5,019,428,718,076.01, 0xdead...2069 0.00)
- Verdict: **FALSE** / `BURNED_SHORT`: dead addresses hold 5.0194% of totalSupply < claimed 7.8200% -0.5%
- Expected from research: FALSE
- On chain: BurnProof `0xF020B9B711781Ed712195584315F8dB49d1f89f4` check #4, filing tx [`0xcdd06d2c043643b784c8ad4af8f24a4ab0110ec5242b20e79ec9bc030b7fb4a7`](https://explorer-studio-dev.genlayer.com/tx/0xcdd06d2c043643b784c8ad4af8f24a4ab0110ec5242b20e79ec9bc030b7fb4a7), filed by `0x96bd3efa59880bd5a51e5debd817bd544f8584ae`

## S5: Akita Inu (AKITA), TRUE

- Quote: "Max Supply: 100,000,000,000,000"
- Archived page: https://web.archive.org/web/20211224103559/https://www.akita.network/ (capture 20211224103559, host `www.akita.network`)
- Token: [`0x3301ee63fb29f863f2333bd4466acb46cd8323e6`](https://etherscan.io/token/0x3301ee63fb29f863f2333bd4466acb46cd8323e6) (Ethereum, 18 decimals)
- Block: [13867390](https://etherscan.io/block/13867390), hash `0x49a12c49b8d351f08278409c055ae92f416abf1dc82d9249fdbd945e62459590`, time 2021-12-24T10:36:17.000Z (18 s after the capture)
- Claim read: SUPPLY_AT_MOST `100,000,000,000,000` = 100000000000000/1, type named by code
- totalSupply: 99,999,999,999,999.99; at dead addresses: 5,019,428,718,076.01 (0x0000...0000 0.00, 0x0000...0001 0.00, 0x0000...dead 5,019,428,718,076.01, 0xdead...2069 0.00)
- Verdict: **TRUE** / `SUPPLY_WITHIN`: totalSupply 99,999,999,999,999.9999 <= claimed 100,000,000,000,000.0000 +0.5%
- Expected from research: TRUE
- On chain: BurnProof `0xF020B9B711781Ed712195584315F8dB49d1f89f4` check #5, filing tx [`0xf6110b27fa506ed5d91967f5fbe1dac8885f3860d64dca4e19c88215f45248de`](https://explorer-studio-dev.genlayer.com/tx/0xf6110b27fa506ed5d91967f5fbe1dac8885f3860d64dca4e19c88215f45248de), filed by `0x96bd3efa59880bd5a51e5debd817bd544f8584ae`

## S6: FLOKI, TRUE

- Quote: "Total Supply: 10,000,000,000,000"
- Archived page: https://web.archive.org/web/20231231033517/https://floki.com/ (capture 20231231033517, host `floki.com`)
- Token: [`0xcf0c122c6b73ff809c693db761e7baebe62b6a2e`](https://etherscan.io/token/0xcf0c122c6b73ff809c693db761e7baebe62b6a2e) (Ethereum, 9 decimals)
- Block: [18902821](https://etherscan.io/block/18902821), hash `0x7664ac7f4e0294d5f5c4d4e25439cafa8f7ed94ea24cb2fadb5d691d85c9b8ed`, time 2023-12-31T03:35:23.000Z (6 s after the capture)
- Claim read: SUPPLY_AT_MOST `10,000,000,000,000` = 10000000000000/1, type named by code
- totalSupply: 10,000,000,000,000.00; at dead addresses: 4,290,913,996,604.43 (0x0000...0000 0.00, 0x0000...0001 0.00, 0x0000...dead 4,290,913,996,537.30, 0xdead...2069 67.12)
- Verdict: **TRUE** / `SUPPLY_WITHIN`: totalSupply 10,000,000,000,000.0000 <= claimed 10,000,000,000,000.0000 +0.5%
- Expected from research: TRUE
- On chain: BurnProof `0xF020B9B711781Ed712195584315F8dB49d1f89f4` check #6, filing tx [`0x8350f24cb592a300fc9851700132e177bb808ed75dc5c53a79cdd3b6adf020a5`](https://explorer-studio-dev.genlayer.com/tx/0x8350f24cb592a300fc9851700132e177bb808ed75dc5c53a79cdd3b6adf020a5), filed by `0xf9469ea4a318403492e230ff60e397aa33319bf2`

## S7: Saitama Inu (SAITAMA v1), TRUE

- Quote: "We have already started with 49% of the supply burned."
- Archived page: https://web.archive.org/web/20211230180830/https://saitamatoken.com/ (capture 20211230180830, host `saitamatoken.com`)
- Token: [`0x8b3192f5eebd8579568a2ed41e6feb402f93f73f`](https://etherscan.io/token/0x8b3192f5eebd8579568a2ed41e6feb402f93f73f) (Ethereum, 9 decimals)
- Block: [13908188](https://etherscan.io/block/13908188), hash `0xb9a9c65b9d1673b38f9d3fca50d0db973ff958ea7e8686845842d11d61b02f0d`, time 2021-12-30T18:08:31.000Z (1 s after the capture)
- Claim read: BURNED_PERCENT `49%` = 49/1, type named by code
- totalSupply: 100,000,000,000,000,000.00; at dead addresses: 56,088,716,675,594,121.51 (0x0000...0000 0.00, 0x0000...0001 0.00, 0x0000...dead 56,088,716,675,594,121.51, 0xdead...2069 0.00)
- Verdict: **TRUE** / `BURNED_ENOUGH`: dead addresses hold 56.0887% of totalSupply >= claimed 49.0000% -0.5%
- Expected from research: TRUE
- On chain: BurnProof `0xF020B9B711781Ed712195584315F8dB49d1f89f4` check #7, filing tx [`0xf2befff771ac2685e5ff34844356f9bc3317f248fe1b4aaf4ab07b433efd0709`](https://explorer-studio-dev.genlayer.com/tx/0xf2befff771ac2685e5ff34844356f9bc3317f248fe1b4aaf4ab07b433efd0709), filed by `0xf9469ea4a318403492e230ff60e397aa33319bf2`
