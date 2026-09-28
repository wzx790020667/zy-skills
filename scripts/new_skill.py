#!/usr/bin/env python3
"""
从 skills/_template 创建一个新 skill。

用法:
    python3 scripts/new_skill.py my-new-skill
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
TEMPLATE = SKILLS_DIR / "_template" / "SKILL.md"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def title_case(name: str) -> str:
    return " ".join(w.capitalize() for w in name.split("-"))


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: python3 scripts/new_skill.py <skill-name>")
        print("命名规则: 小写 kebab-case，长度 <= 40，例如 wechat-draft-polish")
        return 1

    name = sys.argv[1]
    if not NAME_RE.match(name):
        print(f"错误: `{name}` 不是合法的 kebab-case 名称")
        return 1
    if len(name) > 40:
        print(f"错误: `{name}` 超过 40 字符")
        return 1

    dest = SKILLS_DIR / name
    if dest.exists():
        print(f"错误: {dest} 已存在")
        return 1
    if not TEMPLATE.exists():
        print(f"错误: 找不到模板 {TEMPLATE}")
        return 1

    dest.mkdir(parents=True)
    content = TEMPLATE.read_text(encoding="utf-8").replace("{NAME}", name).replace("{TITLE}", title_case(name))
    (dest / "SKILL.md").write_text(content, encoding="utf-8")

    # 只建 scripts/，其余让作者在需要时自己加，避免空目录污染仓库
    print(f"已创建: {dest}/SKILL.md")
    print()
    print("下一步:")
    print(f"  1. 编辑 skills/{name}/SKILL.md，把 TODO 全部替换掉，尤其是 description")
    print(f"  2. 需要脚本就 skills/{name}/scripts/，需要文档就 references/，需要模板/图片就 assets/")
    print(f"  3. python3 scripts/validate.py skills/{name}")
    print(f"  4. ./scripts/install.sh --name {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
