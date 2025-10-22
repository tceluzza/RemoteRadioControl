import socket
import json
import logging

from CIVSerial import CIVSerial
from CIVCommands import CIVCommandSet

def load_config():
  """Loads host and port from server_config.json."""
  try:
    with open('server_config.json', 'r') as f:
      config = json.load(f)
      return config['host'], config['port']
  except (FileNotFoundError, KeyError) as e:
    logging.error(f"Error loading server config: {e}")
    return None, None

def run_server():
  """Runs the UDP server."""
  # Configure logging
  logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
  )

  host, port = load_config()
  if not host or not port:
    return

  # Create a UDP socket
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  
  # Bind the socket to the host and port
  server_address = (host, port)
  logging.info(f"Starting UDP server on {host}:{port}")
  sock.bind(server_address)


  # Initialize CIVSerial and CIVCommandSet
  radio = CIVSerial(port='COM4', baudrate=115200, radio_addr=b'\x94')
  cmdset = CIVCommandSet(radio)

  try:
    while True:
      logging.debug("Waiting for a command...")
      data, address = sock.recvfrom(4096)
      instruction = data.decode().strip().upper()
      logging.debug(f"Received instruction '{instruction}' from {address}")

      commands = instruction.split(" ")
      match len(commands):
        case 1:
          cmd = commands[0]
          data = None
        case 2:
          cmd = commands[0]
          data = commands[1]
        case _:
          logging.warning("Invalid command format received.")
          sock.sendto(str("Invalid").encode(), address)
          continue
        
    
      logging.debug(f"Sending command {commands[0]} to radio with data {commands[1]}")
      resp = cmdset.send_command_by_name(cmd, data)
      
      logging.debug(f"received resp from radio: {resp}")
      logging.debug(f"Sending response to UDP Client: {resp}")

      sock.sendto(str(resp).encode(), address)
      logging.debug("Response sent.")


  except KeyboardInterrupt:
    logging.info("Server is shutting down.")
  finally:
    sock.close()

if __name__ == "__main__":
  run_server()