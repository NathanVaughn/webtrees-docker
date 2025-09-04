import argparse
import json
import os

from common import BASE_IMAGES, IS_GA, THIS_DIR, versions_dict

ROOT_DIR = os.path.dirname(THIS_DIR)
PLATFORMS = ["linux/amd64"]
ARM_PLATFORMS = ["linux/arm/v7", "linux/arm64"]


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
            tags = sorted(
                [f"{bi}:{version}" for bi in BASE_IMAGES]
                + [
                    f"{bi}:{tag}"
                    for bi in BASE_IMAGES
                    for tag in version_info["extra_tags"]
                ]
            )
        matrix_data.append(
            {
                "version": version,
                "php": version_info["php"],
                "upgrade_patch": version_info["upgrade_patch"],
                "tags": tags,
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
        webtrees_target["output"] = [{"type": "registry"}]
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


def main(save_to_file: bool, testing: bool, versions: list[str]) -> None:
    result = bake_file(versions=versions, testing=testing)

    if save_to_file:
        with open(os.path.join(ROOT_DIR, "docker-bake.json"), "w") as fp:
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
        PLATFORMS.extend(ARM_PLATFORMS)

    main(save_to_file=args.file, testing=args.test, versions=args.versions)
