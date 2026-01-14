import argparse
import json
import subprocess

from common import BASE_IMAGES, IS_GA


def main(file: str) -> None:
    with open(file) as f:
        data = json.load(f)

    target = list(data.keys())[0]
    digest = data[target]["containerimage.digest"]
    tags = data[target]["image.name"].split(",")

    for base_image in BASE_IMAGES:
        cmd = ["docker", "buildx", "imagetools", "create", "--append"]

        for tag in [tag for tag in tags if tag.startswith(base_image)]:
            cmd.extend(["-t", tag])

        cmd.append(f"{base_image}@{digest}")

        print(" ".join(cmd))

        if IS_GA:
            subprocess.run(cmd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str)
    args = parser.parse_args()

    main(file=args.file)
