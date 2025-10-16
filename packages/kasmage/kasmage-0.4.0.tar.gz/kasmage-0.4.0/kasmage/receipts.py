import os
import json
from datetime import datetime, timezone
from typing import Optional

from .sentry import format_time_ms

def _iso(ts_ms: Optional[int]) -> str:
    if ts_ms is None:
        return "unknown"
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat()

def write_receipt(
    dirpath: str,
    *,
    address: str,
    txid: str,
    amount_kas: float,
    time_ms: Optional[int],
    fmt: str = "txt",
):
    os.makedirs(dirpath, exist_ok=True)
    ext = "json" if fmt == "json" else "txt"

    short_txid = txid[:10]
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    fname = f"receipt_{date_str}_{short_txid}.{ext}"

    path = os.path.join(dirpath, fname)

    if os.path.exists(path):
        return path  # don't overwrite

    issued_iso = datetime.now(timezone.utc).isoformat()

    if fmt == "json":
        payload = {
            "schema": "kasmage.receipt@1",
            "address": address,
            "txid": txid,
            "amount_kas": round(amount_kas, 8),
            "time_ms": time_ms,
            "time_utc": format_time_ms(time_ms),
            "time_utc_iso": _iso(time_ms),
            "issued_utc_iso": issued_iso,
            "generator": "kasmage",
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    else:
        body = (
            "Payment Receipt\n"
            f"Address: {address}\n"
            f"Amount:  {amount_kas:.8f} KAS\n"
            f"TxID:    {txid}\n"
            f"Time:    {format_time_ms(time_ms)}\n"
            f"Issued:  {issued_iso}\n"
            "Conjured by: Kasmage 🪄\n"
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)

    return path