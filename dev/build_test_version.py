import argparse
import os
import subprocess
import sys

from baker import WEBTREES_PATCH, WEBTREES_PHP

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_FILE = os.path.join(ROOT_DIR, "dev", ".last_built_version")


def main(webtrees_version: str) -> None:
    with open(CACHE_FILE, "w") as fp:
        fp.write(f"{webtrees_version}\n")

    # uncomment the next line to build for arm64
    subprocess.run(
        [
            "docker",
            # "buildx",
            "build",
            # "--platform",
            # "linux/arm64",
            "--build-arg",
            f"WEBTREES_VERSION={webtrees_version}",
            "--build-arg",
            f"PHP_VERSION={next(v for k, v in WEBTREES_PHP.items() if webtrees_version.startswith(k))}",
            "--build-arg",
            f'PATCH_VERSION={WEBTREES_PATCH.get(webtrees_version, WEBTREES_PATCH["default"])}',
            "-t",
            "webtrees:test",
            ".",
        ],
        cwd=os.path.join(ROOT_DIR, "docker"),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--webtrees_version")
    args = parser.parse_args()

    if not args.webtrees_version:
        # try to load last version
        last_version = ""
        if os.path.isfile(CACHE_FILE):
            with open(CACHE_FILE, "r") as fp:
                last_version = fp.read().strip()

        # show last version as default
        prompt = "enter the desired webtrees version"
        if last_version:
            prompt = f"{prompt} ({last_version})"

        # see if user entered anything
        args.webtrees_version = input(f"{prompt}: ") or last_version

    if not args.webtrees_version:
        sys.exit()

    main(args.webtrees_version)
