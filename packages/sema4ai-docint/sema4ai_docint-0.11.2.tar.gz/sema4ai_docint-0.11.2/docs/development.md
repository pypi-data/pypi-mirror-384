# Development guides

## Requires

- Python 3.12 or 3.13
- uv 0.8 or later
- invoke 2.2.0 or later

## Develop

`inv -l`:
- `inv install` : Get dependencies
  - `inv install --update` : Update lock file (CVE updates)
- `inv build`
- `inv test`
- `inv set-version a.b.c`: Update the library version numbers
- `inv check-all` : Run all checks
- `inv sync_wheel` : Copy the wheel to actions folders

👉 Add stuff to ./CHANGELOG.md `Unreleased` section as you develop, `Publish` below will set the version headers 

## Publish
- Update [docs/ChangeLog.md](./docs/CHAngeLOG.md)
- `inv set-version a.b.c`: Updates the library version numbers and changelog
- `inv make-release` : Create a release tag
- Publish to PyPI only via GHA: https://github.com/Sema4AI/document-intelligence/actions/workflows/library_release.yml
  - Correct tag triggers GHA runs  
