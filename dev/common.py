import functools
import json
import os

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_IMAGES = [
    "index.docker.io/nathanvaughn/webtrees",
    "ghcr.io/nathanvaughn/webtrees",
]

IS_GA = os.getenv("GITHUB_ACTIONS") == "true"


@functools.cache
def versions_dict() -> dict:
    with open(os.path.join(THIS_DIR, "versions.json")) as f:
        data = json.load(f)

    return {d["version"]: d for d in data}
