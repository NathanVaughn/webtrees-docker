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
