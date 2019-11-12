import datetime
import json
import os
import subprocess
import sys
import urllib.request

from github import Github

WEBTREES_REPO = "fisharebest/webtrees"
MY_REPO = os.environ["GITHUB_REPOSITORY"]


def get_latest_versions(repo, number=3):
    url = "https://api.github.com/repos/{}/releases".format(repo)
    data = urllib.request.urlopen(url)
    json_data = json.loads(data.read().decode())
    latest_releases = json_data[0:number]

    data = []
    for release in latest_releases:
        data.append({"number": release["name"], "prerelease": release["prerelease"]})

    return data


def update_dockerfile(version):
    phrase = "ENV WEBTREES_VERSION="

    with open("Dockerfile", "r") as f:
        data = f.readlines()
    with open("Dockerfile", "w") as f:
        for line in data:
            if line.startswith(phrase):
                f.write(phrase + version + "\n")
            else:
                f.write(line)


def setup_git():
    subprocess.call(["git", "config", "credential.helper", "store"])
    subprocess.call(["git", "config", "user.name", os.environ["GITHUB_ACTOR"]])
    subprocess.call(
        [
            "git",
            "config",
            "user.email",
            os.environ["GITHUB_ACTOR"] + "@users.noreply.github.com",
        ]
    )

    with open(os.path.join(os.environ["HOME"], ".git-credentials"), "w") as f:
        f.write(
            "https://{}:x-oauth-basic@github.com".format(os.environ["GITHUB_TOKEN"])
        )


def push_changes(version, prerelease):
    subprocess.call(["git", "add", "--all"])

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    automated_message = "Automated deployment: " + timestamp

    nice_message = "Update for Webtrees version " + version

    print(automated_message)
    print(nice_message)

    subprocess.call(["git", "pull", "origin", "master"])
    subprocess.call(["git", "commit", "-m", automated_message])
    subprocess.call(["git", "tag", "-a", version, "-m", nice_message])
    subprocess.call(["git", "push", "-u", "origin", "master"])

    g = Github(os.environ["GITHUB_TOKEN"])
    repo = g.get_repo(MY_REPO)
    repo.create_git_release(
        version, version, nice_message, draft=False, prerelease=prerelease
    )


def main():
    webtrees_versions = get_latest_versions(WEBTREES_REPO)
    my_versions = get_latest_versions(MY_REPO)

    for version in webtrees_versions:
        version_number = version["number"]
        version_prerelease = version["prerelease"]

        if version not in my_versions:
            print("Version {} missing, updating dockerfile.".format(version_number))

            update_dockerfile(version_number)
            setup_git()
            push_changes(version_number, version_prerelease)

            print("Dockerfile updated.")

        else:
            print("Version {} found. Skipping.".format(version_number))

    sys.exit(0)

if __name__ == "__main__":
    main()
