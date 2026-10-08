"""Stage generated artifacts and publish with coordinated rollback on handled failures."""

from copy import deepcopy
from pathlib import Path
import os
import shutil
import tempfile
from typing import Any
from src.utils.config import resolve_path


def staged_config(config: dict[str, Any], staging: Path, keys: tuple[str, ...]) -> dict[str, Any]:
    """Redirect only output paths to isolated staging files, retaining provider inputs."""
    result = deepcopy(config)
    # Remove an environment override from the staged copy without changing process env.
    result["sqlite"]["honor_environment_override"] = False
    for key in keys:
        result["paths"][key] = str(staging / key / resolve_path(config, key).name)
    return result


def publish_artifacts(pairs: list[tuple[Path, Path]]) -> None:
    """Prepare sibling files, then replace targets; restore all targets on an exception.

    Sibling temporaries support outputs on different volumes. Individual replaces are
    atomic; handled publication failures roll back. A process crash across several
    files is not a filesystem-wide atomic transaction; the explicit pre-patch backup
    remains the recovery point for that case.
    """
    if len({target.resolve() for _, target in pairs}) != len(pairs):
        raise ValueError("Artifact output paths must be distinct.")
    prepared: list[tuple[Path, Path, Path | None]] = []
    committed: list[tuple[Path, Path | None]] = []
    recovery_files: set[Path] = set()
    try:
        for source, target in pairs:
            if not source.is_file():
                raise FileNotFoundError(f"Staged output is missing: {source}")
            target.parent.mkdir(parents=True, exist_ok=True)
            descriptor, filename = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.")
            os.close(descriptor)
            temporary = Path(filename)
            shutil.copy2(source, temporary)
            previous = None
            if target.exists():
                descriptor, filename = tempfile.mkstemp(
                    dir=target.parent, prefix=f".{target.name}.rollback."
                )
                os.close(descriptor)
                previous = Path(filename)
                shutil.copy2(target, previous)
            prepared.append((temporary, target, previous))
        for temporary, target, previous in prepared:
            os.replace(temporary, target)
            committed.append((target, previous))
    except BaseException:
        for target, previous in reversed(committed):
            if previous is None:
                target.unlink(missing_ok=True)
            else:
                try:
                    os.replace(previous, target)
                except OSError:
                    recovery_files.add(previous)
        if recovery_files:
            raise RuntimeError(
                f"Publication failed; restore retained recovery files: {sorted(map(str, recovery_files))}"
            )
        raise
    finally:
        for temporary, _, previous in prepared:
            temporary.unlink(missing_ok=True)
            if previous is not None and previous not in recovery_files:
                previous.unlink(missing_ok=True)
