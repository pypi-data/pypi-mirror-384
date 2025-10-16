"""Utilities to execute campaign CLI plans emitted by the FastMCP planner."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, MutableMapping, Optional, Sequence, TextIO


@dataclass(slots=True)
class CliAction:
    """Represents a single CLI invocation described by the planner."""

    step: str
    description: str
    command: Sequence[str]

    def to_dict(self) -> Dict[str, object]:
        return {
            "step": self.step,
            "description": self.description,
            "command": list(self.command),
        }


def execute_cli_actions(
    actions: Iterable[Dict[str, object] | CliAction],
    *,
    project_root: Optional[str] = None,
    env: Optional[MutableMapping[str, str]] = None,
    stream: TextIO = sys.stdout,
) -> List[int]:
    """Execute planner-supplied CLI actions sequentially.

    Parameters
    ----------
    actions:
        Iterable of planner actions. Each action must be a mapping with
        ``step``, ``description``, and ``command`` keys (matching the planner
        output) or an explicit :class:`CliAction` instance.
    project_root:
        Working directory for command execution. Defaults to the current
        working directory when ``None``.
    env:
        Optional environment overrides. When provided, keys extend the current
        process environment.
    stream:
        IO stream for progress messages.

    Returns
    -------
    list[int]
        Return codes for each executed command in order. Execution stops after
        the first non-zero return code.
    """

    cwd = Path(project_root).expanduser().resolve(strict=False) if project_root else Path.cwd()
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    results: List[int] = []
    for raw in actions:
        action = _coerce_action(raw)
        stream.write(f"[imagemcp] step={action.step} -> {' '.join(action.command)}\n")
        stream.flush()
        completed = subprocess.run(
            list(action.command),
            cwd=str(cwd),
            env=merged_env,
            check=False,
        )
        results.append(completed.returncode)
        if completed.returncode != 0:
            stream.write(
                f"[imagemcp] step={action.step} failed with exit code {completed.returncode}\n"
            )
            stream.flush()
            break
    return results


def _coerce_action(payload: Dict[str, object] | CliAction) -> CliAction:
    if isinstance(payload, CliAction):
        return payload
    if not isinstance(payload, dict):  # pragma: no cover - defensive
        raise TypeError("Planner actions must be dicts or CliAction instances")
    try:
        step = str(payload["step"])
        description = str(payload.get("description", step))
        command = payload["command"]
    except KeyError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Missing required action field: {exc.args[0]}") from exc
    if not isinstance(command, Sequence):  # pragma: no cover - defensive
        raise TypeError("Action 'command' must be a sequence of strings")
    return CliAction(step=step, description=description, command=list(command))


__all__ = ["CliAction", "execute_cli_actions"]

