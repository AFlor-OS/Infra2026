from pathlib import Path

import pandas as pd
import pytest

from analysis.report import generate_report


def create_campaign_files(campaign_dir: Path, mode: str):
    campaign_dir.mkdir(parents=True, exist_ok=True)

    if mode == "strong":
        experiment_rows = [
            {"mode": "strong", "n": 100, "processes": 1,
             "mean": 10.1, "std": 0.2, "cv": 0.02,
             "ci_low": 9.9, "ci_high": 10.3},
            {"mode": "strong", "n": 100, "processes": 2,
             "mean": 5.2, "std": 0.1, "cv": 0.019,
             "ci_low": 5.1, "ci_high": 5.3},
            {"mode": "strong", "n": 100, "processes": 4,
             "mean": 3.0, "std": 0.15, "cv": 0.05,
             "ci_low": 2.8, "ci_high": 3.2},
        ]
    else:
        experiment_rows = [
            {"mode": "weak", "n": 100, "processes": 1,
             "mean": 10.1, "std": 0.2, "cv": 0.02,
             "ci_low": 9.9, "ci_high": 10.3},
            {"mode": "weak", "n": 126, "processes": 2,
             "mean": 8.0, "std": 0.3, "cv": 0.0375,
             "ci_low": 7.7, "ci_high": 8.3},
        ]

    baseline = {
        "mode": "sequential",
        "n": 100,
        "processes": 1,
        "mean": 10.0,
        "std": 0.2,
        "cv": 0.02,
        "ci_low": 9.8,
        "ci_high": 10.2,
    }

    summary = pd.DataFrame([baseline] + experiment_rows)
    summary.to_csv(campaign_dir / "summary.csv", index=False)

    if mode == "strong":
        scaling_rows = [
            {"mode": "strong", "n": 100, "processes": 1,
             "speedup": 0.99, "efficiency": 0.99},
            {"mode": "strong", "n": 100, "processes": 2,
             "speedup": 1.92, "efficiency": 0.96},
            {"mode": "strong", "n": 100, "processes": 4,
             "speedup": 3.33, "efficiency": 0.83},
        ]
    else:
        scaling_rows = [
            {"mode": "weak", "n": 100, "processes": 1,
             "speedup": 0.99, "efficiency": 0.99},
            {"mode": "weak", "n": 126, "processes": 2,
             "speedup": 1.25, "efficiency": 0.99},
        ]

    pd.DataFrame(scaling_rows).to_csv(
        campaign_dir / "scaling.csv",
        index=False,
    )


def test_generate_report_creates_files(tmp_path):
    campaign_dir = tmp_path / "campaign"
    create_campaign_files(campaign_dir, "strong")

    output_dir = generate_report(campaign_dir)

    assert output_dir.exists()
    assert (output_dir / "runtime_table.csv").exists()
    assert (output_dir / "scaling_table.csv").exists()
    assert (output_dir / "results.md").exists()


def test_report_contains_strong_results(tmp_path):
    campaign_dir = tmp_path / "campaign"
    create_campaign_files(campaign_dir, "strong")

    output_dir = generate_report(campaign_dir)
    content = (output_dir / "results.md").read_text(encoding="utf-8")

    assert "# E2 - Escalabilidade forte" in content
    assert "Menor tempo médio paralelo: **3.0000 s**" in content
    assert "Maior speedup observado: **3.3300**" in content


def test_report_contains_weak_results(tmp_path):
    campaign_dir = tmp_path / "campaign"
    create_campaign_files(campaign_dir, "weak")

    output_dir = generate_report(campaign_dir)
    content = (output_dir / "results.md").read_text(encoding="utf-8")

    assert "# E3 - Escalabilidade fraca" in content
    assert "Na escalabilidade fraca" in content
    assert "Menor tempo médio paralelo: **8.0000 s**" in content


def test_report_fails_without_summary(tmp_path):
    campaign_dir = tmp_path / "campaign"
    campaign_dir.mkdir()

    with pytest.raises(FileNotFoundError):
        generate_report(campaign_dir)


def test_report_fails_without_scaling(tmp_path):
    campaign_dir = tmp_path / "campaign"
    campaign_dir.mkdir()

    pd.DataFrame([
        {"mode": "sequential", "n": 100, "processes": 1,
         "mean": 10.0, "std": 0.2, "cv": 0.02,
         "ci_low": 9.8, "ci_high": 10.2},
        {"mode": "strong", "n": 100, "processes": 2,
         "mean": 5.0, "std": 0.1, "cv": 0.02,
         "ci_low": 4.9, "ci_high": 5.1},
    ]).to_csv(campaign_dir / "summary.csv", index=False)

    with pytest.raises(FileNotFoundError):
        generate_report(campaign_dir)