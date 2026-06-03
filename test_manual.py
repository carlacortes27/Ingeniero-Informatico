from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))

from ci2_lab.agents.scanner_agent import ScannerAgent


def main() -> None:
    scanner = ScannerAgent()
    result = scanner.scan(PROJECT_ROOT / "examples" / "repo_prueba")
    print(result)


if __name__ == "__main__":
    main()
