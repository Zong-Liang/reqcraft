"""Load the skill and plugin files shared by the installer and packager."""

import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
NAME = "reqcraft"
SKILLS = tuple(sorted((NAME, *(f"{NAME}-{action}" for action in ("analyze", "spec", "audit", "help")))))


def tree(directory):
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError(f"需要实际目录：{directory}")
    files = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"目录包含符号链接：{path}")
        relative = path.relative_to(directory)
        if "__pycache__" in relative.parts or path.name == ".DS_Store" or path.suffix in (".pyc", ".pyo"):
            continue
        if path.is_file():
            files[relative.as_posix()] = path.read_bytes()
        elif not path.is_dir():
            raise ValueError(f"需要普通文件：{path}")
    return files


def load(root=ROOT):
    all_skills = root / "skills"
    if sorted(path.name for path in all_skills.iterdir()) != list(SKILLS):
        raise ValueError("skills/ 中的入口与分发清单不一致")
    skills = {name: tree(all_skills / name) for name in SKILLS}
    for name, files in skills.items():
        text = files.get("SKILL.md", b"").decode("utf-8")
        header = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
        if not header or not re.search(rf"(?m)^name: {re.escape(name)}$", header[1]):
            raise ValueError(f"{name}/SKILL.md 的 name 与目录不一致")
        if not re.search(r"(?m)^description: \S", header[1]):
            raise ValueError(f"{name}/SKILL.md 缺少 description")

    metadata = tree(root / ".claude-plugin")
    plugin = json.loads(metadata["plugin.json"])
    marketplace = json.loads(metadata["marketplace.json"])
    identity = json.loads(skills[NAME]["version.json"])
    version = identity["version"]
    if (
        identity["name"] != NAME or plugin["name"] != NAME or plugin["version"] != version
        or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version)
        or marketplace["name"] != NAME or len(marketplace["plugins"]) != 1
        or marketplace["plugins"][0]["name"] != NAME or marketplace["plugins"][0]["source"] != "./"
    ):
        raise ValueError("技能版本、插件和 marketplace 标识须一致")
    return skills, metadata, version
