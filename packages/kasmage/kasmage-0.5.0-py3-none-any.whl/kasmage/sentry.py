import re
import time
import random
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Callable, Tuple

import requests
from importlib.metadata import version, PackageNotFoundError

from .quips import historical_quips

# --- Optional tz support via stdlib zoneinfo (Python 3.9+) ---
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None  # fallback handled below

ADDRESS_RX = re.compile(r"^kaspa:[a-z0-9]{61,63}$")
PAGE_SIZE = 50

def _pkg_version() -> str:
    try:
        return version("kasmage")
    except PackageNotFoundError:
        return "0.0.0-dev"

_USER_AGENT = f"kasmage/{_pkg_version()}"

# ---------- API ----------
def fetch_transactions_page(address: str, *, limit=PAGE_SIZE, offset=0) -> List[Dict[str, Any]]:
    """
    Fetch one page from kaspa.org with light retry/backoff.
    Returns [] on 200/empty; raises after final failed attempt for network/HTTP errors.
    """
    url = f"https://api.kaspa.org/addresses/{address}/full-transactions"
    headers = {"accept": "application/json", "user-agent": _USER_AGENT}
    params = {"limit": limit, "offset": offset, "resolve_previous_outpoints": "full"}

    last_exc = None
    for attempt in range(3):
        try:
            r = requests.get(url, headers=headers, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return data.get("transactions") or data.get("items") or []
            return []
        except requests.RequestException as e:
            last_exc = e
            time.sleep(1.5 * (attempt + 1))  # simple linear backoff
    raise last_exc  # type: ignore[misc]

def fetch_all_transactions(address: str, *, page_size=PAGE_SIZE, max_pages=200) -> List[Dict[str, Any]]:
    all_txs: List[Dict[str, Any]] = []
    offset = 0
    for _ in range(max_pages):
        page = fetch_transactions_page(address, limit=page_size, offset=offset) or []
        if not page:
            break
        all_txs.extend(page)
        if len(page) < page_size:
            break
        offset += page_size
    return all_txs

# ---------- Parsers ----------
def parse_tx_id(tx: Dict[str, Any]) -> str:
    return str(tx.get("transaction_id") or tx.get("hash") or "unknown")

def parse_time(tx: Dict[str, Any]) -> Optional[int]:
    t = tx.get("block_time") or tx.get("timestamp")
    try:
        t = int(t)
        return t if t >= 10**12 else t * 1000  # ms
    except Exception:
        return None

def _tzinfo_from_name(tz_name: Optional[str]):
    if tz_name is None:
        try:
            return datetime.now().astimezone().tzinfo or timezone.utc
        except Exception:
            return timezone.utc
    if ZoneInfo is None:
        return timezone.utc
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return timezone.utc

def _format_time_ms_tz(t_ms: Optional[int], tz_name: Optional[str]) -> str:
    if t_ms is None:
        return "no-time"
    tzinfo = _tzinfo_from_name(tz_name)
    try:
        dt_utc = datetime.fromtimestamp(t_ms / 1000, tz=timezone.utc)
        dt_local = dt_utc.astimezone(tzinfo) if tzinfo is not None else dt_utc
        return dt_local.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        return "no-time"

def format_time_ms(t_ms: Optional[int]) -> str:
    if t_ms is None:
        return "no-time"
    dt = datetime.fromtimestamp(t_ms/1000, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")

def norm(s: Optional[str]) -> str:
    return s.lower() if isinstance(s, str) else ""

def net_amount_kas_for_address(tx: Dict[str, Any], address: str) -> float:
    addr = norm(address)
    out_total = 0
    for o in tx.get("outputs") or []:
        o_addr = norm(o.get("script_public_key_address") or o.get("address"))
        if o_addr == addr:
            try:
                out_total += int(o.get("amount", 0))
            except Exception:
                pass
    in_total = 0
    for i in tx.get("inputs") or []:
        i_addr = norm(i.get("previous_outpoint_address") or i.get("address"))
        val = i.get("previous_outpoint_amount") or i.get("value")
        if i_addr == addr and val is not None:
            try:
                in_total += int(val)
            except Exception:
                pass
    return (out_total - in_total) / 1e8

def tx_has_sender(tx: Dict[str, Any], expected_sender: str) -> bool:
    want = norm(expected_sender)
    if not want:
        return False
    for i in tx.get("inputs") or []:
        if norm(i.get("previous_outpoint_address") or i.get("address")) == want:
            return True
    return False

def tx_sender_addresses(tx: Dict[str, Any]) -> List[str]:
    seen = set()
    out: List[str] = []
    for i in tx.get("inputs") or []:
        a = (i.get("previous_outpoint_address") or i.get("address") or "").strip().lower()
        if a and a not in seen:
            seen.add(a)
            out.append(a)
    return out

# ---------- Pretty printers ----------
import re as _re
_ANSI_RE = _re.compile(r"\x1b\[[0-9;]*m")

def _strip_ansi(s: str) -> str:
    return _ANSI_RE.sub("", s or "")

def _visible_len(s: str) -> int:
    return len(_strip_ansi(s))

def _short_txid(txid: str, head=6, tail=4) -> str:
    txid = str(txid or "")
    return txid if len(txid) <= head + tail else f"{txid[:head]}…{txid[-tail:]}"

def _color(s: str, code: str, use_color: bool) -> str:
    return f"\x1b[{code}m{s}\x1b[0m" if use_color else s

def _fmt_dir(amt: float, use_color: bool) -> str:
    return _color("IN ", "32;1", use_color) if amt >= 0 else _color("OUT", "31;1", use_color)

def _fmt_amount(amt: float, width: int, decimals: int = 4) -> str:
    return f"{amt:+{width}.{decimals}f}"

def _make_borders(w_time: int, w_amt: int, w_dir: int, w_tx: int, style: str):
    style = (style or "unicode").lower()
    if style == "ascii":
        top_l, top_j, top_r, h, v = "+", "+", "+", "-", "|"
        mid_l, mid_j, mid_r = "+", "+", "+"
        bot_l, bot_j, bot_r = "+", "+", "+"
    elif style == "none":
        return ("", "", "", "", " "), ("", "", "", ""), ("", "", "", "")
    else:  # unicode
        top_l, top_j, top_r, h, v = "┌", "┬", "┐", "─", "│"
        mid_l, mid_j, mid_r = "├", "┼", "┤"
        bot_l, bot_j, bot_r = "└", "┴", "┘"
    top = f"{top_l}{h*(w_time+2)}{top_j}{h*(w_amt+2)}{top_j}{h*(w_dir+2)}{top_j}{h*(w_tx+2)}{top_r}"
    mid = f"{mid_l}{h*(w_time+2)}{mid_j}{h*(w_amt+2)}{mid_j}{h*(w_dir+2)}{mid_j}{h*(w_tx+2)}{mid_r}"
    bot = f"{bot_l}{h*(w_time+2)}{bot_j}{h*(w_amt+2)}{bot_j}{h*(w_dir+2)}{bot_j}{h*(w_tx+2)}{bot_r}"
    return (top, mid, bot, v, v)

def _print_table(rows, use_color: bool, addr_label: str, border_style: str, *, short_txid: bool):
    display_rows = []
    for t_str, amt, txid in rows:
        dir_disp  = _fmt_dir(amt, use_color)
        amt_disp  = _fmt_amount(amt, width=0)
        tx_disp   = _short_txid(txid) if short_txid else txid
        display_rows.append((t_str, amt, dir_disp, tx_disp))

    time_header, amt_header, dir_header, tx_header = "Time", "Amount (KAS)", "Dir", "TxID"

    w_time = max(_visible_len(time_header), *( _visible_len(t) for t, *_ in display_rows ))
    amt_samples = [ _fmt_amount(a, width=0) for _, a, *_ in display_rows ]
    w_amt = max(_visible_len(amt_header), *( _visible_len(s) for s in amt_samples ))
    w_dir = max(_visible_len(dir_header), *( _visible_len(d) for *_, d, _ in display_rows ))
    w_tx  = max(_visible_len(tx_header), *( _visible_len(x) for *_, x in display_rows ))

    display_rows = [(t, _fmt_amount(a, w_amt), d, x) for (t, a, d, x) in display_rows]

    (top, mid, bot, v, _v2) = _make_borders(w_time, w_amt, w_dir, w_tx, border_style)

    if border_style != "none":
        print(f"Address: {addr_label}")
        print(top)
        print(f"{v} {time_header.ljust(w_time)} {v} {amt_header.rjust(w_amt)} {v} {dir_header.ljust(w_dir)} {v} {tx_header.ljust(w_tx)} {v}")
        print(mid)
        for t, a, d, x in display_rows:
            print(f"{v} {t.ljust(w_time)} {v} {a.rjust(w_amt)} {v} {d.ljust(w_dir)} {v} {x.ljust(w_tx)} {v}")
        print(bot)
    else:
        print(f"Address: {addr_label}")
        header = f"{time_header.ljust(w_time)}  {amt_header.rjust(w_amt)}  {dir_header.ljust(w_dir)}  {tx_header.ljust(w_tx)}"
        print(header)
        print("-" * _visible_len(header))
        for t, a, d, x in display_rows:
            print(f"{t.ljust(w_time)}  {a.rjust(w_amt)}  {d.ljust(w_dir)}  {x.ljust(w_tx)}")

def _print_ledger(rows, use_color: bool, addr_label: str, *, short_txid: bool):
    print(f"Address: {addr_label}")
    amt_samples = [ _fmt_amount(a, width=0) for _, a, _ in rows ]
    w_amt = max(_visible_len(s) for s in amt_samples) if amt_samples else 12
    for t_str, amt, txid in rows:
        dir_str = _fmt_dir(amt, use_color)
        tx_disp = _short_txid(txid) if short_txid else txid
        print(f"[{t_str}]  {_fmt_amount(amt, w_amt)} KAS  {dir_str}  tx={tx_disp}")

def _print_jsonl(rows):
    import json
    for t_iso_utc, t_str_local, amt, direction, txid in rows:
        print(json.dumps({
            "time_utc_iso": t_iso_utc,
            "time_local": t_str_local,
            "amount_kas": round(amt, 8),
            "direction": direction,
            "txid": txid,
        }, separators=(",", ":"), ensure_ascii=False))

# ---------- Modes ----------
def validate_addresses(addresses: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for a in addresses:
        a = (a or "").strip().lower()
        if not a:
            continue
        if not ADDRESS_RX.match(a):
            print(f"⚠️ Skipping invalid address: {a}  (expected kaspa: + 61–63 chars)")
            continue
        if a not in seen:
            seen.add(a)
            out.append(a)
    if not out:
        raise SystemExit("No valid Kaspa addresses provided.")
    return out

# on_tx(address, txid, amount_kas, time_ms, tx) → may return True to request stop
OnTxMulti = Callable[[str, str, float, Optional[int], Dict[str, Any]], Optional[bool]]

def run_historical(
    addresses: List[str],
    page_size: int,
    *,
    printer=print,
    style: str = "table",           # "table" | "ledger" | "jsonl"
    color: bool = True,             # colorize IN/OUT for table/ledger
    tz: Optional[str] = "UTC",      # "UTC" (default), IANA tz, or None for system local
    limit: Optional[int] = None,    # cap rows per address
    newest_first: bool = False,     # newest first
    border: str = "unicode",        # "unicode" | "ascii" | "none"
    short_txid: bool = False,       # False = full txid (default), True = shortened
    direction: Optional[str] = None,  # NEW: "in" | "out" | None
):
    style = (style or "table").lower()
    if style not in ("table", "ledger", "jsonl"):
        style = "table"

    dir_filter = (direction or "").lower()
    if dir_filter not in ("in", "out", ""):
        dir_filter = ""

    addrs = validate_addresses(addresses)

    for addr in addrs:
        printer(random.choice(historical_quips[0]).format(address=addr))
        txs = fetch_all_transactions(addr, page_size=page_size)
        if not txs:
            printer(random.choice(historical_quips[1]))
            continue

        # Filter by direction if requested
        if dir_filter:
            filtered = []
            for tx in txs:
                amt = net_amount_kas_for_address(tx, addr)
                if dir_filter == "in" and amt >= 0:
                    filtered.append(tx)
                elif dir_filter == "out" and amt < 0:
                    filtered.append(tx)
            txs = filtered

        txs.sort(key=lambda tx: parse_time(tx) or 0)
        if newest_first:
            txs.reverse()
        if limit is not None and limit >= 0:
            txs = txs[:limit]

        addr_label = addr.replace("kaspa:", "kaspa_")

        if style == "jsonl":
            rows_jsonl = []
            for tx in txs:
                txid = parse_tx_id(tx)
                amt = net_amount_kas_for_address(tx, addr)
                t_ms = parse_time(tx)
                t_iso_utc = (
                    datetime.fromtimestamp((t_ms or 0)/1000, tz=timezone.utc).isoformat()
                    if t_ms is not None else "unknown"
                )
                t_local_str = _format_time_ms_tz(t_ms, tz)
                direction_str = "IN" if amt >= 0 else "OUT"
                rows_jsonl.append((t_iso_utc, t_local_str, amt, direction_str, txid))
            _print_jsonl(rows_jsonl)
        else:
            rows_pretty = []
            for tx in txs:
                txid = parse_tx_id(tx)
                amt = net_amount_kas_for_address(tx, addr)
                t_ms = parse_time(tx)
                t_str = _format_time_ms_tz(t_ms, tz)
                rows_pretty.append((t_str, amt, txid))

            if style == "ledger":
                _print_ledger(rows_pretty, use_color=color, addr_label=addr_label, short_txid=short_txid)
            else:
                _print_table(rows_pretty, use_color=color, addr_label=addr_label, border_style=border, short_txid=short_txid)

    return 0

def run_live(
    addresses: List[str],
    interval: int,
    page_size: int,
    *,
    on_tx: OnTxMulti,
    printer=print,
    stop_after_sec: Optional[int] = None,  # optional timeout
):
    addrs = validate_addresses(addresses)

    seen: set[Tuple[str, str]] = set()
    for addr in addrs:
        current = fetch_all_transactions(addr, page_size=page_size)
        for tx in current:
            txid = parse_tx_id(tx)
            if txid and txid != "unknown":
                seen.add((addr, txid))

    start_ts = time.time()
    printer("🐸🔮 Peering into the orb... (Ctrl+C to stop)")
    try:
        while True:
            if stop_after_sec is not None and (time.time() - start_ts) >= stop_after_sec:
                printer("⏳ Verification timed out — no matching transaction observed.")
                return 2

            for addr in addrs:
                page0 = fetch_transactions_page(addr, limit=page_size, offset=0) or []
                new_seen = False
                for tx in page0:
                    txid = parse_tx_id(tx)
                    key = (addr, txid)
                    if (not txid) or (key in seen):
                        continue
                    seen.add(key)
                    new_seen = True
                    amt = net_amount_kas_for_address(tx, addr)
                    t_ms = parse_time(tx)
                    should_stop = on_tx(addr, txid, amt, t_ms, tx)
                    if should_stop:
                        return 0

                if new_seen and len(page0) == page_size:
                    offset = page_size
                    while True:
                        page = fetch_transactions_page(addr, limit=page_size, offset=offset) or []
                        if not page:
                            break
                        for tx in page:
                            txid = parse_tx_id(tx)
                            key = (addr, txid)
                            if (not txid) or (key in seen):
                                continue
                            seen.add(key)
                            amt = net_amount_kas_for_address(tx, addr)
                            t_ms = parse_time(tx)
                            should_stop = on_tx(addr, txid, amt, t_ms, tx)
                            if should_stop:
                                return 0
                        if len(page) < page_size:
                            break
                        offset += page_size
            time.sleep(max(1, interval))
    except KeyboardInterrupt:
        printer("\n🐸💨 The frog vanishes in a puff of smoke...")
        return 0