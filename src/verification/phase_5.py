"""Record full Phase 5 verification and execute the simulation notebook."""

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
    """Execute in the existing venv and preserve all notebook outputs."""
    path = resolve_path(config, "simulation_notebook")
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
    cells = [c for c in notebook.cells if c.cell_type == "code"]
    images = sum("image/png" in o.get("data", {}) for c in cells for o in c.get("outputs", []))
    assert len(cells) == 3 and images == 2 and all(c.execution_count is not None for c in cells)
    print(
        f"Simulation notebook: {len(cells)} cells executed, {images} embedded charts; schema validated"
    )
    for cell in cells:
        for output in cell.get("outputs", []):
            if output.output_type == "stream":
                print(output.text, end="")


def main() -> None:
    config = load_config()
    keys = (
        "sales_csv",
        "truth_csv",
        "weather_cache",
        "database",
        "truth_database",
        "features_csv",
        "model_bundle",
        "demo_forecast",
        "inventory_orders",
    )
    before = {
        key: hashlib.sha256(resolve_path(config, key).read_bytes()).hexdigest() for key in keys
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
                    "simulate",
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
            print("Protected feature/model source reference scan: PASS")
            daily = pd.read_csv(resolve_path(config, "simulation"))
            items = pd.read_csv(resolve_path(config, "simulation_items"))
            summary = pd.read_csv(resolve_path(config, "simulation_summary"))
            np.testing.assert_allclose(
                daily.opening + daily.received,
                daily.consumed + daily.waste + daily.closing,
                rtol=1e-10,
                atol=1e-6,
            )
            assert (items.demand == items.served + items.lost).all()
            assert (
                (
                    daily[
                        ["opening", "received", "consumed", "waste", "closing", "pending_quantity"]
                    ]
                    >= 0
                )
                .all()
                .all()
            )
            reference = (
                items.loc[items.policy.eq("manual")].set_index(["date", "item"]).demand.sort_index()
            )
            for policy in ("seasonal_naive", "ml"):
                compared = (
                    items.loc[items.policy.eq(policy)]
                    .set_index(["date", "item"])
                    .demand.sort_index()
                )
                pd.testing.assert_series_equal(reference, compared)
            for row in summary.itertuples():
                assert (
                    abs(
                        row.total_cost
                        - (
                            row.initial_stock_value
                            + row.purchase_cost
                            + row.holding_cost
                            + row.lost_sale_penalty
                        )
                    )
                    < 1e-6
                )
            print(
                "Daily FIFO mass balance, nonnegative stock, identical policy demand, unit fulfillment and cost accounting: PASS"
            )
            bank = pd.read_csv(
                resolve_path(config, "simulation_forecasts"), parse_dates=["date", "origin"]
            )
            assert bank.date.ge(bank.origin).all()
            assert bank.groupby("policy").origin.nunique().eq(24).all()
            meta = json.loads(resolve_path(config, "simulation_metadata").read_text())
            assert (
                hashlib.sha256(
                    resolve_path(config, "simulation_forecasts").read_bytes()
                ).hexdigest()
                == meta["forecast_sha256"]
            )
            print(
                f"Forecast bank: {len(bank)} rows, 24 origins per policy, valid dates and cache integrity: PASS"
            )
            for key in (
                "simulation",
                "simulation_items",
                "simulation_orders",
                "simulation_summary",
                "simulation_waste",
                "simulation_forecasts",
            ):
                assert b"\r\r\n" not in resolve_path(config, key).read_bytes()
            print("CSV newline audit: PASS")
            print("No prior-phase source artifacts changed (SHA-256):")
            for key, digest in before.items():
                same = digest == hashlib.sha256(resolve_path(config, key).read_bytes()).hexdigest()
                print(f"{key}: {digest}; unchanged={same}")
                assert same
            manifest = json.loads(
                (resolve_path(config, "backup_pre_1_5") / "manifest.json").read_text()
            )
            for record in manifest:
                assert (
                    hashlib.sha256((PROJECT_ROOT / record["backup"]).read_bytes()).hexdigest()
                    == record["backup_sha256"]
                )
            print(f"Pre-1.5 backup integrity: {len(manifest)} artifacts unchanged")
            print(
                "Weather regressions use mocked responses. No external requests or supplier orders are made."
            )
            print("Phase 5 complete. Stop before Phase 6 API.")
        except Exception:
            traceback.print_exc()
            code = 1
    output = buffer.getvalue()
    resolve_path(config, "phase_5_verification").write_text(output, encoding="utf-8")
    print(output, end="")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
