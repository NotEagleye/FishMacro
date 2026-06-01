from main import Main

import pyautogui as PyAutoGui
import numpy as NumPy

import mss

def Get_Pixel_RGB(self, X, Y, ScreenshotTool):
    if ScreenshotTool is not None:
        try:
            Screenshot = ScreenshotTool.grab({"left": int(X), "top": int(Y), "width": 1, "height": 1})
            Array = NumPy.frombuffer(Screenshot.bgra, dtype = NumPy.uint8).reshape((1, 1, 4))
            
            B, G, R = Array[0, 0, 0], Array[0, 0, 1], Array[0, 0, 2]

            return int(R), int(B), int(G)
        except Exception:
            pass

        Pixel = PyAutoGui.screenshot(region = (X, Y, 1, 1)).getpixel((0, 0))

        return int(Pixel[0]), int(Pixel[1]), int(Pixel[2])

def Is_Indicator_Active(self, Pixel: tuple[int, ...], Threshold: int = 250) -> bool:
    return len(Pixel) >= 3 and Pixel[0] >= Threshold and Pixel[1] >= Threshold and Pixel[2] >= Threshold

def Start_Fishing(Macro: Main):
    Macro.Activate_Roblox()

    ScreenWidth, ScreenHeight = Macro.Get_Screen_Resolution()

    FishingConfig = Macro.Get_Config("fishing")

    Macro.MoveTo(ScreenWidth / 2, ScreenHeight / 2)
    PyAutoGui.click()

    Macro.Start_Pathing("SetupCamera")
    Macro.Start_Pathing("FishingStart")

    Macro.MoveTo(850, 835)
    PyAutoGui.click()

    Fishing_Loop = FishingConfig.get("fishingloop")
    Fishing_Sell_Loop = FishingConfig.get("sellloop")

    ScreenshotTool = mss.MSS()

    Pixel = Get_Pixel_RGB(1175, 836, ScreenshotTool)