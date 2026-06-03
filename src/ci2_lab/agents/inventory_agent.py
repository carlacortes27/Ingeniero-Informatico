from dataclasses import asdict
import json
from pathlib import Path

from ci2_lab.models import ProjectInventory


class InventoryAgent:
    def save(
        self,
        inventory: ProjectInventory,
        output_dir: str | Path = "outputs",
    ) -> Path:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        inventory_path = output_path / "inventory.json"
        inventory_path.write_text(
            json.dumps(asdict(inventory), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        return inventory_path
