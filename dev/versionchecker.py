import argparse
import json
import os
import sys
import urllib.request
from typing import Dict, List, Optional

from retry import retry

WEBTREES_REPO = "fisharebest/webtrees"
MY_REPO = os.getenv("GITHUB_REPOSITORY", default="nathanvaughn/webtrees-docker")

BASE_IMAGES = [
    "docker.io/nathanvaughn/webtrees",
    "ghcr.io/nathanvaughn/webtrees",
    # "cr.nthnv.me/library/webtrees",
]

WEBTREES_PHP = {"1.": "7.4", "2.0": "7.4", "2.1": "8.1"}
WEBTREES_PATCH = {"2.1.18": "1", "2.1.19": "2", "default": "2"}

# used to use 'name' of release, but this has started being blank
VERSION_KEY = "tag_name"


@retry(tries=5, delay=2, backoff=3)
def get_latest_versions(
    repo: str, number: int = 5, check_assets: bool = False
) -> List[dict]:
    """
    Get latest versions from a repository releases
    """

    # build url
    url = f"https://api.github.com/repos/{repo}/releases"
    request = urllib.request.Request(url)

    if os.getenv("GITHUB_TOKEN"):
        request.add_header("Authorization", f'Bearer {os.environ["GITHUB_TOKEN"]}')

    # download data
    data = urllib.request.urlopen(request)
    # parse json
    json_data = json.loads(data.read().decode())
    # only get the latest items
    latest_releases = json_data[:number]

    # skip releases with no assets
    if check_assets:
        for release in latest_releases:
            if not release["assets"]:
                latest_releases.remove(release)

    return latest_releases


def get_tags(versions: List[str]) -> Dict[str, List[str]]:
    """
    Create a list of tags for a given version number
    """
    # dict of list of tags to return
    versions_tags = {}

    # all tags seen, so we don't duplicate
    tags_seen = set()

    # sort descending to work from newest to oldest
    for version in sorted(versions, reverse=True):
        tag_list = [version]

        if version.startswith("1."):
            tag = "latest-1"
        elif version.startswith("2.0"):
            tag = "latest-2.0"
        else:
            tag = "latest"

        if "alpha" in version:
            tag += "-alpha"
        elif "beta" in version:
            tag += "-beta"

        # check against our list of all tags seen to make sure we don't have duplicates
        if tag not in tags_seen:
            tag_list.append(tag)
            tags_seen.add(tag)

        versions_tags[version] = [
            f"{base_image}:{t}" for t in tag_list for base_image in BASE_IMAGES
        ]

    return versions_tags


def main(forced_versions: Optional[List[str]] = None) -> None:
    # get the latest versions of each repo
    wt_version_dicts = get_latest_versions(WEBTREES_REPO, 20, check_assets=True)
    my_version_dicts = get_latest_versions(MY_REPO, 20)

    missing_version_dicts = []

    # go through each version of webtrees
    for wt_version_dict in wt_version_dicts:
        wt_version = wt_version_dict[VERSION_KEY]

        # dropped support for legacy images
        if wt_version.startswith("1."):
            continue

        # check if version is a forced one
        if wt_version in forced_versions:
            # if so, add to list of missing versions
            print(f"Version {wt_version} forcefully added.", file=sys.stderr)
            missing_version_dicts.append(wt_version_dict)

        # check if version is not in my repo
        elif all(v[VERSION_KEY] != wt_version for v in my_version_dicts):
            # if not, add to list of missing versions
            print(f"Version {wt_version} missing.", file=sys.stderr)
            missing_version_dicts.append(wt_version_dict)

    # build authoritative list of all tags we're going to produce
    all_tags = get_tags([v[VERSION_KEY] for v in missing_version_dicts])

    # build output json
    return_data = {"include": []}

    for missing_version_dict in missing_version_dicts:
        version_data = {
            "images": ",".join(all_tags[missing_version_dict[VERSION_KEY]]),
            "webtrees_version": missing_version_dict[VERSION_KEY],
            "php_version": next(
                value
                for key, value in WEBTREES_PHP.items()
                if missing_version_dict[VERSION_KEY].startswith(key)
            ),
            "patch_version" "prerelease": missing_version_dict["prerelease"],
            "src_url": missing_version_dict["html_url"],
        }
        return_data["include"].append(version_data)

    # import pprint
    # pprint.pprint(return_data)

    print(json.dumps(return_data))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--forced", type=str, nargs="*", default=[]
    )  # forcefully add specific versions
    args = parser.parse_args()

    main(args.forced)
