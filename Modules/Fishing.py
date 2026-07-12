from main import Main

import pyautogui as PyAutoGui
import numpy as NumPy
import cv2 as Cv2

import mss
import time

import Modules.Input as Input
from Modules.Calibrations import Get_Calibration
from Modules.Config import Get_Config

# ye alot of this code contains code from coteab so huge credit to them


def Get_Pixel_RGB(X, Y, ScreenshotTool):
    if ScreenshotTool is not None:
        try:
            Screenshot = ScreenshotTool.grab(
                {"left": int(X), "top": int(Y), "width": 1, "height": 1}
            )
            Array = NumPy.frombuffer(Screenshot.bgra, dtype=NumPy.uint8).reshape(
                (1, 1, 4)
            )

            B, G, R = Array[0, 0, 0], Array[0, 0, 1], Array[0, 0, 2]

            return int(R), int(G), int(B)
        except Exception:
            pass

        Pixel = PyAutoGui.screenshot(region=(X, Y, 1, 1)).getpixel((0, 0))

        return int(Pixel[0]), int(Pixel[1]), int(Pixel[2])


def Pick_Scan_Region(
    Bar_Region: tuple[int, int, int, int], Scan_Height: int
) -> tuple[int, int, int, int]:
    X, Y, W, H = Bar_Region
    SH = max(1, min(int(Scan_Height), max(1, int(H))))

    Scan_Y = Y + max(0, (H - SH) // 2)

    return int(X), int(Scan_Y), int(W), int(SH)


def Grab_Region_BGR(
    Region: tuple[int, int, int, int], ScreenshotTool: mss.MSS | None = None
) -> NumPy.ndarray:
    X, Y, W, H = Region

    if ScreenshotTool is not None:
        try:
            Screenshot = ScreenshotTool.grab(
                {"left": int(X), "top": int(Y), "width": int(W), "height": int(H)}
            )
            Array = NumPy.frombuffer(Screenshot.bgra, dtype=NumPy.uint8).reshape(
                (int(H), int(W), 4)
            )

            return Array[:, :, :3]
        except Exception:
            pass

    Image = PyAutoGui.screenshot(region=(int(X), int(Y), int(W), int(H)))
    Array = NumPy.array(Image)

    return Cv2.cvtColor(Array, Cv2.COLOR_RGB2BGR)


def Detect_Color(
    Bar_Color: tuple[int, int, int],
    Bar_Region: tuple[int, int, int, int],
    *,
    Tolerance: int = 12,
    Scan_Height: int = 3,
    ScreenshotTool: mss.MSS | None = None,
) -> bool:
    Scan_Region = Pick_Scan_Region(Bar_Region, Scan_Height=Scan_Height)
    BGR = Grab_Region_BGR(Scan_Region, ScreenshotTool=ScreenshotTool)

    Lower_Bound = NumPy.array(
        [
            max(0, Bar_Color[2] - Tolerance),
            max(0, Bar_Color[1] - Tolerance),
            max(0, Bar_Color[0] - Tolerance),
        ]
    )

    Upper_Bound = NumPy.array(
        [
            min(255, Bar_Color[2] + Tolerance),
            min(255, Bar_Color[1] + Tolerance),
            min(255, Bar_Color[0] + Tolerance),
        ]
    )

    Mask = Cv2.inRange(BGR, Lower_Bound, Upper_Bound)

    return bool(NumPy.any(Mask))


def Is_Indicator_Active(Pixel: tuple[int, ...], Threshold: int = 250) -> bool:
    return (
        len(Pixel) >= 3
        and Pixel[0] >= Threshold
        and Pixel[1] >= Threshold
        and Pixel[2] >= Threshold
    )


def Start_Fishing(Macro: Main):
    Stop_Event = Macro.Fishing_Stop_Event

    def Can_Continue() -> bool:
        return not Stop_Event.is_set()

    def Sleep(Seconds: float, Poll: float = 0.02) -> bool:
        End = time.monotonic() + max(0.0, float(Seconds))

        while time.monotonic() < End:
            if not Can_Continue():
                return False

            Remaining = End - time.monotonic()

            if Remaining <= 0:
                break

            time.sleep(min(Poll, Remaining))

        return Can_Continue()

    Macro.Activate_Roblox()

    ScreenWidth, ScreenHeight = Macro.Get_Screen_Resolution()

    FishingConfig = Get_Config(Macro, "fishing")

    Macro.MoveTo([ScreenWidth / 2, ScreenHeight / 2])
    PyAutoGui.click()

    Fishing_Loop = FishingConfig.get("fishingloop")
    Fishing_Sell_Loop = FishingConfig.get("sellloop")

    ScreenshotTool = mss.MSS()

    Caught_Fish = 0

    Last_Fish_Click = None
    GameModeEnabled = False

    Pathing = None

    try:
        while Can_Continue():
            if Pathing == "Camera":
                if FishingConfig.get("closechat"):
                    PyAutoGui.press("/")

                    Macro.MoveTo(Get_Calibration(Macro, "chat_close_button"))
                    PyAutoGui.click()

                Macro.Start_Pathing("SetupCamera")
                Pathing = "FishPathing"

                continue
            elif Pathing == "FishPathing":
                Macro.Start_Pathing("FishingStart")
                Pathing = None

            if Caught_Fish == int(Fishing_Loop):
                Macro.Start_Pathing("SetupCamera")

                if not Can_Continue():
                    continue

                Macro.Start_Pathing("SellFlarg")

                if not Can_Continue():
                    continue

                Macro.MoveTo(Get_Calibration(Macro, "fishing_flarg_dialogue_box"))

                for _ in range(3):
                    PyAutoGui.click()

                    if not Sleep(0.5):
                        break

                if not Can_Continue():
                    continue

                Macro.MoveTo(Get_Calibration(Macro, "fishing_shop_open_button"))
                PyAutoGui.click()

                if not Sleep(1):
                    continue

                Macro.MoveTo(Get_Calibration(Macro, "fishing_shop_sell_tab"))
                PyAutoGui.click()

                if not Sleep(0.5):
                    continue

                for _ in range(int(Fishing_Sell_Loop)):
                    Macro.MoveTo(Get_Calibration(Macro, "fishing_shop_first_fish"))
                    PyAutoGui.click()

                    if not Sleep(0.4):
                        break

                    Macro.MoveTo(Get_Calibration(Macro, "fishing_shop_sell_all_button"))
                    PyAutoGui.click()

                    if not Sleep(0.8):
                        break

                    Macro.MoveTo(
                        Get_Calibration(Macro, "fishing_confirm_sell_all_button")
                    )
                    PyAutoGui.click()

                    if not Sleep(0.8):
                        break

                if not Can_Continue():
                    continue

                Macro.MoveTo(Get_Calibration(Macro, "fishing_shop_close_button"))
                PyAutoGui.click()

                Caught_Fish = 0

                Pathing = "Camera"

                continue

            if (
                Last_Fish_Click is not None
                and (time.monotonic() - float(Last_Fish_Click)) >= 60
            ):
                Last_Fish_Click = None
                Pathing = "Camera"

                for _ in range(5):
                    Macro.MoveTo(Get_Calibration(Macro, "fishing_close_button_pos"))
                    PyAutoGui.click()

                    if not Sleep(0.11):
                        break

                continue

            if not Last_Fish_Click and not GameModeEnabled:
                Macro.MoveTo(Get_Calibration(Macro, "fishing_click_position"))
                PyAutoGui.click()

                Last_Fish_Click = time.monotonic()

                continue
            elif Last_Fish_Click and not GameModeEnabled:
                PixelColor = Get_Pixel_RGB(
                    *Get_Calibration(Macro, "fishing_detect_pixel"),
                    ScreenshotTool=ScreenshotTool,
                )

                if Is_Indicator_Active(PixelColor):
                    GameModeEnabled = True
                    Last_Fish_Click = None

                    continue
                else:
                    time.sleep(0.05)

                    continue
            elif GameModeEnabled and not Last_Fish_Click:
                Sleep(0.18)

                Bar_Color = Get_Pixel_RGB(
                    *Get_Calibration(Macro, "fishing_midbar_sample_pos"),
                    ScreenshotTool=ScreenshotTool,
                )

                Start = time.time()
                LastShouldClick = None

                while (time.time() - Start) < 9:
                    if not Can_Continue():
                        break

                    Found = Detect_Color(
                        Bar_Color,
                        Get_Calibration(Macro, "fishing_bar_region"),
                        ScreenshotTool=ScreenshotTool,
                    )

                    if LastShouldClick != (not Found):
                        LastShouldClick = not Found

                    if not Found:
                        for Index in range(3):
                            Macro.MoveTo(
                                Get_Calibration(Macro, "fishing_click_position")
                            )
                            PyAutoGui.click()

                            if Index + 1 < 3 and not Sleep(0.0005):
                                break

                    time.sleep(0.002)

                if not Can_Continue():
                    continue

                if not Sleep(0.4):
                    continue

                for _ in range(5):
                    Macro.MoveTo(Get_Calibration(Macro, "fishing_close_button_pos"))
                    PyAutoGui.click()

                    if not Sleep(0.11):
                        break

                Caught_Fish += 1

                if not Sleep(0.15):
                    continue

                if not Can_Continue():
                    continue

                GameModeEnabled = False
    finally:
        Input.ReleaseKeys()

        if ScreenshotTool is not None:
            try:
                ScreenshotTool.close()
            except Exception:
                pass
