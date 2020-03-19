import argparse
import getpass
import json
import os
import sys
import urllib.request

import github

# check if we're currently running from a github action
# if so, this is the string 'true'. Use json.loads() to convert it to a boolean
ACTION = json.loads(os.getenv("GITHUB_ACTIONS", default="false").lower())
WEBTREES_REPO = "fisharebest/webtrees"
MY_REPO = os.getenv("GITHUB_REPOSITORY", default="nathanvaughn/webtrees-docker")


def get_latest_versions(repo, number=5):
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
    # get all releses
    releases = repo.get_releases()
    for release in releases:
        # fore each release, check name
        if release.tag_name == name:
            release.delete_release()
            print("Release {} deleted".format(name))


def delete_tag(repo, name):
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
    # phrase we're looking for
    phrase = "ENV WEBTREES_VERSION="

    # read the data of the file
    with open("Dockerfile", "r") as f:
        data = f.readlines()
    # write out the file line by line
    with open("Dockerfile", "w") as f:
        for line in data:
            if line.startswith(phrase):
                # if the line starts with the desired phrase, overwrite
                f.write(phrase + version + "\n")
            else:
                f.write(line)


def commit_changes(repo, version):
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


def create_release(repo, version, prerelease):
    repo.create_git_release(
        version,
        version,
        "Automated release for webtrees version {}".format(version),
        draft=False,
        prerelease=prerelease,
    )


def main():
    # allow user to pass list of versions to force re-push
    parser = argparse.ArgumentParser()
    parser.add_argument("--forced", type=str, nargs="*")
    parser.add_argument("--dry", action="store_true")
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

            # create a release on github
            print("Creating release")
            create_release(repo, version_number, version_prerelease)

    sys.exit(0)


if __name__ == "__main__":
    main()
