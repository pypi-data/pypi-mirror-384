# Cook book

## Manual build and upload

```
python -m build
```

```
python -m twine upload dist/sommify-0.5.{}*
```

## Automatic build and upload

```bash
git tag {VERSION}
git push origin --tags
```

TODO - automated script for check and build
```bash
build.sh
```