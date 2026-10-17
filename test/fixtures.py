"""Builders for the offline suite: archived pages served the way Wayback
serves them (raw HTML plus Memento-Datetime and Link headers), two mock RPCs
per chain holding ERC-20 state, a model that answers from the quote, and a
wired deployment (BurnProof canonical + demo, BurnGate)."""
import hashlib
import json

import stub
import world

BP = world.module("BurnProof")
GT = world.module("BurnGate")

NOW_ISO = "2026-10-17T12:00:00Z"
NOW = BP.iso_epoch(NOW_ISO)
FIN = 24_000_000
BLOCK = 23_999_000
BLOCK_TS = NOW - 86400
HOUR = 3600
DEAD = BP.DEAD
ETH_A, ETH_B = BP.CHAINS[1][1]
BSC_A, BSC_B = BP.CHAINS[56][1]


def addr(n):
    return "0x" + hashlib.sha256(b"addr%d" % n).hexdigest()[:40]


TOKEN = addr(0x70c)
TOKEN9 = addr(0x709)
FILER = addr(0xf11e)
FILER2 = addr(0xf11f)
FILER3 = addr(0xf120)
PROJECT = addr(0x9a0)

SITE = "example-token.io"
TS = "20211224103559"
SNAP = "https://web.archive.org/web/" + TS + "/https://" + SITE + "/"
RAW = "https://web.archive.org/web/" + TS + "id_/https://" + SITE + "/"
MEMENTO = "Fri, 24 Dec 2021 10:35:59 GMT"


def snap_url(ts=TS, site=SITE, path="/"):
    return "https://web.archive.org/web/" + ts + "/https://" + site + path


def raw_url(ts=TS, site=SITE, path="/"):
    return "https://web.archive.org/web/" + ts + "id_/https://" + site + path


def memento(ts):
    p = BP.parse_ts(ts)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    import datetime as dt
    wd = days[dt.date(p[0], p[1], p[2]).weekday()]
    return wd + ", " + BP.memento_of(p)


def page(body_text, ts=TS, site=SITE, path="/", status=200, memento_ts=None, original=None, headers=None):
    """Serve `body_text` (wrapped in HTML) as the Wayback id_ capture."""
    h = {"memento-datetime": memento(memento_ts or ts),
         "link": '<' + (original or ("https://" + site + path)) + '>; rel="original", <https://web.archive.org/web/timemap/link/x>; rel="timemap"',
         "content-type": "text/html"}
    if headers is not None:
        h = headers
    html_doc = body_text if body_text.lstrip().startswith("<") else \
        "<!DOCTYPE html><html><head><title>t</title><script>var burned='99%';</script></head><body><div>" + body_text + "</div></body></html>"
    stub.WEB.pages[raw_url(ts, site, path)] = (status, html_doc, h)


def word(n):
    return "0x" + ("%064x" % n)


def chains():
    """Two mock RPCs per supported chain, agreeing, finalized at FIN."""
    out = {}
    for cid in BP.CHAINS:
        for url in BP.CHAINS[cid][1]:
            ch = stub.MockChain(cid, FIN, NOW - 600)
            ch.set_block(BLOCK, BLOCK_TS)
            stub.WEB.chains[url] = ch
            out[url] = ch
    return out


def set_token(cid, token, decimals, supply, dead=(0, 0, 0, 0), urls=None, block=None):
    """ERC-20 state on every RPC of the chain (or `urls`), optionally only at `block`."""
    for url in urls or BP.CHAINS[cid][1]:
        ch = stub.WEB.chains[url]
        st = ch.calls if block is None else ch.at.setdefault(block, {}).setdefault("calls", {})
        cd = ch.code if block is None else ch.at.setdefault(block, {}).setdefault("code", {})
        cd[token.lower()] = "0x6080"
        st[(token.lower(), "0x313ce567")] = word(decimals)
        st[(token.lower(), "0x18160ddd")] = word(supply)
        for d, b in zip(DEAD, dead):
            st[(token.lower(), "0x70a08231" + "0" * 24 + d[2:])] = word(b)


def model_answer(t, number, unit=""):
    stub.MODEL.answer = {"type": t, "number": number, "unit": unit}


def model_from_table(table):
    """table: quote substring -> answer dict."""
    def ans(prompt, n):
        for k, v in table.items():
            if k in prompt:
                return json.loads(json.dumps(v))
        return {"type": "NONE", "number": "", "unit": ""}
    stub.MODEL.answer = ans


def reset():
    stub.WEB.reset()
    stub.MODEL.reset()
    stub.FORGE["payload"] = None
    stub.FORGE["mutate"] = None


def deploy(rate_max=5, rate_window=HOUR, demo=False):
    reset()
    w = world.new_world(now_iso=NOW_ISO)
    chains()
    bp = w.deploy("BurnProof", "DEMO" if demo else "CANONICAL", rate_max, rate_window)
    gate = w.deploy("BurnGate", bp)
    return w, bp, gate


def T(n, dec=18):
    return n * 10 ** dec
