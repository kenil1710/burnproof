# v0.3.0
# { "Depends": "py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng" }
import genlayer as gl
from genlayer import *
from dataclasses import dataclass
import json
import typing

# BurnGate - a tiny listing contract that consumes BurnProof. A project asks
# to list its token and names its own website. The gate reads BurnProof's
# latest decisive verdict for that token, using only claims archived from that
# website. "Latest" means the most recent snapshot, not the most recent filing.
# If that verdict is FALSE, the request is refused. Otherwise the token is
# listed.
#
# The verdict is scoped to the applicant's own site, so a third party who
# archives a false claim on some other page cannot get a token refused.
# A newer TRUE filing cannot hide a FALSE claim either: a filing only ranks as
# newer if its snapshot is newer. Every request is logged either way. Nothing
# is written before BurnProof has been read. No value, no owner, no setter.

VERSION = "1.0.0"
MAX_PAGE = 50


@gl.storage.allow
@dataclass
class Request:
    request_id: u64
    sender: str
    chain_id: u64
    token: str
    site: str
    listed: bool
    verdict: str
    check_id: u64
    reason: str
    at: u64


def _site(value: typing.Any) -> str:
    h = str(value).strip().lower()
    if h == "" or len(h) > 253 or "." not in h or ".." in h or h.startswith(".") or h.endswith("."):
        return ""
    for ch in h:
        if ch not in "abcdefghijklmnopqrstuvwxyz0123456789.-":
            return ""
    return h


class BurnGate(gl.contract.Contract):
    burnproof: Address
    n: u64
    n_listed: u64
    n_refused: u64
    requests: gl.storage.TreeMap[u64, Request]
    listed: gl.storage.TreeMap[str, u64]

    def __init__(self, burnproof: str) -> None:
        s = str(burnproof).strip().lower()
        if len(s) != 42 or not s.startswith("0x"):
            raise gl.vm.UserError("burnproof must be a 0x address")
        self.burnproof = Address(s)
        self.n = u64(0)
        self.n_listed = u64(0)
        self.n_refused = u64(0)

    @gl.public.write
    def request_listing(self, chain_id: int, token: str, site: str) -> typing.Any:
        tk = str(token).strip().lower()
        if len(tk) != 42 or not tk.startswith("0x") or not all(c in "0123456789abcdef" for c in tk[2:]):
            raise gl.vm.UserError("REFUSED: BAD_TOKEN_ADDRESS")
        h = _site(site)
        if h == "":
            raise gl.vm.UserError("REFUSED: BAD_SITE")
        cid = int(chain_id)
        try:
            raw = gl.contract.get_at(self.burnproof).view().latest_verdict(cid, tk, h)
            lv = json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            lv = None
        if not isinstance(lv, dict):
            raise gl.vm.UserError("REFUSED: BURNPROOF_UNREADABLE")
        dec = lv.get("latest_decisive") if isinstance(lv.get("latest_decisive"), dict) else None
        verdict = str(dec.get("verdict")) if dec else "NONE"
        check_id = int(dec.get("check_id") or 0) if dec else 0
        ok = verdict != "FALSE"
        if verdict == "FALSE":
            reason = "latest decisive burn claim from " + h + " is FALSE (BurnProof check #" + str(check_id) + ")"
        elif verdict == "TRUE":
            reason = "latest decisive burn claim from " + h + " is TRUE (BurnProof check #" + str(check_id) + ")"
        else:
            reason = "no decisive burn claim from " + h + " on BurnProof"
        # --- writes
        try:
            now = _epoch(str(gl.message.raw.get("datetime", "")))
        except Exception:
            now = 0
        rid = int(self.n) + 1
        self.requests[u64(rid)] = Request(
            request_id=u64(rid), sender=gl.message.sender_address.as_hex.lower(), chain_id=u64(cid), token=tk,
            site=h, listed=ok, verdict=verdict, check_id=u64(check_id), reason=reason, at=u64(now))
        key = str(cid) + ":" + tk
        if ok:
            self.listed[key] = u64(rid)
            self.n_listed = u64(int(self.n_listed) + 1)
        else:
            if key in self.listed:
                del self.listed[key]
            self.n_refused = u64(int(self.n_refused) + 1)
        self.n = u64(rid)
        return {"request_id": rid, "listed": ok, "verdict": verdict, "check_id": check_id, "reason": reason}

    def _view(self, r: Request) -> dict:
        return {"found": True, "request_id": int(r.request_id), "sender": r.sender, "chain_id": int(r.chain_id),
                "token": r.token, "site": r.site, "listed": bool(r.listed), "verdict": r.verdict,
                "check_id": int(r.check_id), "reason": r.reason, "at": int(r.at)}

    @gl.public.view
    def get_request(self, request_id: int) -> typing.Any:
        r = self.requests.get(u64(int(request_id))) if int(request_id) > 0 else None
        if r is None:
            return {"found": False, "request_id": int(request_id)}
        return self._view(r)

    @gl.public.view
    def list_requests(self, start: int, count: int) -> typing.Any:
        s = max(1, int(start))
        k = max(0, min(int(count), MAX_PAGE))
        out = []
        i = s
        while i <= int(self.n) and len(out) < k:
            out.append(self._view(self.requests[u64(i)]))
            i += 1
        return {"total": int(self.n), "start": s, "requests": out}

    @gl.public.view
    def is_listed(self, chain_id: int, token: str) -> typing.Any:
        key = str(int(chain_id)) + ":" + str(token).strip().lower()
        rid = int(self.listed.get(key) or 0)
        return {"listed": rid != 0, "request_id": rid}

    @gl.public.view
    def get_stats(self) -> typing.Any:
        return {"version": VERSION, "burnproof": self.burnproof.as_hex, "requests": int(self.n),
                "listed": int(self.n_listed), "refused": int(self.n_refused)}


def _epoch(value: str) -> int:
    if len(value) < 19:
        return 0
    y, m, d = int(value[0:4]), int(value[5:7]), int(value[8:10])
    hh, mm, ss = int(value[11:13]), int(value[14:16]), int(value[17:19])
    y -= 1 if m <= 2 else 0
    era = (y if y >= 0 else y - 399) // 400
    yoe = y - era * 400
    doy = (153 * (m + (-3 if m > 2 else 9)) + 2) // 5 + d - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    return (era * 146097 + doe - 719468) * 86400 + hh * 3600 + mm * 60 + ss
