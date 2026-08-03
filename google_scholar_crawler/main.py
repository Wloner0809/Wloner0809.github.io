"""Fetch Google Scholar profile data and write it as JSON for the homepage.

The `scholarly` library is now reliably blocked by Google (its requests get
served an interstitial with no `gsc_prf_in` block, so parsing dies with
AttributeError). A plain HTTP request with a normal browser User-Agent still
works, so that is the primary path; `scholarly` is kept as a fallback.

The output schema matches what the site's JS expects:
  {"name", "citedby", "hindex", ..., "publications": {pub_id: {...}}}
"""

import json
import os
import random
import re
import subprocess
import time
from datetime import datetime

SCHOLAR_URL = "https://scholar.google.com/citations"
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


def sanitize_scholar_id(raw_id):
    """Strip URL cruft like '&hl=en' that sometimes ends up in the secret."""
    return raw_id.split("&")[0].strip()


def _unescape(text):
    """Minimal HTML entity decode for the fields we pull out."""
    return (
        text.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&nbsp;", " ")
        .strip()
    )


def fetch_profile_html(scholar_id, max_retries=3):
    """Download the profile page via curl, retrying with a different UA.

    We shell out to curl on purpose: Google fingerprints Python's TLS/HTTP2
    handshake and serves `requests` a CAPTCHA page even with a browser
    User-Agent, while the identical request through curl returns the real
    profile. Verified side by side — curl 146KB with the profile block,
    requests 74KB of CAPTCHA.
    """
    url = (
        f"{SCHOLAR_URL}?user={scholar_id}&hl=en&sortby=pubdate&pagesize=100"
    )
    last_error = None
    for attempt in range(max_retries):
        ua = USER_AGENTS[attempt % len(USER_AGENTS)]
        try:
            print(f"Attempt {attempt + 1}: fetching profile page via curl...")
            result = subprocess.run(
                [
                    "curl", "-sS", "--compressed", "--max-time", "30",
                    "-A", ua,
                    "-H", "Accept-Language: en-US,en;q=0.9",
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=45,
            )
            if result.returncode != 0:
                raise RuntimeError(f"curl exited {result.returncode}: {result.stderr.strip()}")
            html = result.stdout
            if "gsc_prf_in" not in html:
                raise ValueError("profile block missing — request was intercepted")
            return html
        except Exception as e:  # noqa: BLE001 - retry on any transport/parse issue
            last_error = e
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait = (2**attempt) * 5 + random.uniform(0, 3)
                print(f"Waiting {wait:.1f}s before retry...")
                time.sleep(wait)
    raise RuntimeError(f"Could not fetch Scholar profile: {last_error}")


def parse_profile(html, scholar_id):
    """Turn the profile HTML into the JSON structure the homepage consumes."""
    name_match = re.search(r'id="gsc_prf_in">([^<]+)', html)
    if not name_match:
        raise ValueError("could not locate the author name")

    # The stats table lists citedby, citedby5y, hindex, hindex5y, i10, i10-5y.
    stats = [int(n) for n in re.findall(r'gsc_rsb_std">(\d+)', html)]
    stats += [0] * (6 - len(stats))

    publications = {}
    # Each row: publication id + title, then the citation count cell.
    rows = re.findall(
        r"citation_for_view=([\w-]+:[\w-]+)[^>]*>([^<]+)</a>.*?gsc_a_ac[^>]*>(\d*)<",
        html,
        re.S,
    )
    years = re.findall(r'gsc_a_h[^>]*>(\d{4})<', html)
    for index, (pub_id, title, citations) in enumerate(rows):
        publications[pub_id] = {
            "container_type": "Publication",
            "source": "AUTHOR_PUBLICATION_ENTRY",
            "bib": {
                "title": _unescape(title),
                "pub_year": years[index] if index < len(years) else "",
            },
            "filled": False,
            "author_pub_id": pub_id,
            "num_citations": int(citations) if citations else 0,
        }

    affiliation = re.search(r'class="gsc_prf_il"[^>]*>([^<]*)<', html)
    interests = [
        _unescape(i) for i in re.findall(r'/citations\?view_op=search_authors[^>]*>([^<]+)<', html)
    ]

    return {
        "container_type": "Author",
        "filled": ["basics", "publications", "indices", "counts"],
        "scholar_id": scholar_id,
        "source": "AUTHOR_PROFILE_PAGE",
        "name": _unescape(name_match.group(1)),
        "affiliation": _unescape(affiliation.group(1)) if affiliation else "",
        "interests": interests,
        "citedby": stats[0],
        "citedby5y": stats[1],
        "hindex": stats[2],
        "hindex5y": stats[3],
        "i10index": stats[4],
        "i10index5y": stats[5],
        "publications": publications,
    }


def fetch_via_scholarly(scholar_id):
    """Fallback path, kept for the day Google stops blocking the library."""
    from scholarly import scholarly  # imported lazily so it stays optional

    print("Falling back to the scholarly library...")
    author = scholarly.search_author_id(scholar_id)
    scholarly.fill(author, sections=["basics", "indices", "counts", "publications"])
    author["publications"] = {v["author_pub_id"]: v for v in author["publications"]}
    return author


scholar_id = sanitize_scholar_id(os.environ["GOOGLE_SCHOLAR_ID"])
print(f"Fetching data for scholar_id={scholar_id}")

try:
    author = parse_profile(fetch_profile_html(scholar_id), scholar_id)
except Exception as primary_error:  # noqa: BLE001 - fall back before giving up
    print(f"Direct fetch failed: {primary_error}")
    author = fetch_via_scholarly(scholar_id)

if not author.get("publications"):
    raise SystemExit("Refusing to write an empty publication list.")

author["updated"] = str(datetime.now())
print(json.dumps(author, indent=2, ensure_ascii=False))

os.makedirs("results", exist_ok=True)
with open("results/gs_data.json", "w") as outfile:
    json.dump(author, outfile, ensure_ascii=False)

shieldio_data = {
    "schemaVersion": 1,
    "label": "citations",
    "message": f"{author['citedby']}",
}
with open("results/gs_data_shieldsio.json", "w") as outfile:
    json.dump(shieldio_data, outfile, ensure_ascii=False)
