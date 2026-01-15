import argparse
import json
import os

from common import BASE_IMAGES, IS_GA, versions_dict


def main(version: str) -> None:
    """
    Generate metadata for the given version to be used in CI steps.
    """
    version_info = versions_dict()[version]

    tags = sorted(
        [f"{bi}:{version}" for bi in BASE_IMAGES]
        + [f"{bi}:{tag}" for bi in BASE_IMAGES for tag in version_info["extra_tags"]]
    )

    output_data = {
        "release_tag": version,
        "prerelease": version_info["prerelease"],
        "release_body": f"Release for webtrees version {version}: https://github.com/fisharebest/webtrees/releases/tag/{version}\n\nTags pushed:\n{'\n'.join(f'- {tag}' for tag in tags)}",
        "base_images": BASE_IMAGES,
        "tags": ",".join(tags),
    }

    if IS_GA:
        with open(os.environ["GITHUB_OUTPUT"], "w") as fp:
            fp.write(f"metadata={json.dumps(output_data)}")
    else:
        print(json.dumps(output_data, indent=4))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", type=str, help="Specific version to build")
    args = parser.parse_args()

    main(version=args.version)
