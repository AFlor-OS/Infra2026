from pathlib import Path
import yaml

def test_experiment_config_exists():
    path = Path(__file__).resolve().parents[1] / "config" / "experiments.yaml"
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert config["processes"] == [1, 2, 4, 8]
