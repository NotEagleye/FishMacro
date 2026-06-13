from pathlib import Path

import main as Main

import json
import os

BASE_DIR = Path(__file__).resolve().parent.parent

ASSETS_DIR = BASE_DIR / "Assets"
DEFAULT_CALIBRATIONS_PATH = ASSETS_DIR / "DefaultCalibrations.json"

CONFIG_DIR = Path.home() / ".config" / "EaglesMacro"
CALIBRATIONS_PATH = CONFIG_DIR / "Calibrations.json"

os.makedirs(CONFIG_DIR, exist_ok=True)


def Decode_JSON(Path):
    if not Path.exists():
        print(f"Error: file not found at {Path}")
        return None

    try:
        with open(Path, "r") as f:
            Data = json.load(f)
            return Data
    except json.JSONDecodeError as Error:
        print(f"Error decoding JSON in file: {Error}")
        return None


def IsEmpty():
    with open(CALIBRATIONS_PATH, "r") as Config_File:
        return Config_File != ""


if not os.path.exists(CALIBRATIONS_PATH) or IsEmpty():
    with open(CALIBRATIONS_PATH, "w") as Calibrations_File:
        Default_Calibrations = Decode_JSON(DEFAULT_CALIBRATIONS_PATH).get("presets")
        json.dump(
            Default_Calibrations[0].get("calibrations"), Calibrations_File, indent=4
        )


def Decode_JSON(Path):
    if not Path.exists():
        print(f"Error: file not found at {Path}")
        return None

    try:
        with open(Path, "r") as f:
            Data = json.load(f)
            return Data
    except json.JSONDecodeError as Error:
        print(f"Error decoding JSON in file: {Error}")
        return None


def Get_Calibration(Calibration: str):
    Calibrations = Decode_JSON(CALIBRATIONS_PATH)
    Calibration: list = Calibrations.get(Calibration)

    return Calibration


def Set_Calibration(Calibration: str, Value: any):
    Calibrations = Decode_JSON(CALIBRATIONS_PATH)

    try:
        Calibrations[Calibration] = Value
    except Exception:
        pass


def Get_Calibration_Presets():
    Default_Calibrations = Decode_JSON(DEFAULT_CALIBRATIONS_PATH)

    return Default_Calibrations.get("presets")


def Set_Calibrations_Preset(Macro: Main.Main, Resolution, Scale):
    Default_Calibrations = Get_Calibration_Presets()
    Macro_Config = Macro.Config

    for Calibrations in Default_Calibrations:
        Calibration_Resolution = Calibrations.get("resolution")
        Calibration_Scale = Calibrations.get("scale")

        Calibration_Preset = Calibrations.get("calibrations")

        if Calibration_Resolution == Resolution and Calibration_Scale == Scale:
            with open(CALIBRATIONS_PATH, "w") as Calibration_File:
                json.dump(Calibration_Preset, Calibration_File, indent=4)
                Macro_Config["calibrations"] = Calibration_Preset
