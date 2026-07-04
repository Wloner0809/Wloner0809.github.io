import json
import os
import random
import time
from datetime import datetime

from scholarly import ProxyGenerator, scholarly


def sanitize_scholar_id(raw_id):
    """Strip URL cruft like '&hl=en' that sometimes ends up in the secret."""
    return raw_id.split("&")[0].strip()


def enable_proxy():
    """Route scholarly through free proxies to dodge Google Scholar's
    IP block on GitHub Actions' data-center ranges.

    Returns True if a proxy was successfully engaged, False otherwise
    (caller may still attempt a direct connection as a last resort).
    """
    try:
        pg = ProxyGenerator()
        if pg.FreeProxies():
            scholarly.use_proxy(pg)
            print("Proxy enabled via FreeProxies.")
            return True
    except Exception as e:
        print(f"Failed to enable proxy: {e}")
    print("Proceeding without a proxy.")
    return False


def get_author_data_with_retry(scholar_id, max_retries=3):
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1} to fetch data...")

            # Refresh the proxy each attempt: a dead free proxy is the most
            # common cause of a hang, so we rotate rather than reuse.
            enable_proxy()

            time.sleep(random.uniform(2, 5))

            author = scholarly.search_author_id(scholar_id)

            time.sleep(random.uniform(1, 3))

            scholarly.fill(
                author, sections=["basics", "indices", "counts", "publications"]
            )

            return author

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = (2**attempt) * 5
                print(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                raise e


scholar_id = sanitize_scholar_id(os.environ["GOOGLE_SCHOLAR_ID"])
print(f"Fetching data for scholar_id={scholar_id}")
author: dict = get_author_data_with_retry(scholar_id)
name = author["name"]
author["updated"] = str(datetime.now())
author["publications"] = {v["author_pub_id"]: v for v in author["publications"]}
print(json.dumps(author, indent=2))
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
