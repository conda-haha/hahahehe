"""Prepare InterCode SFT training dataset from the validator-mounted miner dataset.

Reads ``gradients-io-tournaments/intercode_bigcode_combined_12k`` from the
validator-mounted miner datasets directory and converts each example to per-step
ReAct training pairs that exactly match the eval format.

Each output row:
    {"messages": [
        {"role": "user",      "content": "<REACT_INIT_MSG + DEMO_BASH_REACT + question + 'Thought 1:'>"},
        {"role": "assistant", "content": " <thought>\\nAction 1: execute[<gold_command>]"},
    ]}

One example per dataset row (execute step only — no submit step, since we have no
real observation for the gold command output).

The user message matches what eval_intercode._run_react_episode() sends to the
model (REACT_INIT_MSG + DEMO_BASH_REACT + question + prior turns + "Thought N:"),
so the model's training distribution aligns with its inference distribution.

Dataset path convention (follows miner_dataset_loader.py):
    MINER_DATASETS_DIR/<hf_org>--<hf_repo>/   (-- replaces / in the HF repo name)
    MINER_DATASETS is a comma-separated list of those directory names.

Usage (run from /workspace/scripts/):
    python -m envs.intercode_dataset --output_path /path/to/dataset
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from datasets import Dataset, DatasetDict

from envs.intercode_format import build_step_prompt
from envs.miner_dataset_loader import _get_miner_datasets_inventory, _load_one_dataset

INTERCODE_HF_REPO = "gradients-io-tournaments/intercode_bigcode_combined_12k"


# ---------------------------------------------------------------------------
# Dataset lookup
# ---------------------------------------------------------------------------

def _find_intercode_dataset() -> tuple[str, Path] | None:
    """Return (hf_name, local_path) for the intercode dataset, or None."""
    for hf_name, local in _get_miner_datasets_inventory():
        if "intercode" in hf_name.lower():
            return hf_name, local
    return None


# ---------------------------------------------------------------------------
# Row converters
# ---------------------------------------------------------------------------


def _gold_to_examples(query: str, gold: str) -> list[dict[str, Any]]:
    """Build a 1-step training example: given the question, execute the gold command.

    We only generate the execute step, not a submit step, because we have no real
    observation for the gold command's output. Training on a fake empty observation
    would teach the model that bash commands always produce empty output, which is
    wrong. The few-shot examples in DEMO_BASH_REACT already demonstrate the submit
    step pattern.
    """
    user1 = build_step_prompt(query, [], 1)
    asst1 = f" I need to run the appropriate bash command.\nAction 1: execute[{gold}]"
    return [{"messages": [
        {"role": "user",      "content": user1},
        {"role": "assistant", "content": asst1},
    ]}]



_PYTHON_PROSE_MARKERS = (
    "```",       # markdown code block (Python explanations use ```python ... ```)
    "def ",      # Python function definition
    "import ",   # Python import statement
    "class ",    # Python class definition
)


def _is_bash_response(response: str) -> bool:
    """Return True if response looks like a bash command rather than Python/prose.

    The dataset is 50% Python coding problems (BigCode) and 50% bash commands
    (Tellina/NL2Bash). Python responses contain markdown code fences, def/import/class
    keywords, and verbose prose explanation. Bash commands are compact and lack these.
    """
    if any(marker in response for marker in _PYTHON_PROSE_MARKERS):
        return False
    # Prose explanations are long multi-paragraph text; bash commands are compact
    if len(response) > 400:
        return False
    return True


def _row_to_react_examples(row: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert one intercode_bigcode_combined_12k row to a ReAct training example.

    The dataset is ~50% Python coding problems (response = prose + code) and ~50%
    bash commands (response = shell command). Only bash rows are kept; Python rows
    are silently skipped because wrapping prose in execute[...] would be wrong.
    """
    instruction = (row.get("instruction") or "").strip()
    response = (row.get("response") or "").strip()
    if not instruction or not response:
        return []
    if not _is_bash_response(response):
        return []
    return _gold_to_examples(instruction, response)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_intercode_sft_dataset() -> DatasetDict | None:
    """Find and convert the InterCode miner dataset; return DatasetDict or None."""
    found = _find_intercode_dataset()
    if found is None:
        print(
            f"[intercode_dataset] '{INTERCODE_HF_REPO}' not found in miner dataset inventory.\n"
            "  Make sure MINER_DATASETS includes "
            "'gradients-io-tournaments--intercode_bigcode_combined_12k' "
            "and MINER_DATASETS_DIR is set.",
            flush=True,
        )
        return None

    hf_name, local = found
    print(f"[intercode_dataset] Loading {hf_name} from {local}", flush=True)

    raw = _load_one_dataset(local)
    if raw is None:
        print(f"[intercode_dataset] Failed to load dataset from {local}", flush=True)
        return None

    print(f"[intercode_dataset] Loaded {len(raw)} rows", flush=True)

    all_examples: list[dict[str, Any]] = []
    skipped = 0
    for row in raw:
        examples = _row_to_react_examples(dict(row))
        if examples:
            all_examples.extend(examples)
        else:
            skipped += 1

    print(
        f"[intercode_dataset] Converted to {len(all_examples)} step-examples "
        f"({skipped}/{len(raw)} rows skipped)",
        flush=True,
    )

    if not all_examples:
        return None

    return DatasetDict({"train": Dataset.from_list(all_examples)})


def main() -> None:
    p = argparse.ArgumentParser(
        description="Convert the InterCode whitelisted dataset to SFT training format."
    )
    p.add_argument("--output_path", required=True, help="Where to save the DatasetDict")
    args = p.parse_args()

    dd = build_intercode_sft_dataset()
    if dd is None:
        sys.exit(1)

    dd.save_to_disk(args.output_path)
    print(
        f"[intercode_dataset] Saved {len(dd['train'])} examples → {args.output_path}",
        flush=True,
    )


if __name__ == "__main__":
    main()
