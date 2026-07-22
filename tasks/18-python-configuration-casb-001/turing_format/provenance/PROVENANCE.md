# Provenance - python-configuration-casb-001

This task is built on the real, unmodified upstream **python-configuration**
project (imported as `config`) plus a single scaffolding commit that adds the
(unimplemented) feature stub, a documentation page, and the visible utility
tests. Everything needed to verify that the baseline came from upstream is in
this directory.

## Upstream

- Repository: https://github.com/tr11/python-configuration
- License: MIT (see upstream `LICENSE`)
- Release: **0.12.1**
- Upstream commit: `75137c6f476c52f4232abd447962665a12ab7aee` (tag `0.12.1`)
- The importable package is upstream's `src/config`.

## Task baseline

- Pristine commit: `7faaf0303bd7c1d8ebe56763a36596c73d78734a`
- Pristine tree:   `79411dd7622636ef0d0f881fcb949fdcd9e71ced`
- Base commit:     `b1716134bd38e9de4b67d150c3766a0ab7b0bb61`
- Base tree:       `550a748517ba52cb8a2134c1f1292ac5f9d8cb88`
- Scaffolding commit message:
  `Add build_effective_report stub, layered-configuration doc, and visible utility tests (feature unimplemented)`

### Pristine layout

The importable `config` package is upstream `src/config`, with two
adjustments that reflect how the package is distributed rather than how it is
kept in git:

- `config/_version.py` is the setuptools-scm generated version file, pinned to
  `0.12.1`. Upstream generates it at build time and does not track it in git
  (its `config/.gitignore` excludes it). The pinned file is carried in this
  directory as `_version.py`.
- `config/.gitignore` (which excludes `_version.py` and `__pycache__`) is not
  shipped in the packaged tree.

### Scaffolding commit

The scaffolding commit adds these files and modifies none of the upstream
package:

| File | Purpose |
| --- | --- |
| `config_report.py` | `build_effective_report(cfg_set, layer_names)`; body raises `NotImplementedError` |
| `docs/layered_configuration.md` | the discoverable layered-configuration doc |
| `tests/pyconf_helpers.py` | shared fixtures for the visible tests |
| `tests/utility/test_U*.py` | the four visible utility tests |

`baseline.patch` in this directory is `git diff <pristine_commit> <base_commit>`.

## How to verify

```bash
bash reconstruct.sh /tmp/pyconf_recon
```

This clones upstream at the pinned `0.12.1` commit (with `core.autocrlf=false`,
`core.eol=lf`), lays out the pristine `config` package (dropping the upstream
`config/.gitignore` and adding the pinned `_version.py`), commits it, applies
`baseline.patch`, commits the scaffolding, and checks that the reconstructed
pristine and base tree hashes equal `79411dd7...` and `550a7485...`
respectively. Matching tree hashes prove the shipped `repo/src/` baseline is
upstream 0.12.1 plus only the declared scaffolding.

To confirm the shipped checkout matches the reconstruction byte-for-byte:

```bash
diff -rq --exclude=.git --exclude=__pycache__ /tmp/pyconf_recon/build ../repo/src
```
