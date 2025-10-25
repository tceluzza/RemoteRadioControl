# CIVCommands.py

#import struct

from CIVSerial import CIVSerial  # import your existing class

class CIVCommandSet:
    """
    A class to manage and send named CI-V commands using a CIVSerial connection.

    This class stores predefined CI-V commands (command number, subcommand,
    and optional data) and provides helper functions to send them to the radio.
    """

    def __init__(self, civ_interface: CIVSerial):
        """
        Initialize the command set with a CI-V serial interface.

        Parameters
        ----------
        civ_interface : CIVSerial
            An initialized CIVSerial object used for communication.
        """
        self.civ = civ_interface

        # Define command dictionary
        # Each entry: name: {"Cn": bytes, "Sc": bytes, "data": bytes}
        self.commands = {
            "FREQUENCY": {"Cn": b"\x25", "Sc": b"\x00"},
            "FILTER_WIDTH": {"Cn": b"\x1A", "Sc": b"\x03"},
            "POWER_OUTPUT": {"Cn": b"\x14", "Sc": b"\x0A"},
            "MODE": {"Cn": b"\x26", "Sc": b"\x00"},
            "QSK": {"Cn": b"\x16", "Sc": b"\x47"},
            "TUNE": {"Cn": b"\x1C", "Sc": b"\x01"},
        }

    def _bcd_to_int_le(self, bcd_bytes: bytes) -> int:
        """
        Convert little-endian packed BCD bytes to an integer.
        Example: b'\x12\x34\x56\x78\x90' -> 9876543210
        """
        digits = ""
        for b in reversed(bcd_bytes):  # little-endian, so reverse
            digits += f"{(b >> 4) & 0xF}{b & 0xF}"
        return int(digits.lstrip("0") or "0")

    def _scale_power(self, raw_bytes: bytes) -> int:
        """
        Convert a 2-byte big-endian packed BCD power value to an integer 0–100.
        """
        if not raw_bytes or len(raw_bytes) != 2:
            return 0
        # decode packed BCD (big-endian) to integer 0..255
        digits = ""
        for b in raw_bytes:
            digits += f"{(b >> 4) & 0xF}{b & 0xF}"
        raw_value = int(digits.lstrip("0") or "0")
        return round((raw_value / 255.0) * 100)

    def _process_response(self, name: str, data: bytes):
        """
        Process raw response data into meaningful values based on command.
        """
        if name == "FREQUENCY":
            # 5-byte BCD little-endian → frequency in Hz
            return self._bcd_to_int_le(data)

        elif name == "POWER_OUTPUT":
            # 1-byte 0–255 → 0–100%
            return self._scale_power(data)

        elif name == "FILTER_WIDTH":
            if not data:
                return None
            bcd_value = self._bcd_to_int_le(data)
            # Map 0–31 → 50–2700 Hz
            #freq_hz = 50 + round((bcd_value / 31) * (2700 - 50) / 10) * 10
            return bcd_value

        elif name == "MODE":
            if not data:
                return None
            mode_map = {
                0x00: "LSB",
                0x01: "USB",
                0x02: "AM",
                0x03: "CW",
                0x04: "RTTY",
                0x05: "FM",
                0x07: "CW-R",
                0x08: "RTYR",
            }
            mode_byte = data[0]
            return mode_map.get(mode_byte, f"UNKNOWN({mode_byte})")

        elif name == "QSK":
            if not data:
                return None
            return data[0]  # 0, 1, or 2

        else:
            return data

    # --- BEGIN NEW/CHANGED HELPERS FOR WRITES ---
    def _int_to_bcd_le(self, value: int, length: int) -> bytes:
        """
        Encode an integer into little-endian packed BCD of `length` bytes.
        Example: length=5 encodes up to 10 decimal digits.
        """
        if value is None:
            return b""
        # produce decimal string padded to 2*length digits (most-significant first)
        digits = str(int(value)).rjust(length * 2, "0")[-(length * 2) :]
        pairs = [digits[i : i + 2] for i in range(0, len(digits), 2)]
        pair_bytes = [((int(p[0]) & 0xF) << 4) | (int(p[1]) & 0xF) for p in pairs]
        # reversed to match _bcd_to_int_le decoding (which reverses bytes)
        return bytes(reversed(pair_bytes))

    def _power_to_bytes(self, power: int) -> bytes:
        """
        Encode 0-100% into 2-byte packed BCD (big-endian) representing 0..255.
        Example: 75% -> raw = round(75/100*255) = 191 -> b'\x01\x91'
        """
        p = min(max(int(power), 0), 100)
        raw = round((p / 100.0) * 255)
        raw = min(max(raw, 0), 255)
        # convert raw integer (0..255) to 2-byte packed BCD big-endian (4 decimal digits)
        s = str(raw).rjust(4, "0")  # ensure 4 digits
        high = ((int(s[0]) & 0xF) << 4) | (int(s[1]) & 0xF)
        low = ((int(s[2]) & 0xF) << 4) | (int(s[3]) & 0xF)
        return bytes([high, low])

    def _filter_width_to_bcd(self, width: int) -> bytes:
        """
        Encode a filter width from 0 to 31 into the single-byte BCD index the code expects.
        Inverse of the read mapping (approximate).
        """
        if width is None:
            return b""
        width = int(width)
        # min_hz, max_hz = 50, 2700
        # proportion = (width - min_hz) / (max_hz - min_hz)
        # proportion = max(0.0, min(1.0, proportion))
        # idx = round(proportion * 31)  # 0..31
        # represent as a single BCD byte like 0x00..0x31
        # tens = idx // 10
        # ones = idx % 10
        tens = width // 10
        ones = width % 10
        return bytes([((tens & 0xF) << 4) | (ones & 0xF)])

    def _encode_mode(self, mode) -> bytes:
        """
        Encode mode name or numeric code into single-byte code used by radio.
        Accepts strings like "LSB", "USB", etc, or integer code.
        """
        mode_map = {
            "LSB": 0x00,
            "USB": 0x01,
            "AM": 0x02,
            "CW": 0x03,
            "RTTY": 0x04,
            "FM": 0x05,
            "CW-R": 0x07,
            "RTYR": 0x08,
        }
        if mode is None:
            return b""
        if isinstance(mode, int):
            return bytes([mode & 0xFF])
        m = str(mode).upper()
        code = mode_map.get(m, None)
        if code is None:
            # attempt numeric parse
            try:
                return bytes([int(mode) & 0xFF])
            except Exception:
                raise ValueError(f"Unknown mode '{mode}'")
        return bytes([code])

    def _process_request_data(self, name: str, data) -> bytes:
        """
        Take a high-level `data` for `name` and return bytes to send.
        - If data is None or empty, return b'' (a read).
        - Otherwise encode appropriately per command.
        """

        if name == "TUNE":
            # set to 02 to set tuning
            return b"\x02"
        
        if data is None or (isinstance(data, (bytes, bytearray)) and len(data) == 0) or data == "":
            return b""

        if name == "FREQUENCY":
            # accept integer Hz or string digits
            val = int(data)
            return self._int_to_bcd_le(val, 5)

        if name == "POWER_OUTPUT":
            # accept percentage 0..100
            return self._power_to_bytes(int(data))

        if name == "FILTER_WIDTH":
            # accept Hz and encode to single BCD byte index
            return self._filter_width_to_bcd(int(data))

        if name == "MODE":
            return self._encode_mode(data)

        if name == "QSK":
            # a single byte (0,1,2)
            return bytes([int(data) & 0xFF])

        # default: if bytes passed through, use them; otherwise convert to bytes utf-8
        if isinstance(data, (bytes, bytearray)):
            return bytes(data)
        return str(data).encode("utf-8")
    # --- END NEW HELPERS ---

    def send_command_by_name(self, name: str, data=None):
        """
        Send a CI-V command by its name and return processed data.
        If `data` is None or empty, a READ is performed (no data bytes).
        If `data` is provided, it will be encoded and sent as WRITE payload.
        """
        if name not in self.commands:
            raise KeyError(f"Command '{name}' not found in command set.")

        cmd = self.commands[name]
        # Prepare data bytes if provided
        data_bytes = self._process_request_data(name, data)
        # If data_bytes is empty => READ, otherwise WRITE (include data)
        if data_bytes:
            # send_with_data; assume CIVSerial.send_and_receive accepts optional data param
            raw = self.civ.send_and_receive(cmd["Cn"], cmd["Sc"], data_bytes)
            # If radio replied with a single-byte status (e.g., 0xFB OK / 0xFA NG) return it directly
            if raw and len(raw) == 1:
                return raw.hex().upper()
        else:
            # read
            raw = self.civ.send_and_receive(cmd["Cn"], cmd["Sc"])
        return self._process_response(name, raw)

if __name__ == "__main__":
    # Example usage
    radio = CIVSerial(port='COM4', baudrate=115200, radio_addr=b'\x94')
    cmdset = CIVCommandSet(radio)

    # Example reads
    freq_data = cmdset.send_command_by_name("FREQUENCY")
    print("Frequency data:", freq_data)

    mode_data = cmdset.send_command_by_name("MODE")
    print("Mode data:", mode_data)

    fil_data = cmdset.send_command_by_name("FILTER_WIDTH")
    print("Filter data:", fil_data)

    pow_data = cmdset.send_command_by_name("POWER_OUTPUT")
    print("Power data:", pow_data)

    qsk_data = cmdset.send_command_by_name("QSK")
    print("QSK data:", qsk_data)

    # Example writes
    # Set frequency to 14.012300 MHz (example)
    print(cmdset.send_command_by_name("FREQUENCY", 14012300))
    # Set power to 75%
    print(cmdset.send_command_by_name("POWER_OUTPUT", 75))
    
    radio.close()