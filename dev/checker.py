import json
import os
import urllib.request

from common import versions_dict


def main() -> None:
    """
    Print a list of new versions found in the upstream repo missing from ours.
    """
    # build url
    url = "https://api.github.com/repos/fisharebest/webtrees/releases?per_page=20"
    request = urllib.request.Request(url)

    if token := os.getenv("GITHUB_TOKEN"):
        request.add_header("Authorization", f"Bearer {token}")

    # download data
    data = urllib.request.urlopen(request)
    # parse json
    json_data = json.loads(data.read().decode())

    # skip releases with no assets
    upstream_versions = []

    for release in json_data:
        if release["assets"]:
            upstream_versions.append(release["tag_name"])

    # filter out versions we already know about
    known_versions = versions_dict().keys()
    print(json.dumps([v for v in upstream_versions if v not in known_versions]))


if __name__ == "__main__":
    main()
