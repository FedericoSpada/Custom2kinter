Development on `/develop` branch.
- create Pull Requests following these guidelines:
  - 1 feature <=> 1 PR: do not condese in a single Pull Requests different changes
  - do not leave commented code: if you need to remove an entire section, just delete it
  - do not add comments that refer to how the code was: "changed", "fixed", "it wasn't present" do not provide useful info and must be avoided
- merge external pull requests into `/develop`
- implement features, fix bugs on `/develop`
- update changelog in `CHANGELOG.md`
- test on all platforms for new graphical features

When ready: Bump version using `tbump`:
```
tbump 5.2.3
```

Create pull request to merge `/develop` into `/master` branch on Github.
- approval by owner, merge to `/master`


Publish new version to PyPI:
```
python -m pip install --upgrade build
python -m pip install --upgrade twine
rm -r dist
python -m build
python -m twine upload dist/*
```
Finally: Update documentation for new features.
