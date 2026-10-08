"""Execute Phase 2 checks and save their complete outputs."""

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
from src.utils.config import PROJECT_ROOT, load_config, resolve_path
from src.data.quality import assert_no_truth_references


def execute_notebook() -> None:
    """Use the active project interpreter and close the kernel on all outcomes."""
    path = PROJECT_ROOT / "notebooks/01_eda.ipynb"
    notebook = nbformat.read(path, as_version=4)
    manager = KernelManager(kernel_name="python3")
    manager.kernel_spec.argv[0] = sys.executable
    try:
        NotebookClient(
            notebook, km=manager, timeout=120, resources={"metadata": {"path": str(PROJECT_ROOT)}}
        ).execute()
    finally:
        if manager.has_kernel:
            manager.shutdown_kernel(now=True)
    nbformat.validate(notebook)
    nbformat.write(notebook, path)
    cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
    images = sum(
        "image/png" in output.get("data", {})
        for cell in cells
        for output in cell.get("outputs", [])
    )
    assert len(cells) == 4 and images == 5
    assert all(cell.execution_count is not None for cell in cells)
    print(
        f"Notebook execution: {len(cells)} code cells, {images} embedded PNG plots; schema validated"
    )
    for cell in cells:
        for output in cell.get("outputs", []):
            if output.output_type == "stream":
                print(output.text, end="")


def main() -> None:
    config = load_config()
    protected = ("sales_csv", "truth_csv", "weather_cache", "database", "truth_database")
    before = {
        key: hashlib.sha256(resolve_path(config, key).read_bytes()).hexdigest() for key in protected
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
                    "features",
                ],
            ):
                print("$ " + " ".join(args))
                result = subprocess.run(args, cwd=PROJECT_ROOT, capture_output=True, text=True)
                print(result.stdout, end="")
                print(result.stderr, end="")
                print(f"exit_code={result.returncode}")
                if result.returncode:
                    raise RuntimeError("Verification command failed.")
            execute_notebook()
            assert_no_truth_references(config)
            print("Protected feature/model source scan: PASS")
            print("Source artifacts unchanged (SHA-256):")
            for key, value in before.items():
                same = value == hashlib.sha256(resolve_path(config, key).read_bytes()).hexdigest()
                print(f"{key}: {value}; unchanged={same}")
                assert same
            features = resolve_path(config, "features_csv")
            manifest = json.loads(resolve_path(config, "feature_manifest").read_text())
            print(f"Feature export: {features}; predictors={len(manifest['feature_columns'])}")
            print("No models trained. Phase 2 complete; stop before Phase 3.")
        except Exception:
            traceback.print_exc()
            code = 1
    output = buffer.getvalue()
    resolve_path(config, "phase_2_verification").write_text(output, encoding="utf-8")
    print(output, end="")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
