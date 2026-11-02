import base64
import struct

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


def to_zosung(timings):
    raw = struct.pack("<%dH" % len(timings), *timings)
    out = bytearray()
    for i in range(0, len(raw), 32):
        chunk = raw[i:i + 32]
        out.append(len(chunk) - 1)
        out += chunk
    return base64.b64encode(bytes(out)).decode()


def build_code(state):
    message = _message(state)
    return to_zosung(message + [5250] + message)
