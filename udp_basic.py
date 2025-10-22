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
    level=logging.DEBUG,
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
  sock.settimeout(5.0)


  # Initialize CIVSerial and CIVCommandSet
  radio = CIVSerial(port='COM4', baudrate=115200, radio_addr=b'\x94')
  cmdset = CIVCommandSet(radio)

  try:
    logging.info("Awaiting commands...")
    while True:
      try:
        data, address = sock.recvfrom(4096)
      except:
        # No data received, continue loop and check for interrupt
        logging.debug(f"No instruction.")
        continue

      instruction = data.decode().strip().upper()
      logging.info(f"Received instruction '{instruction}' from {address}")

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
      
      logging.debug(f"Sending command {cmd} to radio with data {data}")
      try:
        resp = cmdset.send_command_by_name(cmd, data)
      except:
        logging.error(f"Error with command {cmd} and data {data}")
        resp = "Error"
      
      logging.debug(f"Received response from radio: {resp}. Sending to client.")

      sock.sendto(str(resp).encode(), address)
      logging.debug("Response sent to client.")


  except KeyboardInterrupt:
    logging.info("Keyboard interrupt received.")
  finally:
    logging.info("Server is shutting down.")
    sock.close()

if __name__ == "__main__":
  run_server()