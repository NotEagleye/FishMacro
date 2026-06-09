from pathlib import Path

import json

BASE_DIR = Path(__file__).resolve().parent.parent

ASSETS_DIR = BASE_DIR / "Assets"
DATA_DIR = BASE_DIR / "Data"

CALIBRATIONS_PATH = DATA_DIR / "Calibrations.json"
DEFAULT_CALIBRATIONS_PATH = ASSETS_DIR / "DefaultCalibrations.json"


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


def Set_Calibrations_Preset(Resolution, Scale):
    Default_Calibrations = Get_Calibration_Presets()

    for Calibrations in Default_Calibrations:
        Calibration_Resolution = Calibrations.get("resolution")
        Calibration_Scale = Calibrations.get("scale")

        Calibration_Preset = Calibrations.get("calibrations")

        if Calibration_Resolution == Resolution and Calibration_Scale == Scale:
            with open(CALIBRATIONS_PATH, "w") as Calibration_File:
                json.dump(Calibration_Preset, Calibration_File, indent=4)
