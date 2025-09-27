import json
import os
import random
import time
from datetime import datetime

from scholarly import scholarly


def get_author_data_with_retry(scholar_id, max_retries=3):
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1} to fetch data...")

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


author: dict = get_author_data_with_retry(os.environ["GOOGLE_SCHOLAR_ID"])
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
