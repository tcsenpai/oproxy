import socket
import threading
import logging
from datetime import datetime
from typing import Tuple, Optional

class TCPHandler:
    def __init__(self, target_host: str, target_port: int):
        self.target_host = target_host
        self.target_port = target_port

    def log_data_content(self, data: bytes, src: tuple, dst: tuple, direction: str, full_debug: bool = False) -> None:
        try:
            # Always log basic info
            logging.info(f"[{direction}] {src[0]}:{src[1]} -> {dst[0]}:{dst[1]} ({len(data)} bytes)")
            
            # Attempt to decode the data
            if all(32 <= byte <= 126 or byte in (9, 10, 13) for byte in data[:100]):
                decoded = data.decode('utf-8', errors='replace')
                if full_debug:
                    # Log the entire payload with clear separators
                    logging.debug("="*50)
                    logging.debug(f"FULL DATA [{direction}] START")
                    logging.debug("="*50)
                    logging.debug(decoded)
                    logging.debug("="*50)
                    logging.debug(f"FULL DATA [{direction}] END")
                    logging.debug("="*50)
                else:
                    # Log just a preview
                    logging.debug(f"Data preview: {decoded[:200]}...")
            else:
                if full_debug:
                    # For binary data, log the full hex dump
                    logging.debug("="*50)
                    logging.debug(f"FULL BINARY DATA [{direction}] START")
                    logging.debug("="*50)
                    logging.debug(' '.join(f'{byte:02x}' for byte in data))
                    logging.debug("="*50)
                    logging.debug(f"FULL BINARY DATA [{direction}] END")
                    logging.debug("="*50)
                else:
                    logging.debug(f"Binary data: {len(data)} bytes transferred")
        except Exception as decode_err:
            logging.debug(f"Could not decode data: {decode_err}")

    def forward(self, source: socket.socket, destination: socket.socket, 
                direction: str, log_data: bool, full_debug: bool = False) -> None:
        total_bytes = 0
        try:
            while True:
                data = source.recv(4096)
                if not data:
                    break
                total_bytes += len(data)
                destination.send(data)
                
                if log_data:
                    src = source.getpeername()
                    dst = destination.getpeername()
                    self.log_data_content(data, src, dst, direction, full_debug)

        except Exception as e:
            logging.error(f"Error in {direction}: {str(e)}")
        finally:
            logging.info(f"Connection closed ({direction}). Total bytes transferred: {total_bytes}")
            try:
                source.close()
                destination.close()
            except:
                pass

    def handle_client(self, client_socket: socket.socket, log_data: bool, full_debug: bool = False) -> None:
        try:
            client_address = client_socket.getpeername()
            logging.info(f"New connection from {client_address[0]}:{client_address[1]}")
            
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.connect((self.target_host, self.target_port))
            logging.info(f"Connected to target {self.target_host}:{self.target_port}")

            client_to_target = threading.Thread(
                target=self.forward,
                args=(client_socket, target_socket, "CLIENT->TARGET", log_data, full_debug),
                name="ClientToTarget"
            )
            target_to_client = threading.Thread(
                target=self.forward,
                args=(target_socket, client_socket, "TARGET->CLIENT", log_data, full_debug),
                name="TargetToClient"
            )

            client_to_target.start()
            target_to_client.start()

            client_to_target.join()
            target_to_client.join()
            
        except Exception as e:
            logging.error(f"Error in handle_client: {str(e)}")
            try:
                client_socket.close()
            except:
                pass