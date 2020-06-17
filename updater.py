import argparse
import getpass
import json
import os
import subprocess
import sys
import urllib.request

import github

# check if we're currently running from a github action
# if so, this is the string 'true'. Use json.loads() to convert it to a boolean
ACTION = json.loads(os.getenv("GITHUB_ACTIONS", default="false").lower())
WEBTREES_REPO = "fisharebest/webtrees"
MY_REPO = os.getenv("GITHUB_REPOSITORY", default="nathanvaughn/webtrees-docker")

CONTAINER = "nathanvaughn/webtrees"
PLATFORMS = os.getenv("BUILDX_PLATFORMS", "linux/amd64,linux/arm/v7,linux/arm64")


def get_latest_versions(repo, number=5):
    """Get latest versions from a repository releases"""
    # build url
    url = "https://api.github.com/repos/{}/releases".format(repo)
    # download data
    data = urllib.request.urlopen(url)
    # parse json
    json_data = json.loads(data.read().decode())
    # only get the latest items
    latest_releases = json_data[0:number]
    return latest_releases


def delete_release(repo, name):
    """Delete a release from a repository"""
    # get all releses
    releases = repo.get_releases()
    for release in releases:
        # fore each release, check name
        if release.tag_name == name:
            release.delete_release()
            print("Release {} deleted".format(name))


def delete_tag(repo, name):
    """Delete a tag from a repository"""
    name = "tags/{}".format(name)

    try:
        # try to delete the ref for the tag we care about
        ref = repo.get_git_ref(name)
        ref.delete()
        print("Ref {} deleted".format(name))
        return True

    except github.UnknownObjectException:
        # 404
        print("Ref {} not found".format(name))

        print("Refs:")
        for ref in repo.get_git_refs():
            print(ref.ref)

        print("Tags:")
        for tag in repo.get_tags():
            print(tag.name)

        return False


def update_dockerfile(version):
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


def commit_changes(repo, version):
    """Commit and push changes to a repository"""
    # get the blob SHA of the file we're updating
    sha = repo.get_contents("Dockerfile").sha
    # read the local contents in
    with open("Dockerfile", "r") as f:
        content = f.read()
    # update
    repo.update_file(
        "Dockerfile",
        "Automated Dockerfile update for webtrees version {}".format(version),
        content,
        sha,
    )


def create_release(repo, version, prerelease, url):
    """Create a release for a repository"""
    repo.create_git_release(
        version,
        version,
        "Automated release for webtrees version {}: {}".format(version, url),
        draft=False,
        prerelease=prerelease,
    )


def get_tags(version_number):
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


def build_image(tags, basic=False):
    """Build the Docker image"""
    tagging = " ".join(["--tag {}:{}".format(CONTAINER, tag) for tag in tags])

    if not basic:
        build_command = 'docker buildx build . --build-arg BUILD_DATE=`date -u +"%Y-%m-%dT%H:%M:%SZ"` --build-arg VCS_REF=`git rev-parse --short HEAD` --push --platform {} {}'.format(
            PLATFORMS, tagging
        )
    else:
        build_command = 'docker build . --build-arg BUILD_DATE=`date -u +"%Y-%m-%dT%H:%M:%SZ"` --build-arg VCS_REF=`git rev-parse --short HEAD` {}'.format(
            tagging
        )

    print(build_command)
    subprocess.run(build_command, shell=True, check=True)

    if basic:
        for tag in tags:
            subprocess.run("docker push {}:{}".format(CONTAINER, tag), shell=True)


def main():
    # allow user to pass list of versions to force re-push
    parser = argparse.ArgumentParser()
    parser.add_argument("--forced", type=str, nargs="*")
    parser.add_argument("--dry", action="store_true")
    parser.add_argument("--basic", action="store_true")
    args = parser.parse_args()

    # get the latest versions of each repo
    webtrees_versions = get_latest_versions(WEBTREES_REPO)
    my_versions = get_latest_versions(MY_REPO, 20)

    missing_versions = []

    # go through each version of webtrees
    for version in webtrees_versions:
        version_number = version["name"]

        # check if version is a forced one
        if args.forced and any(v == version_number for v in args.forced):
            # if not, add to list of missing versions
            print("Version {} forcefully added.".format(version_number))
            missing_versions.append(version)

        # check if the version number exists in any of the releases from my repo
        elif not any(v["name"] == version_number for v in my_versions):
            # if not, add to list of missing versions
            print("Version {} missing.".format(version_number))
            missing_versions.append(version)

        # else, skip
        else:
            print("Version {} found.".format(version_number))

    # if there are missing versions, process them
    if missing_versions and not args.dry:
        if ACTION:
            # get environment variable for token
            TOKEN = os.environ["GITHUB_TOKEN"]
        else:
            # if not action, prompt user for token
            TOKEN = getpass.getpass(prompt="GitHub Token: ")

        # initialize connection to github
        g = github.Github(TOKEN)
        repo = g.get_repo(MY_REPO)

        for version in missing_versions:
            version_number = version["name"]
            version_prerelease = version["prerelease"]
            version_url = version["html_url"]

            if args.forced:
                # delete an existing release
                print("Deleting release for version {}".format(version_number))
                delete_release(repo, version_number)

                # also delete the tag
                print("Deleting tag {}".format(version_number))
                delete_tag(repo, version_number)

            # update the Dockerfile
            print("Updating Dockerfile for version {}".format(version_number))
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

    sys.exit(0)


if __name__ == "__main__":
    main()
