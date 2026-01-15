import argparse
import subprocess

from common import BASE_IMAGES, IS_GA


def main(tags: list[str], hash: str) -> None:
    for base_image in BASE_IMAGES:
        cmd = ["docker", "buildx", "imagetools", "create", "--append"]

        for tag in [tag for tag in tags if tag.startswith(base_image)]:
            cmd.extend(["-t", tag])

        cmd.append(f"{base_image}@{hash}")

        print(" ".join(cmd))

        if IS_GA:
            subprocess.run(cmd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("tags", type=str)
    parser.add_argument("hash", type=str)
    args = parser.parse_args()

    main(tags=args.tags.split(","), hash=args.hash)
