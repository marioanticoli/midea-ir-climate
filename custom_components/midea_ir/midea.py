from infrared_protocols.commands import Command

from .const import FAN_CODES, MODE_CODES, OFF_FRAME, PREFIX, TEMP_CODES


def build_state(power, mode, temp, fan):
    if not power:
        return OFF_FRAME
    return (
        PREFIX,
        (FAN_CODES[fan] << 5) | 0x1F,
        (TEMP_CODES[temp] << 4) | MODE_CODES[mode],
    )


def _message(data):
    timings = [4450, 4450]
    for byte in data:
        for value in (byte, byte ^ 0xFF):
            for bit in range(7, -1, -1):
                timings += [550, 1650 if (value >> bit) & 1 else 550]
    timings.append(550)
    return timings


class MideaCommand(Command):
    def __init__(self, data) -> None:
        super().__init__(modulation=38000)
        self._data = tuple(data)

    def get_raw_timings(self) -> list[int]:
        message = _message(self._data)
        return message + [5250] + message
