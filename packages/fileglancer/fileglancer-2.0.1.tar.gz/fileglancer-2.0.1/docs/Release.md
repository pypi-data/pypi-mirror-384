# Making a new release of Fileglancer

Make sure to do a clean build before building the package for release:

```bash
./clean.sh
pixi run dev-install
pixi run node-build
```

Bump the version using `hatch`. The current version is visible in `package.json`. See the docs on [hatch-nodejs-version](https://github.com/agoose77/hatch-nodejs-version#semver) for details.<br/>
**Note**: you will need to manually update the version in `package-lock.json`.

```bash
pixi run set-version <new-version>
```

Build the distribution bundle:

```bash
pixi run pypi-build
```

To upload the package to the PyPI, you'll need one of the project owners to add you as a collaborator. After setting up your access token, do:

```bash
pixi run pypi-upload
```

The new version should now be [available on PyPI](https://pypi.org/project/fileglancer/).

Now [draft a new release](https://github.com/JaneliaSciComp/fileglancer/releases/new). Create a new tag that is the same as the version number, and set the release title to the same (e.g. "1.0.0". Click on "Generate release notes" and make any necessary edits. Ideally, you should include any release notes from the associated [fileglancer-central](https://github.com/JaneliaSciComp/fileglancer-central) release.

## Other documentation

- [Development](Development.md)
