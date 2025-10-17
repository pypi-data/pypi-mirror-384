import os
from pathlib import Path
from typing import Dict, Iterable, Optional


def _parse_env_file(p: Path) -> Dict[str, str]:
    data: Dict[str, str] = {}
    try:
        for raw in p.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k:
                data[k] = v
    except Exception:
        # ignore parse errors to keep CLI resilient
        pass
    return data


def _candidate_paths() -> Iterable[Path]:
    cwd = Path.cwd()
    home = Path.home()

    # Windows system drive root (e.g., C:\airoboEnv and C:\airoboEnv.env)
    sys_drive = os.environ.get("SystemDrive", "C:")
    root_base = Path(sys_drive + "\\")
    # Root-level variants
    root_env = root_base / "airoboEnv"
    root_env_dot = root_base / "airoboEnv.env"
    # C:\airobo variants
    airobo_folder = root_base / "airobo"
    airobo_env = airobo_folder / "airoboEnv"
    airobo_env_dot = airobo_folder / "airoboEnv.env"
    # C:\airoboConfigs variants
    configs_folder = root_base / "airoboConfigs"
    configs_env = configs_folder / "airoboEnv"
    configs_env_dot = configs_folder / "airoboEnv.env"

    # Windows roaming appdata fallback
    appdata = os.environ.get("APPDATA")
    appdata_env = Path(appdata) / "airobo" / ".env" if appdata else None

    # Explicit override takes precedence
    custom = os.environ.get("AIROBO_ENV_PATH")
    if custom:
        yield Path(custom)

    # Common names/locations (first found wins)
    for p in (
        cwd / ".env",
        cwd / "airoboEnv",
        cwd / "airoboEnv.env",
        home / ".env",
        home / "airoboEnv",
        home / "airoboEnv.env",
        root_env,
        root_env_dot,
        airobo_env,
        airobo_env_dot,
        configs_env,
        configs_env_dot,
        appdata_env,
    ):
        if p:
            yield p


def load_env_from_known_locations(verbose: bool = False, keys: Optional[Iterable[str]] = None) -> None:
    """
    Load env vars from the first existing file among:
      - ./.env, ./airoboEnv, ./airoboEnv.env
      - ~/.env, ~/airoboEnv, ~/airoboEnv.env
      - C:\\airobo\\airoboEnv, C:\\airobo\\airoboEnv.env
      - C:\\airoboEnv, C:\\airoboEnv.env
      - C:\\airoboConfigs\\airoboEnv, C:\\airoboConfigs\\airoboEnv.env
      - %APPDATA%\\airobo\\.env (Windows)
    Does not override already-set environment variables.
    To force a path, set AIROBO_ENV_PATH to a specific file.
    Optionally pass `keys` to restrict which vars to import.
    """
    wanted = set(k.lower() for k in (keys or ()))
    missing = set(wanted)
    for path in _candidate_paths():
        try:
            if not path or not path.exists():
                continue
            data = _parse_env_file(path)
            if not data:
                continue
            applied_any = False
            for k, v in data.items():
                kl = k.lower()
                if wanted and kl not in wanted:
                    continue
                if k not in os.environ:
                    os.environ[k] = v
                    applied_any = True
                    if kl in missing:
                        missing.discard(kl)
            if applied_any and verbose:
                print(f"🔎 Loaded environment from: {path}")
            # Stop only if no specific keys were requested, or all requested keys are satisfied
            if not wanted or not missing:
                break
        except Exception:
            # fail-quietly to avoid blocking CLI
            continue
