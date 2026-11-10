from pathlib import Path
import yaml


def test_experiment_config_exists():
    path = (
        Path(__file__).resolve().parents[1]
        / "config"
        / "experiments.yaml"
    )

    assert path.exists()

    config = yaml.safe_load(path.read_text(encoding="utf-8"))

    strong = config["experiments"]["strong"]
    weak = config["experiments"]["weak"]

    assert strong["scenario"] == "E2"
    assert strong["matrix_size"] == 4960
    assert strong["processes"] == [1, 2, 4, 8]

    assert weak["scenario"] == "E3"
    assert weak["processes"] == [1, 2, 4, 8]
    assert weak["enabled"] is True