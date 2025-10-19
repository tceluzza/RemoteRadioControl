from CIVSerial import CIVSerial
from CIVCommands import CIVCommandSet
from udp_server import UdpServer

def handle_command(cmd, addr):
    print(f"Received command: '{cmd}' from {addr}")
    command = cmd.split(" ")

    if(len(command) > 2 or len(command) < 1):
        server.send_reply("FA", addr)
        return
    
    result = cmdset.send_command_by_name("FREQUENCY")
    print(result)
    server.send_reply(str(result), addr)

# Example usage
radio = CIVSerial(port='COM4', baudrate=115200, radio_addr=b'\x94')
cmdset = CIVCommandSet(radio)

server = UdpServer(callback=handle_command)
server.start()

try:
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

    while True:
        pass  # Keep the main thread alive
except KeyboardInterrupt:
    server.stop()