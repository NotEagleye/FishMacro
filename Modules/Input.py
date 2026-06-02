import pyautogui as PyAutoGui

HeldKeys = []

def KeyDown(Key):
    PyAutoGui.keyDown(Key)

    HeldKeys.append(Key)

def KeyUp(Key):
    PyAutoGui.keyUp(Key)

    try:
        HeldKeys.remove(Key)
    except ValueError:
        pass

def ReleaseKeys():
    for Key in HeldKeys:
        PyAutoGui.keyUp(Key)

    HeldKeys.clear()