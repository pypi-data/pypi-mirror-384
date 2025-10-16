import os
import re
import argparse
from importlib.metadata import version, PackageNotFoundError

from . import sentry
from . import receipts as receipts_mod

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

def main():
    # Pre-parse just for --version so it works without --address
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
    p.add_argument("--historical-style", choices=["table","ledger","jsonl"], default="table")
    p.add_argument("--historical-border", choices=["unicode","ascii","none"], default="unicode", help="border style for table output")
    p.add_argument("--historical-tz", default="UTC", help='IANA tz like "America/Chicago"; use "local" for system tz if unsure (default: UTC)')
    p.add_argument("--historical-limit", type=int, default=None)
    p.add_argument("--historical-newest-first", action="store_true")
    p.add_argument("--short-txid", action="store_true", help="show shortened txids (default is full) in table/ledger historical output")
    p.add_argument("--no-color", action="store_true")

    # Receipt flag & toggles
    p.add_argument("--receipts", action="store_true", help="write a receipt per new tx (live mode)")
    p.add_argument("--receipts-dir", default="receipts", help="directory for receipts")
    p.add_argument(
        "--receipts-dir-style", choices=["short", "full"], default="short",
        help="subfolder naming for each address: 'short' = kaspa_<first10>, 'full' = full address")
    p.add_argument("--receipt-format", choices=["txt", "json"], default="txt", help="receipt format")
    p.add_argument("--min-amount", type=float, default=None, help="only write a receipt if net amount >= this KAS")

    # Miner-friendly filters
    p.add_argument("--threshold", type=float, default=None, help="only show tx if |amount| >= this KAS")
    p.add_argument("--dir", choices=["in", "out"], default=None, help="filter tx direction; omit to show both")

    # Version flag
    p.add_argument("-V", "--version", action="store_true", help="print version and exit")

    args = p.parse_args()

    if args.version:
        print(f"kasmage {KASMAGE_VERSION}")
        return 0

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
        )

    def make_on_tx_multi(args):
        def on_tx(addr: str, txid: str, amount_kas: float, time_ms, tx_dict, printer=print):
            # Apply filters
            if args.threshold is not None and abs(amount_kas) < args.threshold:
                return
            direction = "in" if amount_kas >= 0 else "out"
            if args.dir and args.dir != direction:
                return

            # Show the tx if it passed filters
            printer(
                f"✨👀 I scry with my amphibian eye a tx: "
                f"{amount_kas:>12.8f} KAS | txid: {txid} | {sentry.format_time_ms(time_ms)}"
            )

            # Optionally write receipt
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