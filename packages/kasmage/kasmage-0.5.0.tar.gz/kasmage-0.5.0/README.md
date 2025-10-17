<!-- ![alt text](assets/kasmage_alt.png "Kasmage") -->
<!-- ![alt text](assets/kasmage.png "Kasmage") -->

<table>
<tr>
<td width="160">
  <img src="assets/kasmage.png" width="160" alt="Flubs Ompi, DAG Mage"/>
</td>
<td>
  <h1>Kasmage</h1>
  <p>
    🐸 Kasmage is a whimsical, lightweight frog-wizard themed CLI that monitors a Kaspa address for transactions. It can print all historical transactions or watch for new ones in real time.
  </p>
</td>
</tr>
</table>

> **Fun fact:** <span style="color:#49eacb">**Flubs Ompi, DAG Mage**</span> is the official name of the Kasmage frog.    
> Follow me on X [<span style="color:#db1f83">@evofcl</span>](https://x.com/evofcl) and DM me to suggest cool new epithets!  
> If you're a graphic designer, send me a .png of your frog design — I might just feature it!

##
##
![PyPI](https://img.shields.io/pypi/v/kasmage?color=brightgreen) 
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/kasmage?period=total&units=international_system&left_color=grey&right_color=magenta&left_text=downloads)](https://pepy.tech/projects/kasmage)
![Python](https://img.shields.io/pypi/pyversions/kasmage?color=blue)

## ⚠️ Note on Testnet Support

As of October 2025, the Kaspa public API does **not** support testnet addresses.  
Kasmage currently only works with **mainnet** (`kaspa:...`) transactions.  

As soon as testnet support becomes available in the API, Kasmage will be updated to support it.

## ✨ NEW!! – Version 0.5.0 Update

Kasmage keeps leveling up! Here’s what’s new in this release:

- **Verification (live)** → use `--verify <amount>` (repeatable) to flag exact inbound payments.  
  - Each amount is only verified once per occurrence (no spam).  
  - Example: `--verify 1 --verify 1 --verify 5.25`  
- **Threshold filtering (live)** → `--threshold <amount>` only shows **inbound** transactions ≥ that KAS value.  
  - Cannot be combined with `--dir`.  
  - Plays an alert sound if `--alert` is enabled.  
- **Direction filtering** → use `--dir in` or `--dir out` in either live or historical mode.  
- **Alert sounds** → add `--alert` to play a WAV sound on threshold or verify hits.  
- **Sender display** → live logs now include a compact list of sender addresses.  
- **Guardrails** → historical mode now blocks live-only flags (like `--receipts`, `--verify`, `--alert`, etc.) to prevent invalid combos.  

👉 See the [CHANGELOG](CHANGELOG.md) for full details.

## ⚙️ Quickstart (Install & Run)
> **Note:** Already installed Kasmage? Run  
> `pipx upgrade kasmage` (or `pip install --upgrade kasmage`) to get the latest version.
<i>Requires Python 3.8+. Tested on 3.10–3.13.</i>

Option 1: Install with pipx (recommended)

pipx installs CLI apps into isolated environments and makes them available globally on your system.

<i>(If you have pipx installed already, skip to step 2)</i>

Step 1.
First, install pipx:
```bash
# if you use homebrew, use:
brew install pipx
pipx ensurepath

# if you don't use homebrew, use:
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# for Windows users (Powershell):
py -m pip install --user pipx
py -m pipx ensurepath
```

⚠️ PATH warning: After installing pipx, you may need to restart your terminal or run
    ```
    exec zsh (or exec bash)
    ```
to refresh your $PATH. If you see zsh: command not found: pipx or zsh: command not found: kasmage, it usually means ~/.local/bin (where pipx puts executables) isn’t in your PATH. Running pipx ensurepath fixes this.

Step 2.
Install Kasmage:
```bash
pipx install kasmage
kasmage --address kaspa:yourkaspaaddresshere
```

Option 2: Install with pip inside a venv
```bash
python -m venv ~/.venvs/kasmage
source ~/.venvs/kasmage/bin/activate
pip install kasmage
kasmage --address kaspa:yourkaspaaddresshere
```

Option 3: Run from source (for developers). Clone the repo, build the wheel, and install locally:
```bash
git clone https://github.com/yourname/kasmage.git
cd kasmage
poetry build
pip install --force-reinstall dist/kasmage-0.2.0-py3-none-any.whl
```
Now run (default live mode):
```bash
kasmage --address kaspa:yourkaspaaddresshere
```

## Features

- **Live mode**: watch one or more addresses and stream new transactions as they confirm. 
- **Historical mode (updated!)**: print all confirmed transactions with your choice of format (table, ledger, JSONL). 
- **Receipts**: automatically save each detected transaction as a TXT or JSON receipt — useful for bookkeeping, POS, or your own transaction records.  
- **Verification (new!)**: flag exact inbound payments with `--verify`.  
- **Threshold alerts (new!)**: filter inbound transactions by minimum amount (`--threshold N`).  
- **Direction filter (new!)**: only show `in` or `out` transactions.  
- **Alert sounds (new!)**: play an optional WAV chime for verify/threshold hits.  
- **Sender display (new!)**: logs now show the originating addresses of each tx.  
- **Timezone support**: show times in UTC, a specific IANA timezone (e.g. America/Chicago), or your local system time. 
- **Configurable folder naming**: choose short or full subfolder names for receipts.  
- *Compatible with Kaspa mainnet addresses (`kaspa:...`)*  


## Usage

Watch new transactions (live mode with receipts)
```bash
kasmage --address kaspa:yourkaspaaddresshere kaspa:... --receipts #add as many addresses as you want!
```
Output example:
```bash
🐸🔮 Peering into the orb... (Ctrl+C to stop)
✨👀 I scry with my amphibian eye a tx:  49.99990000 KAS | txid: b4a4a0993d7e040105261a6f850fb27a0487737d1bb457d789350545f86780aa | 2025-10-15 17:28:13 UTC
    ↳ from: kaspa:qz23v0..., kaspa:qqw81s...
📜 Behold! Another slimy scroll of coinage joins the spellbook: receipts/kaspa_qpwhk9yja6/receipt_20251015_b4a4a0993d.txt
✨👀 I scry with my amphibian eye a tx: -50.00000000 KAS | txid: b4a4a0993d7e040105261a6f850fb27a0487737d1bb457d789350545f86780aa | 2025-10-15 17:28:13 UTC
📜 Behold! Another slimy scroll of coinage joins the spellbook: receipts/kaspa_qz23v0vptc/receipt_20251015_b4a4a0993d.txt
```
Filter live mode by threshold and direction:
```bash
kasmage --address kaspa:yourkaspaaddresshere --threshold 10 --dir in
```
Verify inbound payments
```bash
kasmage --address kaspa:yourkaspaaddresshere --verify 1 --verify 5.25
```
Output example:
```bash
✅ Payment verified: 1.00000000 KAS to kaspa:qpwhk9... | txid: 1234abcd...
    ↳ from: kaspa:qz23v0..., kaspa:qqw81s...
```
Print all past transactions
```bash
kasmage --address kaspa:yourkaspaaddresshere kaspa:... --historical --historical-tz local --historical-limit 5 --historical-newest-first --short-txid
```
Output example:
```
📜 Peering into the enchanted pond, past ripples reveal kaspa:qpwhk9yja6n2l73enwl62s2u52c7u87mjkh4mwhyeueum660ght4735mlsas5’s deeds...
Address: kaspa_qpwhk9yja6n2l73enwl62s2u52c7u87mjkh4mwhyeueum660ght4735mlsas5
┌─────────────────────────┬──────────────┬─────┬─────────────┐
│ Time                    │ Amount (KAS) │ Dir │ TxID        │
├─────────────────────────┼──────────────┼─────┼─────────────┤
│ 2025-10-15 12:28:13 CDT │     +49.9999 │ IN  │ b4a4a0…80aa │
│ 2025-10-15 12:26:11 CDT │     -50.0005 │ OUT │ 613fe2…e043 │
│ 2025-10-14 13:25:20 CDT │     -10.0010 │ OUT │ 15d03d…4419 │
│ 2025-10-14 13:11:17 CDT │    -100.0010 │ OUT │ a5781b…c44f │
│ 2025-10-14 12:57:52 CDT │      +9.9995 │ IN  │ 08d53f…7ffb │
└─────────────────────────┴──────────────┴─────┴─────────────┘
📜 Conjuring arcane transactions for kaspa:qz23v0vptctqztwk39quaeuvdxq4qnpr0ax5s8a6ds47gzgzteapu3lnq5tqg...
Address: kaspa_qz23v0vptctqztwk39quaeuvdxq4qnpr0ax5s8a6ds47gzgzteapu3lnq5tqg
┌─────────────────────────┬──────────────┬─────┬─────────────┐
│ Time                    │ Amount (KAS) │ Dir │ TxID        │
├─────────────────────────┼──────────────┼─────┼─────────────┤
│ 2025-10-15 12:28:13 CDT │     -50.0000 │ OUT │ b4a4a0…80aa │
│ 2025-10-15 12:26:11 CDT │     +50.0000 │ IN  │ 613fe2…e043 │
└─────────────────────────┴──────────────┴─────┴─────────────┘
```
Ledger-style (grep-friendly)
```bash
kasmage --address kaspa:yourkaspaaddresshere --historical --historical-style ledger
```
Output example:
```
📜 Gazing back through the mists of time for kaspa:qpwhk9yja6n2l73enwl62s2u52c7u87mjkh4mwhyeueum660ght4735mlsas5...
Address: kaspa_qpwhk9yja6n2l73enwl62s2u52c7u87mjkh4mwhyeueum660ght4735mlsas5
[2025-07-17 20:55:35 UTC]  +197.0231 KAS  IN   tx=e6b7c3d1ed49453b4780d226b5f182a758e9f2eacde3789cdc75183b1f3c3e45
[2025-07-18 20:40:46 UTC]  -197.0231 KAS  OUT  tx=9ab95d12949435487a6aeebf741782ea3c1e5823c42887e20ff6751aff90be1f
[2025-10-10 22:50:57 UTC]  +200.1184 KAS  IN   tx=1a3ede08005d22fb225a64b1e1633f07f0647eac69c988804450d91240ffd44c
[2025-10-13 00:17:51 UTC]  -100.0005 KAS  OUT  tx=8d54b611e3ca8163ad7147a94ee278fde44703aec3ea4d51d951eb293e0a9896
[2025-10-13 01:36:18 UTC]   +99.9999 KAS  IN   tx=6c7a0b8473badb50eba9c612b4461420d1d62666c96429cd586f95a4ba8736ff
```
JSONL (machine-friendly)
```bash
kasmage --address kaspa:yourkaspaaddresshere --historical --historical-style jsonl
```
Output example:
```
📜 The spellbook creaks open… what fortunes befell kaspa:qpwhk9yja6n2l73enwl62s2u52c7u87mjkh4mwhyeueum660ght4735mlsas5?
{"time_utc_iso":"2025-07-17T20:55:35.051000+00:00","time_local":"2025-07-17 20:55:35 UTC","amount_kas":197.02308234,"direction":"IN","txid":"e6b7c3d1ed49453b4780d226b5f182a758e9f2eacde3789cdc75183b1f3c3e45"}
{"time_utc_iso":"2025-07-18T20:40:46.247000+00:00","time_local":"2025-07-18 20:40:46 UTC","amount_kas":-197.02308234,"direction":"OUT","txid":"9ab95d12949435487a6aeebf741782ea3c1e5823c42887e20ff6751aff90be1f"}
{"time_utc_iso":"2025-10-10T22:50:57.321000+00:00","time_local":"2025-10-10 22:50:57 UTC","amount_kas":200.11837708,"direction":"IN","txid":"1a3ede08005d22fb225a64b1e1633f07f0647eac69c988804450d91240ffd44c"}
{"time_utc_iso":"2025-10-13T00:17:51.135000+00:00","time_local":"2025-10-13 00:17:51 UTC","amount_kas":-100.0005,"direction":"OUT","txid":"8d54b611e3ca8163ad7147a94ee278fde44703aec3ea4d51d951eb293e0a9896"}
{"time_utc_iso":"2025-10-13T01:36:18.832000+00:00","time_local":"2025-10-13 01:36:18 UTC","amount_kas":99.9999,"direction":"IN","txid":"6c7a0b8473badb50eba9c612b4461420d1d62666c96429cd586f95a4ba8736ff"}
```

## Options
```
-h, –help                   Show this message and exit
-V, –version                Print version and exit

–address ADDR [ADDR …]    Kaspa address(es) to monitor (required)
–interval N                 Poll interval in seconds (default: 10).
Tip: use 1–2 for near real-time, but heavier on API.
–page-size N                Number of tx per API page (default: 50)

–historical                 Print all confirmed tx and exit
–historical-style           table | ledger | jsonl (default: table)
–historical-border          unicode | ascii | none (default: unicode)
–historical-tz              IANA tz like “America/Chicago”, or “local” for system tz
–historical-limit N         Limit number of rows
–historical-newest-first    Show newest tx first
–short-txid                 Show shortened txids in table/ledger
–no-color                   Disable colored IN/OUT

–receipts                   Write a receipt per new tx (live mode)
–receipts-dir PATH          Root directory for receipts (default: ./receipts)
–receipts-dir-style         short | full (default: short)
–receipt-format             txt | json (default: txt)
–min-amount N               Only write a receipt if amount >= this KAS

–verify AMOUNT              Flag exact inbound payment(s) of this amount (repeatable, live mode only)
–threshold N                Only show inbound tx if amount >= this KAS (live mode, cannot be combined with –dir)
–dir {in,out}               Only show transactions of this direction (works in live & historical modes)
–alert                      Play a WAV sound on verify or threshold hits (live mode)

–no-update-check            Skip checking PyPI for newer Kasmage versions
```

## So why Kasmage?

You might be wondering: why use this when wallets and explorers already show transactions?

That’s <i>true</i>, but Kasmage fills a different niche:
- **Automation & scripting**: run it headless on a server or in a script to trigger actions whenever a transaction lands.
- **Instant awareness**: instead of refreshing an explorer, Kasmage streams new transactions as they appear.
- **Receipts & audit trails**: automatically save TXT/JSON receipts for bookkeeping, invoicing, or compliance.
- **Lightweight & headless**: no heavy wallet UI or node install required; just a simple CLI tool.
- **Extensible**: fork it, extend it, or integrate with other systems (e.g., Slack, Discord, payment apps).
- **Fun factor**: transaction tracking feels less like work when Flubs Ompi, the DAG Mage is your companion 🐸.

Wallets are for spending. Explorers are for confirming. Kasmage is for watching, logging, and building.

## Contributing

I'm new to programming for the crypto space and this might not be anything game-changing but
it's a fun little project to work on. If you have ideas for new features, 
please open a feature request (Issue).  If you’ve built something cool, feel 
free to fork the repo and submit a PR!  

Please make sure to update tests as appropriate.

## License
[MIT](LICENSE) © Ethan Villalobos