#!/usr/bin/env python3
"""Command-line name generator for Onymancer.

This script provides a convenient way to generate fantasy names using various patterns.
Use --help to see all available options.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from onymancer import generate, load_tokens_from_json, set_tokens


# Predefined patterns with descriptions
PREDEFINED_PATTERNS = {
    "simple": {
        "pattern": "s(dim)",
        "description": "Simple name with literal suffix",
        "example": "thor(dim)"
    },
    "fantasy": {
        "pattern": "!s!v!c",
        "description": "Classic fantasy name with capitalization",
        "example": "Elira"
    },
    "elven": {
        "pattern": "!s<v|l>!c!v",
        "description": "Elven-style name with liquid consonants",
        "example": "Lirael"
    },
    "dwarven": {
        "pattern": "!s!c!c<v|>",
        "description": "Dwarven name with hard consonants",
        "example": "Thrain"
    },
    "title": {
        "pattern": "!t !T",
        "description": "Random title",
        "example": "Master of The Mountains"
    },
    "place": {
        "pattern": "!s<v|c><ford|ham|ton|ville|burg>",
        "description": "Place name",
        "example": "Riverton"
    },
    "insult": {
        "pattern": "!i !s",
        "description": "Humorous insult",
        "example": "Bigheaded Thor"
    },
    "mushy": {
        "pattern": "!m !M",
        "description": "Affectionate term",
        "example": "Sweetie Pie"
    }
}


def load_custom_tokens(filepath: str) -> bool:
    """Load custom tokens from a JSON file.

    Args:
        filepath: Path to the JSON file

    Returns:
        True if loaded successfully, False otherwise
    """
    try:
        success = load_tokens_from_json(filepath)
        if success:
            print(f"✓ Loaded custom tokens from {filepath}")
        else:
            print(f"✗ Failed to load tokens from {filepath}")
        return success
    except Exception as e:
        print(f"✗ Error loading tokens: {e}")
        return False


def generate_names(pattern: str, count: int, seed: int | None = None) -> list[str]:
    """Generate multiple names using the given pattern.

    Args:
        pattern: The pattern to use
        count: Number of names to generate
        seed: Optional seed for reproducibility

    Returns:
        List of generated names
    """
    names = []
    for i in range(count):
        current_seed = seed + i if seed is not None else i
        name = generate(pattern, current_seed)
        names.append(name)
    return names


def main() -> None:
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Generate fantasy names using Onymancer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --pattern "!s!v!c" --count 5
  %(prog)s --preset fantasy --count 3 --seed 42
  %(prog)s --list-patterns
  %(prog)s --custom-tokens my_tokens.json --pattern "!x!y"

Pattern Syntax:
  s: syllable    v: vowel    V: vowel combo    c: consonant
  B: begin cons  C: any cons i: insult         m: mushy name
  M: mushy end   D: dumb cons d: dumb syllable t: title begin
  T: title end   !: capitalize  (): literals   <>: groups
        """
    )

    parser.add_argument(
        "-p", "--pattern",
        help="Pattern to use for name generation"
    )

    parser.add_argument(
        "--preset",
        choices=list(PREDEFINED_PATTERNS.keys()),
        help="Use a predefined pattern"
    )

    parser.add_argument(
        "-c", "--count",
        type=int,
        default=1,
        help="Number of names to generate (default: 1)"
    )

    parser.add_argument(
        "-s", "--seed",
        type=int,
        help="Seed for reproducible generation"
    )

    parser.add_argument(
        "-l", "--list-patterns",
        action="store_true",
        help="List available predefined patterns"
    )

    parser.add_argument(
        "-t", "--custom-tokens",
        help="Load custom tokens from JSON file"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )

    args = parser.parse_args()

    # Handle custom tokens first
    if args.custom_tokens:
        if not load_custom_tokens(args.custom_tokens):
            sys.exit(1)

    # List patterns if requested
    if args.list_patterns:
        print("Available predefined patterns:")
        print("-" * 50)
        for name, info in PREDEFINED_PATTERNS.items():
            print(f"{name:<15} {info['description']} (e.g., {info['example']})")
        print("\nUse --preset <name> to use a predefined pattern")
        return

    # Determine pattern to use
    if args.preset and args.pattern:
        print("✗ Cannot use both --preset and --pattern")
        sys.exit(1)
    elif args.preset:
        pattern = PREDEFINED_PATTERNS[args.preset]["pattern"]
        print(f"Using preset '{args.preset}': {pattern}")
    elif args.pattern:
        pattern = args.pattern
    else:
        print("✗ Must specify either --pattern or --preset")
        print("Use --list-patterns to see available presets")
        sys.exit(1)

    # Generate names
    try:
        names = generate_names(pattern, args.count, args.seed)

        if args.json:
            result = {
                "pattern": pattern,
                "count": args.count,
                "seed": args.seed,
                "names": names
            }
            print(json.dumps(result, indent=2))
        else:
            print(f"Generated {args.count} name(s) using pattern: {pattern}")
            if args.seed is not None:
                print(f"Seed: {args.seed}")
            print("\nNames:")
            for i, name in enumerate(names, 1):
                print(f"{i:2d}. {name}")

    except Exception as e:
        print(f"✗ Error generating names: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()