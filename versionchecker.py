import argparse
import json
import os
import sys
import urllib.request
from typing import List, Optional

WEBTREES_REPO = "fisharebest/webtrees"
MY_REPO = os.getenv("GITHUB_REPOSITORY", default="nathanvaughn/webtrees-docker")

BASE_IMAGES = [
    "docker.io/nathanvaughn/webtrees",
    "ghcr.io/nathanvaughn/webtrees",
    "cr.nthnv.me/library/webtrees",
]

# used to use 'name' of release, but this has started being blank
VERSION_KEY = "tag_name"


def get_latest_versions(
    repo: str, number: int = 5, check_assets: bool = False
) -> List[dict]:
    """
    Get latest versions from a repository releases
    """

    # build url
    url = f"https://api.github.com/repos/{repo}/releases"
    # download data
    data = urllib.request.urlopen(url)
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


def get_tags(version_number: str) -> List[str]:
    """
    Create a list of tags for a given version number
    """
    if "alpha" in version_number:
        end_tag = "latest-alpha"
    elif "beta" in version_number:
        end_tag = "latest-beta"
    elif version_number.startswith("1."):
        end_tag = "latest-legacy"
    else:
        end_tag = "latest"

    end_tag_list = [end_tag, version_number]
    return [f"{base_image}:{tag}" for tag in end_tag_list for base_image in BASE_IMAGES]


def main(forced_versions: Optional[List[str]] = None) -> None:
    # get the latest versions of each repo
    wt_versions = get_latest_versions(WEBTREES_REPO, check_assets=True)
    my_versions = get_latest_versions(MY_REPO, 20)

    missing_versions = []

    # go through each version of webtrees
    for wt_version in wt_versions:
        wt_version_number = wt_version[VERSION_KEY]

        # check if version is a forced one
        if wt_version_number in forced_versions:
            # if so, add to list of missing versions
            print(f"Version {wt_version_number} forcefully added.", file=sys.stderr)
            missing_versions.append(wt_version)

        # check if version is not in my repo
        elif all(v[VERSION_KEY] != wt_version_number for v in my_versions):
            # if not, add to list of missing versions
            print(f"Version {wt_version_number} missing.", file=sys.stderr)
            missing_versions.append(wt_version)

    # build output json
    return_data = {"include": []}
    for m_version in missing_versions:
        # dropping support for any legacy updates
        if m_version[VERSION_KEY].startswith("1."):
            continue

        version_data = {
            "images": ",".join(get_tags(m_version[VERSION_KEY])),
            "webtrees_version": m_version[VERSION_KEY],
            "prerelease": m_version["prerelease"],
            "src_url": m_version["html_url"],
        }
        return_data["include"].append(version_data)

    print(json.dumps(return_data))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--forced", type=str, nargs="*", default=[]
    )  # forcefully add specific versions
    args = parser.parse_args()

    main(args.forced)
