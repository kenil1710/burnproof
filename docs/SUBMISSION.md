# Submission

Plain ASCII. Character counts are measured by `tools/submission.mjs`.

## One-liner (179 / 180 characters)

```
BurnProof checks one archived token-burn claim against Ethereum and answers TRUE, FALSE or UNVERIFIABLE. Code decides every number and verdict; the model only labels one sentence.
```

## Description (986 / 1000 characters)

```
BurnProof checks one published token-burn claim against the chain. The filer picks the one claim: a token, a web.archive.org snapshot of the project's page, one exact quote and a block. Code checks the quote is on the archived page: the archive must serve that exact capture of that host, and the quote must sit inside one block of its visible text. Code finds the single claim-shaped number in the quote; ranges, several numbers, invisible characters and qualifiers (fees, plans, circulating supply) end UNVERIFIABLE. The model only formats that one sentence into {type, number, unit}; code requires the number to be written in the quote and equal to its own parse, and two readings must agree. Code computes every number and the verdict: two RPCs must agree exactly at a pinned finalized block, burned is the sum held by four frozen dead addresses, with 0.5% tolerance. BurnGate refuses listings whose latest burn claim is FALSE. Seeds: 7 real claims, 4 TRUE, 1 FALSE, 2 UNVERIFIABLE.
```

## Review verification (385 / 500 characters)

```
BurnProof 0x85807B7781303c0519a4b53734e04798DAD33fda on Studio Dev. Run node tools/verify_source.mjs: deployed code equals contracts/ at HEAD. Run node test/tx.mjs --set=final --c=BurnProof --view=get_check --args='[1]' and open its Wayback and Etherscan block links to recompute the verdict. python3 -m unittest in test/ runs 358 offline tests. docs/FINAL_CHECK.md has the full check.
```

## Links

- Repository: https://github.com/kenil1710/burnproof
- BurnProof (canonical): 0x85807B7781303c0519a4b53734e04798DAD33fda
- BurnProofDemo: 0x9433099Eb1Ece546c9A092A09D9695c23fc12353
- BurnGate: 0x019C114C50D2a9B3e526E1B473b4840EEE7C0De0
- BurnGateDemo: 0x01cc28ff81e5d773F6fAe6b37E4e71b85e2Bc1C4
- Network: GenLayer Studio Dev, chain id 61997, https://studio-dev.genlayer.com/api
