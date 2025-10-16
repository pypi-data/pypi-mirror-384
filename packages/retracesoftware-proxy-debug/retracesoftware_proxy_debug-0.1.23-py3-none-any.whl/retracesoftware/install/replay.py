from retracesoftware.proxy import *

from retracesoftware.install import globals

import os, json, re, glob
from pathlib import Path
from datetime import datetime

def latest_from_pattern(pattern: str) -> str | None:
    """
    Given a strftime-style filename pattern (e.g. "recordings/%Y%m%d_%H%M%S_%f"),
    return the path to the most recent matching file, or None if no files exist.
    """
    # Turn strftime placeholders into '*' for globbing
    # (very simple replacement: %... -> *)
    glob_pattern = re.sub(r"%[a-zA-Z]", "*", pattern)

    # Find all matching files
    candidates = glob.glob(glob_pattern)
    if not candidates:
        return None

    # Derive the datetime format from the pattern (basename only)
    base_pattern = os.path.basename(pattern)

    def parse_time(path: str):
        name = os.path.basename(path)
        return datetime.strptime(name, base_pattern)

    # Find the latest by parsed timestamp
    latest = max(candidates, key=parse_time)
    return latest

def replay_system(thread_state, immutable_types, config):

    recording_path = Path(latest_from_pattern(config['recording_path']))

    # print(f"replay running against path: {recording_path}")

    globals.recording_path = globals.RecordingPath(recording_path)

    assert recording_path.exists()
    assert recording_path.is_dir()

    with open(recording_path / "env", "r", encoding="utf-8") as f:
        os.environ.update(json.load(f))

    with open(recording_path / "tracing_config.json", "r", encoding="utf-8") as f:
        tracing_config = json.load(f)

    with open(recording_path / "mainscript", "r", encoding="utf-8") as f:
        mainscript = f.read()

    return ReplayProxySystem(thread_state = thread_state, 
                                immutable_types = immutable_types,
                                tracing_config = tracing_config,
                                mainscript = mainscript,
                                path = recording_path / 'trace.bin')
