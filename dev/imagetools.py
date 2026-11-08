import argparse
import glob
import json
import os
import subprocess

from common import BASE_IMAGES, IS_GA


def main(tags: list[str]) -> None:
    """
    Update the image index with the given tags pointing to the given hash.
    """
    hashes = []

    # read the hashes from the downloaded build metadata files
    for metadata_file in glob.glob(
        os.path.join(
            os.environ.get("GITHUB_WORKSPACE", os.getcwd()), "**", "build-metadata.json"
        )
    ):
        with open(metadata_file, "r") as f:
            metadata = json.load(f)
            hashes.append(metadata["webtrees"]["containerimage.digest"])

    # create manifest for each base image
    for base_image in BASE_IMAGES:
        cmd = ["docker", "buildx", "imagetools", "create"]

        for tag in [tag for tag in tags if tag.startswith(base_image)]:
            cmd.extend(["-t", tag])

        for hash in hashes:
            cmd.append(f"{base_image}@{hash}")

        print(" ".join(cmd))

        if IS_GA:
            subprocess.run(cmd, check=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("tags", type=str)
    args = parser.parse_args()

    main(tags=args.tags.split(","))
