#!/usr/bin/env python3
"""
扫描 skills/ 下所有 skill，重写 README.md 中的索引表格。

用法:
    python3 scripts/update_index.py          # 就地更新 README.md
    python3 scripts/update_index.py --check  # 只检查是否已是最新（CI 用）
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
README = ROOT / "README.md"

START = "<!-- SKILL_INDEX_START -->"
END = "<!-- SKILL_INDEX_END -->"

FM_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def get_field(fm: str, key: str) -> str | None:
    m = re.search(rf"^{re.escape(key)}:\s*(.*)$", fm, re.M)
    if not m:
        return None
    v = m.group(1).strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1].strip()
    return v or None


def last_updated(skill_dir: Path) -> str:
    rel = skill_dir.relative_to(ROOT)
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ad", "--date=short", "--", str(rel)],
            cwd=ROOT, capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:
        pass
    ts = max((p.stat().st_mtime for p in skill_dir.rglob("*") if p.is_file()), default=0)
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d") if ts else "-"


def collect() -> list[dict]:
    items = []
    for d in sorted(SKILLS_DIR.iterdir()):
        if not d.is_dir() or d.name.startswith(("_", ".")):
            continue
        skill_md = d / "SKILL.md"
        if not skill_md.exists():
            continue
        text = skill_md.read_text(encoding="utf-8")
        m = FM_RE.match(text)
        if not m:
            continue
        fm = m.group(1)
        desc = get_field(fm, "description") or ""
        desc = " ".join(desc.split())
        if len(desc) > 90:
            desc = desc[:87] + "..."
        resources = [f"`{s}`" for s in ("scripts", "references", "assets") if (d / s).is_dir() and any((d / s).iterdir())]
        items.append({
            "name": d.name,
            "desc": desc or "_(缺少 description)_",
            "resources": " ".join(resources) or "—",
            "updated": last_updated(d),
        })
    return items


def build_table(items: list[dict]) -> str:
    if not items:
        return "还没有任何 skill。用 `python3 scripts/new_skill.py <name>` 创建第一个。"
    lines = [
        "| Skill | 说明 | 资源 | 最近更新 |",
        "|-------|------|------|----------|",
    ]
    for it in items:
        lines.append(f"| [`{it['name']}`](skills/{it['name']}/) | {it['desc']} | {it['resources']} | {it['updated']} |")
    return "\n".join(lines)


def main() -> int:
    if not README.exists():
        print(f"找不到 {README}")
        return 1

    content = README.read_text(encoding="utf-8")
    if START not in content or END not in content:
        print(f"README.md 中缺少 {START} / {END} 标记")
        return 1

    items = collect()
    table = build_table(items)
    pattern = re.compile(rf"{re.escape(START)}.*?{re.escape(END)}", re.DOTALL)
    new_content = pattern.sub(f"{START}\n\n{table}\n\n{END}", content)

    if new_content == content:
        print(f"README 索引已是最新（{len(items)} 个 skill）")
        return 0

    if "--check" in sys.argv:
        print("README 索引不是最新的，请运行: python3 scripts/update_index.py")
        return 1

    README.write_text(new_content, encoding="utf-8")
    print(f"README 索引已更新（{len(items)} 个 skill）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
