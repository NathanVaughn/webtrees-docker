import argparse
import datetime
import getpass
import json
import os
import subprocess
import sys
import urllib.request
from typing import List, Tuple

import github
import github.Repository

# check if we're currently running from a github action
# if so, this is the string 'true'. Use json.loads() to convert it to a boolean
ACTION = json.loads(os.getenv("GITHUB_ACTIONS", default="false").lower())
WEBTREES_REPO = "fisharebest/webtrees"
MY_REPO = os.getenv("GITHUB_REPOSITORY", default="nathanvaughn/webtrees-docker")

IMAGES = [
    "docker.io/nathanvaughn/webtrees",
    "ghcr.io/nathanvaughn/webtrees",
    "cr.nthnv.me/library/webtrees",
]
PLATFORMS = os.getenv("BUILDX_PLATFORMS", "linux/amd64,linux/arm/v7,linux/arm64")


def get_latest_versions(
    repo: str, number: int = 5, check_assets: bool = False
) -> List[dict]:
    """Get latest versions from a repository releases"""
    # build url
    url = f"https://api.github.com/repos/{repo}/releases"
    # download data
    data = urllib.request.urlopen(url)
    # parse json
    json_data = json.loads(data.read().decode())
    # only get the latest items
    latest_releases = json_data[:number]

    # skip releases with no assets
    if check_assets:
        for release in latest_releases:
            if not release["assets"]:
                latest_releases.remove(release)

    return latest_releases


def delete_release(repo: github.Repository.Repository, name: str) -> None:
    """Delete a release from a repository"""
    # get all releses
    releases = repo.get_releases()
    for release in releases:
        # fore each release, check name
        if release.tag_name == name:
            release.delete_release()
            print(f"Release {name} deleted")


def delete_tag(repo: github.Repository.Repository, name: str) -> bool:
    """Delete a tag from a repository"""
    name = f"tags/{name}"

    try:
        # try to delete the ref for the tag we care about
        ref = repo.get_git_ref(name)
        ref.delete()
        print(f"Ref {name} deleted")
        return True

    except github.UnknownObjectException:
        # 404
        print(f"Ref {name} not found")

        print("Refs:")
        for ref in repo.get_git_refs():
            print(ref.ref)

        print("Tags:")
        for tag in repo.get_tags():
            print(tag.name)

        return False


def update_dockerfile(version: str) -> None:
    """Update the Dockerfile with a new webtrees version number"""
    # read the data of the file
    with open("Dockerfile", "r") as f:
        data = f.readlines()
    # write out the file line by line
    with open("Dockerfile", "w") as f:
        # phrase we're looking for
        phrase = "ENV WEBTREES_VERSION="

        for line in data:
            if line.startswith(phrase):
                # if the line starts with the desired phrase, overwrite
                f.write(phrase + version + "\n")
            else:
                f.write(line)


def commit_changes(repo: github.Repository.Repository, version: str) -> None:
    """Commit and push changes to a repository"""
    # get the blob SHA of the file we're updating
    sha = repo.get_contents("Dockerfile").sha  # type: ignore
    # read the local contents in
    with open("Dockerfile", "r") as f:
        content = f.read()
    # update
    repo.update_file(
        "Dockerfile",
        f"Automated Dockerfile update for webtrees version {version}",
        content,
        sha,
    )


def create_release(
    repo: github.Repository.Repository, version: str, prerelease: bool, url: str
) -> None:
    """Create a release for a repository"""
    try:
        repo.create_git_release(
            version,
            version,
            f"Automated release for webtrees version {version}: {url}",
            draft=False,
            prerelease=prerelease,
        )
    except:
        print("Release could not be created, ignore")


def get_tags(version_number: str) -> List[str]:
    """Get comma separated tags for a version number"""
    if "alpha" in version_number:
        tag = "latest-alpha"
    elif "beta" in version_number:
        tag = "latest-beta"
    elif version_number.startswith("1."):
        tag = "latest-legacy"
    else:
        tag = "latest"

    return [tag, version_number]


def build_image(tags: List[str], basic: bool = False) -> None:
    """Build the Docker image"""

    # build the list of tags
    # ex:
    # - docker.io/nathanvaughn/webtrees:latest
    # - docker.io/nathanvaughn/webtrees:2.0.0
    # - ghcr.io/nathanvaughn/webtrees:latest
    # - ghcr.io/nathanvaughn/webtrees:2.0.0
    tagging_list = []
    for image in IMAGES:
        tagging_list.extend(f"{image}:{tag}" for tag in tags)

    # join everything together into a big command with a --tag for each tag
    tagging_cmd = " ".join(f"--tag {tagging}" for tagging in tagging_list)

    # prepare the building command
    if basic:
        build_command = f"docker build . {tagging_cmd}"
    else:
        build_command = (
            f"docker buildx build . --push --platform {PLATFORMS} {tagging_cmd}"
        )

    # build the image
    print(build_command)
    subprocess.run(build_command, shell=True, check=True)

    if basic:
        # push all the tags
        for tagging in tagging_list:
            push_command = f"docker push {tagging}"
            print(push_command)
            subprocess.run(push_command, shell=True)


def main():
    # allow user to pass list of versions to force re-push
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--forced", type=str, nargs="*"
    )  # forcefully add specific versions
    parser.add_argument("--dry", action="store_true")  # only perform a dry run
    parser.add_argument(
        "--check", action="store_true"
    )  # only check for updates and output true/false
    parser.add_argument("--basic", action="store_true")  # only x86 builds
    args = parser.parse_args()

    # get the latest versions of each repo
    webtrees_versions = get_latest_versions(WEBTREES_REPO, check_assets=True)
    my_versions = get_latest_versions(MY_REPO, 20)

    missing_versions = []

    # go through each version of webtrees
    for version in webtrees_versions:
        version_number = version["name"]

        # check if version is a forced one
        if args.forced and any(v == version_number for v in args.forced):
            # if so, add to list of missing versions
            if not args.check:
                print(f"Version {version_number} forcefully added.")
            missing_versions.append(version)

        # check if the version number exists in any of the releases from my repo
        elif not any(v["name"] == version_number for v in my_versions):
            # if not, add to list of missing versions
            if not args.check:
                print(f"Version {version_number} missing.")
            missing_versions.append(version)

        # else, skip
        else:
            if not args.check:
                print(f"Version {version_number} found.")

    # if there are missing versions, process them
    if missing_versions and not args.dry and not args.check:
        if ACTION:
            # get environment variable for token
            TOKEN = os.environ["GITHUB_TOKEN"]
        else:
            # if not action, prompt user for token
            TOKEN = getpass.getpass(prompt="GitHub Token: ")

        # initialize connection to github
        g = github.Github(TOKEN)
        repo = g.get_repo(MY_REPO)

        # needed so the highest version goes last, and overwrites
        # the latest tag
        missing_versions = sorted(missing_versions, key=lambda d: d["name"])

        for version in missing_versions:
            version_number = version["name"]
            version_prerelease = version["prerelease"]
            version_url = version["html_url"]

            if args.forced:
                # delete an existing release
                print(f"Deleting release for version {version_number}")
                delete_release(repo, version_number)

                # also delete the tag
                print(f"Deleting tag {version_number}")
                delete_tag(repo, version_number)

            # update the Dockerfile
            print(f"Updating Dockerfile for version {version_number}")
            update_dockerfile(version_number)

            # commit the changes to the file
            print("Committing changes")
            commit_changes(repo, version_number)

            # build and push image
            print("Building and pushing image")
            tags = get_tags(version_number)
            build_image(tags, basic=args.basic)

            # create a release on github
            print("Creating release")
            create_release(repo, version_number, version_prerelease, version_url)

    if args.check:
        print(str(bool(missing_versions)).lower())


if __name__ == "__main__":
    main()
    sys.exit(0)
