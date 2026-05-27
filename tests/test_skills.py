from agent.skills import SkillStore, SkillSelector, render_skill_system_prompt


def test_skill_store_loads_markdown_skill(tmp_path):
    skills_dir = tmp_path / ".skills"
    review_dir = skills_dir / "review"
    review_dir.mkdir(parents=True)
    (review_dir / "_meta.json").write_text(
        """{
  "name": "review",
  "version": "1.0.0",
  "description": "Use for code review.",
  "triggers": ["review", "审查"]
}""",
        encoding="utf-8",
    )
    (review_dir / "SKILL.md").write_text(
        "Lead with findings.\n",
        encoding="utf-8",
    )

    store = SkillStore(skills_dir)
    skills = store.load_all()

    assert len(skills) == 1
    assert skills[0].name == "review"
    assert skills[0].version == "1.0.0"
    assert skills[0].description == "Use for code review."
    assert skills[0].triggers == ["review", "审查"]
    assert "Lead with findings." in skills[0].body


def test_skill_selector_matches_trigger(tmp_path):
    skill = SkillStore.parse_markdown(
        """---
name: review
description: Use for code review.
triggers:
  - review
---

Lead with findings.
"""
    )

    selected = SkillSelector([skill]).select("please review this code")

    assert selected.mode == "implicit"
    assert [item.name for item in selected.skills] == ["review"]
    assert selected.explicit_names == []
    assert selected.missing_explicit_names == []


def test_render_skill_system_prompt():
    skill = SkillStore.parse_markdown(
        """---
name: review
description: Use for code review.
triggers:
  - review
---

Lead with findings.
"""
    )

    prompt = render_skill_system_prompt([skill])

    assert "Active skills" in prompt
    assert "review" in prompt
    assert "Lead with findings." in prompt
