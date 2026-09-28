PY ?= python3
INSTALL_DIR ?= $(HOME)/.workbuddy/skills

.PHONY: help new validate index install install-copy uninstall list check

help:
	@echo "常用命令:"
	@echo "  make new name=<skill-name>   新建一个 skill"
	@echo "  make validate                校验所有 skill 是否符合规范"
	@echo "  make install                 软链安装到 $(INSTALL_DIR) (改源码即时生效)"
	@echo "  make install-copy            用副本安装"
	@echo "  make uninstall               卸载本仓库安装过的 skill"
	@echo "  make index                   重新生成 README 里的 skill 索引"
	@echo "  make list                    列出所有 skill"
	@echo "  make check                   validate + index 检查（提交前跑）"

new:
	@test -n "$(name)" || (echo "用法: make new name=my-skill"; exit 1)
	$(PY) scripts/new_skill.py $(name)

validate:
	$(PY) scripts/validate.py

index:
	$(PY) scripts/update_index.py

check:
	$(PY) scripts/validate.py
	$(PY) scripts/update_index.py

install:
	./scripts/install.sh

install-copy:
	./scripts/install.sh --copy

uninstall:
	./scripts/install.sh --uninstall

list:
	@for d in skills/*/; do \
		[ -d "$$d" ] || continue; \
		n=$$(basename "$$d"); \
		case "$$n" in _*|.*) continue;; esac; \
		printf '%-32s %s\n' "$$n" "$$d"; \
	done
