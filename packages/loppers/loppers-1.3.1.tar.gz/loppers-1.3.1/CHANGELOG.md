# CHANGELOG

## v1.3.1 (2025-10-17)

### Documentation

* docs: Add MIT license ([`81b26ee`](https://github.com/undo76/loppers/commit/81b26ee29d7ae25ea1fe40b4d2eba968e5937f9c))

### Fix

* fix: Use tsx language for .tsx ([`7bc72c9`](https://github.com/undo76/loppers/commit/7bc72c9f7e25b9d3d858b736d4db856c8be6a1c7))

## v1.3.0 (2025-10-16)

### Chore

* chore(release): 1.3.0 ([`734c69c`](https://github.com/undo76/loppers/commit/734c69cdd4d5813994c946d101468a528b48f3f2))

### Feature

* feat: Add support for 5 new programming languages

**New Languages:**
- Swift: Functions and methods with function_body extraction
- Lua: Functions with block extraction (end-based syntax)
- Scala: Functions and methods with block extraction
- Groovy: Methods with smart query-based filtering (excludes class bodies)
- Objective-C: Methods with compound_statement extraction

**Implementation:**
- Added language configs to LANGUAGE_CONFIGS in loppers.py (lines 115-144)
- Improved line removal logic to handle single-line and multi-line bodies correctly
- Added special handling for Lua&#39;s end-based syntax (not brace-based)
- Used pure query-based approach for all languages (no custom code needed)

**Testing:**
- Added 5 comprehensive test cases covering each language
- All 29 tests pass (24 existing + 5 new)

**Documentation:**
- Updated README.md: 12 → 17 supported languages
- Added language feature matrix for new languages
- Updated features list

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`65749ab`](https://github.com/undo76/loppers/commit/65749ab73c3991339267c668bf2b50f71f060653))

## v1.2.1 (2025-10-16)

### Chore

* chore(release): 1.2.1 ([`3279e26`](https://github.com/undo76/loppers/commit/3279e2690f9fc099ed01838bbe2386820a926740))

### Fix

* fix: Add hatchling version configuration

Configure tool.hatch.version to read from top-level version field in
pyproject.toml using regex pattern matching.

This allows:
- Hatchling to find the version when building
- semantic-release to update the top-level version field

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`f29c9c9`](https://github.com/undo76/loppers/commit/f29c9c9147f7310eebe1eff07214487b86cd7afd))

* fix: Use top-level version field for semantic-release

- Move version to top-level in pyproject.toml
- Mark version as dynamic in [project] section
- Use version_variables (plural) configuration
- This allows semantic-release to update version at top level

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`e08e3e9`](https://github.com/undo76/loppers/commit/e08e3e9ad637526d7ceaf8da3671c0e9894b3fde))

* fix: Configure semantic-release for proper version updates

- Use standard version_variable path: pyproject.toml:version
- Add explicit parser configuration for conventional commits
- Remove __version__ from __init__ (use pyproject.toml as single source)
- Keep build_command empty (publish workflow handles building)

This setup separates concerns:
- semantic-release: Updates version, creates tags/releases
- publish workflow: Builds and publishes to PyPI

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`2c51d6c`](https://github.com/undo76/loppers/commit/2c51d6ca0fb56720082854292deeedc217102328))

## v1.2.0 (2025-10-16)

### Chore

* chore(release): 1.2.0 ([`109852d`](https://github.com/undo76/loppers/commit/109852d327bd72514a3eb132c380cd84a7eb0b14))

### Feature

* feat: Add __version__ to package for semantic-release versioning

Add __version__ string to src/loppers/__init__.py that semantic-release
can update. This is more reliable than updating TOML files.

semantic-release will now update this version on releases.

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`9ada3a1`](https://github.com/undo76/loppers/commit/9ada3a17fa7c8caa04067a8d172b75d78dd074d4))

## v1.1.3 (2025-10-16)

### Chore

* chore(release): 1.1.3 ([`f979f10`](https://github.com/undo76/loppers/commit/f979f106261cc8ee97c6fd468ad515222db73e02))

### Fix

* fix: Correct version_variable path for semantic-release

The version in pyproject.toml is nested under [project], so the path
should be &#39;pyproject.toml:project.version&#39; not &#39;pyproject.toml:version&#39;.

This enables semantic-release to properly update the version during releases.

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`5a5cace`](https://github.com/undo76/loppers/commit/5a5cace625d76ba366f2d968156cf01b96a41768))

## v1.1.2 (2025-10-16)

### Chore

* chore(release): 1.1.2 ([`7508e2d`](https://github.com/undo76/loppers/commit/7508e2d5779a9b9fea23047d9bdebc1a2c403a85))

### Fix

* fix: Add git user configuration to semantic-release workflow

- Configure git user name and email for commit operations
- This allows semantic-release to commit version updates to pyproject.toml

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`8ec0384`](https://github.com/undo76/loppers/commit/8ec0384779dd572be28ad35143c8fda39dba75a7))

## v1.1.1 (2025-10-16)

### Chore

* chore(release): 1.1.1 ([`1e806e5`](https://github.com/undo76/loppers/commit/1e806e5f11ba8e39b59ca8f995a4a8da712d3f7c))

### Fix

* fix: Disable build in semantic-release, let publish workflow handle it

semantic-release runs in isolated environment without build dependencies.
The publish workflow already handles building (uv build) and publishing.

semantic-release should focus on:
- Updating version in pyproject.toml
- Creating CHANGELOG entries
- Creating git tags and GitHub releases

The publish workflow (on release published) will:
- Build the package (uv build)
- Publish to PyPI

This separation of concerns works better with the GitHub Actions ecosystem.

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`bb396be`](https://github.com/undo76/loppers/commit/bb396be3d7705c25c3fec37e19c389d12bcf94d7))

* fix: Use python -m build instead of uv build in semantic-release

The semantic-release action runs in its own environment where &#39;uv&#39; is not
available in PATH. Use &#39;python -m build&#39; which only requires the &#39;build&#39;
package (already available as a dev dependency).

This allows the build step to work properly during automated releases.

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`f0b5677`](https://github.com/undo76/loppers/commit/f0b5677e5369b5c48d6b2026a30798e0a6e19f9c))

* fix: Test semantic-release workflow with proper configuration

This test commit verifies:
- Stable version of semantic-release action (v9.8.3)
- Version variable update from pyproject.toml configuration
- Build command using uv build
- Proper environment variables for GitHub and PyPI

Expected outcome:
- Version bumped from 1.0.1 to 1.0.2 (patch bump for fix)
- CHANGELOG.md updated with this commit
- New GitHub release created (v1.0.2)
- Package built and published to PyPI

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`43e4cf4`](https://github.com/undo76/loppers/commit/43e4cf44ca32b813e0243bf30bc668f4d3636f4e))

* fix: Remove invalid build_command parameter from GitHub Action

The GitHub Action does not accept build_command as an input parameter.
The build_command is configured in pyproject.toml under [tool.semantic_release]
and will be read from there by the action.

Valid action parameters: entryPoint, args, root_options, directory, github_token,
git_committer_name, git_committer_email, ssh keys, prerelease, force, commit,
tag, push, changelog, vcs_release, build_metadata

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`f8732be`](https://github.com/undo76/loppers/commit/f8732be54a32ccd316b8b15379b5f61a311f71b8))

* fix: Simplify version_variable configuration for semantic-release

- Update version_variable back to simple format: &#34;pyproject.toml:version&#34;
- Add directory parameter to GitHub Action for clarity
- This should allow semantic-release to properly update the version field

The nested TOML path might not be supported by the Python semantic-release
action, so we&#39;re using the simpler format that maps to the top-level version
variable directly.

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`8139951`](https://github.com/undo76/loppers/commit/81399519a8e78740725e88dc107024fe22b3791c))

* fix: Fix semantic-release to properly update version in pyproject.toml

**Root causes fixed:**
1. Using unstable @master version of semantic-release action
2. Incorrect version_variable path (was &#34;pyproject.toml:version&#34;, should be &#34;pyproject.toml:project.version&#34;)
3. Using &#34;python -m build&#34; instead of &#34;uv build&#34;
4. Insufficient parameters in GitHub Action configuration

**Changes:**
- Update action to stable version: python-semantic-release/python-semantic-release@v9.8.3
- Fix version_variable path to proper TOML notation: pyproject.toml:project.version
- Update build_command to use uv: &#34;uv build&#34;
- Add proper environment variables: GH_TOKEN, PYPI_TOKEN
- Simplify GitHub Action parameters, relying on pyproject.toml config

**How it works now:**
1. Push commits to main with conventional commit format (feat:, fix:, etc.)
2. semantic-release detects version bump requirement
3. Automatically updates version in pyproject.toml:project.version
4. Builds package with &#34;uv build&#34;
5. Creates git tag and commits changes
6. Pushes to GitHub
7. Creates GitHub Release
8. Publishes to PyPI (via upload_to_pypi = true)

Next release will automatically update the version. No manual intervention needed!

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`d8cafd0`](https://github.com/undo76/loppers/commit/d8cafd08230116f13e692185ab4677345c928b12))

### Test

* test: Final test of semantic-release workflow

This commit tests the corrected workflow:
- semantic-release disables building (empty build_command)
- semantic-release updates version in pyproject.toml
- semantic-release creates GitHub release
- publish workflow will build and publish on release

Expected outcome:
- Version bumped in pyproject.toml
- CHANGELOG updated
- GitHub release created
- Publish workflow triggered automatically

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`03974e9`](https://github.com/undo76/loppers/commit/03974e95547997901325ef1c19268684b3b60d4d))

## v1.1.0 (2025-10-16)

### Chore

* chore(release): 1.1.0 ([`8f8a7e7`](https://github.com/undo76/loppers/commit/8f8a7e7290b39fdf5a749a5a7e309116610d27cc))

* chore: Update lock file ([`8449915`](https://github.com/undo76/loppers/commit/84499151633e5d951857f213422ab7dda1da1a7a))

* chore: Update lock file ([`b0ca406`](https://github.com/undo76/loppers/commit/b0ca4061a89baf2fed745b3780c8f3e11df53515))

### Documentation

* docs: Consolidate markdown files into README

**Removed files:**
- DEVELOPMENT.md → content moved to README Development section
- EXAMPLES.md → added Before/After Examples section
- HANDLED_CASES.md → merged into Supported Languages section

**Added to README:**
- &#34;Examples: Before and After&#34; section with Python, TypeScript, Java examples
- &#34;What Gets Preserved / Removed&#34; for clear feature list
- &#34;Known Limitations&#34; section
- Expanded language support table with specific features
- Updated Project Structure to reflect file changes

**Benefits:**
- Single source of truth (README.md)
- Easier to maintain documentation
- Better discovery of examples and limitations
- Reduced documentation fragmentation

**Kept files:**
- CHANGELOG.md - Release history
- CLAUDE.md - Claude Code development notes

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`c6eec28`](https://github.com/undo76/loppers/commit/c6eec28152542091c7b6bb6d14ff139b13051fdd))

* docs: Consolidate and improve README

**Major improvements:**
- Reorganized for better flow: features → quick start → CLI/API
- Added prominent CLI usage section with practical examples
- Better structured API reference with examples for each function
- Added supported languages table for quick reference
- Clearer &#34;How It Works&#34; section explaining tree-sitter queries
- Simplified development and publishing sections
- Added project structure diagram
- Explicit dependencies section
- Better references and links

**Structure:**
1. Quick intro with key capabilities
2. Features overview
3. Installation instructions
4. Quick Start (CLI, Python API examples)
5. Supported Languages (table format)
6. API Reference (organized by category)
7. How It Works (technical explanation)
8. Development (setup, testing, publishing)
9. Adding New Languages (step-by-step)
10. Project Structure
11. Dependencies
12. References

**Content improvements:**
- More practical CLI examples
- Better Python API examples
- Clearer parameter descriptions
- Language features documented in table
- Technical details in dedicated section
- Development workflow clarified

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`f4693e1`](https://github.com/undo76/loppers/commit/f4693e19bfdedea37540610f142ea74745eff860))

### Feature

* feat: Add Kotlin language support

- Add Kotlin to LANGUAGE_CONFIGS with tree-sitter queries
- Support .kt and .kts file extensions
- Extract function/method bodies, getters, and setters
- Add comprehensive Kotlin test case
- Create sample.kt file with various language constructs
- Update documentation and language count (11 → 12 languages)

Supported Kotlin features:
- Regular functions and top-level functions
- Extension functions
- Member functions in classes
- Property getters and setters
- Companion object methods
- Data class methods
- Type hints and signatures preserved

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`980ef26`](https://github.com/undo76/loppers/commit/980ef2632d9356cdf8cfd47f68b483de374b10f8))

* feat: Add directory and recursive traversal support to CLI

- Add `collect_files()` function to handle files and directories
- Support recursive directory traversal with -r/--recursive flag
- Auto-filter by supported file extensions
- Process files in sorted order for consistent output
- Improved CLI help text with examples for common use cases

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`3ec1d91`](https://github.com/undo76/loppers/commit/3ec1d91bae136c9bdc38f2bc9e61236922b0e478))

### Refactor

* refactor: Use binaryornot library for simpler binary file detection

- Replace filetype with binaryornot (lightweight, focused library)
- Simplify is_binary_file() to 4 lines with clear logic
- binaryornot uses proven detection methods:
  * Known binary file extensions
  * Null byte detection
  * UTF-8 decoding validation
- Remove complexity, use battle-tested library
- Update tests to match binaryornot&#39;s detection behavior
- Update documentation

**Advantages:**
- Simpler, more focused implementation
- Well-maintained library by David Wolever
- Smaller dependency footprint
- Same reliability with less code

**Tests:**
- 24/24 passing
- Binary detection tests use null bytes (what binaryornot checks for)
- All concatenation and extraction tests passing

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`efff379`](https://github.com/undo76/loppers/commit/efff379acc275bebfc521870a778ea744b3a3971))

* refactor: Use filetype library for robust binary file detection

- Add `filetype&gt;=1.2.0` to dependencies
- Replace custom binary detection with filetype library (magic bytes)
- Use multi-stage detection:
  1. Magic bytes analysis via filetype (most accurate)
  2. MIME type classification (text vs binary)
  3. UTF-8 decoding + null byte detection (fallback)
- Update is_binary_file() signature (removes chunk_size parameter)
- Update tests to use real file signatures:
  * PDF magic bytes for PDF detection
  * PNG/JPEG/GIF magic bytes for image detection
  * Real binary content with null bytes
- Better detection of actual file types vs extensions
- More reliable across different file types

**Benefits:**
- Robust detection based on file content, not just extension
- Supports 50+ file types natively via filetype
- Graceful fallback for unknown types
- Pure Python implementation (no system dependencies)

**Tests:**
- 24/24 passing
- All binary detection tests use real magic bytes
- Real PDF signatures, image magic bytes
- Null byte detection for edge cases

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`49e0d5c`](https://github.com/undo76/loppers/commit/49e0d5ca94e859b72a01c6bb224190e5753e8de9))

* refactor: Move file concatenation to library with binary file detection

- Create new `concatenator.py` module for file operations
- Add `is_binary_file()` function with multi-method detection:
  * Known binary extensions (.pdf, .jpg, .exe, .bin, etc.)
  * Null byte detection
  * UTF-8 decoding validation
- Move `concatenate_files()` and `collect_files()` from CLI to library
- Add `extract_skeletons` parameter to control skeleton extraction
- Auto-skip binary files, include all text files
- Support mixing files and directories in single call
- Add CLI flag `--no-extract` to include original file content
- Export new functions in __init__.py (7 public functions total)
- Add comprehensive test suite (10 new tests):
  * Binary file detection tests
  * File concatenation tests
  * Skeleton extraction integration tests
- Update API documentation with usage examples

**Breaking Changes:**
- `concatenate_files()` signature changed (added `extract_skeletons` parameter)
- Moved from `cli.py` to `concatenator.py` module

**Tests:**
- 24/24 passing (14 skeleton extraction + 10 new utility tests)

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`853b1b8`](https://github.com/undo76/loppers/commit/853b1b880e85af89b45caebcb4309b1f28a1824b))

## v1.0.2 (2025-10-16)

### Chore

* chore(release): 1.0.2 ([`d5b8dc2`](https://github.com/undo76/loppers/commit/d5b8dc22c6e781c550b21cd69f1de3976b5273f5))

* chore(release): Update version to 1.0.1 in pyproject.toml ([`b752a3f`](https://github.com/undo76/loppers/commit/b752a3fdb63ec21243d97cf508312a1f716a9979))

### Fix

* fix: Explicitly enable release steps in semantic-release workflow

Since build: false skips some steps, we need to explicitly enable:
- commit: update pyproject.toml with new version
- tag: create the version tag
- push: push changes to remote
- vcs_release: create GitHub release (triggers publish workflow) ([`bd6857b`](https://github.com/undo76/loppers/commit/bd6857b29e2a3fc40c06324e7b5c70fdb6964de4))

## v1.0.1 (2025-10-16)

### Chore

* chore(release): 1.0.1 ([`98ad447`](https://github.com/undo76/loppers/commit/98ad44743576c302e046fae272b504b00f49f9b1))

* chore(release): Update version to 1.0.0 and enable PyPI publishing ([`56b1246`](https://github.com/undo76/loppers/commit/56b12463432a0ba044ad2096518ed76feb3c6054))

* chore: Update lock file and changelog from release ([`b083952`](https://github.com/undo76/loppers/commit/b083952440a2924d69c965bbbed6dfd05c6bde46))

### Documentation

* docs: Add release and publishing instructions

- Added &#39;Release &amp; Publishing&#39; section with semantic-release guidance
- Documented prerequisites (GitHub token, PyPI token)
- Included commands for publishing to PyPI and manual builds
- Explained conventional commit format for auto-versioning

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`5062fc1`](https://github.com/undo76/loppers/commit/5062fc152933ab6f6bdfcf9b16c2c92e9fab178f))

### Fix

* fix: Disable build in semantic-release action

Semantic-release runs in a container and can&#39;t access the build tool. Since the publish.yml workflow handles building and publishing, we can disable building in semantic-release by setting build: false. ([`4e7bdcb`](https://github.com/undo76/loppers/commit/4e7bdcba2a7e9159feb6953385a607c992cbed29))

* fix: Install build tool with pip before semantic-release runs

The GitHub Actions workflow now explicitly installs &#39;build&#39; with pip to ensure it&#39;s available when semantic-release runs the build command. This avoids PATH issues with uv&#39;s virtual environment. ([`6dbb52f`](https://github.com/undo76/loppers/commit/6dbb52fffbe27df5030c2b49e210ebda0ebf80c8))

* fix: Use .venv/bin/python for build command in GitHub Actions

The &#39;uv sync&#39; workflow step creates a .venv directory. semantic-release needs to use the Python from that venv, not the system Python. ([`1249711`](https://github.com/undo76/loppers/commit/12497119d121e2fcf3b96dcefb5dc33d4f1391fd))

* fix: Use python -m build directly in semantic-release build command

When semantic-release runs the build command in GitHub Actions, &#39;uv&#39; is not in the PATH even though setup-uv was called. Since &#39;uv sync&#39; already installed all dependencies, we can run &#39;python -m build&#39; directly. ([`a98dfa3`](https://github.com/undo76/loppers/commit/a98dfa308ddc82b222d54994bef403010cb1d5ba))

* fix: Update semantic release configuration for uv package manager

- Update build command to use &#39;uv run python -m build&#39; instead of pip
- Add &#39;build&#39; to uv dev-dependencies so it&#39;s available in the environment

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`9c80239`](https://github.com/undo76/loppers/commit/9c802394f152056221038e33a0ca3580a4ee8461))

## v1.0.0 (2025-10-16)

### Chore

* chore(release): 1.0.0 ([`4c40d4f`](https://github.com/undo76/loppers/commit/4c40d4f5bf5337608f95446ba8a8f7e2ded1b425))

### Feature

* feat: Add CLI tool for concatenating files with skeleton extraction

- New `loppers` command-line tool to concatenate multiple files
- Extracts skeletons using language detection from file extensions
- Falls back to original content if extraction fails
- Supports custom separators and verbose output
- Files separated with headers indicating their names
- Output to stdout or file with --output flag

Usage:
  loppers file1.py file2.js
  loppers --output combined.txt *.py
  loppers --verbose --separator &#34;---&#34; src/**/*.py

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`c8d459d`](https://github.com/undo76/loppers/commit/c8d459d4ba1bc95e9ce67218a108a92c819d05af))

* feat: Add Python Semantic Release for automated versioning

- Configured python-semantic-release to automatically bump version
- Analyzes conventional commits (feat:, fix:, BREAKING CHANGE:)
- Creates releases and updates changelog automatically
- Uses uv for building packages
- Workflow triggers on push to main branch

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`39b661b`](https://github.com/undo76/loppers/commit/39b661b8dfeff1f9d430c21598d5b2323b204b11))

### Fix

* fix: Update semantic release build command to use python -m build

- Semantic release container doesn&#39;t have uv installed
- Changed build_command to use standard python build tools
- Allows semantic release workflow to complete successfully

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`5c54566`](https://github.com/undo76/loppers/commit/5c545667d6a30c5ec52c384775f298b6d597d3ab))

### Refactor

* refactor: Simplify header format in concatenate_files

- Changed header format from multi-line with separator to simple `--- path/to/file`
- Removed unused separator parameter from function signature
- Updated CLI to remove --separator option
- Makes output cleaner and more readable

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`4e51ef3`](https://github.com/undo76/loppers/commit/4e51ef36c782c2b3fc265bbfa6b8b6d8a1bdea4d))

## v0.1.0 (2025-10-16)

### Feature

* feat: Add GitHub Actions workflow for PyPI publishing

- Added publish.yml workflow that triggers on release
- Uses uv for package building
- Implements PyPI trusted publishers authentication
- Includes manual workflow_dispatch trigger

🤖 Generated with Claude Code

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`93bfb64`](https://github.com/undo76/loppers/commit/93bfb648742eb5dcfe6f2c6eacfca1866054a022))

### Unknown

* Initial commit ([`0d6114e`](https://github.com/undo76/loppers/commit/0d6114e87d53dda552e297f56256cef1d9c1618a))
