import datetime
import json
import os
import subprocess
import sys
import urllib.request

from github import Github

WEBTREES_REPO = "fisharebest/webtrees"
MY_REPO = os.environ["GITHUB_REPOSITORY"]


def get_latest_version(repo):
    url = "https://api.github.com/repos/{}/releases".format(repo)
    data = urllib.request.urlopen(url)
    json_data = json.loads(data.read().decode())
    latest_release = json_data[0]

    version = latest_release["name"]
    prerelease = latest_release["prerelease"]

    print("{} latest version: {}".format(repo, version))
    return version, prerelease


def determine_branch(version, prerelease):
    if not prerelease:
        return "master"
    elif "beta" in version:
        return "beta"
    elif "alpha" in version:
        return "alpha"


def checkout_branch(branch):
    subprocess.call(["git", "checkout", "-B", branch])


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

    with open(os.path.join(os.environ["HOME"], ".git-credentials", "w")) as f:
        f.write(
            "https://{}:x-oauth-basic@github.com".format(os.environ["GITHUB_TOKEN"])
        )


def push_changes(branch, version, prerelease):
    subprocess.call(["git", "add", "--all"])

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    automated_message = "Automated deployment: " + timestamp

    nice_message = "Update for Webtrees version " + version

    print(automated_message)
    print(nice_message)

    subprocess.call(["git", "commit", "-m", automated_message])
    subprocess.call(["git", "tag", "-a", version, "-m", nice_message])
    subprocess.call(["git", "push", "origin", branch])

    g = Github(os.environ["GITHUB_TOKEN"])
    repo = g.get_repo(MY_REPO)
    repo.create_git_release(
        version, version, nice_message, draft=False, prerelease=prerelease
    )


def main():
    webtrees_version, webtrees_prerelease = get_latest_version(WEBTREES_REPO)
    my_version, _ = get_latest_version(MY_REPO)

    if webtrees_version != my_version:
        print("Version mismatch, updating dockerfile")

        branch = determine_branch(webtrees_version, webtrees_prerelease)
        checkout_branch(branch)
        update_dockerfile(webtrees_version)
        setup_git()
        push_changes(branch, webtrees_version, webtrees_prerelease)
        sys.exit(0)

    else:
        print("Versions are same. Exiting.")
        sys.exit(1)


if __name__ == "__main__":
    main()
