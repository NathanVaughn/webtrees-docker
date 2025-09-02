import argparse
import functools
import json
import os
import urllib.request

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(THIS_DIR)
IS_GA = os.getenv("GITHUB_ACTIONS") == "true"

PLATFORMS = ["linux/amd64"]
BASE_IMAGES = [
    "index.docker.io/nathanvaughn/webtrees",
    "ghcr.io/nathanvaughn/webtrees",
]


@functools.cache
def versions_dict() -> dict:
    with open(os.path.join(THIS_DIR, "versions.json")) as f:
        data = json.load(f)

    return {d["version"]: d for d in data}


def find_new_versions() -> list[str]:
    """
    Return a list of new versions found in the upstream repo.
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
    new_versions = [v for v in upstream_versions if v not in known_versions]
    return new_versions


def bake_file(versions: list[str], testing: bool) -> dict:
    """
    Generate the contents of a docker-bake.json file.
    """
    # build the matrix data
    matrix_data = []
    for version in versions:
        if version not in versions_dict():
            raise ValueError(f"Version {version} not found in versions.json")

        version_info = versions_dict()[version]

        if testing:
            tags = [f"webtrees:{version}-test"]
        else:
            # build a list of tags. Use every base image with the version,
            # plus any extra tags (e.g., latest)
            tags = [f"{bi}:{version}" for bi in BASE_IMAGES] + [
                f"{bi}:{tag}"
                for bi in BASE_IMAGES
                for tag in version_info["extra_tags"]
            ]
        matrix_data.append(
            {
                "version": version,
                "php": version_info["php"],
                "upgrade_patch": version_info["upgrade_patch"],
                "tags": sorted(tags),
            }
        )

    # https://docs.docker.com/build/bake/reference/
    webtrees_target = {
        "name": 'webtrees-${replace(tgt.version, ".", "-")}',
        "context": "docker/",
        "dockerfile": "Dockerfile",
        "platforms": PLATFORMS,
        "matrix": {"tgt": matrix_data},
        "args": {
            "WEBTREES_VERSION": "${tgt.version}",
            "PHP_VERSION": "${tgt.php}",
            "UPGRADE_PATCH_VERSION": "${tgt.upgrade_patch}",
        },
        "tags": "${tgt.tags}",
    }

    if IS_GA:
        # items specific to GitHub Actions
        webtrees_target["cache-from"] = [{"type": "gha"}]
        webtrees_target["cache-to"] = [{"type": "gha"}]
        webtrees_target["attest"] = [
            {"type": "provenance", "mode": "max"},
            {"type": "sbom"},
        ]
    else:
        # items specific to local builds
        webtrees_target["cache-from"] = [
            {
                "type": "local",
                "src": os.path.join(ROOT_DIR, ".buildx-cache"),
            }
        ]
        webtrees_target["cache-to"] = [
            {
                "type": "local",
                "dest": os.path.join(ROOT_DIR, ".buildx-cache"),
            }
        ]

    return {
        "$schema": "https://www.schemastore.org/docker-bake.json",
        "target": {"webtrees": webtrees_target},
    }


def main(save_to_file: bool, testing: bool, forced_versions: list[str]) -> None:
    new_versions = find_new_versions()
    versions = sorted(set(new_versions) | set(forced_versions), reverse=True)

    result = bake_file(versions=versions, testing=testing)

    if save_to_file:
        with open("docker-bake.json", "w") as fp:
            json.dump(result, fp, indent=4)
    else:
        print(json.dumps(result, indent=4))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", action="store_true", help="Include ARM architecture")
    parser.add_argument("--file", action="store_true", help="Output to JSON")
    parser.add_argument("--test", action="store_true", help="Only save the tag 'test")
    parser.add_argument(
        "--versions",
        type=str,
        nargs="*",
        default=[],
        help="Specific versions to include",
    )
    args = parser.parse_args()

    if args.arm:
        PLATFORMS.extend(["linux/arm/v7", "linux/arm64"])

    main(save_to_file=args.file, testing=args.test, forced_versions=args.versions)
