import argparse
from pathlib import Path

from ci2_lab.agents.auditor_agent import AuditorAgent
from ci2_lab.utils import GitHubCloneError, clone_github_repo, is_github_url
from ci2_lab.utils import remove_temporary_directory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ci2-lab",
        description="CI2 Lab repository analysis agent",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan a repository and show a basic inventory summary.",
    )
    scan_parser.add_argument("input", help="Repository path or GitHub URL to scan.")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "scan":
        scan_input = args.input
        temporary_path: str | None = None

        try:
            if is_github_url(scan_input):
                print(f"Clonando repositorio: {scan_input}")
                scan_input, _repo_name = clone_github_repo(scan_input)
                temporary_path = str(Path(scan_input).parent)
                print("Repositorio clonado correctamente.")
                print()

            inventory = AuditorAgent().scan(scan_input)
            return 0 if inventory.audit.get("is_valid") else 1
        except GitHubCloneError as error:
            print(f"Error: {error}")
            return 1
        finally:
            if temporary_path:
                print()
                print("Limpiando carpeta temporal...")
                remove_temporary_directory(temporary_path)
                print("Listo.")

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
