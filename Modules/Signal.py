from typing import Callable


class Signal:
    def __init__(self):
        self.Connections = []

    def Connect(self, Function: Callable):
        self.Connections.append(Function)

        return len(self.Connections)

    def Disconnect(self, Index: int):
        self.Connections[Index] = None

    def Fire(self, *Arguments):
        for Callback in self.Connections:
            Callback(*Arguments)

    def Destroy(self):
        self.Connections.clear()
        self.Connections = None
        self = None
