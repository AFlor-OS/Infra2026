
import json
import uuid

from datetime import datetime, timezone
from pathlib import Path

from orchestrator.runner import get_environment, get_git_commit

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGNS_FILE = ROOT / "data" / "campaigns.json"


def load_campaigns() -> list[dict]:
    """Carrega o histórico de campanhas."""
    if not CAMPAIGNS_FILE.exists():
        return []

    with CAMPAIGNS_FILE.open(encoding="utf-8") as file:
        return json.load(file)


def save_campaigns(campaigns: list[dict]) -> None:
    """Salva o histórico de forma atômica."""
    CAMPAIGNS_FILE.parent.mkdir(parents=True, exist_ok=True)

    temporary_file = CAMPAIGNS_FILE.with_suffix(".tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(campaigns, file, indent=2, ensure_ascii=False)

    temporary_file.replace(CAMPAIGNS_FILE)


def create_campaign(config: dict) -> str:
    """Cria uma campanha e registra seus metadados."""
    campaign_id = str(uuid.uuid4())

    campaign = {
        "campaign_id": campaign_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "finished_at_utc": None,
        "status": "running",
        "git_commit": get_git_commit(),
        "environment": get_environment("mpi"),
        "config": config,
    }

    campaigns = load_campaigns()
    campaigns.append(campaign)
    save_campaigns(campaigns)

    print(f"Campanha iniciada: {campaign_id}")

    return campaign_id


def finish_campaign(
    campaign_id: str,
    status: str = "completed",
    error: str | None = None,
) -> None:
    """Atualiza o estado final de uma campanha."""
    campaigns = load_campaigns()

    for campaign in campaigns:
        if campaign["campaign_id"] == campaign_id:
            campaign["finished_at_utc"] = (
                datetime.now(timezone.utc).isoformat()
            )
            campaign["status"] = status

            if error:
                campaign["error"] = error

            save_campaigns(campaigns)
            print(f"Campanha {campaign_id}: {status}")
            return

    raise ValueError(f"Campanha não encontrada: {campaign_id}")
