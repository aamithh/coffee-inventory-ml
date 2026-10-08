"""Record full Phase 4 verification, including immutable source and backup checks."""

from contextlib import redirect_stdout, redirect_stderr
import hashlib
import io
import json
import subprocess
import sys
import traceback
import numpy as np
import pandas as pd
from src.data.quality import assert_no_truth_references
from src.inventory.requirements import material_requirements
from src.inventory.reorder import recommend_orders, planning_horizon
from src.utils.config import PROJECT_ROOT, load_config, resolve_path


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
                    "inventory",
                ],
            ):
                print("$ " + " ".join(args))
                result = subprocess.run(args, cwd=PROJECT_ROOT, capture_output=True, text=True)
                print(result.stdout, end="")
                print(result.stderr, end="")
                print(f"exit_code={result.returncode}")
                if result.returncode:
                    raise RuntimeError("Verification command failed.")
            assert_no_truth_references(config)
            print("Protected feature/model source reference scan: PASS")
            forecast = pd.read_csv(
                resolve_path(config, "inventory_forecasts"), parse_dates=["date"]
            )
            saved = pd.read_csv(resolve_path(config, "material_requirements"), parse_dates=["date"])
            expected = material_requirements(forecast, config)
            pd.testing.assert_frame_equal(expected, saved, check_exact=False, rtol=1e-12, atol=1e-9)
            origin = forecast.origin.iloc[0]
            snapshot = pd.read_csv(resolve_path(config, "inventory_snapshot"))
            orders = recommend_orders(saved, snapshot, origin, config)
            exported = pd.read_csv(resolve_path(config, "inventory_orders"))
            assert len(orders) == len(config["materials"])
            np.testing.assert_allclose(orders.order_qty, exported.order_qty, rtol=1e-12, atol=1e-9)
            for row in orders.itertuples():
                material = config["materials"][row.material]
                multiple = material.get("order_multiple", material["min_order_qty"])
                assert (
                    row.coverage_days
                    <= material["shelf_life_days"] - config["inventory"]["buffer_days"]
                )
                assert row.order_qty <= row.max_order_quantity + 1e-8
                assert abs(row.order_qty / multiple - round(row.order_qty / multiple)) < 1e-8
                assert row.order_qty == 0 or row.order_qty >= material["min_order_qty"] - 1e-8
            print(
                f"Forecast/BOM recomputation: PASS; {len(forecast)} item rows, {len(saved)} material rows, {planning_horizon(config)} days"
            )
            print("Ten-material recommendation replay, expiry caps, MOQ and pack multiples: PASS")
            for key in (
                "inventory_bom",
                "inventory_forecasts",
                "material_requirements",
                "inventory_snapshot",
                "inventory_orders",
            ):
                raw = resolve_path(config, key).read_bytes()
                assert b"\r\r\n" not in raw
            print("CSV newline audit: PASS; no doubled carriage returns")
            print("Recommendations (complete):")
            print(
                orders[
                    [
                        "material",
                        "unit",
                        "order_now",
                        "order_qty",
                        "safety_stock",
                        "pre_arrival_shortfall",
                        "unmet_order_quantity",
                        "reason",
                    ]
                ].to_string(index=False)
            )
            print("No source artifacts changed (SHA-256):")
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
                "Weather regression tests use mocked API responses; inventory planning uses existing cached observations."
            )
            print("Phase 4 complete. Stop before Phase 5 simulation.")
        except Exception:
            traceback.print_exc()
            code = 1
    output = buffer.getvalue()
    resolve_path(config, "phase_4_verification").write_text(output, encoding="utf-8")
    print(output, end="")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
