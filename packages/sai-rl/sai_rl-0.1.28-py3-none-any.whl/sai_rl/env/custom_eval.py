import json
import hashlib
from pathlib import Path

from rich.prompt import Confirm
from rich.panel import Panel

from sai_rl.utils.config import config
from sai_rl.sai_console import SAIConsole

APPROVED_SCRIPTS_PATH = Path.home() / ".sai" / "approved_scripts.json"


def get_hash(script_string: str) -> str:
    return hashlib.sha256(script_string.encode("utf-8")).hexdigest()


def load_approved_hashes() -> set:
    if APPROVED_SCRIPTS_PATH.exists():
        with open(APPROVED_SCRIPTS_PATH, "r") as f:
            return set(json.load(f))
    return set()


def save_approved_hashes(hashes: set):
    APPROVED_SCRIPTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(APPROVED_SCRIPTS_PATH, "w") as f:
        json.dump(list(hashes), f)


def ask_custom_eval_approval(
    console: SAIConsole, competition_id: str, script_content: str
) -> bool:
    script_hash = get_hash(script_content)
    approved_hashes = load_approved_hashes()

    if script_hash in approved_hashes:
        return True

    console.print(
        Panel.fit(
            "[bold yellow]A custom evaluation function will be loaded.[/bold yellow]\n"
            "It wraps the environment's reward to match server benchmarking.\n\n"
            f"View script: [blue underline]{config.platform_url}/competitions/{competition_id}?tab=evaluation[/blue underline]\n"
            "Approve to allow this script to run in the future. You'll be asked again if it changes.\n\n"
            "[dim]To disable this prompt, set [bold]use_custom_eval=False[/bold] in sai.make_env or sai.benchmark.[/dim]",
            title="Script Approval Required",
        )
    )

    approved = Confirm.ask("Approve loading this evaluation function?", default=False)
    if approved:
        approved_hashes.add(script_hash)
        save_approved_hashes(approved_hashes)
    return approved
