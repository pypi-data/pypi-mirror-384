# CHANGELOG

<!-- version list -->

## v1.0.2 (2025-10-16)

### Bug Fixes

- Explicitly enable release steps in semantic-release workflow
  ([`bd6857b`](https://github.com/undo76/loppers/commit/bd6857b29e2a3fc40c06324e7b5c70fdb6964de4))

### Chores

- **release**: Update version to 1.0.1 in pyproject.toml
  ([`b752a3f`](https://github.com/undo76/loppers/commit/b752a3fdb63ec21243d97cf508312a1f716a9979))


## v1.0.1 (2025-10-16)

### Bug Fixes

- Disable build in semantic-release action
  ([`4e7bdcb`](https://github.com/undo76/loppers/commit/4e7bdcba2a7e9159feb6953385a607c992cbed29))

- Install build tool with pip before semantic-release runs
  ([`6dbb52f`](https://github.com/undo76/loppers/commit/6dbb52fffbe27df5030c2b49e210ebda0ebf80c8))

- Update semantic release configuration for uv package manager
  ([`9c80239`](https://github.com/undo76/loppers/commit/9c802394f152056221038e33a0ca3580a4ee8461))

- Use .venv/bin/python for build command in GitHub Actions
  ([`1249711`](https://github.com/undo76/loppers/commit/12497119d121e2fcf3b96dcefb5dc33d4f1391fd))

- Use python -m build directly in semantic-release build command
  ([`a98dfa3`](https://github.com/undo76/loppers/commit/a98dfa308ddc82b222d54994bef403010cb1d5ba))

### Chores

- Update lock file and changelog from release
  ([`b083952`](https://github.com/undo76/loppers/commit/b083952440a2924d69c965bbbed6dfd05c6bde46))

- **release**: Update version to 1.0.0 and enable PyPI publishing
  ([`56b1246`](https://github.com/undo76/loppers/commit/56b12463432a0ba044ad2096518ed76feb3c6054))

### Documentation

- Add release and publishing instructions
  ([`5062fc1`](https://github.com/undo76/loppers/commit/5062fc152933ab6f6bdfcf9b16c2c92e9fab178f))


## v1.0.0 (2025-10-16)

### Bug Fixes

- Update semantic release build command to use python -m build
  ([`5c54566`](https://github.com/undo76/loppers/commit/5c545667d6a30c5ec52c384775f298b6d597d3ab))

### Features

- Add CLI tool for concatenating files with skeleton extraction
  ([`c8d459d`](https://github.com/undo76/loppers/commit/c8d459d4ba1bc95e9ce67218a108a92c819d05af))

- Add Python Semantic Release for automated versioning
  ([`39b661b`](https://github.com/undo76/loppers/commit/39b661b8dfeff1f9d430c21598d5b2323b204b11))

### Refactoring

- Simplify header format in concatenate_files
  ([`4e51ef3`](https://github.com/undo76/loppers/commit/4e51ef36c782c2b3fc265bbfa6b8b6d8a1bdea4d))


## v0.1.0 (2025-10-16)

- Initial Release
