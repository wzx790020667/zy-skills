#!/usr/bin/env bash
#
# 把 skills/ 下的 skill 安装到本机 WorkBuddy skills 目录。
#
# 用法:
#   ./scripts/install.sh              # 默认用软链安装（改仓库源码即时生效，推荐开发用）
#   ./scripts/install.sh --copy       # 用副本安装（跨机器/无软链权限时用）
#   ./scripts/install.sh --uninstall  # 卸载本仓库安装过的 skill
#   ./scripts/install.sh --name foo   # 只处理指定 skill
#   ./scripts/install.sh --force      # 目标已存在时先备份到 ~/.workbuddy/skills_backup 再覆盖
#   DRY_RUN=1 ./scripts/install.sh    # 只打印将要做什么

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"
TARGET_DIR="${WORKBUDDY_SKILLS_DIR:-$HOME/.workbuddy/skills}"
BACKUP_DIR="$HOME/.workbuddy/skills_backup"

MODE="link"
UNINSTALL="false"
FORCE="false"
ONLY=""
DRY_RUN="${DRY_RUN:-0}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --copy)      MODE="copy"; shift ;;
    --link)      MODE="link"; shift ;;
    --uninstall) UNINSTALL="true"; shift ;;
    --force)     FORCE="true"; shift ;;
    --name)      ONLY="${2:-}"; [[ -n "$ONLY" ]] || { echo "--name 需要参数"; exit 1; }; shift 2 ;;
    -h|--help)   sed -n '2,15p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
done

link_count=0; copy_count=0; skip_count=0; rm_count=0

log()  { echo "$1"; }
note() { echo "  - $1"; }

do_install() {
  local src="$1" name="$2" target="$TARGET_DIR/$2"

  if [[ -L "$target" ]]; then
    local current; current="$(readlink "$target")"
    if [[ "$current" == "$src" ]]; then
      note "$name: 已经是本仓库的软链，跳过"; skip_count=$((skip_count+1)); return
    fi
    if [[ "$UNINSTALL" == "true" ]]; then
      log "卸载 $name (软链指向 $current)"; [[ "$DRY_RUN" == "1" ]] || rm "$target"
      rm_count=$((rm_count+1)); return
    fi
    handle_conflict "$name" "$target" "$src" "软链指向 $current"
    return
  fi

  if [[ -e "$target" ]]; then
    if [[ "$UNINSTALL" == "true" ]]; then
      if [[ -f "$target/.zy-skills-source" ]]; then
        log "卸载 $name (副本安装)"; [[ "$DRY_RUN" == "1" ]] || rm -rf "$target"
        rm_count=$((rm_count+1))
      else
        note "$name: 存在但非本仓库安装，未改动（如需移除请手动处理）"; skip_count=$((skip_count+1))
      fi
      return
    fi
    handle_conflict "$name" "$target" "$src" "已存在的目录"
    return
  fi

  if [[ "$UNINSTALL" == "true" ]]; then
    skip_count=$((skip_count+1)); return
  fi

  if [[ "$MODE" == "link" ]]; then
    log "软链安装 $name -> $src"
    [[ "$DRY_RUN" == "1" ]] || ln -s "$src" "$target"
    link_count=$((link_count+1))
  else
    log "副本安装 $name"
    if [[ "$DRY_RUN" != "1" ]]; then
      mkdir -p "$target"
      (tar -C "$src" --exclude='.DS_Store' -cf - .) | (tar -C "$target" -xf -)
      printf '%s\n' "$src" > "$target/.zy-skills-source"
    fi
    copy_count=$((copy_count+1))
  fi
}

handle_conflict() {
  local name="$1" target="$2" src="$3" reason="$4"

  marketplace=""
  [[ -f "$target/_skillhub_meta.json" || -f "$target/_knot_meta.json" ]] && marketplace="（这是市场上安装的 skill）"

  if [[ "$FORCE" != "true" ]]; then
    note "$name: 目标已存在，$reason $marketplace，跳过。加 --force 可覆盖（会先备份）"
    skip_count=$((skip_count+1)); return
  fi

  local backup="$BACKUP_DIR/${name}-$(date +%Y%m%d%H%M%S)"
  log "$name: 备份原目标到 $backup 后安装"
  if [[ "$DRY_RUN" != "1" ]]; then
    mkdir -p "$BACKUP_DIR"
    mv "$target" "$backup"
    if [[ "$MODE" == "link" ]]; then
      ln -s "$src" "$target"; link_count=$((link_count+1))
    else
      mkdir -p "$target"
      (tar -C "$src" --exclude='.DS_Store' -cf - .) | (tar -C "$target" -xf -)
      printf '%s\n' "$src" > "$target/.zy-skills-source"
      copy_count=$((copy_count+1))
    fi
  fi
}

if [[ ! -d "$SKILLS_DIR" ]]; then
  echo "找不到 skills 目录: $SKILLS_DIR"; exit 1
fi
if [[ "$UNINSTALL" != "true" ]]; then
  mkdir -p "$TARGET_DIR"
fi

log "仓库: $REPO_ROOT"
log "目标: $TARGET_DIR"
log "模式: $MODE"
[[ "$DRY_RUN" == "1" ]] && log "(DRY RUN，不会真的改动)"
echo

for dir in "$SKILLS_DIR"/*/; do
  [[ -d "$dir" ]] || continue
  name="$(basename "$dir")"
  [[ "$name" == _* || "$name" == .* ]] && continue
  [[ -n "$ONLY" && "$name" != "$ONLY" ]] && continue
  [[ -f "$dir/SKILL.md" ]] || { note "$name: 无 SKILL.md，跳过"; continue; }
  do_install "${dir%/}" "$name"
done

echo
log "完成：软链 $link_count / 副本 $copy_count / 卸载 $rm_count / 跳过 $skip_count"
if [[ "$link_count" -gt 0 || "$copy_count" -gt 0 ]]; then
  log "WorkBuddy 可能需要重开会话才能识别新安装的 skill。"
fi
