import argparse
import json
import os

from common import BASE_IMAGES, IS_GA, THIS_DIR, versions_dict

ROOT_DIR = os.path.dirname(THIS_DIR)
PLATFORMS = ["linux/amd64"]
ARM_PLATFORMS = ["linux/arm/v7", "linux/arm64"]


def bake_file(version: str, testing: bool) -> dict:
    """
    Generate the contents of a docker-bake.json file.
    """
    if version not in versions_dict():
        raise ValueError(f"Version {version} not found in versions.json")

    version_info = versions_dict()[version]

    if testing:
        tags = [f"webtrees:{version}-test"]
    else:
        # build a list of tags. Use every base image with the version,
        # plus any extra tags (e.g., latest)
        tags = sorted(
            [f"{bi}:{version}" for bi in BASE_IMAGES]
            + [
                f"{bi}:{tag}"
                for bi in BASE_IMAGES
                for tag in version_info["extra_tags"]
            ]
        )

    # https://docs.docker.com/build/bake/reference/
    webtrees_target = {
        # "name": "webtrees", # only for matrix builds
        "context": "docker/",
        "dockerfile": "Dockerfile",
        "platforms": PLATFORMS,
        "args": {
            "WEBTREES_VERSION": version,
            "PHP_VERSION": version_info["php"],
            "UPGRADE_PATCH_VERSION": str(version_info["upgrade_patch"]),
        },
        "tags": tags,
    }

    if IS_GA:
        # items specific to GitHub Actions
        webtrees_target["cache-from"] = [{"type": "gha"}]
        webtrees_target["cache-to"] = [{"type": "gha"}]
        webtrees_target["attest"] = [
            {"type": "provenance", "mode": "max"},
            {"type": "sbom"},
        ]
        # don't push to registry by name, only push by digest
        webtrees_target["output"] = [
            {
                "type": "image",
                "push-by-digest": True,
                "push": True,
                "name-canonical": True,
            }
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


def main(save_to_file: bool, testing: bool, version: str) -> None:
    result = bake_file(version=version, testing=testing)

    if save_to_file:
        with open(os.path.join(ROOT_DIR, "docker-bake.json"), "w") as fp:
            json.dump(result, fp, indent=4)
    else:
        print(json.dumps(result, indent=4))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", action="store_true", help="Include ARM architecture")
    parser.add_argument("--file", action="store_true", help="Output to JSON")
    parser.add_argument("--test", action="store_true", help="Only save the tag 'test'")
    parser.add_argument("--version", type=str, help="Specific version to build")
    args = parser.parse_args()

    if args.arm:
        PLATFORMS.extend(ARM_PLATFORMS)

    main(save_to_file=args.file, testing=args.test, version=args.version)
