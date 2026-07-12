import json
import os
import sys
import time
from pathlib import Path
from threading import Event, Lock, Thread
from typing import Any, Callable, Optional

import pyautogui as PyAutoGui
import pywinctl as PyWin
from crossfiledialog import open_file as Open_File
from pynput import keyboard as Keyboard, mouse as Mouse
from PyQt5.QtCore import Qt, QRegExp, QObject, pyqtSignal
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QVBoxLayout, QWidget, QScrollArea
from qfluentwidgets import (
    ComboBox,
    FluentIcon,
    FluentStyleSheet,
    FluentWindow,
    LineEdit,
    PrimaryPushButton,
    SpinBox,
    SwitchButton,
    Theme,
    setTheme,
    setThemeColor,
)
from screeninfo import get_monitors as Get_Monitors

import Modules.Calibrations as Calibrations
import Modules.Input as Input
from Modules.Config import (
    Edit_Config,
    Get_Config,
    Grab_Config,
    Import_Config,
    Save_Config,
)

Main_Monitor = Get_Monitors()[0]

CONFIG_DIR = Path.home() / ".config" / "EaglesMacro"
CONFIG_FILE = CONFIG_DIR / "Config.json"

os.makedirs(CONFIG_DIR, exist_ok=True)

BASE_DIR = Path(__file__).resolve().parent

PATHING_DIR = BASE_DIR / "Pathing"
ASSETS_DIR = BASE_DIR / "Assets"


class Main(FluentWindow):
    def __init__(self):
        super().__init__()

        self.Config, self.ConfigSignal = Grab_Config(self)
        self.ConfigChangedCallbacks = {}


        def DeepSearch(Config, Callbacks):
            for Key, Value in Callbacks.items():
                if isinstance(Value, dict):
                    DeepSearch(Config[Key], Value)
                elif isinstance(Value, list):
                    for Function in Value:
                        Function(Config[Key])

        def SignalCalled(Path: str, Value: any):
            if Path != "config" and Path != "calibrations":
                PathIndexes = Path.split(".")
                Pointer = self.ConfigChangedCallbacks

                for Index in PathIndexes:
                    Pointer = Pointer[Index]

                for Function in Pointer:
                    try:
                        Function(Value)
                    except Exception:
                        pass
            elif Path == "config":
                DeepSearch(Value, self.ConfigChangedCallbacks)
            elif Path == "calibrations":
                for Key, List in self.ConfigChangedCallbacks["calibrations"].items():
                    for Function in List:
                        Function(Value[Key])

        self.ConfigSignal.Connect(SignalCalled)

        ThemeColor = self.Config.get("themecolor")

        try:
            setThemeColor(ThemeColor)
        except Exception:
            pass

        self.Fishing_Stop_Event = Event()
        self.Fishing_Lock = Lock()
        self.Fishing_Thread = None

        self.resize(800, 500)
        self.setWindowTitle("Eagle's Macro")

        for Interface in self.Create_Interfaces():
            Widget, Icon, Name = Interface

            Widget = self.WrapScroll(Widget)
            Widget.setObjectName(Name)

            Widget.setStyleSheet("""
                QScrollArea {
                    background: transparent;
                    border: none;
                }

                QScrollArea QWidget {
                    background: transparent;
                }

                QScrollBar:vertical {
                    width: 0px;
                }

                QScrollBar:horizontal {
                    height: 0px;
                }
                """)

            self.addSubInterface(Widget, Icon, Name)

        def Pressed(Key):
            try:
                if Key == Keyboard.Key.f1:
                    self.StartMacro()
                elif Key == Keyboard.Key.f2:
                    self.PauseMacro()
                elif Key == Keyboard.Key.f3:
                    self.close()
            except AttributeError:
                pass

        self.Listener = Keyboard.Listener(on_press=Pressed)
        self.Listener.start()

        setTheme(Theme.DARK)

    def closeEvent(self, Event):
        self.Stop_Fishing_Worker()

        Save_Config(self)
        Calibrations.Save_Calibrations(self)

        self.Listener.stop()

        Input.ReleaseKeys()
        Event.accept()

    def ConfigCallback(
        self, Path, GetValue: Optional[Callable[[Any], Any]] = None
    ) -> Callable[[Any], None]:
        def Callback(Value):
            if GetValue:
                Edit_Config(self, Path, GetValue(Value))
            else:
                Edit_Config(self, Path, Value)

        return Callback

    def ChangeToConfig(
        self,
        Path: str,
        Function: Callable,
        Value: Optional[Callable[[Any], Any]] = None,
    ):
        PathIndexes = Path.split(".")
        LastIndex = PathIndexes.pop()

        Pointer = self.ConfigChangedCallbacks

        for Index in PathIndexes:
            try:
                Pointer = Pointer[Index]
            except Exception:
                Pointer[Index] = {}
                Pointer = Pointer[Index]

        try:
            Pointer[LastIndex].append(
                lambda ChangedValue: Function(
                    Value and Value(ChangedValue) or ChangedValue
                )
            )
        except Exception:
            Pointer[LastIndex] = []
            Pointer[LastIndex].append(
                lambda ChangedValue: Function(
                    Value and Value(ChangedValue) or ChangedValue
                )
            )

    def WrapScroll(self, Widget):
        Scroll = QScrollArea()
        Scroll.setWidgetResizable(True)
        Scroll.setFrameShape(QScrollArea.NoFrame)
        Scroll.setWidget(Widget)

        return Scroll

    def CreateInterface(self, Name, TitleCard) -> tuple[QWidget, QVBoxLayout]:
        Interface = QWidget()
        Interface.setObjectName(Name)

        FluentStyleSheet.SETTING_CARD.apply(Interface)

        Layout = QVBoxLayout(Interface)
        Layout.setContentsMargins(30, 30, 30, 30)
        Layout.setSpacing(20)

        Title = QLabel(TitleCard)
        Title.setStyleSheet("font-size: 25px; font-weight: bold;")

        Layout.addWidget(Title)

        return Interface, Layout

    def Create_Row(self, Text: str, *Widgets: QWidget) -> QHBoxLayout:
        Layout = QHBoxLayout()

        Label = QLabel(Text)
        Label.setStyleSheet("font-size: 14px;")

        Layout.addWidget(Label)

        for Widget in Widgets:
            Layout.addWidget(Widget)

        Layout.setContentsMargins(10, 0, 0, 0)
        Layout.addStretch()

        return Layout

    def Add_Layouts(self, MainLayout: QHBoxLayout, Layouts: tuple[QHBoxLayout]):
        for Layout in Layouts:
            MainLayout.addLayout(Layout)

    def Home_Interface(self):
        HomeInterface, HomeLayout = self.CreateInterface("Home", "Home")

        StartButton = PrimaryPushButton(FluentIcon.PLAY, "Start")

        StartButton.clicked.connect(self.StartMacro)

        StartButton.setFixedWidth(100)
        StartButton.setContentsMargins(10, 0, 0, 0)

        PauseButton = PrimaryPushButton(FluentIcon.PAUSE, "Pause")

        PauseButton.clicked.connect(self.PauseMacro)

        PauseButton.setFixedWidth(100)
        PauseButton.setContentsMargins(10, 0, 0, 0)

        StopButton = PrimaryPushButton(FluentIcon.CLOSE, "Stop")

        StopButton.clicked.connect(self.close)

        StopButton.setFixedWidth(100)
        StopButton.setContentsMargins(10, 0, 0, 0)

        self.Add_Layouts(
            HomeLayout,
            [
                self.Create_Row("Start Macro (F1):", StartButton),
                self.Create_Row("Pause Macro (F2):", PauseButton),
                self.Create_Row("Stop Macro (F3):", StopButton),
            ],
        )

        HomeLayout.addStretch()

        return HomeInterface

    def Fishing_Interface(self):
        FishingConfig = Get_Config(self, "fishing")

        FishingInterface, FishingLayout = self.CreateInterface(
            "Fishing", "Fishing Settings"
        )

        Toggle = SwitchButton()

        Toggle.setChecked(isChecked=FishingConfig.get("enabled"))
        self.ChangeToConfig("fishing.enabled", Toggle.setChecked)

        Toggle.checkedChanged.connect(self.ConfigCallback("fishing.enabled"))

        PathingComboBox = ComboBox()
        PathingComboBox.setFixedWidth(200)

        PathingComboBox.addItems(["Normal", "VIP"])

        PathingComboBox.setCurrentText(FishingConfig.get("pathing"))
        self.ChangeToConfig("fishing.pathing", PathingComboBox.setCurrentText)

        PathingComboBox.currentTextChanged.connect(
            self.ConfigCallback("fishing.pathing")
        )

        FishSpinBox = SpinBox()

        FishSpinBox.setFixedWidth(150)
        FishSpinBox.setMaximum(10**9)

        FishSpinBox.setValue(FishingConfig.get("fishingloop"))
        self.ChangeToConfig("fishing.fishingloop", FishSpinBox.setValue)

        FishSpinBox.valueChanged.connect(self.ConfigCallback("fishing.fishingloop"))

        SellSpinBox = SpinBox()

        SellSpinBox.setFixedWidth(150)
        SellSpinBox.setMaximum(56)

        SellSpinBox.setValue(FishingConfig.get("sellloop"))
        self.ChangeToConfig("fishing.sellloop", SellSpinBox.setValue)

        SellSpinBox.valueChanged.connect(self.ConfigCallback("fishing.sellloop"))

        CloseChatToggle = SwitchButton()

        CloseChatToggle.setChecked(isChecked=FishingConfig.get("closechat"))
        self.ChangeToConfig("fishing.closechat", CloseChatToggle.setChecked)

        CloseChatToggle.checkedChanged.connect(self.ConfigCallback("fishing.closechat"))

        self.Add_Layouts(
            FishingLayout,
            [
                self.Create_Row("Fishing Mode:", Toggle),
                self.Create_Row("Pathing Mode:", PathingComboBox),
                self.Create_Row("Fish x fishes:", FishSpinBox),
                self.Create_Row("Sell x fishes:", SellSpinBox),
                self.Create_Row("Close chat before fishing:", CloseChatToggle),
            ],
        )

        FishingLayout.addStretch()

        return FishingInterface

    def Calibrations_Interface(self):
        CalibrationsInterface, CalibrationsLayout = self.CreateInterface(
            "Calibrations", "Calibrations"
        )

        MacroCalibrations = self.Get_Calibrations()
        CalibrationsList = []

        PresetResolutionBox = ComboBox()
        PresetResolutionBox.setFixedWidth(150)

        PresetResolutionBox.addItems(["1920x1080"])

        PresetScaleBox = ComboBox()
        PresetScaleBox.setFixedWidth(150)

        PresetScaleBox.addItems(["100%", "125%"])

        SetPrimaryButton = PrimaryPushButton(FluentIcon.DICTIONARY_ADD, "Set")

        SetPrimaryButton.clicked.connect(
            lambda: Calibrations.Set_Calibrations_Preset(
                self,
                PresetResolutionBox.currentText(),
                PresetScaleBox.currentText(),
            )
        )

        for Calibration, Value in MacroCalibrations.items():
            VectorLength = len(Value)

            CalibrationInput = LineEdit()

            def CalibrationChanged(Vector: list[int, int], Widget=CalibrationInput):
                String = ", ".join(map(str, Vector))

                Widget.setText(String)

            def StringToVector(String):
                Vector = list(map(int, String.split(',')))

                return Vector

            RegEx = VectorLength == 2 and QRegExp(r"^\d+\s*,\s*\d+$") or QRegExp(r"^\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*\d+$")
            CalibrationInput.setValidator(
                QRegExpValidator(RegEx)
            )

            CalibrationInput.setText(", ".join(map(str, Value)))
            CalibrationInput.editingFinished.connect(
                lambda Widget=CalibrationInput, Key=Calibration: 
                    self.ConfigCallback(
                        "calibrations." + Key, 
                        lambda String: StringToVector(String)
                    )(Widget.text())
            )

            self.ChangeToConfig("calibrations." + Calibration, CalibrationChanged)

            CalibrationSetButton = PrimaryPushButton(FluentIcon.DICTIONARY_ADD, "Set")

            def SetCalibrationCoordinates(_, Current_Key=Calibration, Current_Length=VectorLength):
                self.Activate_Roblox()

                class ClickBridge(QObject):
                    Clicked = Current_Length == 2 and pyqtSignal(int, int, str) or pyqtSignal(int, int, int, int, str)

                    def __init__(self):
                        super().__init__()

                Bridge = ClickBridge()

                if Current_Length == 2:
                    Bridge.Clicked.connect(lambda X, Y, Key: Calibrations.Set_Calibration(self, Key, [X, Y]))

                    def OnClick(X, Y, Button, Pressed):
                        if Button == Mouse.Button.left and Pressed:
                            Bridge.Clicked.emit(int(X), int(Y), Current_Key)

                            return False
                elif Current_Length == 4:
                    Bridge.Clicked.connect(lambda X, Y, W, H, Key: Calibrations.Set_Calibration(self, Key, [X, Y, W, H]))

                    Vectors = []

                    def OnClick(X, Y, Button, Pressed):
                        if Button == Mouse.Button.left and Pressed:
                            if len(Vectors) != 2:
                                Vectors.append([X, Y])

                            if len(Vectors) == 2:
                                P1, P2 = Vectors[0], Vectors[1]

                                Start_X = min(P1[0], P2[0])
                                Start_Y = min(P1[1], P2[1])

                                W = abs(P1[0] - P2[0])
                                H = abs(P1[1] - P2[1])

                                W = max(1, W)
                                H = max(1, H)

                                Bridge.Clicked.emit(int(Start_X), int(Start_Y), int(W), int(H), Current_Key)

                                return False

                            return True

                MouseListener = Mouse.Listener(on_click=OnClick, daemon = True)
                MouseListener.start()

            CalibrationSetButton.clicked.connect(SetCalibrationCoordinates)

            CalibrationsList.append(self.Create_Row(
                (" ".join(word.capitalize() for word in Calibration.split('_'))) + ":",
                CalibrationInput,
                CalibrationSetButton
            ))


        self.Add_Layouts(
            CalibrationsLayout,
            [
                self.Create_Row(
                    "Presets:",
                    PresetResolutionBox,
                    PresetScaleBox,
                    SetPrimaryButton,
                )
            ] + CalibrationsList,
        )

        CalibrationsLayout.addStretch()

        return CalibrationsInterface

    def Config_Interface(self):
        ConfigInterface, ConfigLayout = self.CreateInterface("Config", "Configurations")

        ImportConfigButton = PrimaryPushButton(FluentIcon.DOWNLOAD, "Import")

        def ImportConfig():
            Imported_Config_Path = Open_File(
                title="Choose a config", filter={"Config JSON": "*.json"}
            )

            if Imported_Config_Path:
                Import_Config(self, Imported_Config_Path)

        ImportConfigButton.clicked.connect(ImportConfig)

        ImportCalibrationButton = PrimaryPushButton(FluentIcon.DOWNLOAD, "Import")

        def ImportCalibration():
            Imported_Calibration_Path = Open_File(
                title="Choose a calibration", filter={"Calibration JSON": "*.json"}
            )

            if Imported_Calibration_Path:
                Calibrations.Import_Calibrations(self, Imported_Calibration_Path)

        ImportCalibrationButton.clicked.connect(ImportCalibration)

        ThemeColorBox = ComboBox()

        ThemeColorBox.addItems(
            [
                "White",
                "Cyan",
                "Red",
                "Magenta",
                "Green",
                "Yellow",
                "Blue",
            ]
        )

        ThemeColorBox.setCurrentText(self.Config.get("themecolor"))
        self.ChangeToConfig("themecolor", ThemeColorBox.setCurrentText)

        ThemeColorBox.currentTextChanged.connect(
            self.ConfigCallback(
                "themecolor", lambda Color: setThemeColor(Color) or Color
            )
        )

        self.Add_Layouts(
            ConfigLayout,
            [
                self.Create_Row("Import Config:", ImportConfigButton),
                self.Create_Row("Import Calibration:", ImportCalibrationButton),
                self.Create_Row("Color Theme:", ThemeColorBox),
            ],
        )

        ConfigLayout.addStretch()

        return ConfigInterface

    def Potion_Interface(self):
        PotionInterface, PotionLayout = self.CreateInterface(
            "Potions", "Potion Crafting"
        )

        PotionsComboBox = ComboBox()

        PotionsComboBox.addItems(
            [
                "Fortune Potion I",
                "Fortune Potion II",
                "Fortune Potion III",
                "Haste Potion I",
                "Haste Potion II",
                "Haste Potion III",
                "Jewelry Potion",
                "Zombie Potion",
                "Rage Potion",
                "Diver Potion",
                "Potion of Bound",
                "Heavenly Potion",
                "Godly Potion (Zeus)",
                "Godly Potion (Poseidon)",
                "Godly Potion (Hades)",
                "Warp Potion",
                "Godlike Potion",
            ]
        )

        PotionLayout.addStretch()

        return PotionInterface

    def Create_Interfaces(self):
        return [
            [self.Home_Interface(), FluentIcon.HOME, "Home"],
            [self.Fishing_Interface(), FluentIcon.SETTING, "Fishing"],
            [self.Calibrations_Interface(), FluentIcon.SYNC, "Calibrations"],
            [self.Potion_Interface(), FluentIcon.MOVE, "Potion Crafting"],
            [self.Config_Interface(), FluentIcon.DEVELOPER_TOOLS, "Configuration"],
        ]

    def Decode_JSON(self, Path):
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

    def Get_Calibrations(self):
        Config = self.Config

        return Config.get("calibrations")

    def Get_Screen_Resolution(self):
        return Main_Monitor.width, Main_Monitor.height

    def Get_Roblox_Window(self):
        Windows = PyWin.getAllTitles()
        Roblox_Window = None

        for Window in Windows:
            if "Sober" in Window:
                Roblox_Window = PyWin.getWindowsWithTitle(Window)[0]
                break

        if not Roblox_Window:
            print("Couldn't find roblox Window.")

        return Roblox_Window

    def Activate_Roblox(self):
        Roblox_Window = self.Get_Roblox_Window()

        if Roblox_Window:
            try:
                Roblox_Window.activate()
            except Exception as Error:
                print(f"Failed to activate Window: {Error}")

    def Load_Pathing_Data(self, Pathing: str):
        File_Path = PATHING_DIR / Pathing

        if File_Path.exists():
            JSON = self.Decode_JSON(File_Path)

            return JSON.get("pathing")
        else:
            return None

    def Wait(self, Seconds):
        FishingConfig = Get_Config(self, "fishing")

        if FishingConfig.get("pathing") == "VIP":
            Seconds = Seconds * 0.78

        time.sleep(Seconds)

    def MoveTo(self, Coordinates, DontTween: bool | None = None):
        if not DontTween:
            PyAutoGui.moveTo(*Coordinates, 0.1, PyAutoGui.linear)
        else:
            PyAutoGui.moveTo(*Coordinates)

    def Start_Pathing(self, Pathing: str):
        Pathing = Pathing + ".json"
        Pathing_Data = self.Load_Pathing_Data(Pathing)

        if Pathing_Data:
            for Properties in Pathing_Data:
                Action_Type = Properties.get("type")
                Key = Properties.get("key")

                SleepTime = Properties.get("sleep")
                WaitTime = Properties.get("wait")

                if Action_Type == "press":
                    if (
                        Key == "space"
                    ):  # just pressing space doesnt jump for some reason
                        Input.KeyDown(Key)

                        time.sleep(0.01)

                        Input.KeyUp(Key)
                    else:
                        PyAutoGui.press(Key)
                elif Action_Type == "down":
                    Input.KeyDown(Key)
                elif Action_Type == "up":
                    Input.KeyUp(Key)
                elif Action_Type == "moveTo":
                    Coordinates = Properties.get("coordinates")
                    Coordinates = Calibrations.Get_Calibration(self,Coordinates)

                    self.MoveTo(Coordinates)
                elif Action_Type == "click":
                    PyAutoGui.click()

                if SleepTime:
                    time.sleep(SleepTime)
                elif WaitTime:
                    self.Wait(WaitTime)

    def Start_Fishing_Worker(self):
        with self.Fishing_Lock:
            if self.Fishing_Thread and self.Fishing_Thread.is_alive():
                return

            self.Fishing_Stop_Event.clear()

            def Worker():
                try:
                    from Modules.Fishing import Start_Fishing

                    Start_Fishing(self)
                except Exception as Error:
                    print(f"Fishing failed: {Error}")

            self.Fishing_Thread = Thread(target=Worker, daemon=True)
            self.Fishing_Thread.start()

    def Stop_Fishing_Worker(self):
        with self.Fishing_Lock:
            self.Fishing_Stop_Event.set()

            FishingThread = self.Fishing_Thread

            if FishingThread and FishingThread.is_alive():
                FishingThread.join(timeout=0.1)

            if not FishingThread or FishingThread and not FishingThread.is_alive():
                self.Fishing_Thread = None

    def StartMacro(self):
        Roblox_Window = self.Get_Roblox_Window()

        if Roblox_Window:
            FishingConfig = Get_Config(self, "fishing")

            if FishingConfig.get("enabled"):
                self.Start_Fishing_Worker()
            else:
                self.Stop_Fishing_Worker()

    def PauseMacro(self):
        self.Stop_Fishing_Worker()


if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    App = QApplication(sys.argv)

    Window = Main()
    Window.show()

    sys.exit(App.exec_())
