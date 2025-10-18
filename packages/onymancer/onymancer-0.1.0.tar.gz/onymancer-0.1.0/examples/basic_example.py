#!/usr/bin/env python3
"""Basic example of using Onymancer to generate fantasy names."""


from onymancer import generate, set_token


def main() -> None:
    """Generate and display fantasy names."""
    print("Generating fantasy names...")

    # Generate a simple name
    name1 = generate("s(dim)", seed=42)
    print(f"Simple name: {name1}")

    # Generate a fantasy name with capitalization
    name2 = generate("!s!v!c", seed=123)
    print(f"Capitalized name: {name2}")

    # Use groups for variety
    name3 = generate("<s|v>c", seed=456)
    print(f"Grouped name: {name3}")

    # Generate a title
    title = generate("!t !T", seed=789)
    print(f"Title: {title}")

    # Set custom token
    set_token("x", ["dragon", "phoenix", "griffin"])
    name4 = generate("!x", seed=101)
    print(f"Custom token name: {name4}")

    # You can also load tokens from JSON (if you have a tokens.json file)
    # tokens_file = Path("tokens.json")
    # if tokens_file.exists():
    #     if load_tokens_from_json(str(tokens_file)):
    #         print("Loaded custom tokens from JSON")
    #         name5 = generate("!s!v!c", seed=202)
    #         print(f"Name with custom tokens: {name5}")
    #     else:
    #         print("Failed to load tokens from JSON")

    print("\nName generation complete!")


if __name__ == "__main__":
    main()
