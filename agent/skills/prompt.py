from __future__ import annotations

from agent.skills.store import Skill

def render_skill_system_prompt(skills: list[Skill]) -> str:
    if not skills:
        return ""

    sections = ["Active skills:"]

    for skill in skills:
        sections.append(
            f"""## {skill.name}
Description: {skill.description}

Instructions:
{skill.body}
"""
        )

    return "\n\n".join(sections)