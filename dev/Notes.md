# Notes

## Patches

To create a patch, download a release .zip file and extract.

Slice out the contents of `fetchLatestVersion` leaving
`return Site::getPreference('LATEST_WT_VERSION');`
in webtrees\app\Services\UpgradeService.php and make a copy.

Run

```powershell
git diff .\UpgradeService.php .\UpgradeServicePatched.php > .\UpgradeService.patch
```

in that folder.

Rename and copy into the repo. Update the dict in `versionchecker.py`.

## PHP Versions

<https://webtrees.net/download>

Also see <https://www.php.net/archive/2026.php#2026-10-21-5>

## Release Dates

<https://api.github.com/repos/fisharebest/webtrees/releases?per_page=20>

## Building Image

Example:

```powershell
uv run .\dev\baker.py --file --version 2.2.4
docker buildx bake webtrees
```
