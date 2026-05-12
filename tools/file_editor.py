import logging
from pathlib import Path
from shutil import copy2
from datetime import datetime
from typing import Dict, Any, Optional


def _ensure_logger(logger: Optional[logging.Logger] = None) -> logging.Logger:
    """
    Ensure a logger with a reasonable console handler and format exists.
    """
    if logger is not None:
        return logger

    logger = logging.getLogger("file_editor")
    logger.setLevel(logging.INFO)

    # Avoid adding multiple handlers if reused
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def _is_relative_to(path: Path, base: Path) -> bool:
    """
    Safe check for containment without relying on Path.is_relative_to (pre-3.9 compatible).
    """
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def apply_file_edits(
    project_root: str | Path,
    file_map: Dict[str, str],
    *,
    dry_run: bool = False,
    create_missing_dirs: bool = True,
    backup_existing: bool = True,
    encoding: str = "utf-8",
    logger: Optional[logging.Logger] = None,
) -> Dict[str, Any]:
    """
    Apply edits to files under a project root using a mapping of relative file paths to new content.

    Args:
        project_root: The root directory of the project (absolute or relative).
        file_map: Dict mapping relative file paths (e.g., "src/App.jsx") to new file content.
        dry_run: If True, only log what would happen without writing files.
        create_missing_dirs: Create parent directories for new files when missing.
        backup_existing: Create timestamped .bak backups for files before overwriting.
        encoding: Text encoding for reading/writing.
        logger: Optional logger; if not provided, a default console logger is configured.

    Returns:
        A summary dict with counts and per-file outcomes.
    """
    log = _ensure_logger(logger)
    root = Path(project_root).resolve()

    if not root.exists() or not root.is_dir():
        raise NotADirectoryError(f"Project root is not a directory: {root}")

    summary = {
        "root": str(root),
        "created": 0,
        "updated": 0,
        "unchanged": 0,
        "failed": 0,
        "skipped": 0,
        "backups": 0,
        "dry_run": dry_run,
        "details": [],
    }

    log.info("Starting file edits | root=%s | files=%d | dry_run=%s",
             root, len(file_map), dry_run)

    for rel_path, new_content in file_map.items():
        rel_str = str(rel_path)
        target = (root / rel_str)
        try:
            resolved = target.resolve()

            # Prevent path traversal outside root (e.g., ../../etc/passwd)
            if not _is_relative_to(resolved, root):
                summary["skipped"] += 1
                msg = f"SKIP outside root: {rel_str}"
                log.warning(msg)
                summary["details"].append({"path": rel_str, "status": "skipped_outside_root", "note": msg})
                continue

            # Ensure parent dirs
            parent = resolved.parent
            if not parent.exists():
                if create_missing_dirs:
                    if not dry_run:
                        parent.mkdir(parents=True, exist_ok=True)
                        log.info("CREATE DIR %s", parent)
                    else:
                        log.info("WOULD CREATE DIR %s", parent)
                else:
                    summary["failed"] += 1
                    msg = f"Parent directory missing and create_missing_dirs=False: {parent}"
                    log.error(msg)
                    summary["details"].append({"path": rel_str, "status": "failed_no_parent", "note": msg})
                    continue

            # Detect existing content safely
            file_existed = resolved.exists()
            existing = None

            if file_existed:
                try:
                    existing = resolved.read_text(encoding=encoding)
                except Exception as read_err:
                    log.warning("READ ERROR (treat as changed) %s | err=%s", resolved, read_err)

            # Skip if nothing changed
            if existing is not None and existing == new_content:
                summary["unchanged"] += 1
                log.info("UNCHANGED %s", resolved)
                summary["details"].append({"path": rel_str, "status": "unchanged"})
                continue

            # Backup existing files before overwrite
            if backup_existing and file_existed:
                ts = datetime.now().strftime("%Y%m%d%H%M%S")
                backup_path = resolved.with_name(resolved.name + f".bak.{ts}")
                if not dry_run:
                    copy2(resolved, backup_path)
                    summary["backups"] += 1
                    log.info("BACKUP %s -> %s", resolved, backup_path)
                else:
                    log.info("WOULD BACKUP %s -> %s", resolved, backup_path)

            # Write new content
            if not dry_run:
                resolved.write_text(new_content, encoding=encoding)

            # Assign status based on whether it existed BEFORE writing
            status = "updated" if file_existed else "created"

            if status == "created":
                summary["created"] += 1
                log.info("%s %s", "WOULD CREATE" if dry_run else "CREATED", resolved)
            else:
                summary["updated"] += 1
                log.info("%s %s", "WOULD UPDATE" if dry_run else "UPDATED", resolved)

            summary["details"].append({"path": rel_str, "status": status})

        except Exception as e:
            summary["failed"] += 1
            log.exception("FAILED %s | err=%s", target, e)
            summary["details"].append({"path": rel_str, "status": "failed", "error": str(e)})

    log.info(
        "Done | created=%d updated=%d unchanged=%d skipped=%d backups=%d failed=%d",
        summary["created"], summary["updated"], summary["unchanged"],
        summary["skipped"], summary["backups"], summary["failed"]
    )
    return summary