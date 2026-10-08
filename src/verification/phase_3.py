"""Full Phase 3 verification with recorded commands and notebook execution."""

from contextlib import redirect_stdout, redirect_stderr
import hashlib
import io
import json
import subprocess
import sys
import traceback
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
import numpy as np
import pandas as pd
from src.data.quality import assert_no_truth_references
from src.utils.config import PROJECT_ROOT, load_config, resolve_path


def execute_notebook(config: dict) -> None:
    """Use this interpreter, retain outputs and shut down the kernel on every outcome."""
    path = resolve_path(config, "modeling_notebook")
    notebook = nbformat.read(path, as_version=4)
    manager = KernelManager(kernel_name="python3")
    manager.kernel_spec.argv[0] = sys.executable
    try:
        NotebookClient(
            notebook,
            km=manager,
            timeout=config["cli"]["notebook_timeout_seconds"],
            resources={"metadata": {"path": str(PROJECT_ROOT)}},
        ).execute()
    finally:
        if manager.has_kernel:
            manager.shutdown_kernel(now=True)
    nbformat.validate(notebook)
    nbformat.write(notebook, path)
    cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
    plots = sum(
        "image/png" in output.get("data", {})
        for cell in cells
        for output in cell.get("outputs", [])
    )
    assert (
        len(cells) == 4 and plots == 3 and all(cell.execution_count is not None for cell in cells)
    )
    print(
        f"Modeling notebook: {len(cells)} code cells executed; {plots} embedded charts; schema validated"
    )
    for cell in cells:
        for output in cell.get("outputs", []):
            if output.output_type == "stream":
                print(output.text, end="")


def main() -> None:
    config = load_config()
    paths = (
        "sales_csv",
        "truth_csv",
        "weather_cache",
        "database",
        "truth_database",
        "features_csv",
    )
    before = {
        key: hashlib.sha256(resolve_path(config, key).read_bytes()).hexdigest() for key in paths
    }
    buffer = io.StringIO()
    code = 0
    with redirect_stdout(buffer), redirect_stderr(buffer):
        try:
            for args in (
                [sys.executable, "-m", "pytest", "-q"],
                [sys.executable, "-m", "ruff", "check", "src", "tests"],
                [sys.executable, "-m", "ruff", "format", "--check", "src", "tests"],
                [sys.executable, "-m", "pip", "check"],
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(PROJECT_ROOT / "tasks.ps1"),
                    "-Task",
                    "train",
                ],
            ):
                print("$ " + " ".join(args))
                result = subprocess.run(args, cwd=PROJECT_ROOT, capture_output=True, text=True)
                print(result.stdout, end="")
                print(result.stderr, end="")
                print(f"exit_code={result.returncode}")
                if result.returncode:
                    raise RuntimeError("Verification command failed.")
            execute_notebook(config)
            assert_no_truth_references(config)
            print("Protected feature/model reference scan: PASS")
            cv = pd.read_csv(resolve_path(config, "model_cv_results"))
            assert (pd.to_datetime(cv.train_end) < pd.to_datetime(cv.validation_start)).all()
            assert cv.fold.nunique() >= 5
            print(
                f"Walk-forward: {cv.fold.nunique()} folds; {len(cv)} model/candidate/fold rows; every training cutoff before validation"
            )
            from src.models.predict import load_artifact
            from src.features.build_features import load_feature_dataset

            artifact = load_artifact(config)
            dataset = load_feature_dataset(config)
            rows = dataset.frame.loc[
                dataset.frame.split.eq("test") & dataset.frame.record_status.eq("clean")
            ]
            model = artifact["point_models"][artifact["selected_point"]]
            values = model.predict(rows)
            saved = pd.read_csv(resolve_path(config, "model_predictions"))
            np.testing.assert_allclose(
                values, saved[artifact["selected_point"]], rtol=1e-12, atol=1e-12
            )
            print("Saved artifact reload vs exported test predictions: PASS")
            print("No source artifacts changed (SHA-256):")
            for key, digest in before.items():
                same = digest == hashlib.sha256(resolve_path(config, key).read_bytes()).hexdigest()
                print(f"{key}: {digest}; unchanged={same}")
                assert same
            backup = resolve_path(config, "backup_pre_1_5")
            manifest = json.loads((backup / "manifest.json").read_text())
            for record in manifest:
                assert (
                    hashlib.sha256((PROJECT_ROOT / record["backup"]).read_bytes()).hexdigest()
                    == record["backup_sha256"]
                )
            print(f"Pre-1.5 backup integrity: {len(manifest)} artifacts unchanged")
            print(
                "Optional SARIMAX remains disabled. No inventory engine or simulation implemented."
            )
            print("Phase 3 complete. Stop before Phase 4.")
        except Exception:
            traceback.print_exc()
            code = 1
    output = buffer.getvalue()
    resolve_path(config, "phase_3_verification").write_text(output, encoding="utf-8")
    print(output, end="")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
