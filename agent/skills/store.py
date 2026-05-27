from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import json

@dataclass(frozen=True)
class Skill:
    name: str
    version: str
    description: str
    triggers: list[str]
    body: str

class SkillStore:
    def __init__(self, root: Path | str = ".skills") -> None:
        self.root = Path(root)


    def load_all(self) -> list[Skill]:
        if not self.root.exists():
            return []

        skills = []
        for skill_path in sorted(self.root.glob("*/SKILL.md")):
            skill_dir = skill_path.parent
            meta_path = skill_dir / "_meta.json"

            if not meta_path.exists():
                continue

            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
            body = skill_path.read_text(encoding="utf-8").strip()

            skills.append(
                Skill(
                    name=metadata["name"],
                    version=metadata.get("version", ""),
                    description=metadata.get("description", ""),
                    triggers=metadata.get("triggers", []),
                    body=body,
                )
            )

        return skills
    
    @staticmethod
    def parse_markdown(text: str, default_name: str | None = None) -> Skill:
        if not text.startswith("---"):
            raise ValueError("Skill file must start with frontmatter")

        _, metadata_text, body = text.split("---", 2)
        metadata = _parse_frontmatter(metadata_text)

        return Skill(
            name = metadata.get("name", default_name),
            description=metadata.get("description", ""),
            triggers=metadata.get("triggers", []),
            body=body.strip(),
            version=metadata.get("version", "")
        )

def _parse_frontmatter(text: str) -> dict:
    data: dict[str, object] = {}
    current_list_key: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
    
        if line.startswith("-") and current_list_key:
            data.setdefault(current_list_key, [])
            data[current_list_key].append(line[2:].strip())
            continue
        
    
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()

        if value:
            data[key] = value
            current_list_key = None
        else:
            data[key]= []
            current_list_key = key 
    
    return data