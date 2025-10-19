import socket
import json
import time

class UdpClient:
  """
  A UDP client class for sending commands and receiving responses.
  """
  def __init__(self, config_file='client_config.json', timeout=5):
    """
    Initializes the client by loading configuration and creating a socket.
    
    Args:
      config_file (str): The path to the client configuration file.
      timeout (int): The socket timeout in seconds.
    """
    self.config_file = config_file
    self.timeout = timeout
    # self.server_address = None
    # self.sock = None
    self._load_config()
    self._create_socket()

  def _load_config(self):
    """Loads server host and port from the config file."""
    # try:
    with open(self.config_file, 'r') as f:
      config = json.load(f)
      host = config['server_host']
      port = config['server_port']
      self.server_address = (host, port)
      print(f"Loaded server address from config: {host}:{port}")
    # except (FileNotFoundError, KeyError) as e:
    #   print(f"Error loading client config: {e}")
    #   self.server_address = None

  def _create_socket(self):
    """Creates and configures the UDP socket."""
    if self.server_address:
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      self.sock.settimeout(self.timeout)

  def send_command(self, command):
    """
    Sends a command to the server and waits for a response.
    
    Args:
      command (str): The command string to send.
      
    Returns:
      str: the server's response.
    """
    if not self.sock:
      return "Client not initialized."

    try:
      self.sock.sendto(command.encode(), self.server_address)
      data, address = self.sock.recvfrom(4096)
      return data.decode()
        
    except socket.timeout:
      return "Timeout"
    except Exception as e:
      print(f"An error occurred: {e}")
      return "Error"

  def close(self):
    """Closes the client socket."""
    if self.sock:
      self.sock.close()
      print("Client socket closed.")

def main():
  """Main function to demonstrate the client."""
  client = UdpClient()
  if not client.server_address:
    return

  try:
    while True:
      command = input("> ").strip()
      if command.lower() == 'exit':
        break

      print(f"Sending command '{command}' to server...")
      response = client.send_command(command)
      print(f"Response: {response}")

      # time.sleep(0.1)
  except KeyboardInterrupt:
    print("Client is shutting down.")
  finally:
    client.close()

if __name__ == "__main__":
  main()