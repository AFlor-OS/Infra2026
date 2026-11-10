from pathlib import Path

from analysis.report import generate_report


campaigns = [
    "e5ece5bf-b895-4693-bcc2-ad9b4bc5ce54",
    "ddb7eabf-3584-414a-ade5-816ff1dac410",
]

for campaign_id in campaigns:
    campaign_dir = Path("data/processed") / campaign_id

    print(f"\nProcessando campanha: {campaign_id}")
    generate_report(campaign_dir)