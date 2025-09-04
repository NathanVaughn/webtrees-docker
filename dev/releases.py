import argparse
import json
import os

from common import BASE_IMAGES, IS_GA, versions_dict


def main(versions: list[str]) -> None:
    release_data = []

    for version in versions:
        version_info = versions_dict()[version]

        tags = sorted(
            [f"{bi}:{version}" for bi in BASE_IMAGES]
            + [
                f"{bi}:{tag}"
                for bi in BASE_IMAGES
                for tag in version_info["extra_tags"]
            ]
        )

        release_data.append(
            {
                "tag": version,
                "prerelease": version_info["prerelease"],
                "body": f"Release for webtrees version {version}: https://github.com/fisharebest/webtrees/releases/tag/{version}\nTags pushed:\n{'\n'.join(f'- {tag}' for tag in tags)}",
            }
        )

    output_data = {"include": release_data}

    if IS_GA:
        with open(os.environ["GITHUB_OUTPUT"], "w") as fp:
            fp.write(f"matrix={json.dumps(output_data)}")
    else:
        print(json.dumps(output_data, indent=4))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--versions",
        type=str,
        nargs="*",
        default=[],
        help="Specific versions to include",
    )
    args = parser.parse_args()

    main(versions=args.versions)
