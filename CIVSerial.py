import serial
import time


class CIVSerial:
    """
    A class to handle CI-V (Computer Interface-V) serial communication
    with a radio transceiver.

    This class abstracts the low-level details of forming CI-V frames and
    sending or receiving them over a serial connection.

    Attributes
    ----------
    PREAMBLE : bytes
        Two-byte CI-V preamble, always b'\\xFE\\xFE'
    EOM : bytes
        End-of-message byte, always b'\\xFD'
    CONTROLLER_ADDR : bytes
        Controller address (the CI-V "from" address), always b'\\xCE'
    serial_port : str
        The name/path of the serial port (e.g., '/dev/ttyUSB0', 'COM3')
    baudrate : int
        Serial communication baud rate
    radio_addr : bytes
        The CI-V address of the target radio
    ser : serial.Serial
        The serial port connection object
    """

    PREAMBLE = b"\xFE\xFE"
    EOM = b"\xFD"
    CONTROLLER_ADDR = b"\xCE"

    def __init__(self, port: str, baudrate: int, radio_addr: bytes):
        """
        Initialize a CI-V serial communication session.

        Parameters
        ----------
        port : str
            The serial port name (e.g., '/dev/ttyUSB0' or 'COM3')
        baudrate : int
            Baud rate for serial communication (typically 19200 or 9600)
        radio_addr : bytes
            The CI-V address of the radio (1 byte, e.g., b'\\x94')
        """
        self.serial_port = port
        self.baudrate = baudrate
        self.radio_addr = radio_addr

        # Initialize serial connection
        self.ser = serial.Serial(
            port=self.serial_port,
            baudrate=self.baudrate,
            #bytesize=serial.EIGHTBITS,
            #parity=serial.PARITY_NONE,
            #stopbits=serial.STOPBITS_TWO,
            timeout=1.0
        )
        
        self.ser.dtr = False

    def setDTR(self, state: bool) -> None:
        self.ser.dtr = state

    def send_command(self, command: bytes, subcommand: bytes = b"", data: bytes = b"") -> None:
        """
        Send a CI-V command frame to the radio.

        Parameters
        ----------
        command : bytes
            The CI-V command number (1 byte).
        subcommand : bytes, optional
            The CI-V subcommand (1–2 bytes), may be omitted.
        data : bytes, optional
            Additional data payload for the command, may be empty.
        """
        payload = command + subcommand + data
        frame = (
            self.PREAMBLE
            + self.radio_addr
            + self.CONTROLLER_ADDR
            + payload
            + self.EOM
        )
        self.ser.write(frame)
        time.sleep(0.05)

    def _read_frame(self) -> bytes:
        """
        Read a single CI-V frame (terminated by EOM).

        Returns
        -------
        bytes
            A complete CI-V frame (including preamble and EOM),
            or an empty bytes object if timeout occurs.
        """
        frame = self.ser.read_until(self.EOM)
        return frame if frame else b""

    def receive_response(self) -> bytes:
        """
        Receive a CI-V response frame, skipping over the echoed command.

        Returns
        -------
        bytes
            The data portion of the CI-V response (after command and subcommand),
            or a single-byte status (0xFB OK / 0xFA NG) if the radio replies with that,
            or an empty bytes object if no valid response is received.
        """
        start_time = time.time()
        while True:
            frame = self._read_frame()
            if not frame:
                break  # timeout, nothing received

            if not frame.startswith(self.PREAMBLE) or len(frame) < 6:
                continue  # malformed or incomplete

            to_addr = frame[2:3]
            from_addr = frame[3:4]

            # Ignore echo (TO=radio, FROM=controller)
            if to_addr == self.radio_addr and from_addr == self.CONTROLLER_ADDR:
                continue

            # Valid response (TO=controller, FROM=radio)
            if to_addr == self.CONTROLLER_ADDR and from_addr == self.radio_addr:
                # Strip off preamble, TO, FROM, and trailing EOM
                body = frame[4:-1]

                # If the radio replied with a single status byte (e.g., 0xFB OK / 0xFA NG), return it.
                if len(body) == 1:
                    return body

                # Normal response includes at least CN + SC followed by data.
                if len(body) < 2:
                    return b""

                # Remove command + subcommand (first 2 bytes) and return remaining data
                return body[2:]

            if time.time() - start_time > 2.0:
                break

        return b""


    def send_and_receive(self, command: bytes, subcommand: bytes = b"", data: bytes = b"") -> bytes:
        """
        Send a CI-V command and wait for the corresponding response.

        Parameters
        ----------
        command : bytes
            The CI-V command number (1 byte).
        subcommand : bytes, optional
            The CI-V subcommand (1–2 bytes), may be omitted.
        data : bytes, optional
            Additional data payload for the command, may be empty.

        Returns
        -------
        bytes
            The received response frame.
        """
        self.send_command(command, subcommand, data)
        return self.receive_response()

    def close(self) -> None:
        """
        Close the serial connection.
        """
        if self.ser.is_open:
            self.ser.close()
