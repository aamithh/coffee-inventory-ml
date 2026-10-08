"""Reproduce and print the complete Phase 1.5 verification transcript."""

from contextlib import closing, redirect_stdout, redirect_stderr
from copy import deepcopy
import hashlib
import io
import json
import logging
import sqlite3
import subprocess
import sys
import pandas as pd
from src.utils.config import PROJECT_ROOT, load_config, resolve_path
from src.data.generator import run_pipeline, generate_dataset
from src.data.loader import load_sales
from src.data.truth_loader import load_truth
from src.data.quality import (
    reconcile_sales,
    weather_effects,
    residual_correlation,
    assert_no_truth_references,
)
from src.utils.dates import date_context


def command(args):
    print("$ " + " ".join(args))
    result = subprocess.run(args, cwd=PROJECT_ROOT, capture_output=True, text=True)
    print(result.stdout, end="")
    print(result.stderr, end="")
    print("exit_code=" + str(result.returncode))
    return result.returncode


def digest(config):
    result = {}
    for key in ("sales_csv", "truth_csv", "weather_cache"):
        result[key] = hashlib.sha256(resolve_path(config, key).read_bytes()).hexdigest()
    for key, table in (
        ("database", "sales"),
        ("database", "weather"),
        ("truth_database", "simulation_truth"),
    ):
        with closing(sqlite3.connect(resolve_path(config, key))) as db:
            order = '"date", "item"' if table != "weather" else '"date"'
            rows = db.execute(f'SELECT * FROM "{table}" ORDER BY {order}').fetchall()
            result[key + ":" + table] = hashlib.sha256(
                json.dumps(rows, separators=(",", ":")).encode()
            ).hexdigest()
    return result


def verify():
    config = load_config()
    python = sys.executable
    for args in (
        [python, "-m", "pytest", "-q"],
        [python, "-m", "ruff", "check", "src", "tests"],
        [python, "-m", "ruff", "format", "--check", "src", "tests"],
        [python, "-m", "src.cli", "setup-check"],
    ):
        assert command(args) == 0
    for name in ("train", "simulate", "api", "dashboard"):
        assert command([python, "-m", "src.cli", name]) == 2
    print("PIPELINE RUN 1")
    run_pipeline(config)
    first = digest(config)
    print("PIPELINE RUN 2")
    summary = run_pipeline(config)
    second = digest(config)
    print("CSV and database CONTENT SHA-256 (run 1 / run 2)")
    for key in first:
        print(f"{key}: {first[key]} / {second[key]} identical={first[key] == second[key]}")
    assert first == second
    sales, truth = load_sales(config), load_truth(config)
    print("Reconciliation:")
    print(json.dumps(reconcile_sales(sales, truth), indent=2))
    closed = sales.loc[sales.closure_flag.eq(1)]
    closure_truth = truth.loc[truth.date.isin(closed.date)]
    assert closed.groupby("date").size().eq(len(config["menu"])).all()
    assert closed.sales.eq(0).all() and closure_truth.latent_demand.eq(0).all()
    print(
        f"Closure days={closed.date.nunique()}, rows={len(closed)}, all 10 items zero observed and latent=True"
    )
    observed = sales.sales.dropna()
    print(
        f"Negative observed counts={int(observed.lt(0).sum())}; noninteger observed counts={int(observed.mod(1).ne(0).sum())}"
    )
    assert observed.ge(0).all() and observed.mod(1).eq(0).all()
    print("Clean-row weather comparisons (actual descriptive means):")
    effects = weather_effects(sales, config)
    for item, values in effects.items():
        names = (
            ("hot_mean", "normal_mean")
            if item in config["quality"]["cold_items"]
            else ("rainy_mean", "dry_mean")
        )
        values["expected_direction_observed"] = values[names[0]] > values[names[1]]
    print(json.dumps(effects, indent=2))
    print("Per-item promotion counts:")
    promotions = sales.groupby("item").promo_flag.sum().astype(int).to_dict()
    print(json.dumps(promotions, indent=2))
    assert min(promotions.values()) >= 40
    baseline = deepcopy(config)
    baseline["generator"]["shop_daily_shock"]["sigma"] = 0
    weather = pd.read_csv(resolve_path(config, "weather_cache"), parse_dates=["date"])
    baseline_truth = generate_dataset(baseline, weather=weather)[1]
    before, after = residual_correlation(baseline_truth), residual_correlation(truth)
    print(
        f"Mean cross-item normalized residual correlation: sigma=0 {before}; sigma=0.07 {after}; increase={after - before}"
    )
    assert after > before
    print("Exclusive record statuses:")
    print(json.dumps(summary["record_status_counts"], indent=2))
    assert sum(summary["record_status_counts"].values()) == len(sales)
    print(f"Training-eligible rows={int(sales.usable_for_training.sum())}")
    print("As-of, chronological splits, drift:")
    print(json.dumps(date_context(config), indent=2))
    assert_no_truth_references(config)
    print("Protected-folder truth reference scan: PASS")
    for key in ("database", "truth_database"):
        with closing(sqlite3.connect(resolve_path(config, key))) as db:
            tables = [
                row[0]
                for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
            ]
            integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
            mode = db.execute("PRAGMA journal_mode").fetchone()[0]
            print(f"{key}: tables={tables}; integrity={integrity}; journal_mode={mode}")
            assert integrity == "ok" and mode == "delete"
            if key == "database":
                assert "simulation_truth" not in tables
    manifest = json.loads((resolve_path(config, "backup_pre_1_5") / "manifest.json").read_text())
    for record in manifest:
        assert (
            hashlib.sha256((PROJECT_ROOT / record["backup"]).read_bytes()).hexdigest()
            == record["backup_sha256"]
        )
    print(f"Pre-patch backup integrity: {len(manifest)} artifacts unchanged")
    print(
        "Weather API outage/recovery verified with mocked responses; real historical cache reused."
    )
    print(
        "2027 lunar festival extension: TODO; pinned holiday data does not supply reliable Holi; missing coverage raises a tested validation error."
    )
    print("Phase 1.5 verification complete. Phase 2 has not started.")


def main():
    buffer = io.StringIO()
    code = 0
    with redirect_stdout(buffer), redirect_stderr(buffer):
        logging.basicConfig(level=logging.INFO, stream=buffer, force=True)
        try:
            verify()
        except Exception:
            import traceback

            traceback.print_exc()
            code = 1
    output = buffer.getvalue()
    path = resolve_path(load_config(), "verification_output")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(output, encoding="utf-8")
    print(output, end="")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
