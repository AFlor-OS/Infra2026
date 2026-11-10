from pathlib import Path

from analysis.plots import generate_campaign_plots


campaigns = [
    {
        "id": "e5ece5bf-b895-4693-bcc2-ad9b4bc5ce54",
        "mode": "strong",
        "name": "E2",
    },
    {
        "id": "ddb7eabf-3584-414a-ade5-816ff1dac410",
        "mode": "weak",
        "name": "E3",
    },
]

for campaign in campaigns:
    campaign_dir = (
        Path("data/processed") / campaign["id"]
    )

    output_dir = campaign_dir / "plots"

    generate_campaign_plots(
        campaign_dir=campaign_dir,
        output_dir=output_dir,
        mode=campaign["mode"],
        experiment_name=campaign["name"],
    )

    print(f"Gráficos de {campaign['name']} gerados em {output_dir}")