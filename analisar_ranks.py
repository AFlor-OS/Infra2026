import json
from pathlib import Path
from collections import defaultdict
from statistics import mean

campaign = "ddb7eabf-3584-414a-ade5-816ff1dac410"

timings = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
files_found = 0

for path in Path("data/raw").glob("*.json"):
    try:
        data = json.loads(path.read_text())

        if data.get("campaign_id") != campaign:
            continue

        result = data.get("result", data)

        if "rank_timings" not in result:
            continue

        files_found += 1
        processes = result["processes"]

        for item in result["rank_timings"]:
            rank = item["rank"]

            for metric in [
                "total_seconds",
                "compute_seconds",
                "communication_seconds",
                "gather_seconds",
            ]:
                timings[processes][rank][metric].append(item[metric])

    except (KeyError, TypeError, json.JSONDecodeError):
        continue

print(f"Arquivos MPI analisados: {files_found}")

for processes in sorted(timings):
    print(f"\n=== {processes} processos ===")
    print("Rank | Total | Compute | Comm. | Gather")

    for rank in sorted(timings[processes]):
        values = timings[processes][rank]

        print(
            f"{rank:4} | "
            f"{mean(values['total_seconds']):6.3f} | "
            f"{mean(values['compute_seconds']):7.3f} | "
            f"{mean(values['communication_seconds']):5.3f} | "
            f"{mean(values['gather_seconds']):6.3f}"
        )