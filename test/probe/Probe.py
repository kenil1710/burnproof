# v0.3.0
# { "Depends": "py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng" }
import genlayer as gl
from genlayer import *
import json
import typing


class Probe(gl.contract.Contract):
    out: str

    def __init__(self) -> None:
        self.out = ""

    @gl.public.write
    def run(self, url: str, rpcs: str, prompt: str) -> None:
        def leader() -> str:
            r = {}
            try:
                res = gl.nondet.web.request(url, method="GET")
                b = res.body if isinstance(res.body, bytes) else str(res.body).encode()
                h = getattr(res, "headers", None)
                hv = {}
                if h is not None:
                    for k in h:
                        if str(k).lower() in ("memento-datetime", "location", "content-type", "link"):
                            hv[str(k)] = str(h[k])[:160]
                r["page"] = [getattr(res, "status", None), len(b), type(h).__name__, len(h) if h is not None else -1, hv, [str(k) for k in h][:40] if h is not None else []]
            except Exception as e:
                r["page"] = "ERR " + repr(e)[:200]
            for u in json.loads(rpcs):
                try:
                    body = json.dumps({"jsonrpc": "2.0", "id": 0, "method": "eth_getBlockByNumber", "params": ["finalized", False]})
                    res = gl.nondet.web.request(u, method="POST", body=body, headers={"Content-Type": "application/json"})
                    d = json.loads(res.body.decode("utf-8"))
                    r[u] = [getattr(res, "status", None), str(d.get("result", d)).replace("'", "")[:90]]
                except Exception as e:
                    r[u] = "ERR " + repr(e)[:200]
            if prompt:
                try:
                    r["model"] = gl.nondet.exec_prompt(prompt, response_format="json")
                except Exception as e:
                    r["model"] = "ERR " + repr(e)[:200]
            return json.dumps(r)

        self.out = gl.vm.run_nondet(leader, lambda res: True)

    @gl.public.view
    def get(self) -> str:
        return self.out
