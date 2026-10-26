#!/usr/bin/env python3
"""uptime-watch — cek status, latency, dan masa berlaku SSL beberapa URL sekaligus.

Contoh:
    python3 main.py https://barlve.com https://cpns.barlve.com
    python3 main.py --file urls.txt --json hasil.json --fail-on down
"""
from __future__ import annotations
import argparse, json, socket, ssl, sys, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path


def sisa_hari_ssl(host: str, port: int = 443, timeout: float = 8.0):
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ss:
                cert = ss.getpeercert()
        exp = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        return (exp - datetime.now(timezone.utc)).days, cert.get("issuer", [])
    except Exception as e:  # noqa: BLE001
        return None, str(e)


def cek(url: str, timeout: float = 10.0) -> dict:
    hasil = {"url": url, "status": None, "ms": None, "ok": False, "redirect": None, "ssl_hari": None, "error": ""}
    mulai = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": "uptime-watch/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            r.read(2048)
            hasil.update(status=r.status, ok=True, redirect=r.geturl() if r.geturl() != url else None)
    except urllib.error.HTTPError as e:
        hasil.update(status=e.code, ok=e.code < 500, error=f"HTTP {e.code}")
    except Exception as e:  # noqa: BLE001
        hasil["error"] = type(e).__name__
    hasil["ms"] = int((time.time() - mulai) * 1000)
    if url.startswith("https://"):
        host = urllib.parse.urlparse(url).hostname
        hari, info = sisa_hari_ssl(host) if host else (None, "")
        hasil["ssl_hari"] = hari
        if hari is None:
            hasil["error"] = hasil["error"] or f"ssl: {str(info)[:60]}"
    return hasil


def main() -> int:
    ap = argparse.ArgumentParser(description="uptime-watch — monitor URL & SSL")
    ap.add_argument("urls", nargs="*")
    ap.add_argument("--file", help="file berisi URL (satu per baris)")
    ap.add_argument("--json", help="simpan hasil JSON")
    ap.add_argument("--ssl-warn", type=int, default=14)
    ap.add_argument("--fail-on", choices=["down", "ssl-warn"], help="exit 1 bila kondisi terpenuhi")
    a = ap.parse_args()

    urls = list(a.urls)
    if a.file:
        urls += [x.strip() for x in Path(a.file).read_text().splitlines() if x.strip() and not x.startswith("#")]
    if not urls:
        ap.print_help(); return 2

    hasil = [cek(u) for u in urls]
    print(f"\n{'STATUS':10} {'LATENCY':>8}  {'SSL':>6}  URL")
    for h in hasil:
        status = "UP" if h["ok"] else "DOWN"
        if h["status"] and h["status"] >= 400:
            status = f"HTTP {h['status']}"
        ssl_txt = "-" if h["ssl_hari"] is None else f"{h['ssl_hari']}d"
        print(f"{status:10} {(str(h['ms']) + 'ms'):>8}  {ssl_txt:>6}  {h['url']} {h['error']}")

    down = [h for h in hasil if not h["ok"]]
    ssl_dekat = [h for h in hasil if h["ssl_hari"] is not None and h["ssl_hari"] <= a.ssl_warn]
    print(f"\n{len(hasil) - len(down)}/{len(hasil)} up · {len(ssl_dekat)} SSL ≤ {a.ssl_warn} hari")

    if a.json:
        Path(a.json).write_text(json.dumps({"waktu": datetime.now(timezone.utc).isoformat(), "hasil": hasil}, indent=2))
        print("JSON:", a.json)

    if a.fail_on == "down" and down:
        return 1
    if a.fail_on == "ssl-warn" and ssl_dekat:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
