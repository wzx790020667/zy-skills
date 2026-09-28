#!/usr/bin/env python3
"""
校验 skills/ 目录下所有（或指定）skill 是否符合 WorkBuddy Skill 规范。

用法:
    python3 scripts/validate.py                 # 校验全部
    python3 scripts/validate.py skills/foo      # 只校验一个
    python3 scripts/validate.py --strict        # 警告也当错误处理（CI 推荐）
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’_-]*")
REL_PATH_RE = re.compile(r"`((?:scripts|references|assets)/[A-Za-z0-9._/-]+)`")

MAX_BODY_UNITS = 5000  # SKILL.md 正文上限：英文词 + 中文字的近似单位
MIN_DESC_LEN = 40      # description 太短通常意味着没写清触发条件
KNOWN_FIELDS = {
    "name", "description", "agent_created", "license",
    "allowed-tools", "allowed_tools", "disable", "disable_model_invocation",
    "version", "tags", "hooks",
}


class Report:
    def __init__(self, skill: str) -> None:
        self.skill = skill
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def ok(self) -> bool:
        return not self.errors


def parse_frontmatter(text: str) -> tuple[str | None, str]:
    if not text.startswith("---"):
        return None, text
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    return m.group(1), m.group(2)


def get_field(fm: str, key: str) -> str | None:
    m = re.search(rf"^{re.escape(key)}:\s*(.*)$", fm, re.M)
    if not m:
        return None
    value = m.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1].strip()
    return value or None


def top_level_fields(fm: str) -> list[str]:
    return re.findall(r"^([A-Za-z][A-Za-z0-9_-]*):", fm, re.M)


def count_units(body: str) -> int:
    return len(WORD_RE.findall(body)) + len(CJK_RE.findall(body))


def validate_skill(skill_dir: Path) -> Report:
    rep = Report(skill_dir.name)
    name = skill_dir.name

    if not NAME_RE.match(name):
        rep.error(f"目录名 `{name}` 必须是小写 kebab-case（仅小写字母、数字、单连字符）")
    if len(name) > 40:
        rep.error(f"目录名 `{name}` 超过 40 字符")

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        rep.error("缺少 SKILL.md")
        return rep

    try:
        text = skill_md.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        rep.error("SKILL.md 不是 UTF-8 编码")
        return rep

    fm, body = parse_frontmatter(text)
    if fm is None:
        rep.error("SKILL.md 缺少合法的 YAML frontmatter（文件必须以 `---` 开头）")
        return rep

    # frontmatter 必填字段
    fm_name = get_field(fm, "name")
    if fm_name is None:
        rep.error("frontmatter 缺少 name")
    elif fm_name != name:
        rep.error(f"frontmatter 的 name (`{fm_name}`) 与目录名 (`{name}`) 不一致")

    desc = get_field(fm, "description")
    if desc is None:
        rep.error("frontmatter 缺少 description")
    else:
        if "<" in desc or ">" in desc:
            rep.error("description 不能包含尖括号 < >")
        if len(desc) < MIN_DESC_LEN:
            rep.warn(f"description 过短（{len(desc)} 字符），建议写清做什么 + 何时触发")
        if re.search(r"(TODO|TBD|待补充)", desc):
            rep.error("description 仍是 TODO 占位")
        if not re.search(r"(This skill should be used when|use when|when the user)", desc, re.I):
            rep.warn("description 未包含触发条件，建议加上 \"This skill should be used when ...\"")

    if get_field(fm, "agent_created") != "true":
        rep.warn("frontmatter 建议包含 `agent_created: true`，否则后续无法被工具自动修改/删除")

    unknown = [f for f in top_level_fields(fm) if f not in KNOWN_FIELDS]
    if unknown:
        rep.warn(f"frontmatter 出现未知字段 {unknown}（可能是拼写错误）")

    # 正文
    units = count_units(body)
    if units > MAX_BODY_UNITS:
        rep.warn(
            f"SKILL.md 正文约 {units} 单位，超过 {MAX_BODY_UNITS}；"
            "把细节文档挪到 references/，保持 SKILL.md 精简"
        )
    if not body.strip():
        rep.error("SKILL.md 正文为空")
    if re.search(r"(TODO|TBD|待补充)", body):
        rep.warn("正文仍在 TODO 占位")

    # 引用的资源路径必须真实存在
    for rel in sorted(set(REL_PATH_RE.findall(body))):
        if not (skill_dir / rel).exists():
            rep.warn(f"SKILL.md 引用了不存在的资源 `{rel}`")
    # 反向：存在资源目录却在 SKILL.md 里完全没提
    for sub in ("scripts", "references", "assets"):
        d = skill_dir / sub
        if d.is_dir():
            if not any(d.iterdir()):
                rep.warn(f"{sub}/ 是空目录，删掉或放入内容")
            elif sub not in body:
                rep.warn(f"{sub}/ 下有文件，但 SKILL.md 未说明如何使用")

    # 目录里不允许出现不该有的东西
    allowed_top = {"SKILL.md", "scripts", "references", "assets", "README.md", "LICENSE.txt"}
    for p in skill_dir.iterdir():
        if p.name.startswith(".") and p.name != ".gitkeep":
            continue
        if p.name not in allowed_top:
            rep.warn(f"skill 根目录出现多余文件 `{p.name}`")

    return rep


def main() -> int:
    args = [a for a in sys.argv[1:]]
    strict = "--strict" in args
    args = [a for a in args if not a.startswith("--")]

    targets: list[Path]
    if args:
        targets = [Path(a).resolve() for a in args]
    else:
        if not SKILLS_DIR.is_dir():
            print(f"找不到 skills 目录：{SKILLS_DIR}")
            return 1
        targets = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir() and not p.name.startswith(("_", ".")))

    if not targets:
        print("没有找到需要校验的 skill")
        return 0

    reports = [validate_skill(t) for t in targets]

    total_err = total_warn = 0
    for rep in reports:
        in_repo = rep.skill
        if rep.ok and not rep.warnings:
            print(f"  OK    {in_repo}")
            continue
        status = "FAIL" if not rep.ok else "WARN"
        print(f"  {status}  {in_repo}")
        for msg in rep.errors:
            print(f"        [E] {msg}")
        for msg in rep.warnings:
            print(f"        [W] {msg}")
        total_err += len(rep.errors)
        total_warn += len(rep.warnings)

    print()
    print(f"共 {len(reports)} 个 skill：{total_err} 个错误，{total_warn} 个警告")

    if total_err:
        return 1
    if strict and total_warn:
        print("--strict 模式：存在警告，视为失败")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
