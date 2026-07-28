#!/usr/bin/env python3
"""
Minimal DNS Stamp (sdns://) encoder + decoder for DoH stamps.
Spec: https://dnscrypt.info/stamps-specifications
DoH stamp layout (protocol id 0x02):
  0x02 || props(u64 LE) || LP(addr) || VLP(hashes) || LP(hostname) || LP(path) [|| VLP(bootstrap_ips)]
LP  = length-prefixed (1 byte len + bytes)
VLP = vector of LP, high bit of each length byte = "more follow"
Base64: URL-safe, no padding.
"""
import base64, struct, sys

def b64d(s):
    s = s.replace("sdns://", "")
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

def b64e(b):
    return "sdns://" + base64.urlsafe_b64encode(b).decode().rstrip("=")

# ---- decode ----
def read_lp(buf, i):
    n = buf[i]; i += 1
    return buf[i:i+n], i+n

def read_vlp(buf, i):
    out = []
    while True:
        n = buf[i]; i += 1
        more = n & 0x80
        n &= 0x7f
        out.append(buf[i:i+n]); i += n
        if not more:
            break
    return out, i

def decode(stamp):
    b = b64d(stamp)
    proto = b[0]
    assert proto == 0x02, f"not a DoH stamp (proto={proto})"
    i = 1
    props = struct.unpack("<Q", b[i:i+8])[0]; i += 8
    addr, i = read_lp(b, i)
    hashes, i = read_vlp(b, i)
    host, i = read_lp(b, i)
    path, i = read_lp(b, i)
    boot = []
    if i < len(b):
        boot, i = read_vlp(b, i)
    return {
        "proto": proto,
        "props": {"dnssec": bool(props & 1), "nolog": bool(props & 2), "nofilter": bool(props & 4)},
        "addr": addr.decode(),
        "hashes": [h.hex() for h in hashes if h],
        "hostname": host.decode(),
        "path": path.decode(),
        "bootstrap": [x.decode() for x in boot],
    }

# ---- encode ----
def wr_lp(bs):
    assert len(bs) < 128
    return bytes([len(bs)]) + bs

def wr_vlp(items):
    out = b""
    for k, it in enumerate(items):
        last = (k == len(items) - 1)
        ln = len(it) | (0 if last else 0x80)
        out += bytes([ln]) + it
    if not items:
        out = b"\x00"
    return out

def encode(addr, hostname, path, hashes=None, dnssec=True, nolog=True, nofilter=True, bootstrap=None):
    props = (1 if dnssec else 0) | (2 if nolog else 0) | (4 if nofilter else 0)
    b = bytes([0x02]) + struct.pack("<Q", props)
    b += wr_lp(addr.encode())
    hashes = hashes or []
    b += wr_vlp([bytes.fromhex(h) for h in hashes])
    b += wr_lp(hostname.encode())
    b += wr_lp(path.encode())
    if bootstrap:
        b += wr_vlp([x.encode() for x in bootstrap])
    return b64e(b)

if __name__ == "__main__":
    import json
    if sys.argv[1] == "decode":
        print(json.dumps(decode(sys.argv[2]), indent=2, ensure_ascii=False))
    elif sys.argv[1] == "roundtrip":
        d = decode(sys.argv[2])
        re = encode(d["addr"], d["hostname"], d["path"], d["hashes"],
                    d["props"]["dnssec"], d["props"]["nolog"], d["props"]["nofilter"],
                    d["bootstrap"] or None)
        print("orig:", sys.argv[2])
        print("re:  ", re)
        print("match:", re == sys.argv[2])