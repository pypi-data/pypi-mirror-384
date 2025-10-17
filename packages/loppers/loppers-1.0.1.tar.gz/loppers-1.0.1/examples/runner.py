"""Run loppers on all language samples.

This script reads all sample.* files in the examples directory and demonstrates
the skeleton extraction for each language.
"""

from __future__ import annotations

import sys
from pathlib import Path

from loppers import extract, EXTENSION_TO_LANGUAGE


def get_examples_dir() -> Path:
    """Get the examples directory."""
    return Path(__file__).parent


def run_all_samples() -> None:
    """Run extraction on all sample files."""
    examples_dir = get_examples_dir()
    sample_files = sorted(examples_dir.glob("sample.*"))

    if not sample_files:
        print("No sample files found in examples directory")
        return

    for sample_file in sample_files:
        ext = sample_file.suffix
        if ext not in EXTENSION_TO_LANGUAGE:
            print(f"Skipping {sample_file.name} (unsupported extension)")
            continue

        language = EXTENSION_TO_LANGUAGE[ext]
        # Add filename for languages with multiple extensions
        suffix = f" ({sample_file.name})" if ext in (".ts", ".tsx", ".cpp", ".c", ".hpp", ".h", ".pyi", ".pyw", ".cjs", ".mjs", ".cts", ".mts", ".erb", ".rbx", ".phtml") else ""
        display_name = f"{language.upper()}{suffix}"

        print("\n" + "=" * 70)
        print(display_name)
        print("=" * 70)

        try:
            source_code = sample_file.read_text()
            skeleton = extract(source_code, language)
            print(skeleton)
        except Exception as e:
            print(f"Error processing {sample_file.name}: {e}")


def run_single_sample(language: str) -> None:
    """Run extraction on a single sample file.

    Args:
        language: Language identifier (e.g., 'python', 'javascript')
    """
    examples_dir = get_examples_dir()

    # Find the sample file for this language
    for ext, lang in EXTENSION_TO_LANGUAGE.items():
        if lang == language:
            sample_file = examples_dir / f"sample{ext}"
            if sample_file.exists():
                print("=" * 70)
                print(f"{language.upper()}")
                print("=" * 70)
                try:
                    source_code = sample_file.read_text()
                    skeleton = extract(source_code, language)
                    print(skeleton)
                except Exception as e:
                    print(f"Error: {e}")
                return

    print(f"No sample found for language: {language}")
    available_langs = sorted(set(EXTENSION_TO_LANGUAGE.values()))
    print(f"Available languages: {', '.join(available_langs)}")


def main() -> None:
    """Main entry point."""
    if len(sys.argv) > 1:
        # Run single language
        language = sys.argv[1]
        run_single_sample(language)
    else:
        # Run all
        run_all_samples()


if __name__ == "__main__":
    try:
        main()
    except ImportError as e:
        print(f"Error: {e}")
        print("\nInstall dependencies with:")
        print("  uv sync --extra dev")
