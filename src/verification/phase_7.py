"""Full Phase 7 checks with temporary live Streamlit startup and artifact integrity."""

from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import io
import json
import os
import socket
import subprocess
import sys
import time
import traceback
import httpx
import yaml
from PIL import Image
from src.data.quality import assert_no_truth_references
from src.utils.config import PROJECT_ROOT, load_config, resolve_path


def live_dashboard(config: dict) -> None:
    """Launch real dashboard CLI on a temporary loopback port, then stop it."""
    settings = deepcopy(config)
    with socket.socket() as allocation:
        allocation.bind(("127.0.0.1", 0))
        port = allocation.getsockname()[1]
    settings["dashboard"]["host"] = "127.0.0.1"
    settings["dashboard"]["port"] = port
    staging = resolve_path(config, "pipeline_staging")
    staging.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=staging, prefix="dashboard_verify_") as directory:
        config_path = Path(directory) / "config.yaml"
        config_path.write_text(yaml.safe_dump(settings, sort_keys=False), encoding="utf-8")
        log_path = Path(directory) / "dashboard.log"
        with log_path.open("w", encoding="utf-8") as log:
            process = subprocess.Popen(
                [sys.executable, "-m", "src.cli", "--config", str(config_path), "dashboard"],
                cwd=PROJECT_ROOT,
                stdout=log,
                stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            try:
                with httpx.Client(
                    base_url=f"http://127.0.0.1:{port}",
                    timeout=config["dashboard"]["request_timeout_seconds"],
                    trust_env=False,
                ) as client:
                    deadline = (
                        time.monotonic() + config["dashboard"]["verification_startup_seconds"]
                    )
                    while True:
                        if process.poll() is not None:
                            raise RuntimeError("Dashboard exited during startup.")
                        try:
                            response = client.get("/_stcore/health")
                            if response.status_code == 200 and response.text == "ok":
                                break
                        except httpx.TransportError:
                            pass
                        if time.monotonic() > deadline:
                            raise RuntimeError("Dashboard startup timed out.")
                        time.sleep(config["dashboard"]["verification_poll_seconds"])
                    print("Live dashboard CLI: HTTP 200 health=ok")
                    page = client.get("/")
                    assert page.status_code == 200 and "streamlit" in page.text.lower()
                    print("Live dashboard root: HTTP 200; Streamlit application shell available")
            finally:
                # CLI starts Streamlit as a child; stop this temporary process tree.
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                        capture_output=True,
                        check=False,
                    )
                else:
                    process.terminate()
                try:
                    process.wait(timeout=config["dashboard"]["verification_shutdown_seconds"])
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        print("Live dashboard output (complete):")
        print(log_path.read_text(encoding="utf-8"), end="")


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
        "simulation",
        "simulation_metrics",
        "simulation_forecasts",
    )
    before = {
        key: hashlib.sha256(resolve_path(config, key).read_bytes()).hexdigest() for key in keys
    }
    inventory_path = resolve_path(config, "api_inventory_state")
    inventory_before = inventory_path.read_bytes() if inventory_path.exists() else None
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
                print("$ " + " ".join(args))
                result = subprocess.run(args, cwd=PROJECT_ROOT, capture_output=True, text=True)
                print(result.stdout, end="")
                print(result.stderr, end="")
                print(f"exit_code={result.returncode}")
                if result.returncode:
                    raise RuntimeError("Verification command failed.")
            live_dashboard(config)
            assert_no_truth_references(config)
            print(
                "Seven screens, stock/scenario forms, conflicts, export and HTTP backend: AppTest checks PASS"
            )
            print("Protected feature/model source reference scan: PASS")
            for filename in ("overview.jpg", "demand_forecast.jpg", "model_performance.jpg"):
                path = resolve_path(config, "dashboard_screenshots") / filename
                with Image.open(path) as image:
                    image.verify()
                print(f"Browser screenshot: {filename}; valid JPEG ({path.stat().st_size} bytes)")
            print("Prior source artifacts unchanged (SHA-256):")
            for key, digest in before.items():
                same = digest == hashlib.sha256(resolve_path(config, key).read_bytes()).hexdigest()
                print(f"{key}: {digest}; unchanged={same}")
                assert same
            assert (
                inventory_path.read_bytes() if inventory_path.exists() else None
            ) == inventory_before
            print("Persistent demo inventory unchanged: PASS")
            manifest = json.loads(
                (resolve_path(config, "backup_pre_1_5") / "manifest.json").read_text()
            )
            for record in manifest:
                assert (
                    hashlib.sha256((PROJECT_ROOT / record["backup"]).read_bytes()).hexdigest()
                    == record["backup_sha256"]
                )
            print(f"Pre-1.5 backup integrity: {len(manifest)} artifacts unchanged")
            print("Weather regressions use mocks; live startup uses only loopback HTTP.")
            print("Phase 7 complete. Stop before Phase 8 final quality/docs.")
        except Exception:
            traceback.print_exc()
            code = 1
    transcript = output.getvalue()
    resolve_path(config, "phase_7_verification").write_text(transcript, encoding="utf-8")
    print(transcript, end="")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
