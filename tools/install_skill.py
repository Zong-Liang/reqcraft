#!/usr/bin/env python3
"""Install ReqCraft into a local Agent skills directory."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory, mkdtemp

# A preview must not create a Python cache in the source tree.
sys.dont_write_bytecode = True
from bundle import NAME, load, tree


def changes(parent, skills, replace):
    pending = {}
    for name, files in skills.items():
        target = parent / name
        previous = tree(target) if target.exists() or target.is_symlink() else None
        if previous == files:
            continue
        if previous is not None and not replace:
            raise ValueError(f"{target} 已存在且内容不同，使用 --replace 备份后更新")
        pending[name] = previous
    return pending


def apply(parent, skills, pending):
    backups = {}
    installed = []
    backup_root = None
    with TemporaryDirectory(prefix=".reqcraft-install-", dir=parent.parent) as directory:
        stage = Path(directory)
        for name in pending:
            for relative, content in skills[name].items():
                path = stage / name / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
        try:
            for name, previous in pending.items():
                target = parent / name
                current = tree(target) if target.exists() or target.is_symlink() else None
                if current != previous:
                    raise ValueError(f"安装期间目标已变更：{target}")
                if previous is not None:
                    if backup_root is None:
                        backup_root = Path(mkdtemp(prefix="reqcraft-backup-", dir=parent.parent))
                    backups[name] = target.rename(backup_root / name)
                (stage / name).rename(target)
                installed.append(name)
        except (OSError, ValueError):
            for name in reversed(installed):
                (parent / name).rename(stage / name)
            for name, backup in backups.items():
                backup.rename(parent / name)
            if backup_root:
                backup_root.rmdir()
            raise
    return {name: str(path) for name, path in backups.items()}


def install(parent, *, replace=False, dry_run=False, main_only=False):
    skills, _, version = load()
    if main_only:
        skills = {NAME: skills[NAME]}
    parent = parent.expanduser().absolute()
    if parent.is_symlink():
        raise ValueError(f"安装目录是符号链接：{parent}")
    result = {"directory": str(parent), "version": version, "skills": list(skills)}
    if dry_run:
        return dict(result, status="DRY_RUN", changes=list(changes(parent, skills, replace)))
    parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(parent, os.O_RDONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        pending = changes(parent, skills, replace)
        if not pending:
            return dict(result, status="UNCHANGED")
        return dict(result, status="INSTALLED", backups=apply(parent, skills, pending))
    finally:
        os.close(fd)


def main():
    parser = argparse.ArgumentParser(description="安装 ReqCraft 主技能和动作入口。")
    parser.add_argument("--host", choices=("codex", "claude"), default="codex")
    parser.add_argument("--dest", type=Path, help="技能父目录，可指向项目级目录")
    parser.add_argument("--dry-run", action="store_true", help="预览，仅读取文件")
    parser.add_argument("--replace", action="store_true", help="保留备份后更新已安装的入口")
    parser.add_argument("--main-only", action="store_true", help="仅安装主技能")
    args = parser.parse_args()
    folder = ".agents" if args.host == "codex" else ".claude"
    try:
        result = install(
            args.dest or Path.home() / folder / "skills",
            replace=args.replace, dry_run=args.dry_run, main_only=args.main_only,
        )
    except (KeyError, ValueError, OSError) as error:
        print(f"安装失败：{error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
