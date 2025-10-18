# Releasing

This project uses `setuptools-scm`. The version comes from the tag.

## Steps
1. Land commits on `main`.
2. Tag the release:
   ```bash
   git tag -a vX.Y.Z -m vX.Y.Z
   git push origin vX.Y.Z
