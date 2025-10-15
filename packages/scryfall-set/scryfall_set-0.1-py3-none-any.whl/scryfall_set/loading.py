from time import sleep
from threading import Thread
from itertools import cycle


class Loading:
    """
    a nice loading bar to play while waiting for request.
    """

    def __init__(self) -> None:
        self.symbols = ["⣷", "⣯", "⣟", "⡿", "⢿", "⣻", "⣽", "⣾"]
        self.message = "Drawing cards from Scryfall..."
        self._thread = Thread(target=self._animate, daemon=True)
        self.waiting = True

    def start(self):
        self._thread.start()
        return self

    def _animate(self):
        for sym in cycle(self.symbols):
            if not self.waiting:
                break
            print(f"\r{sym} {self.message}", end="", flush=True)
            sleep(0.1)

    def end(self):
        self.waiting = False
        print(f"\r{" "*(len(self.message)+2)}\r", end="", flush=True)
