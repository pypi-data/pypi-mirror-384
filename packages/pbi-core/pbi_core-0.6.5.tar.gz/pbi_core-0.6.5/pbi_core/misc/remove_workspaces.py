import json
import shutil
from pathlib import Path

from pbi_core.ssas.setup import PbiCoreStartupConfig

settings_path = Path(__file__).parents[1] / "local" / "settings.json"


def get_workspaces() -> list[Path]:
    settings = PbiCoreStartupConfig.model_validate(json.load(settings_path.open("r")))
    return list(settings.workspace_dir.iterdir())


def list_workspaces() -> None:
    settings = PbiCoreStartupConfig.model_validate(json.load(settings_path.open("r")))
    workspaces = get_workspaces()
    if len(workspaces) == 0:
        print(f"No workspaces to remove from {settings.workspace_dir.absolute().as_posix()}")
    else:
        print("Folders to remove:")
        for folder in workspaces:
            print(folder)


def clear_workspaces() -> None:
    settings = PbiCoreStartupConfig.model_validate(json.load(settings_path.open("r")))
    workspaces = get_workspaces()
    if len(workspaces) == 0:
        print(f"No workspaces to remove from {settings.workspace_dir.absolute().as_posix()}")

    for folder in workspaces:
        print(f"Deleting: {folder.absolute().as_posix()}")
        try:
            shutil.rmtree(folder)
        except PermissionError:
            print("\tWorkspace currently being used by an SSAS instance")
