import cv2


class ControlKey:
    """Handles control keys for video playback."""

    def __init__(self, **kwargs):
        """
        Initializes the ControlKey instance.

        Args:
            **kwargs:Arbitrary keyword arguments.
                - momentum (float):Factor for momentum, default is 1.0.
                - ignore_case (bool):Whether to ignore case for key matching, default is True.
        """
        self.kwargs = kwargs
        self.momentum = max(self.kwargs.get("momentum", 1.0), 1.0)
        self.ignore_case = self.kwargs.get("ignore_case", True)
        self.delay = self.kwargs.get("delay", 1)
        self.reset()

        self._pause = self.match_case("pause", "\r")
        self._forward = self.match_case("forward", "f")
        self._rewind = self.match_case("rewind", "b")
        self._skip = self.match_case("skip", "q")
        self._exit = self.match_case("exit", "\x1b")
        self._reset = self.match_case("reset", "r")
        if self.has_duplicates():
            raise ValueError("Duplicate keys detected.")

    def has_duplicates(self):
        """Checks for duplicate keys.

        Returns:
            bool:True if there are duplicate keys, False otherwise.
        """
        lst = (
            self._pause
            + self._forward
            + self._rewind
            + self._exit
            + self._skip
            + self._reset
        )
        return len(lst) != len(set(lst))

    def match_case(self, name, default):
        """Matches keys with case sensitivity based on settings.

        Args:
            name (str):The name of the key.
            default (str):The default key value.

        Returns:
            list:List of Unicode values for the matched keys.
        """
        values = "".join(self.kwargs.get(name, default))
        if self.ignore_case:
            values = list(set(values.upper() + values.lower()))
        values = [ord(x) for x in values]
        return values

    def reset(self):
        """Resets the control key states."""
        self.forward_speed = 1
        self.rewind_speed = 2
        self.wk = self.delay

    def __call__(self, key):
        """
        Changes the index based on the key pressed.

        Args:
            key (int):The Unicode code of the key pressed.

        Returns:
            int:The updated index.
        """
        if key == self._exit:  # ESC key
            exit()

        value = 0

        if key in self._skip:
            self.reset()
            value = 1e10
        elif key in self._reset:
            self.reset()
            value = -1e10
        elif key in self._forward:
            self.rewind_speed = 2
            self.forward_speed *= self.momentum
            value = int(self.forward_speed)
        elif key in self._rewind:
            self.forward_speed = 1
            self.rewind_speed *= self.momentum
            value = -int(self.rewind_speed)

        if key in self._pause:
            self.forward_speed = 1
            self.rewind_speed = 2
            if self.wk != 0:
                self.wk = 0
            else:
                self.wk = self.delay
        return int(value)

    def update_idx(self, idx, key):
        return max(0, idx + self(key))
