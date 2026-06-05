"""Pre-import shim that points HuggingFace cache at a writable location.

Why this exists:
- ~/.bashrc on train05 exports HF_HOME=/data/shared-models/.cache/huggingface-shuhao
  which is shared and read-only for this user.
- We redirect HF cache vars to ~/.cache/hf-models when the configured location
  is not writable, so SentenceTransformer / transformers downloads succeed.
- Default HF_ENDPOINT to https://hf-mirror.com (huggingface.co is firewalled
  on this network).

Usage: import this module before importing transformers / sentence_transformers.
"""
from __future__ import annotations

import os as _os

# Redirect HF cache to a writable location if the configured one is not writable.
_default_hf_home = _os.path.expanduser("~/.cache/hf-models")
_existing_hf_home = _os.environ.get("HF_HOME")
_use_default = False
if not _existing_hf_home:
    _use_default = True
else:
    try:
        _os.makedirs(_existing_hf_home, exist_ok=True)
        _probe = _os.path.join(_existing_hf_home, ".write-probe")
        with open(_probe, "w") as _fh:
            _fh.write("ok")
        _os.unlink(_probe)
    except OSError:
        _use_default = True

if _use_default:
    _os.makedirs(_default_hf_home, exist_ok=True)
    _hub_dir = _os.path.join(_default_hf_home, "hub")
    _os.makedirs(_hub_dir, exist_ok=True)
    _os.environ["HF_HOME"] = _default_hf_home
    _os.environ["HUGGINGFACE_HUB_CACHE"] = _hub_dir
    _os.environ["HF_HUB_CACHE"] = _hub_dir
    _os.environ["TRANSFORMERS_CACHE"] = _hub_dir

# Default to the hf-mirror endpoint when the user has not picked one.
_os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
