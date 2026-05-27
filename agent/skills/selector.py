from __future__ import annotations

from dataclasses import dataclass
from agent.skills.store import Skill

@dataclass(frozen=True)
class SkillSelection:
    skills: list[Skill]
    mode: str
    explicit_names: list[str]
    missing_explicit_names: list[str]
    cleaned_text: str

class SkillSelector:
    def __init__(self, skills: list[Skill]) -> None:
        self.skills = skills

    def select(self, user_text: str) -> SkillSelection:
        explicit_names, cleaned_text = self._parse_explicit_names(user_text)

        if explicit_names:
            selected = [
                skill for skill in self.skills
                if skill.name in explicit_names
            ]
            selected_names = {skill.name for skill in selected}
            missing = [
                name for name in explicit_names
                if name not in selected_names
            ]

            return SkillSelection(
                skills=selected,
                mode="explicit",
                explicit_names=explicit_names,
                missing_explicit_names=missing,
                cleaned_text=cleaned_text,
            )
        

        normalized = user_text.lower()
        selected = [
            skill for skill in self.skills
            if any(trigger.lower() in normalized for trigger in [skill.name, *skill.triggers])
        ]

        return SkillSelection(
            skills=selected,
            mode="implicit" if selected else "none",
            explicit_names=[],
            missing_explicit_names=[],
            cleaned_text=user_text,
        )
    

    def _parse_explicit_names(self, user_text: str) -> tuple[list[str], str]:
        stripped = user_text.strip()

        if not stripped.startswith("/"):
            return [], user_text

        first, _, rest = stripped.partition(" ")

        name = first.removeprefix("/").strip()

        if not name:
            return [], user_text

        return [name], rest.strip()