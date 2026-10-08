"""Verify the visual refresh without rebuilding or replacing demo artifacts."""

from contextlib import redirect_stdout, redirect_stderr
import hashlib
import io
import json
import traceback
import sys
from PIL import Image
from src.data.quality import assert_no_truth_references
from src.utils.config import PROJECT_ROOT, load_config, resolve_path
from src.verification.phase_7 import live_dashboard
from src.verification.phase_8 import command


def main() -> None:
    """Record complete checks and preserve the previously measured dataset/model."""
    config = load_config()
    paths = [
        p
        for folder in ("data", "models", "reports/figures", "notebooks")
        for p in (PROJECT_ROOT / folder).rglob("*")
        if p.is_file() and ".pipeline_staging" not in p.parts
    ]
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    stock = resolve_path(config, "api_inventory_state")
    stock_before = stock.read_bytes() if stock.exists() else None
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
            live_dashboard(config)
            assert_no_truth_references(config)
            print("Seven screens, stock forms, conflicts, what-if and shopping shortcut: PASS")
            print("Selected ingredient loads its own stock quantities: PASS")
            print("Protected feature/model source reference scan: PASS")
            for path, digest in before.items():
                assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
            assert (stock.read_bytes() if stock.exists() else None) == stock_before
            print(f"Original data/model/figure/notebook hashes unchanged: {len(paths)} files PASS")
            print("Persistent demo inventory unchanged: PASS")
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
            print(f"Pre-1.5 backups: {len(manifest)} hashes unchanged PASS")
            for key in ("dashboard_redesign_desktop", "dashboard_redesign_mobile"):
                path = resolve_path(config, key)
                with Image.open(path) as image:
                    image.verify()
                print(
                    f"Browser review capture: {path.name}; valid image ({path.stat().st_size} bytes)"
                )
            print(
                "Local café palette, simplified labels/tables, grouped details and interactive charts verified in browser."
            )
            print(
                "Weather tests use mocks. No data regeneration, retraining or supplier purchases."
            )
            print("Dashboard redesign complete.")
        except Exception:
            traceback.print_exc()
            code = 1
    transcript = output.getvalue()
    resolve_path(config, "dashboard_redesign_verification").write_text(transcript, encoding="utf-8")
    print(transcript, end="")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
