# Google Scholar auto-update

Keeps `results/gs_data.json` in sync with the Google Scholar profile. The
homepage reads that file from GitHub's raw URL to render citation counts.

## Why this runs locally instead of in CI

Google serves GitHub Actions runners a CAPTCHA page, so the old workflow
(`.github/workflows/update-scholar.yml`, now disabled) timed out every week for
months. A normal machine reaches Scholar fine, so the refresh runs here and
pushes the result.

Two related gotchas worth knowing:

- **`scholarly` and Python `requests` are both blocked.** Google fingerprints
  Python's TLS handshake — same URL, same User-Agent, `requests` gets 74KB of
  CAPTCHA while `curl` gets the real 146KB profile. `main.py` therefore shells
  out to `curl` and parses the HTML itself.
- **launchd needs a non-SIP interpreter.** `/usr/bin/python3` and `/usr/bin/git`
  are SIP-restricted, and macOS refuses to pass Full Disk Access through to
  them, so a scheduled job using them hangs. Use Homebrew builds.

## Files

| File | Purpose |
| --- | --- |
| `main.py` | Fetches and parses the profile, writes `results/*.json` |
| `update_scholar.sh` | Runs the crawler, commits and pushes when data changed |
| `install_scheduler.sh` | Generates and loads the launchd agent |
| `requirements.txt` | Only needed for the `scholarly` fallback path |

`update_scholar.sh` resolves the repo root, python, and git at runtime, so
nothing is hardcoded to one machine.

## Manual run

```bash
./google_scholar_crawler/update_scholar.sh
```

Add `USE_PROXY=1` to route through a local proxy (defaults to
`http://127.0.0.1:7890`, override with `PROXY_URL`).

## Setting it up on a new machine

```bash
# 1. Clone and enter the repo
git clone https://github.com/Wloner0809/Wloner0809.github.io.git
cd Wloner0809.github.io

# 2. Make sure a non-SIP python and git exist
brew install python git

# 3. Confirm git can push (the script commits on your behalf)
gh auth login          # or configure credentials however you prefer

# 4. Install the daily job (defaults to 11:11; pass HOUR MINUTE to change)
./google_scholar_crawler/install_scheduler.sh
```

Step 4 prints the path you must add under **System Settings → Privacy &
Security → Full Disk Access**. Without that grant, launchd cannot read the repo
and the job will hang — the manual run above still works either way.

Verify with:

```bash
launchctl start com.yuwang.scholar-update
sleep 30 && cat ~/Library/Logs/scholar-update.log
```

To change the schedule, re-run `install_scheduler.sh 9 30`. To remove it,
run `install_scheduler.sh --uninstall`.

## Changing whose profile is tracked

`update_scholar.sh` defaults to `GOOGLE_SCHOLAR_ID=w55OAegAAAAJ`. Override it
in the environment, and update the `citation:` ids in `_data/publications.yml`
to match the new profile's publication ids.
