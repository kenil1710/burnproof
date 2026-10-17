# Submission

Plain ASCII. Character counts are measured by `tools/submission.mjs`.

## One-liner (171 / 180 characters)

```
BurnProof checks one archived token-burn claim against Ethereum as it stood at the capture, and answers TRUE, FALSE or UNVERIFIABLE. Code decides every number and verdict.
```

## Description (969 / 1000 characters)

```
BurnProof lets a listing desk, auditor or holder check one token-burn or supply claim from a project's own archived website against Ethereum as of the capture. The filer gives a token, a Wayback snapshot, one exact quote and a block within 24 hours after the capture. Code confirms the quote is on that exact capture, finds its one claim-shaped number, and names the claim type when the words settle it ("burned", "total supply"). For other quotes the model names the type; it never supplies a number, and disagreeing readings end UNVERIFIABLE. Two RPCs must agree on totalSupply and four dead-address balances; integer math gives TRUE if the claim holds within 0.5%, else FALSE. Seeds, all decided by code: SHIB 40% burned TRUE, SHIB "50% burned to Vitalik" FALSE, Akita 7.82% FALSE, Akita and FLOKI supply TRUE, Saitama 49% TRUE, a two-number quote UNVERIFIABLE. BurnGate refuses listings whose latest claim is FALSE. Scope: Ethereum, burns counted at dead addresses.
```

## Review verification (420 / 500 characters)

```
BurnProof 0xF020B9B711781Ed712195584315F8dB49d1f89f4 on Studio Dev. Run node tools/verify_source.mjs: deployed code equals contracts/ at HEAD. Run node test/tx.mjs --set=final --c=BurnProof --view=get_check --args='[1]' and open its Wayback and Etherscan block links (block within 24 h of the capture) to recompute the verdict. python3 -m unittest in test/ runs 372 offline tests. docs/FINAL_CHECK.md has the full check.
```

## Links

- Repository: https://github.com/kenil1710/burnproof
- BurnProof (canonical): 0xF020B9B711781Ed712195584315F8dB49d1f89f4
- BurnProofDemo: 0x019603fa4756dafDf820932b192D49d2Fe8D5014
- BurnGate: 0x16aAcCD15eB1756075bE15e727Ab3eBaBe8d2448
- BurnGateDemo: 0x307ed86b8CccAb6841ae18FaE1c559C89d7F606E
- Network: GenLayer Studio Dev, chain id 61997, https://studio-dev.genlayer.com/api
- Seeds: https://github.com/kenil1710/burnproof/blob/main/docs/SEEDS.md

## Evidence links (Studio Dev explorer)

- BurnProof: https://explorer-studio-dev.genlayer.com/address/0xF020B9B711781Ed712195584315F8dB49d1f89f4
- BurnProofDemo: https://explorer-studio-dev.genlayer.com/address/0x019603fa4756dafDf820932b192D49d2Fe8D5014
- BurnGate: https://explorer-studio-dev.genlayer.com/address/0x16aAcCD15eB1756075bE15e727Ab3eBaBe8d2448
- BurnGateDemo: https://explorer-studio-dev.genlayer.com/address/0x307ed86b8CccAb6841ae18FaE1c559C89d7F606E
- S1 TRUE (check #1, BURNED_ENOUGH): https://explorer-studio-dev.genlayer.com/tx/0x2e72697f77aa204d949830d81b9403b85214a3e74d108c5ccf524e2dad2214a2
- S2 FALSE (check #2, BURNED_SHORT): https://explorer-studio-dev.genlayer.com/tx/0xb00c26c581b5002d4c977b9fb971054ac00cd0a4e40152948e314a3248475968
- S3 UNVERIFIABLE (check #3, MULTIPLE_CLAIM_NUMBERS): https://explorer-studio-dev.genlayer.com/tx/0xd558484cb5f68857ddea9ea67a0ac2547e16125855702a9ee22a95c7ddda11a5
- S4 FALSE (check #4, BURNED_SHORT): https://explorer-studio-dev.genlayer.com/tx/0xcdd06d2c043643b784c8ad4af8f24a4ab0110ec5242b20e79ec9bc030b7fb4a7
- S5 TRUE (check #5, SUPPLY_WITHIN): https://explorer-studio-dev.genlayer.com/tx/0xf6110b27fa506ed5d91967f5fbe1dac8885f3860d64dca4e19c88215f45248de
- S6 TRUE (check #6, SUPPLY_WITHIN): https://explorer-studio-dev.genlayer.com/tx/0x8350f24cb592a300fc9851700132e177bb808ed75dc5c53a79cdd3b6adf020a5
- S7 TRUE (check #7, BURNED_ENOUGH): https://explorer-studio-dev.genlayer.com/tx/0xf2befff771ac2685e5ff34844356f9bc3317f248fe1b4aaf4ab07b433efd0709
- BurnGateDemo allow (SHIB): https://explorer-studio-dev.genlayer.com/tx/0x86eb28acbe0b6811f0b9fd7c4a2866e17ff6dce943695ab0751c79df907b3e4d
- BurnGateDemo refuse (AKITA): https://explorer-studio-dev.genlayer.com/tx/0xa6cb4e321e3735d6cf98a0bad6978a563ed7645fc579d3193e9e3d536f03c5bf
- BurnProofDemo BLOCK_AFTER_WINDOW (SHIB 40% at today's block): https://explorer-studio-dev.genlayer.com/tx/0x12ed1a4c43602efe9afadf1b8434cae9dead6b0a659ddbadf483bbdbde2de68f
- BurnProofDemo model path (FLOKI TVL quote): https://explorer-studio-dev.genlayer.com/tx/0x05c9fd416632d58265fc96e37ab9fe1f924a6820e2eb6c3f35f658cb5bc4182d
