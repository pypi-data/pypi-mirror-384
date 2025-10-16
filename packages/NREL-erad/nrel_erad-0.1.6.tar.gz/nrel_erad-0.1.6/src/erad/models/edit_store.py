from pathlib import Path
import json

from pydantic import BaseModel

from gdm.tracked_changes import TrackedChange


class EditStore(BaseModel):
    updates: list[TrackedChange] = []

    def to_json(self, filename: Path):
        filename = Path(filename)
        with open(filename, "w") as f:
            f.write(self.model_dump_json(indent=4))

    @classmethod
    def from_json(cls, filename: Path):
        filename = Path(filename)
        with open(filename) as f:
            data = json.load(f)
            return EditStore(**data)
