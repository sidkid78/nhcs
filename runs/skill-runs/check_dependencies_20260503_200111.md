---
skill: check_dependencies
manifest: pyproject.toml
ecosystem: Python
generated: 2026-05-03 20:01:11
vulnerabilities: none
outdated: 5
---

# Dependency Audit Report

**Manifest:** `pyproject.toml`
**Ecosystem:** `Python`
**Package Manager:** `uv`
**Direct Dependencies:** `25` (`20` prod, `5` dev)
**Lockfile present:** `yes` (`uv.lock`)
**Audit tool:** `pip-audit (skipped due to environment issues)`

---

## 🔒 Security Vulnerabilities

**⚠️ Vulnerability check failed to run.**

The audit tool `pip-audit` failed because the current environment (Python 3.13) is incompatible with some project dependencies:
- `open3d==0.19.0` — only has wheels for Python 3.11 and 3.12.
- `contourpy==1.3.3` — failed resolution in a Python 3.13 environment.

To run a full security audit, consider running this in a Python 3.12 environment or updating the dependencies.

---

## ⚠️ Dependency Hygiene

| Issue | Package | Detail |
|-------|---------|--------|
| Unpinned / Loose | `gudhi`, `ripser`, `persim`, `hypernetx`, `networkx`, `torch`, `geoopt`, `sentence-transformers`, `pydantic`, `sqlitedict`, `jax`, `jaxlib`, `scipy`, `numpy`, `pylsl`, `simple-pid`, `open3d`, `pyzmq`, `pyyaml` | Almost all dependencies use `>=` without upper bounds in `pyproject.toml`. |
| Platform Incompatibility | `open3d` | Supports up to Python 3.12; current environment is 3.13. |
| Platform Incompatibility | `contourpy` | Issues detected with version 1.3.3 on Python 3.13. |

---

## 📦 Available Updates

### 🟡 Minor
| Package | Current | Latest | Dev? |
|---------|---------|--------|------|
| `mpmath` | `1.3.0` | `1.4.1` | No |

### 🟢 Patch
| Package | Current | Latest | Dev? |
|---------|---------|--------|------|
| `mistune` | `3.2.0` | `3.2.1` | No |
| `setuptools` | `81.0.0` | `82.0.1` | No |
| `tinycss2` | `1.4.0` | `1.5.1` | No |
| `tokenizers` | `0.22.2` | `0.23.1` | No |

---

## 🛠 Recommended Actions

Prioritized — do these first:

1. **[ENVIRONMENT]** Use Python 3.12 — `open3d` and other packages are not yet fully compatible with Python 3.13.
2. **[HYGIENE]** Pin dependencies — Add upper bounds to your dependencies in `pyproject.toml` (e.g., `numpy>=2.0.0,<3.0.0`) to avoid breaking changes from future major releases.
3. **[PATCH BATCH]** — Safe to run: `uv lock --upgrade` to update `mistune`, `setuptools`, `tinycss2`, and `tokenizers`.

---

## Execution Log
```bash
$ uv run pip-audit --format=json
error: Distribution `open3d==0.19.0 @ registry+https://pypi.org/simple` can't be installed because it doesn't have a source distribution or wheel for the current platform
hint: You're using CPython 3.13 (`cp313`), but `open3d` (v0.19.0) only has wheels with the following Python ABI tags: `cp311`, `cp312`

$ uv pip list --outdated
Package    Version Latest Type
---------- ------- ------ -----
mistune    3.2.0   3.2.1  wheel
mpmath     1.3.0   1.4.1  wheel
setuptools 81.0.0  82.0.1 wheel
tinycss2   1.4.0   1.5.1  wheel
tokenizers 0.22.2  0.23.1 wheel
```
