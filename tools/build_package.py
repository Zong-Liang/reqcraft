#!/usr/bin/env python3
"""Build three reproducible ReqCraft ZIP packages and a candidate manifest."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from bundle import NAME, ROOT, load


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def write_archive(path, files):
    with ZipFile(path, "w") as archive:
        for name, content in sorted(files.items()):
            info = ZipInfo(name)
            info.compress_type = ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)
    digest = sha256(path.read_bytes())
    path.with_suffix(".zip.sha256").write_text(f"{digest}  {path.name}\n", encoding="utf-8")
    return {"name": path.name, "sha256": digest, "files": len(files)}


def build(output):
    skills, metadata, version = load()
    license_path = ROOT / "LICENSE"
    license_text = license_path.read_bytes()
    entries = {
        f"{name}/{relative}": data
        for name, files in skills.items()
        for relative, data in files.items()
    }
    plugin = {f"skills/{name}": data for name, data in entries.items()}
    plugin.update({f".claude-plugin/{name}": data for name, data in metadata.items()})
    plugin["LICENSE"] = license_text
    layouts = {
        f"{NAME}.zip": {
            **{f"{NAME}/{name}": data for name, data in skills[NAME].items()},
            f"{NAME}/LICENSE": license_text,
        },
        f"{NAME}-skills.zip": {
            **{f"{NAME}-skills/{name}": data for name, data in entries.items()},
            f"{NAME}-skills/LICENSE": license_text,
        },
        f"{NAME}-plugin.zip": {f"{NAME}/{name}": data for name, data in plugin.items()},
    }
    output.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".reqcraft-build-", dir=output) as directory:
        stage = Path(directory)
        manifest = {
            "name": NAME,
            "version": version,
            "mode": "candidate",
            "sources": {name: sha256(data) for name, data in plugin.items()},
            "packages": [write_archive(stage / name, files) for name, files in layouts.items()],
        }
        manifest_name = "release-manifest.json"
        (stage / manifest_name).write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8",
        )
        # Serialize publication and put the manifest in place last.
        fd = os.open(output, os.O_RDONLY)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            if load() != (skills, metadata, version) or license_path.read_bytes() != license_text:
                raise ValueError("打包期间源文件有变更，请重新构建")
            (output / manifest_name).unlink(missing_ok=True)
            for path in sorted(stage.iterdir()):
                if path.name != manifest_name:
                    path.replace(output / path.name)
            (stage / manifest_name).replace(output / manifest_name)
        finally:
            os.close(fd)
    return manifest


def main():
    parser = argparse.ArgumentParser(description="生成 ReqCraft 技能分发包和 SHA-256 清单。")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    try:
        result = build(args.output_dir)
    except (KeyError, ValueError, OSError) as error:
        print(f"打包失败：{error}", file=sys.stderr)
        return 2
    print(json.dumps(result["packages"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
