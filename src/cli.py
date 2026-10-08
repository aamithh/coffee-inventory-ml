"""Windows-friendly command runner; incomplete phases fail explicitly."""

import argparse
import importlib
import json
import logging
import subprocess
import sys
from src.utils.config import PROJECT_ROOT, load_config
from src.utils.dates import date_context, validate_forecast_calendar


def main(argv: list[str] | None = None) -> int:
    """Dispatch a project command and return its process exit status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None, help="Optional alternative YAML configuration.")
    parser.add_argument(
        "command",
        choices=(
            "setup-check",
            "data",
            "features",
            "train",
            "inventory",
            "simulate",
            "api",
            "dashboard",
            "test",
        ),
    )
    arguments = parser.parse_args(argv)
    if arguments.command == "test":
        return subprocess.run(
            [sys.executable, "-m", "pytest", "-q"], cwd=PROJECT_ROOT, check=False
        ).returncode
    config = load_config(arguments.config)
    validate_forecast_calendar(config)
    if arguments.command == "setup-check":
        print(f"Python: {sys.version.split()[0]}")
        print(f"Executable: {sys.executable}")
        print(f"Virtual environment: {sys.prefix != sys.base_prefix}")
        for module in config["cli"]["setup_check_imports"]:
            importlib.import_module(module)
        print(f"Required library imports: {len(config['cli']['setup_check_imports'])} OK")
        print(json.dumps(date_context(config), indent=2))
        return subprocess.run([sys.executable, "-m", "pip", "check"], check=False).returncode
    if arguments.command == "dashboard":
        command = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(PROJECT_ROOT / "src" / "dashboard" / "app.py"),
            "--server.address",
            config["dashboard"]["host"],
            "--server.port",
            str(config["dashboard"]["port"]),
            "--theme.base",
            config["dashboard"]["theme"],
            "--theme.primaryColor",
            config["dashboard"]["colors"]["primary"],
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
        ]
        if arguments.config:
            command.extend(["--", "--config", arguments.config])
        return subprocess.run(command, cwd=PROJECT_ROOT, check=False).returncode
    if arguments.command == "api":
        import uvicorn
        from src.api.main import create_app

        if config["api"]["workers"] != 1:
            raise ValueError("Aggregate inventory persistence requires api.workers = 1.")
        uvicorn.run(
            create_app(config),
            host=config["api"]["host"],
            port=config["api"]["port"],
            log_level=config["api"]["log_level"],
        )
        return 0
    if arguments.command == "simulate":
        from src.inventory.simulation_report import run_simulation

        run_simulation(config)
        return 0
    if arguments.command == "inventory":
        from src.inventory.planner import run_inventory

        run_inventory(config)
        return 0
    if arguments.command == "train":
        from src.models.train import run_training

        run_training(config)
        return 0
    if arguments.command == "features":
        from src.eda.report import run_phase_2

        run_phase_2(config)
        return 0
    from src.data.generator import run_pipeline

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    print(json.dumps(run_pipeline(config), indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
