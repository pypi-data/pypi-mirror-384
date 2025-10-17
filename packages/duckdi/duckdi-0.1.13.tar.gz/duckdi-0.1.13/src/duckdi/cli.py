import argparse
import sys
from pathlib import Path


def init(path: str = "injections.toml"):
    """
    Creates a basic injection file at the specified path.
    """
    file = Path(path)

    if file.exists():
        print(f"[DuckDI] ⚠️ File already exists at: {path}")
        sys.exit(1)

    # Create directories if necessary
    file.parent.mkdir(parents=True, exist_ok=True)

    file.write_text(
        "[injections]\n"
        '# "interface_key" = "adapter_key"\n'
        "# Example:\n"
        '# "user_repository" = "postgres_user_repository"\n'
    )

    print(f"[DuckDI] ✅ Injection file created at: {path}")


def main():
    parser = argparse.ArgumentParser(prog="duckdi", description="DuckDI CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init", help="Create a default injections.toml file"
    )
    init_parser.add_argument(
        "path",
        nargs="?",
        default="injections.toml",
        help="Path to create the injections.toml",
    )

    args = parser.parse_args()

    if args.command == "init":
        init(args.path)


if __name__ == "__main__":
    main()
