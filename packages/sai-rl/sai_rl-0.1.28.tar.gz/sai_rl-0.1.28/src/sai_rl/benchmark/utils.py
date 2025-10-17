from typing import Optional, Union

import numpy as np
import time

from rich.table import Table
from rich.panel import Panel
from rich.align import Align

from sai_rl.sai_console import SAIConsole


def generate_table(
    console: SAIConsole,
    timestep: int = 0,
    active_count: int = 0,
    num_envs: int = 0,
    current_score: Union[float, np.float64] = 0,
    current_fps: float = 0,
    time_elapsed: float = 0,
    timeout: Optional[int] = None,
) -> Table:
    table = console.table(title=None, show_header=True, show_lines=False)
    table.add_column("Steps", justify="center", style="cyan")
    table.add_column("Finished Envs", justify="center", style="green")
    table.add_column("Completed", justify="center", style="magenta")
    table.add_column("Avg Score", justify="center", style="green")
    table.add_column("FPS", justify="center", style="blue")
    table.add_column("Time", justify="center", style="yellow")
    table.add_column("Remaining", justify="center", style="red")

    completed = num_envs - active_count
    completion_percentage = (
        f"{(completed / num_envs) * 100:.1f}%" if num_envs > 0 else "0%"
    )

    table.add_row(
        str(timestep),
        f"{completed}/{num_envs}",
        completion_percentage,
        f"{current_score:.2f}",
        f"{current_fps:.1f}",
        f"{time_elapsed:.1f}s",
        f"{timeout - time_elapsed:.1f}s" if timeout else "0.0s",
    )

    return table


def generate_batch_panel(
    console: SAIConsole,
    batch_active_count: int = 0,
    batch_size: int = 0,
    batch_idx: int = 0,
    batch_start_time: float = 0,
    batch_score: float = 0,
    batch_timesteps: int = 0,
    batch_timeout: Optional[int] = None,
    num_envs: int = 0,
    num_batches: int = 0,
    is_final: bool = False,
) -> Panel:
    now = time.time() - batch_start_time
    fps_now = batch_timesteps / now if now > 0 else 0
    table = generate_table(
        console,
        batch_timesteps,
        batch_active_count if not is_final else 0,
        batch_size,
        batch_score,
        fps_now,
        now,
        batch_timeout if not is_final else 0,
    )
    return console.panel(
        Align.center(table),
        title=f"Evaluation Progress (Batch {batch_idx + 1}/{num_batches})",
        subtitle=f"{(batch_size - (batch_active_count if not is_final else 0) + batch_idx * batch_size)}/{num_envs} envs",
        border_style="blue",
        title_align="center",
    )
