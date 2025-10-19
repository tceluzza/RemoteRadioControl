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
            "READ_FREQUENCY": {"Cn": b"\x25", "Sc": b"\x00", "data": b""},
            "READ_FILTER_WIDTH": {"Cn": b"\x1A", "Sc": b"\x03", "data": b""},
            "READ_POWER_OUTPUT": {"Cn": b"\x14", "Sc": b"\x0A", "data": b""},
            "READ_MODE": {"Cn": b"\x26", "Sc": b"\x00", "data": b""},
            "READ_QSK": {"Cn": b"\x16", "Sc": b"\x47", "data": b""},
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
        Convert a 2-byte big-endian power value to an integer 0–100.
        """
        if not raw_bytes or len(raw_bytes) != 2:
            return 0
        raw_value = (raw_bytes[0] << 8) | raw_bytes[1]  # combine two bytes
        return round((raw_value / 0x0255) * 100)  # scale 0–0x0255 → 0–100


    def _process_response(self, name: str, data: bytes):
        """
        Process raw response data into meaningful values based on command.
        """
        if name == "READ_FREQUENCY":
            # 5-byte BCD little-endian → frequency in Hz
            return self._bcd_to_int_le(data)

        elif name == "READ_POWER_OUTPUT":
            # 1-byte 0–255 → 0–100%
            return self._scale_power(data)

        elif name == "READ_FILTER_WIDTH":
            if not data:
                return None
            bcd_value = self._bcd_to_int_le(data)
            # Map 0–31 → 50–2700 Hz
            freq_hz = 50 + round((bcd_value / 31) * (2700 - 50) / 100) * 100
            return freq_hz

        elif name == "READ_MODE":
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

        elif name == "READ_QSK":
            if not data:
                return None
            return data[0]  # 0, 1, or 2

        else:
            return data

    def send_command_by_name(self, name: str):
        """
        Send a CI-V command by its name and return processed data.
        """
        if name not in self.commands:
            raise KeyError(f"Command '{name}' not found in command set.")

        cmd = self.commands[name]
        raw = self.civ.send_and_receive(cmd["Cn"], cmd["Sc"], cmd.get("data", b""))
        return self._process_response(name, raw)

if __name__ == "__main__":
    # Example usage
    radio = CIVSerial(port='COM4', baudrate=115200, radio_addr=b'\x94')
    cmdset = CIVCommandSet(radio)

    freq_data = cmdset.send_command_by_name("READ_FREQUENCY")
    print("Frequency data:", freq_data)

    mode_data = cmdset.send_command_by_name("READ_MODE")
    print("Mode data:", mode_data)

    fil_data = cmdset.send_command_by_name("READ_FILTER_WIDTH")
    print("Filter data:", fil_data)

    pow_data = cmdset.send_command_by_name("READ_POWER_OUTPUT")
    print("Power data:", pow_data)

    qsk_data = cmdset.send_command_by_name("READ_QSK")
    print("QSK data:", qsk_data)
    

    radio.close()