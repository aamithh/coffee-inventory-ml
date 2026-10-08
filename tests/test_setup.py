"""Phase 0 smoke checks for the shared configuration contract."""

from pathlib import Path
import pytest
from src.utils.config import PROJECT_ROOT, load_config, resolve_path


def test_default_configuration() -> None:
    config = load_config()
    assert config["project"]["seed"] == 42
    assert len(config["menu"]) == 10
    assert len(config["materials"]) == 10
    assert set(config["recipes"]) == set(config["menu"])


def test_paths_do_not_depend_on_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = load_config()
    assert resolve_path(config, "raw") == PROJECT_ROOT / "data" / "raw"


def test_material_constraints() -> None:
    for material in load_config()["materials"].values():
        assert material["shelf_life_days"] > 0
        assert 1 <= material["lead_time_days"] <= 4
        assert material["unit_cost"] > 0
        assert material["min_order_qty"] > 0
        assert 0.03 <= material["wastage_factor"] <= 0.08
