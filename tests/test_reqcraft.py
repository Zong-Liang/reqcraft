import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
SKILLS = {"reqcraft", "reqcraft-analyze", "reqcraft-spec", "reqcraft-audit", "reqcraft-help"}
SPEC = """# 保存提醒

## 1. 业务场景

| SC-01 | 用户编辑提醒 | 保存 | 提醒已保存 | PRD |

## 2. 业务规则与状态

| BR-01 | 名称包含 A\\|B 时仍可保存 | SC-01 | PRD 已明确 |

## 3. 业务验收标准

### AC-01：保存提醒（关联 SC-01、BR-01）

- **Given**：已填写名称
- **When**：保存提醒
- **Then**：再次打开时可看到名称
- **状态**：已确认

## 5. 待确认事项

| Q-01 | 是否可清空名称 | BR-01、AC-01 | 非阻塞 | 待确认 |

## 6. 验收审计

| AC-01 | 已确认 | 未检查 | 证据不足 |

```md
## 3. 业务验收标准
### AC-01：示例
```
"""


class ReqCraftTest(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name)

    def cli(self, script, *args):
        return subprocess.run(
            [sys.executable, "-B", str(ROOT / script), *map(str, args)],
            cwd=self.workspace, capture_output=True, text=True, encoding="utf-8",
        )

    def test_check_spec_reports_structure_and_is_read_only(self):
        spec = self.workspace / "spec.md"
        spec.write_text(SPEC, encoding="utf-8")
        check = "skills/reqcraft/scripts/check_spec.py"
        result = self.cli(check, spec)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(spec.read_text(encoding="utf-8"), SPEC)
        bad = SPEC.replace("关联 SC-01、BR-01", "关联 SC-01、BR-99").replace(
            "- **Then**：再次打开时可看到名称", "### AC-01：重复条目",
        )
        spec.write_text(bad, encoding="utf-8")
        result = self.cli(check, spec)
        self.assertEqual(result.returncode, 1)
        for expected in ("重复定义 AC-01", "未定义的 BR-99", "缺少有效的 Then"):
            self.assertIn(expected, result.stderr)

    def test_install_previews_repeats_and_preserves_backup(self):
        destination = self.workspace / ".agents" / "skills"
        install = "tools/install_skill.py"
        args = (install, "--host", "codex", "--dest", destination)
        preview = self.cli(*args, "--dry-run")
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertFalse(destination.exists())
        first = self.cli(*args)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual({path.name for path in destination.iterdir()}, SKILLS)
        repeat = self.cli(*args)
        self.assertEqual(json.loads(repeat.stdout)["status"], "UNCHANGED")
        action = destination / "reqcraft-spec" / "SKILL.md"
        changed = action.read_bytes() + b"\nlocal edit\n"
        action.write_bytes(changed)
        refused = self.cli(*args)
        self.assertEqual(refused.returncode, 2)
        self.assertEqual(action.read_bytes(), changed)
        update = self.cli(*args, "--replace")
        self.assertEqual(update.returncode, 0, update.stderr)
        backup = Path(json.loads(update.stdout)["backups"]["reqcraft-spec"])
        self.assertFalse(backup.is_relative_to(destination))
        self.assertEqual((backup / "SKILL.md").read_bytes(), changed)
        self.assertEqual(action.read_bytes(), (ROOT / "skills/reqcraft-spec/SKILL.md").read_bytes())

    def test_archives_are_reproducible_and_links_resolve(self):
        output = self.workspace / "dist"
        args = ("tools/build_package.py", "--output-dir", output)
        first = self.cli(*args)
        self.assertEqual(first.returncode, 0, first.stderr)
        manifest_path = output / "release-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["mode"], "candidate")
        expected = {
            "reqcraft.zip": "reqcraft/SKILL.md",
            "reqcraft-skills.zip": "reqcraft-skills/reqcraft-spec/SKILL.md",
            "reqcraft-plugin.zip": "reqcraft/.claude-plugin/marketplace.json",
        }
        self.assertEqual({entry["name"] for entry in manifest["packages"]}, expected.keys())
        license_text = (ROOT / "LICENSE").read_bytes()
        self.assertEqual(manifest["sources"]["LICENSE"], hashlib.sha256(license_text).hexdigest())
        for entry in manifest["packages"]:
            path = output / entry["name"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry["sha256"])
            with ZipFile(path) as archive:
                names = archive.namelist()
                self.assertIn(expected[path.name], names)
                archive_root = expected[path.name].split("/", 1)[0]
                self.assertEqual(archive.read(f"{archive_root}/LICENSE"), license_text)
                self.assertFalse(any("tools/" in name or "tests/" in name for name in names))
                unpacked = self.workspace / path.stem
                archive.extractall(unpacked)
            for markdown in unpacked.rglob("*.md"):
                for target in re.findall(r"\]\(([^()\s]+)\)", markdown.read_text(encoding="utf-8")):
                    self.assertTrue((markdown.parent / target).exists(), f"{markdown}: {target}")
        second = self.cli(*args)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(first.stdout, second.stdout)


if __name__ == "__main__":
    unittest.main()
