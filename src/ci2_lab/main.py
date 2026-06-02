import argparse

from ci2_lab.agents.auditor_agent import AuditorAgent


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
    scan_parser.add_argument("path", help="Repository path to scan.")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "scan":
        inventory = AuditorAgent().scan(args.path)
        return 0 if inventory.audit.get("is_valid") else 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
