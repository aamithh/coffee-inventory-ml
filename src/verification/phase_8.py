"""Final quality checks and isolated, full-size end-to-end workflow verification."""

from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import io
import json
import shutil
import subprocess
import sys
import traceback
import nbformat
import numpy as np
import pandas as pd
import yaml
from src.data.quality import assert_no_truth_references
from src.utils.config import PROJECT_ROOT, load_config, resolve_path
from src.verification.phase_6 import live_smoke
from src.verification.phase_7 import live_dashboard


def command(args: list[str]) -> None:
    """Retain complete output and fail immediately on a nonzero command status."""
    print("$ " + " ".join(args), flush=True)
    result = subprocess.run(args, cwd=PROJECT_ROOT, capture_output=True, text=True)
    print(result.stdout, end="")
    print(result.stderr, end="")
    print(f"exit_code={result.returncode}", flush=True)
    if result.returncode:
        raise RuntimeError("Verification command failed.")


def isolated_workflow(config: dict) -> None:
    """Generate, train and replay from empty output paths using validated cached weather.

    This checks the full configured data range and tuning grid, without publishing
    over the project's demo artifacts. It reuses the installed Windows venv; it
    does not claim to verify a new environment installation or GNU Make itself.
    """
    staging = resolve_path(config, "pipeline_staging")
    staging.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=staging, prefix="final_workflow_") as directory:
        root = Path(directory)
        settings = deepcopy(config)
        settings["sqlite"]["honor_environment_override"] = False
        for key in settings["paths"]:
            settings["paths"][key] = str(root / key / Path(config["paths"][key]).name)
        # The current validated real-weather cache keeps this check offline.
        # Sales, databases, fitted models and forecast bank are regenerated.
        for key in ("weather_cache", "weather_metadata"):
            destination = resolve_path(settings, key)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(resolve_path(config, key), destination)
        path = root / "config.yaml"
        path.write_text(yaml.safe_dump(settings, sort_keys=False), encoding="utf-8")
        print("Isolated workflow: full configured history/grid; empty sales/model/replay outputs")
        for task in ("setup-check", "data", "features", "train", "inventory", "simulate"):
            command(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(PROJECT_ROOT / "tasks.ps1"),
                    "-Task",
                    task,
                    "--config",
                    str(path),
                ]
            )
        measured = json.loads(resolve_path(settings, "metrics").read_text(encoding="utf-8"))
        original = json.loads(resolve_path(config, "metrics").read_text(encoding="utf-8"))
        assert measured["selected_point_model"] == original["selected_point_model"]
        np.testing.assert_allclose(
            measured["relative_wape_improvement"], original["relative_wape_improvement"]
        )
        replay = pd.read_csv(resolve_path(settings, "simulation_summary"))
        prior = pd.read_csv(resolve_path(config, "simulation_summary"))
        assert replay.policy.tolist() == prior.policy.tolist()
        np.testing.assert_allclose(
            replay.select_dtypes("number"), prior.select_dtypes("number"), rtol=1e-9, atol=1e-8
        )
        print(
            "Regenerated model selection/WAPE and all policy summary numbers match saved results: PASS"
        )
        live_smoke(settings)
        live_dashboard(settings)
        print(
            "Isolated workflow and both live CLI startups: PASS; temporary outputs removed afterward"
        )


def main() -> None:
    """Run final checks, record raw results and preserve all preexisting data artifacts."""
    config = load_config()
    protected = [
        p
        for folder in ("data", "models", "reports/figures", "notebooks")
        for p in (PROJECT_ROOT / folder).rglob("*")
        if p.is_file() and ".pipeline_staging" not in p.parts
    ]
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    output = io.StringIO()
    code = 0
    with redirect_stdout(output), redirect_stderr(output):
        try:
            for args in (
                [sys.executable, "-m", "pytest", "-q"],
                [sys.executable, "-m", "ruff", "check", "src", "tests"],
                [sys.executable, "-m", "ruff", "format", "--check", "src", "tests"],
                [sys.executable, "-m", "pip", "check"],
            ):
                command(args)
            isolated_workflow(config)
            assert_no_truth_references(config)
            print("Protected feature/model source reference scan: PASS")
            for filename in ("01_eda.ipynb", "02_modeling.ipynb", "03_simulation.ipynb"):
                notebook = nbformat.read(PROJECT_ROOT / "notebooks" / filename, as_version=4)
                nbformat.validate(notebook)
                cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
                assert all(cell.execution_count is not None for cell in cells)
                assert not any(
                    o.output_type == "error" for cell in cells for o in cell.get("outputs", [])
                )
                print(f"Saved executed notebook: {filename}; schema/no-error output PASS")
            for path, digest in before.items():
                assert path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == digest
            print(
                f"Original data/model/figure/notebook file hashes unchanged: {len(before)} files PASS"
            )
            manifest = json.loads(
                (resolve_path(config, "backup_pre_1_5") / "manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            for record in manifest:
                assert (
                    hashlib.sha256((PROJECT_ROOT / record["backup"]).read_bytes()).hexdigest()
                    == record["backup_sha256"]
                )
            print(f"Pre-1.5 backup integrity: {len(manifest)} artifacts PASS")
            for key in ("final_report", "slide_outline", "demo_script"):
                assert resolve_path(config, key).is_file()
                print(f"Final document: {config['paths'][key]} PRESENT")
            print(
                "Weather tests use mocks; workflow uses the validated real cache; live HTTP is loopback only."
            )
            print(
                "Fresh pip installation and GNU Make execution were not run: existing Windows venv/wrapper verified."
            )
            print("Phase 8 complete. All requested phases finished.")
        except Exception:
            traceback.print_exc()
            code = 1
    transcript = output.getvalue()
    resolve_path(config, "phase_8_verification").write_text(transcript, encoding="utf-8")
    print(transcript, end="")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
