#!/usr/bin/env python
"""Download the scan-model checkpoint into MODEL_DIR.

    python scripts/fetch_model.py                  # default repo from settings
    python scripts/fetch_model.py --repo owner/name --dest ./models/my-model

The checkpoint must be a Hugging Face image-classification model. If its class labels
differ from the default HAM10000 names, set MODEL_LABEL_WEIGHTS (JSON) accordingly.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.ml.vit_analyzer import checkpoint_present  # noqa: E402

PATTERNS = ["config.json", "preprocessor_config.json", "model.safetensors", "README.md"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=settings.MODEL_REPO_ID)
    parser.add_argument("--dest", type=Path, default=settings.MODEL_DIR)
    parser.add_argument("--revision", default=None, help="pin a commit hash for reproducibility")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if checkpoint_present(args.dest) and not args.force:
        print(f"Checkpoint already present in {args.dest} (use --force to re-download).")
        return 0
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("huggingface_hub is not installed: pip install -r requirements-ml.txt", file=sys.stderr)
        return 1

    args.dest.mkdir(parents=True, exist_ok=True)
    snapshot_download(args.repo, revision=args.revision, local_dir=args.dest, allow_patterns=PATTERNS)
    if not checkpoint_present(args.dest):
        print(f"Download finished but no usable checkpoint found in {args.dest}", file=sys.stderr)
        return 1
    print(f"Model {args.repo} saved to {args.dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
