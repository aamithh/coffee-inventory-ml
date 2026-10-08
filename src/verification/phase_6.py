"""Full Phase 6 checks, live loopback API smoke test and immutable-source audit."""

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
from src.data.quality import assert_no_truth_references
from src.utils.config import PROJECT_ROOT, load_config, resolve_path


def live_smoke(config: dict) -> None:
    """Launch the real CLI server on an ephemeral loopback port and always stop it."""
    settings = deepcopy(config)
    with socket.socket() as allocation:
        allocation.bind(("127.0.0.1", 0))
        port = allocation.getsockname()[1]
    settings["api"]["host"] = "127.0.0.1"
    settings["api"]["port"] = port
    staging = resolve_path(config, "pipeline_staging")
    staging.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=staging, prefix="api_verify_") as directory:
        config_path = Path(directory) / "config.yaml"
        config_path.write_text(yaml.safe_dump(settings, sort_keys=False), encoding="utf-8")
        log_path = Path(directory) / "server.log"
        with log_path.open("w", encoding="utf-8") as log:
            process = subprocess.Popen(
                [sys.executable, "-m", "src.cli", "--config", str(config_path), "api"],
                cwd=PROJECT_ROOT,
                stdout=log,
                stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            try:
                deadline = time.monotonic() + config["api"]["verification_startup_seconds"]
                with httpx.Client(
                    base_url=f"http://127.0.0.1:{port}",
                    timeout=config["api"]["verification_request_seconds"],
                    trust_env=False,
                ) as client:
                    while True:
                        if process.poll() is not None:
                            raise RuntimeError("API server exited during startup.")
                        try:
                            response = client.get("/health")
                            if response.status_code == 200:
                                break
                        except httpx.TransportError:
                            pass
                        if time.monotonic() > deadline:
                            raise RuntimeError("API startup timed out.")
                        time.sleep(config["api"]["verification_poll_seconds"])
                    assert response.json()["status"] == "ready"
                    print("Live CLI API: loopback startup and ready health PASS")
                    for path, key, count in (
                        ("/forecast/items?days=1", "forecasts", 10),
                        ("/forecast/materials?days=1", "requirements", 10),
                        ("/recommendations/orders", "recommendations", 10),
                        ("/inventory", "rows", 10),
                    ):
                        result = client.get(path)
                        assert result.status_code == 200 and len(result.json()[key]) == count
                        print(f"GET {path}: HTTP {result.status_code}; {count} rows")
                    result = client.get("/model/metrics")
                    assert (
                        result.status_code == 200
                        and result.json()["metrics"]["selected_point_model"] == "lightgbm"
                    )
                    print(
                        "GET /model/metrics: HTTP 200; saved model/simulation measurements available"
                    )
                    result = client.post(
                        "/whatif",
                        json={
                            "days": 1,
                            "promotions": {"latte": True},
                            "temp_max": 35,
                            "temp_min": 25,
                            "rainfall": 0,
                            "festivals": {"2025-07-20": True},
                        },
                    )
                    assert result.status_code == 200 and result.json()["scenario"]["scenario"]
                    print(
                        f"POST /whatif: HTTP 200; point-total change={result.json()['point_total_change']:.6f}"
                    )
                    result = client.get("/forecast/items?days=31")
                    assert result.status_code == 422
                    print("GET /forecast/items?days=31: HTTP 422; limit validation PASS")
                    assert client.get("/docs").status_code == 200
                    schema = client.get("/openapi.json")
                    assert schema.status_code == 200 and len(schema.json()["paths"]) == 7
                    schema_path = resolve_path(config, "api_schema")
                    schema_path.parent.mkdir(parents=True, exist_ok=True)
                    schema_path.write_text(json.dumps(schema.json(), indent=2), encoding="utf-8")
                    print(
                        "GET /docs and /openapi.json: HTTP 200; seven business paths, eight endpoint operations"
                    )
            finally:
                # Windows venv launchers can retain a child holding the log open.
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                        capture_output=True,
                        check=False,
                    )
                else:
                    process.terminate()
                try:
                    process.wait(timeout=config["api"]["verification_shutdown_seconds"])
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        print("Live server output (complete):")
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
    state = resolve_path(config, "api_inventory_state")
    state_before = state.read_bytes() if state.exists() else None
    buffer = io.StringIO()
    code = 0
    with redirect_stdout(buffer), redirect_stderr(buffer):
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
            live_smoke(config)
            assert_no_truth_references(config)
            print("Protected feature/model source reference scan: PASS")
            print("Prior source artifacts unchanged (SHA-256):")
            for key, digest in before.items():
                same = digest == hashlib.sha256(resolve_path(config, key).read_bytes()).hexdigest()
                print(f"{key}: {digest}; unchanged={same}")
                assert same
            assert (state.read_bytes() if state.exists() else None) == state_before
            print("Live smoke leaves persistent inventory state unchanged: PASS")
            manifest = json.loads(
                (resolve_path(config, "backup_pre_1_5") / "manifest.json").read_text()
            )
            for record in manifest:
                assert (
                    hashlib.sha256((PROJECT_ROOT / record["backup"]).read_bytes()).hexdigest()
                    == record["backup_sha256"]
                )
            print(f"Pre-1.5 backup integrity: {len(manifest)} artifacts unchanged")
            print("Weather regressions use mocks; live smoke uses only local loopback HTTP.")
            print("Phase 6 complete. Stop before Phase 7 dashboard.")
        except Exception:
            traceback.print_exc()
            code = 1
    output = buffer.getvalue()
    resolve_path(config, "phase_6_verification").write_text(output, encoding="utf-8")
    print(output, end="")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
