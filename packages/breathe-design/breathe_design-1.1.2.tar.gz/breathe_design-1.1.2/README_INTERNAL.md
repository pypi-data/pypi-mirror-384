# Release public repo (docs and examples)

This repo is private, and not intended to be shown to customers.

Instead, there is another public repo that IS intended to be shown to customers.  This public repo is a submodule of this repo for the purposes of this release machinary only.

The scripts in [public_release_scripts](public_release_scripts) manage releasing (copying) select files from this repo, to that public repo.

Run

```
python public_release_scripts\create_public_release.py
```

to perform the release.  This will clone the public repo into a folder `public_repo`, create a new branch, copy the new files accross, commit and push the branch.  It will open an MR to merge the public documents (this step requires a GitHub token though - you can skip it and do it manually).

You will have an option to inspect the contents of `public_repo` before it is committed and pushed, in order to check the contents is correct before it is made public.

**This step must currently be run manually until the gitlab CI step is fixed**

# Release wheel

The wheel generates by this repo is uploaded to out private repository in JFrog, and also to the public PyPi repository.

On MRs, the wheel is optionally (via a manual CI step) released to `https://test.pypi.org/legacy/`.
See [buildAndUploadPackageToTestPypi.ps1](buildAndUploadPackageToTestPypi.ps1) for

# Changelogs

[CHANGELOG.md](CHANGELOG.md) is an internal changelog.  Note your changes in here as normal, for a developer audience.

[PUBLIC_CHANGELOG.md](PUBLIC_CHANGELOG.md) is a PUBLIC changelog.  It is copied to the public repo on release, so must be worded as for a public audience.

# Troubleshooting

See the [TROUBLESHOOTING.md](TROUBLESHOOTING.md) file for troubleshooting errors.
