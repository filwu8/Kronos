#!/usr/bin/env python3
"""
Repository organizer for Kronos project.
- Move all root-level test/verification scripts into tests/
- Move external data (data/, logs/, models/) into volumes/ (merge-safe)
- Update references in tests to use volumes/models
- Remove redundant backup files (*.backup)

Safe, idempotent, prints a summary of actions.
"""
from __future__ import annotations
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS_DIR = ROOT / "tests"
VOLUMES = ROOT / "volumes"

MOVE_TEST_PATTERNS = [
    re.compile(r"^test_.*\.py$", re.I),
    re.compile(r"^final_.*\.py$", re.I),
    re.compile(r"^quick_?test\.py$", re.I),
]

EXTERNAL_DIRS = {
    "data": VOLUMES / "data",
    "logs": VOLUMES / "logs",
    "models": VOLUMES / "models",
}

BACKUP_GLOBS = [
    "**/*.backup",
    "**/__pycache__/*",  # clean files inside; leave dir if removal fails
]

IGNORED_ROOT_FILES = {"run.py", "requirements.txt", "docker-compose.yml", "start.sh", "start_docker.ps1", "manage.sh", "manage.bat"}


def ensure_dirs():
    TESTS_DIR.mkdir(parents=True, exist_ok=True)
    for _k, d in EXTERNAL_DIRS.items():
        d.mkdir(parents=True, exist_ok=True)


def move_root_tests():
    moved = []
    for p in ROOT.iterdir():
        if not p.is_file():
            continue
        name = p.name
        if name in IGNORED_ROOT_FILES:
            continue
        if any(pat.match(name) for pat in MOVE_TEST_PATTERNS):
            dest = TESTS_DIR / name
            if dest.resolve() == p.resolve():
                continue
            print(f"[TEST] Move {p} -> {dest}")
            shutil.move(str(p), str(dest))
            moved.append((p, dest))
    return moved


def merge_dir(src: Path, dst: Path, include=None):
    if not src.exists():
        return []
    moved = []
    for root, dirs, files in os.walk(src):
        rel = Path(root).relative_to(src)
        (dst / rel).mkdir(parents=True, exist_ok=True)
        for f in files:
            sp = Path(root) / f
            if include and not include(sp):
                continue
            dp = dst / rel / f
            if dp.exists():
                # Overwrite existing
                try:
                    shutil.copy2(sp, dp)
                except Exception:
                    shutil.copy(sp, dp)
            else:
                try:
                    shutil.move(str(sp), str(dp))
                except PermissionError:
                    # Fallback on Windows when file is locked: copy instead
                    try:
                        shutil.copy2(sp, dp)
                    except Exception:
                        shutil.copy(sp, dp)
                except Exception:
                    # As a last resort, try copy
                    try:
                        shutil.copy2(sp, dp)
                    except Exception:
                        shutil.copy(sp, dp)
            moved.append((sp, dp))
    # Try to remove empty source tree (ignore if locked files remain)
    try:
        shutil.rmtree(src)
    except Exception:
        pass
    return moved


def move_external_data():
    moved = {}
    for name, dst in EXTERNAL_DIRS.items():
        src = ROOT / name
        if src.exists() and src.is_dir():
            print(f"[DATA] Merge {src} -> {dst}")
            moved[name] = merge_dir(src, dst)
    return moved


def update_tests_references():
    # Update tests/verify_models.py models -> volumes/models
    tm = TESTS_DIR / "verify_models.py"
    changed = False
    if tm.exists():
        txt = tm.read_text(encoding="utf-8")
        new = re.sub(r"models_dir\s*=\s*Path\([\"']models[\"']\)", "models_dir = Path('volumes/models')", txt)
        if new != txt:
            tm.write_text(new, encoding="utf-8")
            changed = True
            print("[REF] Updated tests/verify_models.py to use volumes/models")
    return changed


def remove_backups():
    removed = []
    # explicit known backups
    for p in [ROOT/"app"/"prediction_service.py.backup", ROOT/"finetune"/"config.py.backup"]:
        if p.exists():
            print(f"[CLEAN] Remove {p}")
            p.unlink(missing_ok=True)
            removed.append(p)
    # generic globs
    for pat in BACKUP_GLOBS:
        for p in ROOT.glob(pat):
            try:
                if p.is_file():
                    p.unlink(missing_ok=True)
                    removed.append(p)
            except Exception:
                pass
    return removed


def main():
    print("== Kronos Repository Organizer ==")
    ensure_dirs()
    t = move_root_tests()
    d = move_external_data()
    r = update_tests_references()
    b = remove_backups()

    print("\nSummary:")
    print(f"  Tests moved: {len(t)} files")
    print(f"  External data moved: {sum(len(v) for v in d.values())} files")
    print(f"  References updated: {'yes' if r else 'no'}")
    print(f"  Backups removed: {len(b)} items")
    print("Done.")

if __name__ == "__main__":
    main()

