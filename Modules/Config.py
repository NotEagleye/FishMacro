import json
import os

from pathlib import Path

import main as Main
from Modules.Signal import Signal

CONFIG_DIR = Path.home() / ".config" / "EaglesMacro"
CONFIG_FILE = CONFIG_DIR / "Config.json"

os.makedirs(CONFIG_DIR, exist_ok=True)

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "Assets"


def Grab_Config(Macro: Main.Main):
    Default_Config_Path = ASSETS_DIR / "DefaultConfig.json"

    Default_Config = Macro.Decode_JSON(Default_Config_Path)

    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as Config_File:
            json.dump(Default_Config, Config_File, indent=4)

    Config = Macro.Decode_JSON(CONFIG_FILE)

    for Configs in Default_Config:
        if Configs not in Config:
            Config[Configs] = Default_Config.get(Configs)
            continue

        try:
            iter(Default_Config.get(Configs))
        except Exception:
            continue

        for Property in Default_Config.get(Configs):
            try:
                iter(Config[Configs].get(Property))
            except Exception:
                continue

            if Config[Configs].get(Property) is None:
                Config[Configs][Property] = Default_Config[Configs][Property]

    return Config, Signal()


def Save_Config(Macro: Main.Main):
    with open(CONFIG_FILE, "w") as Config_File:
        print(Macro.Config)
        json.dump(Macro.Config, Config_File, indent=4)


def Get_Config(Macro: Main.Main, Property):
    if Macro.Config:
        return Macro.Config.get(Property)
    else:
        return None


def Edit_Config(Macro: Main.Main, Path: str, Value: any):
    ConfigSignal = Macro.ConfigSignal
    Pointer = Macro.Config

    PathIndexes = Path.split(".")
    LastIndex = PathIndexes.pop()

    for PathIndex in PathIndexes:
        Pointer = Pointer[PathIndex]

    Pointer[LastIndex] = Value
    ConfigSignal.Fire(Path, Value)


def Import_Config(Macro: Main.Main, Path: str):
    ConfigSignal: Signal = Macro.ConfigSignal

    try:
        Config_Data = None

        with open(Path, "r") as Imported_Config:
            Config_Data = json.load(Imported_Config)

        Macro.Config = Config_Data
        ConfigSignal.Fire("config", Macro.Config)
    except Exception as Error:
        print(f"Error while trying to import config. Error: {Error}")
