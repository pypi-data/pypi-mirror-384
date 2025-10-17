import os
import re
import argparse
import requests
from importlib.metadata import version, PackageNotFoundError
from decimal import Decimal, ROUND_HALF_UP

# Optional playsound (only used when --alert is set)
try:
    import playsound  # type: ignore
    _HAS_PLAYSOUND = True
except Exception:
    _HAS_PLAYSOUND = False

# Zip-safe package resource access for the wav file
try:
    from importlib import resources as _pkg_res  # Py3.9+
except Exception:
    _pkg_res = None  # best-effort; _play_alert() will no-op if unavailable

from . import sentry
from . import receipts as receipts_mod

# --- Optional semantic version support ---
try:
    from packaging.version import Version, InvalidVersion  # type: ignore
except Exception:
    Version = None  # type: ignore
    InvalidVersion = Exception  # type: ignore


def _pkg_version() -> str:
    try:
        return version("kasmage")
    except PackageNotFoundError:
        return "0.0.0-dev"


KASMAGE_VERSION = _pkg_version()

# -------- Art --------
FROG_KASMAGE = r"""
                        
                     .@@@.                       
                    @*=-@#                       
                   @  ==%@                       
                  %+===+*%@                      
                 @#= -=+##@.                    
               :#+=+.=++=*%@                    
            =%%@@+++.=*+ :%@          ] .  m,  m, .mm  m,  mm  m, 
           @@#==+****@@@@@@@@@@@      ].` ' ] ] ' ]]] ' ] ]`T ]`] 
             %.@@@@@@@@@@@%%%@@@      ]T  ."T  "\ ]]] ."T ] ] ]"" 
            .+*+.    =@@# %-          ] \ 'mT 'm/ ]]] 'mT 'bT 'b/ 
            %*----------   -+                              ,]
             +               -%                            '`
              @             %%=@:               
            %:%       %   @     @@              
            -*@ #     % = @      @              
           +%*@ *@    % @=:+%*  @:              
          %@@=%@ .%@@.# @@ .  %@=               
                            ...                     
"""

# ---- Update checker helpers ----
def _norm_parts(v: str):
    parts = re.split(r"[.\-+]", v)
    out = []
    for p in parts:
        out.append(int(p) if p.isdigit() else p)
    return out


def _is_newer(latest: str, current: str) -> bool:
    """Return True if latest > current."""
    if not latest or not current:
        return False
    if Version is not None:
        try:
            return Version(latest) > Version(current)
        except InvalidVersion:
            return latest != current
    try:
        return _norm_parts(latest) > _norm_parts(current)
    except Exception:
        return False


def _is_equal(a: str, b: str) -> bool:
    if not a or not b:
        return False
    if Version is not None:
        try:
            return Version(a) == Version(b)
        except InvalidVersion:
            return a == b
    return a == b


def _check_for_update(current: str, *, timeout: float = 0.8) -> None:
    """Tiny network check against PyPI. Silently continues on error."""
    try:
        resp = requests.get("https://pypi.org/pypi/kasmage/json", timeout=timeout)
        resp.raise_for_status()
        latest = (resp.json().get("info") or {}).get("version") or ""
        if not latest:
            return

        if current == "0.0.0-dev":
            return  # skip update check for local/dev builds
        elif _is_newer(latest, current):
            print(
                f"This is ancient magic! Upgrade to Kasmage {latest} (you're currently on version {current})\n"
                "   pipx upgrade kasmage\n"
                "   pip install --upgrade kasmage\n"
            )
        elif _is_equal(latest, current):
            print(f"You’re on the latest version {current}.")
        else:
            # Local/dev build newer than PyPI
            print(f"You’re running a dev build ({current}) newer than PyPI ({latest}).")
    except Exception:
        # offline or transient; stay quiet
        pass


# Filename sanitizer (Windows/macOS/Linux)
_BAD_FS = re.compile(r'[<>:"/\\|?*\x00-\x1F]+')
def _sanitize_for_fs(s: str) -> str:
    s = (s or "").strip()
    s = _BAD_FS.sub("_", s)
    return s.rstrip(". ")


def _shorten_addr(addr: str) -> str:
    """
    Build a short, readable per-address folder name using the first 10 chars
    of the address (after 'kaspa:'). Example:
        kaspa:qy2f... -> kaspa_qy2fxxxxxx
    """
    a = (addr or "").lower().strip()
    core = a.split(":", 1)[1] if a.startswith("kaspa:") else a
    return f"kaspa_{core[:10]}"


def _address_dir(addr: str, style: str) -> str:
    """
    Return the directory name for an address based on style.
        - 'short' -> 'kaspa_<first10>'
        - 'full'  -> full address (sanitized), with ':' swapped for '_'
    """
    if style == "full":
        name = addr.replace(":", "_")
    else:  # 'short'
        name = _shorten_addr(addr)
    return _sanitize_for_fs(name)


# --- Precise amount helpers (sompi) ---
SOMPI_PER_KAS = 100_000_000

def _to_sompi_from_str(kas_str: str) -> int:
    # Parse exact decimal string to integer sompi, rounding half up.
    q = (Decimal(kas_str) * Decimal(SOMPI_PER_KAS)).to_integral_value(rounding=ROUND_HALF_UP)
    return int(q)


def main():
    # Pre-parse just for -V & --version so they work without --address
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("-V", "--version", action="store_true", help="print version and exit")
    pre_args, _ = pre.parse_known_args()
    if pre_args.version:
        print(f"kasmage {KASMAGE_VERSION}")
        return 0

    print(FROG_KASMAGE)

    p = argparse.ArgumentParser(description="Kasmage — Kaspa transaction logger (historical or live)")
    p.add_argument("--address", nargs="+", required=True, help="kaspa:...")
    p.add_argument(
        "--interval", type=int, default=10,
        help=(
            "poll seconds (live mode, default: 10). "
            "Shorter intervals (1–2s) provide near real-time detection but increase API load."
        ),
    )
    p.add_argument("--page-size", type=int, default=sentry.PAGE_SIZE, help="transactions per page")

    # Historical flag & toggles
    p.add_argument("--historical", action="store_true", help="print ALL historical tx(s) per address and exit")
    p.add_argument("--historical-style", choices=["table", "ledger", "jsonl"], default="table")
    p.add_argument("--historical-border", choices=["unicode", "ascii", "none"], default="unicode", help="border style for table output")
    p.add_argument("--historical-tz", default="UTC", help='IANA tz like "America/Chicago"; use "local" for system tz if unsure (default: UTC)')
    p.add_argument("--historical-limit", type=int, default=None)
    p.add_argument("--historical-newest-first", action="store_true")
    p.add_argument("--short-txid", action="store_true", help="show shortened txids (default is full) in table/ledger historical output")
    p.add_argument("--no-color", action="store_true")

    # Receipts (live mode only)
    p.add_argument("--receipts", action="store_true", help="write a receipt per new tx (live mode)")
    p.add_argument("--receipts-dir", default="receipts", help="directory for receipts")
    p.add_argument(
        "--receipts-dir-style", choices=["short", "full"], default="short",
        help="subfolder naming for each address: 'short' = kaspa_<first10>, 'full' = full address")
    p.add_argument("--receipt-format", choices=["txt", "json"], default="txt", help="receipt format")
    p.add_argument("--min-amount", type=float, default=None, help="only write a receipt if net amount >= this KAS")

    # Alert sound (live mode only)
    p.add_argument("--alert", action="store_true", help="enable sound effects (live mode)")

    # Filters
    p.add_argument("--threshold", type=float, default=None, help="only show inbound tx if amount >= this KAS (live mode)")
    p.add_argument("--dir", choices=["in", "out"], default=None, help="filter tx direction; works in both modes")

    # Verification (live mode)
    p.add_argument(
        "--verify", action="append", metavar="AMOUNT",
        help="flag exact inbound payments by amount; repeatable. Example: --verify 1 --verify 1 --verify 5.25 (live mode)"
    )

    # Update check controls
    p.add_argument("--no-update-check", action="store_true", help="skip checking PyPI for a newer Kasmage version")

    # Version flag (duplicate of pre-parse to keep help output intact)
    p.add_argument("-V", "--version", action="store_true", help="print version and exit")

    args = p.parse_args()

    # Optional update check
    if not (args.no_update_check):
        _check_for_update(KASMAGE_VERSION)

    if args.version:
        print(f"kasmage {KASMAGE_VERSION}")
        return 0

    # --- Mode guardrails: block live-only flags in historical mode ---
    if args.historical:
        live_conflicts = []
        if args.receipts:
            live_conflicts.append("--receipts")
        if args.receipts_dir != "receipts":
            live_conflicts.append("--receipts-dir")
        if args.receipts_dir_style != "short":
            live_conflicts.append("--receipts-dir-style")
        if args.receipt_format != "txt":
            live_conflicts.append("--receipt-format")
        if args.min_amount is not None:
            live_conflicts.append("--min-amount")
        if args.threshold is not None:
            live_conflicts.append("--threshold")
        if args.verify:
            live_conflicts.append("--verify")
        if args.alert:
            live_conflicts.append("--alert")
        if live_conflicts:
            opts = ", ".join(live_conflicts)
            raise SystemExit(f"These options are only valid in live mode and cannot be used with --historical: {opts}")

    # --- Threshold vs dir guardrail (threshold is inbound-only) ---
    if args.threshold is not None and args.dir is not None:
        raise SystemExit("--threshold and --dir cannot be used together. Threshold applies only to inbound transactions.")

    # ---Historical mode ---
    if args.historical:
        tz_arg = None if (args.historical_tz.lower() == "local") else args.historical_tz
        return sentry.run_historical(
            args.address,
            page_size=args.page_size,
            style=args.historical_style,
            color=not args.no_color,
            tz=tz_arg,
            limit=args.historical_limit,
            newest_first=args.historical_newest_first,
            border=args.historical_border,
            short_txid=args.short_txid,
            direction=args.dir
        )

    # --- Live mode  ---

    # Parse & validate verify amounts (multiset: sompi -> count)
    pending_verify: dict[int, int] = {}
    if args.verify:
        for item in args.verify:
            try:
                sompi = _to_sompi_from_str(item.strip())
            except Exception:
                raise SystemExit(f"--verify amount must be a number, got: {item!r}")
            pending_verify[sompi] = pending_verify.get(sompi, 0) + 1

    def _play_alert():
        if not (args.alert and _HAS_PLAYSOUND and _pkg_res):
            return
        try:
            # Locate the wav inside the installed package in a zip-safe way
            with _pkg_res.as_file(_pkg_res.files("kasmage").joinpath("assets", "tx-sfx.wav")) as p:
                playsound.playsound(str(p))
        except Exception:
            # Stay silent on any audio error
            pass

    def make_on_tx_multi(args):
        verify_multiset = dict(pending_verify)

        def on_tx(addr: str, txid: str, amount_kas: float, time_ms, tx_dict, printer=print):
            verified_here = False

            # 1) Verification path (bypasses filters). Only for inbound.
            if verify_multiset and amount_kas >= 0:
                observed_sompi = int(Decimal(amount_kas).scaleb(8).to_integral_value(rounding=ROUND_HALF_UP))
                if observed_sompi in verify_multiset and verify_multiset[observed_sompi] > 0:
                    verified_here = True
                    _play_alert()
                    printer(f"✅ Payment verified: {amount_kas:.8f} KAS to {addr} | txid: {txid} | {sentry.format_time_ms(time_ms)}")
                    senders = sentry.tx_sender_addresses(tx_dict)
                    if senders:
                        pretty = ", ".join(senders[:5])
                        if len(senders) > 5:
                            pretty += ", …"
                        printer(f"    ↳ from: {pretty}")
                    if args.receipts and (args.min_amount is None or amount_kas >= args.min_amount):
                        root_dir = _sanitize_for_fs(args.receipts_dir)
                        per_addr_dir = os.path.join(root_dir, _address_dir(addr, args.receipts_dir_style))
                        path = receipts_mod.write_receipt(
                            per_addr_dir,
                            address=addr,
                            txid=txid,
                            amount_kas=amount_kas,
                            time_ms=time_ms,
                            fmt=args.receipt_format,
                        )
                        printer(f"📜 Payment received, scroll sealed in the archives: {path}")
                    verify_multiset[observed_sompi] -= 1
                    if verify_multiset[observed_sompi] <= 0:
                        verify_multiset.pop(observed_sompi, None)

            # 2) Normal logging (subject to filters) — skip if we just printed a verify line for this tx
            if not verified_here:
                if args.threshold is not None:
                    # Threshold mode = inbound-only + amount >= threshold
                    if amount_kas < 0 or amount_kas < args.threshold:
                        return
                    _play_alert()
                else:
                    # Non-threshold mode: honor --dir if provided
                    direction = "in" if amount_kas >= 0 else "out"
                    if args.dir and args.dir != direction:
                        return

                printer(
                    f"✨👀 I scry with my amphibian eye a tx: "
                    f"{amount_kas:>12.8f} KAS | txid: {txid} | {sentry.format_time_ms(time_ms)}"
                )
                senders = sentry.tx_sender_addresses(tx_dict)
                if senders:
                    pretty = ", ".join(senders[:5])
                    if len(senders) > 5:
                        pretty += ", …"
                    printer(f"    ↳ from: {pretty}")

                if args.receipts and (args.min_amount is None or amount_kas >= args.min_amount):
                    root_dir = _sanitize_for_fs(args.receipts_dir)
                    per_addr_dir = os.path.join(root_dir, _address_dir(addr, args.receipts_dir_style))
                    path = receipts_mod.write_receipt(
                        per_addr_dir,
                        address=addr,
                        txid=txid,
                        amount_kas=amount_kas,
                        time_ms=time_ms,
                        fmt=args.receipt_format,
                    )
                    printer(f"📜 Behold! Another slimy scroll of coinage joins the spellbook: {path}")

            return None  # keep running

        return on_tx

    on_tx = make_on_tx_multi(args)
    return sentry.run_live(
        args.address,
        interval=args.interval,
        page_size=args.page_size,
        on_tx=on_tx,
    )


if __name__ == "__main__":
    raise SystemExit(main())